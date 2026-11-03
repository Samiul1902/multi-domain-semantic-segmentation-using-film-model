"""Isolated synthetic fixtures only. No real CSV, checkpoint or execution command."""
import base64
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from scripts.analysis.barr_m1_v1_0d_repaired import contracts as c, authorization as a, analysis as h, storage as s
from scripts.analysis.barr_m1_v1_0d_repaired.__main__ import main


def fixture():
    n = 4957
    ids = [f"synthetic_{i:05}" for i in range(n)]
    domains = np.repeat(list(c.COUNTS), list(c.COUNTS.values()))
    d = np.linspace(-.1, .1, n)
    d[0], d[1] = 0, -1e-10
    sel = np.arange(n) < 1239
    accept = np.arange(n) < 1205
    patients = [f"patient_{i % 267}" if dom == "KUB" else "NOT_AVAILABLE" for i, dom in enumerate(domains)]
    return dict(
        phase25c_oof_labels=pd.DataFrame(dict(sample_id=ids, domain=domains, delta_dice=d,
            global_dice=.5, candidate_refined_dice=.5+d, fold_refiner_checkpoint_sha="a"*64, action_available=1)),
        phase25e_c8_membership=pd.DataFrame(dict(sample_id=ids, selected=sel.astype(int),
            policy_id="C8_lambda0.25_budget0.25", budget=.25, **{"lambda": .25}, action_available=1)),
        phase25f_oof_safety=pd.DataFrame(dict(sample_id=ids, domain=domains, p_accept_oof=accept.astype(float),
            safety_decision_oof=np.where(accept, "ACCEPT_REFINEMENT", "FALLBACK_GLOBAL"))),
        phase25b_dev_metadata=pd.DataFrame(dict(sample_id=ids, domain=domains)),
        patient_grouping=pd.DataFrame(dict(sample_id=ids, patient_id=patients, split="train")))


def small():
    j = pd.DataFrame(dict(sample_id=list("abcdefg"), domain=["BUSI", "ISIC", "KUB", "KUB", "KUB", "KVASIR", "KVASIR"],
                          patient_id=["NOT_AVAILABLE", "NOT_AVAILABLE", "p1", "p1", "p2", "NOT_AVAILABLE", "NOT_AVAILABLE"]))
    values = np.array([0., .2, 0., 0., 1., .1, .1])
    return j, dict(A0=np.zeros(7), A1=values, A8=values/2)


class Authorization(unittest.TestCase):
    def setUp(self):
        # Ephemeral keys exist only in memory inside this test class.
        self.key = Ed25519PrivateKey.generate()
        self.trust = {"test": dict(public_key=self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw), approver="TEST ONLY")}
        self.payload = dict(study_identifier="BARR-M1", classification="DESCRIPTIVE_POLICY_COMPARISON",
            arms=["A0", "A1", "A8"], population="ROUTER_DEVELOPMENT", population_n=4957,
            evaluation_class="IN_SAMPLE", execution_mode="CPU_ONLY_RE_ANALYSIS_ONLY",
            input_shas=c.INPUT_SHAS.copy(), checkpoint_shas=c.CHECKPOINT_SHAS.copy(),
            protocol_sha256=c.PROTOCOL_SHA, erratum_sha256=c.ERRATUM_SHA, exclusions=c.EXCLUSIONS,
            authorization_id="SYNTHETIC-NOT-APPROVAL", authorized_by="TEST ONLY",
            approval_date="2026-10-26T00:00:00Z", expires_at="2026-10-28T00:00:00Z", harness_sha256="b"*64)
        self.now = datetime(2026, 10, 27, tzinfo=timezone.utc)

    def envelope(self):
        return dict(key_id="test", payload=copy.deepcopy(self.payload),
                    signature=base64.b64encode(self.key.sign(c.canonical(self.payload))).decode())

    def verify(self, env=None, **kwargs):
        return a.verify_envelope(self.envelope() if env is None else env, self.trust, "b"*64, now=self.now, **kwargs)

    def test_signed_synthetic_positive(self):
        self.assertEqual(self.verify(), self.payload)

    def test_unsigned(self):
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_UNSIGNED"):
            self.verify({"payload": self.payload})

    def test_missing(self):
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_UNSIGNED"):
            a.verify_envelope(None, self.trust, "b"*64)

    def test_forged_signature(self):
        env = self.envelope(); env["signature"] = base64.b64encode(bytes(64)).decode()
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_SIGNATURE_INVALID"):
            self.verify(env)

    def test_modified_payload(self):
        env = self.envelope(); env["payload"]["authorization_id"] = "altered"
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_SIGNATURE_INVALID"):
            self.verify(env)

    def test_untrusted_signer(self):
        env = self.envelope(); env["key_id"] = "unknown"
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_SIGNATURE_INVALID"):
            self.verify(env)

    def test_absent_trust(self):
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_TRUST_ANCHOR_ABSENT"):
            a.verify_envelope(self.envelope(), {}, "b"*64)

    def test_production_cannot_use_test_signature(self):
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_TRUST_ANCHOR_ABSENT"):
            a.production_authorization(self.envelope())

    def test_revoked_id(self):
        with self.assertRaises(c.Refusal):
            self.verify(revoked_ids={self.payload["authorization_id"]})

    def test_revoked_key(self):
        with self.assertRaises(c.Refusal):
            self.verify(revoked_keys={"test"})

    def test_missing_required_field(self):
        del self.payload["authorization_id"]
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_SCOPE_MISMATCH"):
            self.verify()

    def test_payload_cannot_supply_trust_anchor(self):
        env = self.envelope(); env["public_key"] = "self supplied"
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_SCOPE_MISMATCH"):
            self.verify(env)

    def test_bad_signature_encoding(self):
        env = self.envelope(); env["signature"] = "!not base64!"
        with self.assertRaisesRegex(c.Refusal, "E_AUTHORIZATION_SIGNATURE_INVALID"):
            self.verify(env)


def auth_negative(name, key, value, code="E_AUTHORIZATION_SCOPE_MISMATCH"):
    def test(self):
        self.payload[key] = value
        with self.assertRaisesRegex(c.Refusal, code):
            self.verify()
    setattr(Authorization, "test_" + name, test)


for name, key, value in [
    ("other_study", "study_identifier", "BARR-M2"), ("other_arms", "arms", ["A7", "A8"]),
    ("other_population", "population_n", 4000), ("wrong_mode", "execution_mode", "INFERENCE"),
    ("missing_input_sha", "input_shas", {}), ("missing_checkpoint_sha", "checkpoint_shas", {}),
    ("wrong_protocol", "protocol_sha256", "f"*64), ("missing_exclusions", "exclusions", []),
    ("expired", "expires_at", "2026-10-26T00:00:00Z"), ("invalid_date", "approval_date", "invalid"),
    ("future_date", "approval_date", "2026-10-28T00:00:00Z"), ("wrong_approver", "authorized_by", "SELF")]:
    auth_negative(name, key, value)
auth_negative("other_harness", "harness_sha256", "f"*64, "E_AUTHORIZATION_HARNESS_SHA_MISMATCH")


class Arrays(unittest.TestCase):
    def test_complete_synthetic_pipeline_and_commit(self):
        result = h.analyze_frames(fixture())
        self.assertEqual(len(result["per_case"]), 4957)
        self.assertEqual(set(result["paired_contrasts"]), {"A8-A0", "A8-A1", "A1-A0"})
        self.assertEqual(result["evaluation"], "IN_SAMPLE")
        with tempfile.TemporaryDirectory() as tmp:
            binding = dict(input_shas=c.INPUT_SHAS, checkpoint_shas=c.CHECKPOINT_SHAS,
                           authorization_id="SYNTHETIC-NOT-APPROVAL", harness_sha256=c.bundle_sha())
            p = s.commit(tmp, binding, result)
            self.assertEqual(p, s.commit(tmp, binding, result))

    def test_positive_and_execution_counts(self):
        j = h.validate_population(fixture()); arms, sel, acc = h.construct_deltas(j)
        stats = h.statistics(arms, j)
        self.assertEqual((sel.sum(), acc.sum()), (1239, 1205))
        self.assertEqual(stats["A8"]["n_candidate_executed"], 1239)
        self.assertEqual(stats["A8"]["n_accepted"], 1205)
        self.assertEqual(stats["A8"]["n_rejected"], 34)
        self.assertEqual(stats["A0"]["n_candidate_executed"], 0)
        self.assertEqual(stats["A1"]["n_candidate_executed"], 4957)

    def test_row_permutation_keyed_join(self):
        f = fixture(); expected = h.validate_population(f)
        shuffled = {k: v.sample(frac=1, random_state=i) for i, (k, v) in enumerate(f.items())}
        pd.testing.assert_frame_equal(expected, h.validate_population(shuffled))

    def test_unsafe_positional_domain_mismatch(self):
        f = fixture(); f["phase25c_oof_labels"]["sample_id"] = f["phase25c_oof_labels"].sample_id.iloc[::-1].to_numpy()
        with self.assertRaisesRegex(c.Refusal, "E_DOMAIN_IDENTITY"):
            h.validate_population(f)

    def test_nonzero_skip(self):
        j = h.validate_population(fixture()); arms, sel, acc = h.construct_deltas(j)
        arms["A8"][~acc] = .1
        with self.assertRaisesRegex(c.Refusal, "E_STRUCTURAL_ZERO"):
            h.validate_deltas(arms, j, sel, acc)

    def test_harm_boundaries(self):
        result = h.harm(np.array([-.1, -1e-10, -1e-9, 0, .1]), 4)
        self.assertEqual(result["strict"]["count"], 3)
        self.assertEqual(result["tolerance_adjusted"]["count"], 1)
        self.assertEqual(result["strict"]["rate_all"], 3/5)
        self.assertEqual(result["strict"]["rate_conditional"], 3/4)

    def test_pooled_not_macro(self):
        j, arms = small(); values = arms["A1"]
        with self.assertRaisesRegex(c.Refusal, "E_MACRO_ESTIMAND"):
            h.validate_macro(float(values.mean()), values, j.domain.to_numpy())
        h.validate_macro((0 + .2 + 1/3 + .1)/4, values, j.domain.to_numpy())

    def test_cluster_multiplicity(self):
        j, arms = small()
        class Deterministic:
            def choice(self, items, count, replace):
                return np.array([0, 0]) if isinstance(items, int) else np.resize(items, count)
        ix = h.resample_indices(j, Deterministic())["KUB"]
        np.testing.assert_array_equal(ix, [2, 3, 2, 3])
        self.assertEqual(arms["A1"][ix].mean(), 0)
        self.assertNotEqual(arms["A1"][ix].mean(), arms["A1"][[2, 3, 4]].mean())

    def test_incorrect_case_resampling_refused(self):
        j, _ = small()
        sample = h.resample_indices(j, np.random.default_rng(42))
        sample["KUB"] = np.array([2, 2, 4])
        with self.assertRaisesRegex(c.Refusal, "E_KUB_CLUSTER_SPLIT"):
            h.validate_resample(j, sample)

    def test_bootstrap_reproducible_and_order_invariant(self):
        j, arms = small(); first = h.bootstrap(arms, j)
        self.assertEqual(first, h.bootstrap(arms, j))
        order = np.array([6, 1, 4, 0, 5, 2, 3])
        self.assertEqual(first, h.bootstrap({k: v[order] for k, v in arms.items()}, j.iloc[order]))
        self.assertEqual(first["A8-A0"]["replicates"], 2000)
        np.testing.assert_allclose(first["A8-A0"]["macro_ci95"], np.array(first["A1-A0"]["macro_ci95"])/2)


def array_negative(name, mutate, code):
    def test(self):
        frames = fixture(); mutate(frames)
        with self.assertRaisesRegex(c.Refusal, code):
            h.validate_population(frames)
    setattr(Arrays, "test_" + name, test)


def set_column(frames, source, name, value):
    frame = frames[source]
    frame[name] = value


array_negative("K_zero", lambda f: set_column(f, "phase25e_c8_membership", "selected", 0), "E_A8_K")
array_negative("K_wrong", lambda f: f["phase25e_c8_membership"].loc.__setitem__((0, "selected"), 0), "E_A8_K")
array_negative("budget_override", lambda f: set_column(f, "phase25e_c8_membership", "budget", .3), "E_CONFIG_FROZEN")
array_negative("wrong_count", lambda f: f.__setitem__("phase25c_oof_labels", f["phase25c_oof_labels"].iloc[:-1]), "E_POPULATION_COUNT")
array_negative("duplicate_id", lambda f: f["phase25c_oof_labels"].loc.__setitem__((0, "sample_id"), "synthetic_00001"), "E_SAMPLE_ID_DUPLICATE")
array_negative("missing_id", lambda f: f["phase25c_oof_labels"].loc.__setitem__((0, "sample_id"), None), "E_SAMPLE_ID_MISSING")
array_negative("different_id", lambda f: f["phase25e_c8_membership"].loc.__setitem__((0, "sample_id"), "other"), "E_POPULATION_IDENTITY")
array_negative("missing_patient", lambda f: set_column(f, "patient_grouping", "patient_id", "NOT_AVAILABLE"), "E_KUB_PATIENT_ID")
array_negative("malformed_patient", lambda f: set_column(f, "patient_grouping", "patient_id", "bad patient"), "E_KUB_PATIENT_ID")
array_negative("missing_checkpoint", lambda f: set_column(f, "phase25c_oof_labels", "fold_refiner_checkpoint_sha", ""), "E_CHECKPOINT_SHA_MISSING")
array_negative("accepted_partition", lambda f: f["phase25f_oof_safety"].loc.__setitem__((0, ["safety_decision_oof", "p_accept_oof"]), ["FALLBACK_GLOBAL", 0]), "E_A8_PARTITION")
array_negative("nan_delta", lambda f: f["phase25c_oof_labels"].loc.__setitem__((0, "delta_dice"), np.nan), "E_INPUT_VALUE")
array_negative("ineligible_selected", lambda f: f["phase25e_c8_membership"].loc.__setitem__((0, "action_available"), 0), "E_MEMBERSHIP_ELIGIBILITY")
array_negative("protected_population", lambda f: set_column(f, "patient_grouping", "split", "TEST"), "E_POPULATION_PROTECTED")


class Boundaries(unittest.TestCase):
    def test_frozen_gate_bytes(self):
        self.assertEqual(c.digest(c.GATE.read_bytes()), c.GATE_SHA)

    def test_missing_K_config(self):
        config = copy.deepcopy(c.CONFIG); del config["K"]
        with self.assertRaisesRegex(c.Refusal, "E_CONFIG_FROZEN"):
            c.validate_config(config, {})

    def test_config_positive(self):
        self.assertEqual(c.validate_config(copy.deepcopy(c.CONFIG), {}), c.CONFIG)

    def test_environment_override(self):
        with self.assertRaisesRegex(c.Refusal, "E_CONFIG_ENV_OVERRIDE"):
            c.validate_config(c.CONFIG, {"BARR_M1_K": "0"})

    def test_invalid_cli_override(self):
        with self.assertRaises(SystemExit) as error:
            main(["--K", "0"])
        self.assertEqual(error.exception.code, 2)

    def test_execute_disabled_direct_function_only(self):
        # A unit test of dispatch, not a shell scientific execution command.
        with patch.object(a, "verify_envelope", return_value={"approved": True}):
            self.assertEqual(main(["--execute"]), 2)

    def test_real_loader_disabled(self):
        with self.assertRaisesRegex(c.Refusal, "E_EXECUTION_DISABLED"):
            h.load_production_sources()

    def test_verified_synthetic_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = b"sample_id,value\nsynthetic,1\n"
            (Path(tmp)/"fixture.csv").write_bytes(data)
            self.assertEqual(len(h.verified_csv(tmp, "fixture.csv", c.digest(data), {"fixture.csv"})), 1)
            with self.assertRaisesRegex(c.Refusal, "E_INPUT_SHA_MISMATCH"):
                h.verified_csv(tmp, "fixture.csv", "0"*64, {"fixture.csv"})
            with self.assertRaisesRegex(c.Refusal, "E_INPUT_SHA_MISSING"):
                h.verified_csv(tmp, "fixture.csv", None, {"fixture.csv"})

    def test_unknown_path(self):
        with self.assertRaisesRegex(c.Refusal, "E_PATH_UNAUTHORIZED"):
            h.checked_path(".", "unknown.csv", {"fixture.csv"})


for field, value in [("K", 0), ("K", 1200), ("budget", .5), ("n", 0), ("population", "TEST"), ("seed", 1), ("bootstrap_reps", 2)]:
    def _config_case(self, field=field, value=value):
        config = copy.deepcopy(c.CONFIG); config[field] = value
        with self.assertRaisesRegex(c.Refusal, "E_CONFIG_FROZEN"):
            c.validate_config(config, {})
    setattr(Boundaries, "test_config_"+field+"_"+str(value).replace(".", "_"), _config_case)
for path in ["TEST/data.csv", "ROUTER_HOLDOUT/data.csv", "external/data.csv", "checkpoints/model.pt", "../data.csv"]:
    def _path_case(self, path=path):
        with self.assertRaises(c.Refusal):
            h.checked_path(".", path, {path})
    setattr(Boundaries, "test_path_"+path.replace("/", "_").replace(".", "_"), _path_case)


class Restart(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binding = dict(input_shas=c.INPUT_SHAS, checkpoint_shas=c.CHECKPOINT_SHAS,
                            authorization_id="SYNTHETIC", harness_sha256="b"*64)
        self.result = dict(per_case=[dict(sample_id="synthetic_1", A0=0)], per_domain={}, contrasts={})

    def test_idempotent_resume(self):
        p = s.commit(self.root, self.binding, self.result)
        before = p.stat().st_mtime_ns
        self.assertEqual(p, s.commit(self.root, self.binding, self.result))
        self.assertEqual(before, p.stat().st_mtime_ns)

    def test_concurrent_resume_refused(self):
        lock = self.root / (c.digest(c.canonical(self.binding)) + ".lock")
        with s.exclusive_run_lock(lock):
            with self.assertRaisesRegex(c.Refusal, "E_OUTPUT_CONCURRENT_OR_CONFLICT"):
                s.commit(self.root, self.binding, self.result, recover=True)

    def test_corrupt_committed(self):
        p = s.commit(self.root, self.binding, self.result); p.write_bytes(b"broken")
        with self.assertRaisesRegex(c.Refusal, "E_OUTPUT_CORRUPT"):
            s.commit(self.root, self.binding, self.result, recover=True)

    def test_truncated_committed(self):
        p = s.commit(self.root, self.binding, self.result)
        p.write_bytes(p.read_bytes()[:30])
        with self.assertRaisesRegex(c.Refusal, "E_OUTPUT_CORRUPT"):
            s.commit(self.root, self.binding, self.result, recover=True)

    def test_conflicting_result(self):
        s.commit(self.root, self.binding, self.result)
        self.result["per_case"][0]["A0"] = 1
        with self.assertRaisesRegex(c.Refusal, "E_OUTPUT_CONFLICT"):
            s.commit(self.root, self.binding, self.result)

    def test_duplicate_case(self):
        self.result["per_case"] *= 2
        with self.assertRaisesRegex(c.Refusal, "E_SAMPLE_ID_DUPLICATE"):
            s.commit(self.root, self.binding, self.result)

    def test_missing_input_binding(self):
        self.binding["input_shas"] = {}
        with self.assertRaisesRegex(c.Refusal, "E_OUTPUT_INPUT_SHA"):
            s.commit(self.root, self.binding, self.result)

    def test_corrupt_partial(self):
        p = self.root / (c.digest(c.canonical(self.binding)) + ".partial"); p.write_bytes(b"corrupt")
        with self.assertRaisesRegex(c.Refusal, "E_PARTIAL_CONFLICT"):
            s.commit(self.root, self.binding, self.result, recover=True)


# The helper below is bound onto ``Restart`` under a ``test_interruption_*`` name and
# must NOT itself be named ``test``: a module-level function called ``test`` is
# collected by pytest in its own right, and its first parameter ``self`` is then read
# as a fixture request, which errors at setup with "fixture 'self' not found".
for point in ["before_write", "during_write", "before_commit", "after_commit"]:
    def _interruption_case(self, point=point):
        def crash(observed):
            if observed == point:
                raise RuntimeError("synthetic interruption")
        with self.assertRaisesRegex(RuntimeError, "synthetic interruption"):
            s.commit(self.root, self.binding, self.result, fault=crash)
        if point in {"during_write", "before_commit"}:
            with self.assertRaisesRegex(c.Refusal, "E_PARTIAL_RECOVERY_REQUIRED"):
                s.commit(self.root, self.binding, self.result)
        p = s.commit(self.root, self.binding, self.result, recover=True)
        self.assertEqual(p.read_bytes(), s.encode_result(self.binding, self.result))
        self.assertEqual(p, s.commit(self.root, self.binding, self.result))
    setattr(Restart, "test_interruption_" + point, _interruption_case)


if __name__ == "__main__":
    unittest.main()
