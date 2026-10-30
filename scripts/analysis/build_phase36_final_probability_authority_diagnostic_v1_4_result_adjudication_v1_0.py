"""Builder: Phase36 final-probability-authority diagnostic v1.4 RESULT ADJUDICATION v1.0.

STATIC / EXISTING-EVIDENCE FORENSICS ONLY.

This builder does NOT execute the v1.4 diagnostic, does NOT read checkpoint weights,
does NOT read the VAL image, does NOT read VAL ground truth, does NOT read the TEST
split, does NOT read the ROUTER_HOLDOUT split, does NOT run perturbations, does NOT
retry v1.4, does NOT create v1.15, does NOT start Phase37.  It only re-hashes frozen
evidence already on disk and writes ONE write-once adjudication artifact recording the
adjudicated conclusions for:

  * D61  - canonical ACCEPT-fusion repair proof freeze (D61 repaired + reproduced).
  * D75  - final-scoring-representation boundary adjudication + minimal v1.15 policy.
  * Journal 29 -> 31 reconciliation (post-RESULT-snapshot result-write BEGIN/COMPLETE).
  * Frozen-source preservation re-hash.

Write-once semantics: os.O_CREAT | os.O_EXCL | os.O_WRONLY (+ O_BINARY on Windows),
full-write loop, os.fsync, post-write st_size check.  Refuses to overwrite.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

AUDIT_DIR = ROOT / "reports" / "audits"
JOURNAL_DIR = AUDIT_DIR / "phase36_final_probability_authority_diagnostic_v1_4_journal"

OUT_PATH = AUDIT_DIR / "phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_v1_0.json"


# --------------------------------------------------------------------------- #
# Frozen identifiers
# --------------------------------------------------------------------------- #
DECISION_ID = "D75"
ADJUDICATION_KIND = "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_4_RESULT_ADJUDICATION"

# 7 source pins + 7 governance pins = 14-pin family (canonical disjoint ids).
SOURCE_PINS = {
    "diagnostic": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_4.py",
        "778af67fe41e44cec0717365b2c3427bcfd43442145af09a7aca2abe1f4a3eab",
    ),
    "launcher": (
        "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_4.py",
        "221a15a1f2dd341c59a65d9f8c0f57f4e339ff5a66f8bece6c7b2a5d8ad10a0a",
    ),
    "supervisor": (
        "scripts/analysis/supervise_phase36_final_probability_authority_diagnostic_v1_4.py",
        "792302085ccde4f09bfc7d3ca6534f411a9b776b54cbca5b83e8a7ad02277c2b",
    ),
    "unit": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_4.py",
        "a4f1ddb854847435388e1dd9984812bc0b295c42443f63c76ac5d55c01b34738",
    ),
    "preflight": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_4.py",
        "bb14fca6f9344459f9c812d61de6c1abf90fd5fe7d8a966d46a6ca10fbadc1ec",
    ),
    "negative_controls": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.py",
        "492c03fd231969dc80347713c3106c7970854d060d2d5780e285ffbac8372256",
    ),
    "builder": (
        "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_4.py",
        "ec5432ac875580b331a9e2e5910499d15c41f30de843c01e589005d9ea8fb29b",
    ),
}

GOVERNANCE_PINS = {
    "contract": (
        "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_4.json",
        "1052946e87b9060bec5e06488569ab06b1cb85cf52d2969e2876a4a7355d5a57",
    ),
    "source_freeze": (
        "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_4.json",
        "ff1d23e11da61645cc117bbc0e7674b680056c83164cad9266beb24d6c5e0ba0",
    ),
    "preflight": (
        "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_4.json",
        "224cf6d1f108119caf3ce365bfa4cfe36945d0fd4a7d334e472f2b3e7cd32006",
    ),
    "negative_controls": (
        "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.json",
        "fe35ac673bca59e6bcb20900f4c541f283ba3bc6aaf3bf8b4e82ba537a08bcb2",
    ),
    "eligibility": (
        "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_4.json",
        "9ba0c2fd94c6d5d7d29b50430b2c78d13e48e7003725c80cac2012b6ddb1ad11",
    ),
    "no_execution_audit": (
        "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_4.json",
        "09feb4bfc9e7c9ffa157a3afb93a0d9085e462d4b6c2bc3676295d03f3c80a37",
    ),
    "v1_3_to_v1_4_diff": (
        "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_to_v1_4_diff.json",
        "ccffd91d4dff41a6ea4d9a6be3c66237e5c17a4cc6bb92103e122eb9dbae8ee2",
    ),
}

ATTEMPT_ARTIFACTS = {
    "START": (
        "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_4.json",
        "298f56414eaa39281e8dfaf33faa5e1260d6e7708ae5bfe5f850bcf04520caca",
    ),
    "RESULT": (
        "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_4.json",
        "046a1e3c3053fb00b97895d8d1834d0011f8b190209daa01795e6915b7fd5284",
    ),
    "PROCESS_EXIT": (
        "reports/audits/phase36_final_probability_authority_diagnostic_process_exit_v1_4.json",
        "7475ce8c8a6abfc7f8697a1682ec3a93f22178503bb342ef52569175ca8061e2",
    ),
    "STDOUT": (
        "reports/audits/phase36_final_probability_authority_diagnostic_stdout_v1_4.txt",
        "822adf6b61ff8b4cdec307d5d755cb83b3cc583dcf2de4dd94f3fb9be548b393",
    ),
    "STDERR": (
        "reports/audits/phase36_final_probability_authority_diagnostic_stderr_v1_4.txt",
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    ),
}

# FAILURE must be ABSENT.
FAILURE_REL = "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_4.json"

PRIOR_GOVERNANCE_ARTIFACTS = {
    "D72_attestation": (
        "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_final_readiness_attestation_v1_0.json",
        "4cffd388f6fbdacf15abc2d5984c8cad9e6f186c7a3d8137c796a53b6b96db27",
    ),
    "D73_D74_reconciliation": (
        "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_final_readiness_attestation_reconciliation_v1_1.json",
        "0448876bec3b18da87a77e8b64a6c4ba5fe36c9f62b0cf4687a4d7d3012b3279",
    ),
}

SCIENTIFIC_TARGETS = {
    "phase27_final_prob_f16": (
        "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy",
        "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf",
    ),
    "phase27_global_prob_f16": (
        "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy",
        "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13",
    ),
    "phase27_per_sample_scores": (
        "reports/tables/phase27_val808_per_sample_scores.csv",
        "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12",
    ),
}


def sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_map(pins: dict) -> dict:
    out = {}
    for k, (rel, exp) in pins.items():
        p = ROOT / rel
        actual = sha256_file(p)
        out[k] = {
            "path": rel,
            "sha256_expected": exp,
            "sha256_actual": actual,
            "match": (actual == exp),
        }
    return out


def write_once(path: Path, payload: bytes) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags)
    try:
        written = 0
        while written < len(payload):
            n = os.write(fd, payload[written:])
            if n <= 0:
                raise IOError("short write")
            written += n
        os.fsync(fd)
    finally:
        os.close(fd)
    st = os.stat(str(path))
    if st.st_size != len(payload):
        raise IOError(
            f"post-write size mismatch: {st.st_size} != {len(payload)}"
        )


def main() -> int:
    if OUT_PATH.exists():
        print(f"REFUSE_OVERWRITE: {OUT_PATH} already exists")
        return 2

    # ---- Section 11: source preservation re-hash -------------------------- #
    src_map = hash_map(SOURCE_PINS)
    gov_map = hash_map(GOVERNANCE_PINS)
    attempt_map = hash_map(ATTEMPT_ARTIFACTS)
    prior_map = hash_map(PRIOR_GOVERNANCE_ARTIFACTS)
    target_map = hash_map(SCIENTIFIC_TARGETS)

    n_expected = len(SOURCE_PINS) + len(GOVERNANCE_PINS)
    all_pins_match = all(v["match"] for v in src_map.values()) and all(
        v["match"] for v in gov_map.values()
    )
    attempt_ok = all(v["match"] for v in attempt_map.values())
    prior_ok = all(v["match"] for v in prior_map.values())
    target_ok = all(v["match"] for v in target_map.values())
    failure_absent = not (ROOT / FAILURE_REL).exists()

    # ---- Section 10: journal reconciliation ------------------------------- #
    journal_files = sorted(p.name for p in JOURNAL_DIR.iterdir() if p.is_file())
    journal_hashes = {}
    journal_chains = {}
    for name in journal_files:
        p = JOURNAL_DIR / name
        journal_hashes[name] = sha256_file(p)
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            rec = {}
        aid = rec.get("attempt_id") or rec.get("attempt", {}).get("attempt_id")
        journal_chains.setdefault(aid, []).append(name)

    journal_snapshot_records = len(journal_files)  # 31 on disk
    # RESULT internally reported 29 (records_written).
    journal_final_records = 29
    extra = sorted(
        name
        for name in journal_files
        if name.startswith("029_101_result_write") or name.startswith("030_101_result_write")
    )
    if journal_snapshot_records == 31 and journal_final_records == 29 and len(extra) == 2:
        journal_class = "EXPECTED_POST_RESULT_SNAPSHOT_COMPLETION"
    else:
        journal_class = "UNRESOLVED"

    payload = {
        "artifact_kind": ADJUDICATION_KIND,
        "revision": "v1.0",
        "decision_ids": ["D61", "D75", "JOURNAL_29_TO_31"],
        "purpose": (
            "Static, existing-evidence-only adjudication of the consumed successful v1.4 "
            "first attempt. Freeze the D61 canonical ACCEPT-fusion repair proof; adjudicate "
            "the D75 final-scoring-representation boundary; determine the minimal v1.15 "
            "repair policy (POLICY_A vs POLICY_B); reconcile the journal record count 29->31; "
            "re-verify frozen-source preservation. NO execution, NO retry, NO new science."
        ),
        "execution_scope": "STATIC_NON_CONSUMING_EXISTING_EVIDENCE_ONLY",

        # ---- Section 2/3: attempt state --------------------------------- #
        "attempt_state": {
            "classification": "CONSUMED_RESULT",
            "attempt_id": "v1_4_29980_2026-10-10T09:56:09Z",
            "authorized_attempt": True,
            "retry_permitted": False,
            "post_execution_retry_forbidden": True,
            "failure_artifact_absent": failure_absent,
            "stderr_empty": (
                attempt_map["STDERR"]["sha256_actual"]
                == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            ),
        },

        # ---- Section 11: frozen-source preservation --------------------- #
        "source_preservation": {
            "n_expected_pins": n_expected,
            "n_source_pins": len(SOURCE_PINS),
            "n_governance_pins": len(GOVERNANCE_PINS),
            "source_pins": src_map,
            "governance_pins": gov_map,
            "all_14_pins_match": all_pins_match,
            "post_run_14_pins_unchanged": all_pins_match,
            "attempt_artifacts": attempt_map,
            "attempt_artifacts_match": attempt_ok,
            "prior_governance_artifacts": prior_map,
            "prior_governance_artifacts_match": prior_ok,
            "scientific_targets": target_map,
            "scientific_targets_match": target_ok,
        },

        # ---- Section 4: D61 repair-proof freeze ------------------------- #
        "D61_proof_freeze": {
            "classification": (
                "D61_CANONICAL_FUSION_REPAIR_REPRODUCES_PHASE27_FINAL_AUTHORITY"
            ),
            "d61_repair_classification": "D61_CANONICAL_ACCEPT_FUSION_REPAIR",
            "canonical_accept_call": "fuse_full_field(p_global, refined, geom)",
            "old_accept_call_absent": True,
            "uses_same_geom_from_canonical_roi_path": True,
            "uses_same_refined_from_canonical_r_psi": True,
            "replay_token": "PHASE36_FINAL_PROB_AUTHORITY_V1_4_D61_REPAIR_PROOF_REPLAY",
            "final_f16_bit_identical_all": True,
            "total_f16_element_mismatch_count": 0,
            "max_abs_f16_difference": 0.0,
            "n_samples_with_any_f16_difference": 0,
            "affected_sample_ids": [],
            "n_samples": 808,
            "establishes_repaired_clean_final_probability_authority_only": True,
            "does_not_execute_robustness_science": True,
            "not_automatically_g_mismatch": True,
        },

        # ---- Section 5: global G reproduction (bit-identical) ----------- #
        "global_G_reproduction": {
            "reference_path": (
                "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy"
            ),
            "reference_sha256": "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13",
            "preferred": "BIT_IDENTICAL_FLOAT16_PERSISTED_GLOBAL_PROBABILITY",
            "pass": True,
            "bit_identical": True,
            "mismatch_count": 0,
            "max_abs": 0.0,
            "note": (
                "G is reproduced bit-identically; therefore D75 is NOT attributable to the "
                "global G component."
            ),
        },

        # ---- Section 6: protected / science counters -------------------- #
        "protected_counters": {
            "VAL_GT_READ": 0,
            "unique_val_gt": 0,
            "router_holdout_reads": 0,
            "test_reads": 0,
            "metric_evaluations": 0,
            "image_perturbation_instances": 0,
            "proposal_perturbation_instances": 0,
            "training": 0,
            "optimizer_steps": 0,
            "parameter_mutations": 0,
            "perturbation_executed": False,
            "scientific_output": False,
            "nonfinite_samples": {},
            "blocked_gt_calls": [],
        },
        "science_counters": {
            "clean_g_forwards": 808,
            "b_phi_forwards": 808,
            "r_psi_forwards": 279,
            "s_omega_forwards": 279,
            "final_probability_passes": 808,
            "clean_passes": 808,
            "clean_g_reproduction_gate_invocations": 1,
        },

        # ---- Section 7/8/9: D75 boundary + scoring semantics ------------ #
        "D75_boundary": {
            "segmentation_output_threshold": 0.50,
            "f16_half": 0.5,
            "live_vs_self_f16_threshold_flip_count": 954,
            "self_f16_vs_phase27_f16_threshold_mismatch_count": 0,
            "live_vs_phase27_threshold_mismatch_count": 954,
            "n_pixels_generated_f16_eq_half_total": 2815,
            "n_measured_q_live_below_half_total": 954,
            "n_samples_live_f32_bit_equal_to_bound_f16": 0,
        },
        "D75_scoring_semantics": {
            "phase27_executed_scientific_result_is_scored_by": (
                "PhaseB run_phase27_exec_phaseB.py: g_bin/f_bin = "
                "(np.asarray(gp[i]/fp[i], dtype=np.float32) >= SEG) where gp/fp are the "
                "PERSISTED float16 caches (loaded under a hash barrier) cast UP to float32 "
                "=> path = f16 -> f32 -> 0.50"
            ),
            "phase27_phaseA_note": (
                "PhaseA run_phase27_exec_phaseA.py writes _final.png masks via live-f32 "
                "thresholding (header: 'Binary decisions are taken in float32 BEFORE any "
                "float16 storage cast') and persists final_prob_f16; these masks were NOT "
                "the scored authority."
            ),
            "v1_14_clean_scoring": (
                "phase36_robustness_execution_v1_14.py _evaluate_clean_sample L2413-2414 "
                "thresholds the LIVE float32 final_probability ((final_prob >= "
                "SEGMENTATION_OUTPUT_THRESHOLD)) => path = live-f32 -> 0.50"
            ),
            "mismatch_root": (
                "v1.14 clean scoring thresholds live-float32, but the historical Phase27 "
                "SCORED authority thresholds the persisted float16 representation cast up "
                "to float32.  Where the f16-rounded value equals exactly 0.5 and the live "
                "f32 value is just below 0.5, the two representations disagree (954 pixels)."
            ),
            "classification": "D75_FINAL_SCORING_REPRESENTATION_BOUNDARY_ADJUDICATED",
        },

        # ---- Section 9: minimal v1.15 repair policy --------------------- #
        "v1_15_repair_policy": {
            "policy": "POLICY_B",
            "policy_definition": (
                "p_final_scored = p_final_live.astype(np.float16).astype(np.float32), then "
                "threshold at 0.50, applied uniformly to ALL Phase36 conditions (clean and "
                "perturbed) so that Phase36 scoring uses the SAME representation as the "
                "historical Phase27 PhaseB scored authority."
            ),
            "policy_A_definition": (
                "Keep live-float32 thresholding (as in v1.14 clean scoring); do NOT change "
                "the scoring representation."
            ),
            "policy_B_is_historically_faithful": True,
            "policy_rationale": (
                "The Phase27 PhaseB scored authority thresholds the persisted float16 "
                "representation (f16 -> f32 -> 0.50).  POLICY_B reproduces that exact "
                "historical scoring semantics; POLICY_A (live-f32) does not.  Because the "
                "diagnostic established that the repaired final probability is BIT-IDENTICAL "
                "to the Phase27 float16 authority (D61 proof), adopting POLICY_B makes the "
                "Phase36 downstream binary/score pipeline byte-consistent with the historical "
                "authority, eliminating the 954-pixel representation boundary."
            ),
            "not_implemented": True,
            "scope": "MINIMAL_SCORING_REPRESENTATION_ONLY__NO_NEW_SCIENCE",
        },

        # ---- Section 10: journal reconciliation ------------------------- #
        "journal_reconciliation": {
            "journal_dir": (
                "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_journal"
            ),
            "journal_snapshot_records": journal_snapshot_records,
            "journal_final_records": journal_final_records,
            "n_extra_records": journal_snapshot_records - journal_final_records,
            "extra_record_names": extra,
            "extra_records_are_result_write_begin_complete": (
                [n for n in extra] == [
                    "029_101_result_write__BEGIN.json",
                    "030_101_result_write__COMPLETE.json",
                ]
            ),
            "journal_29_to_31_classification": journal_class,
            "single_attempt_chain": (len(journal_chains) == 1),
            "attempt_chains": {str(k): v for k, v in journal_chains.items()},
            "file_sha256": journal_hashes,
            "last_durable_stage": "098_gt_and_comparison_gate",
            "last_complete_stage": "098_gt_and_comparison_gate",
            "first_started_not_completed_stage": None,
            "explanation": (
                "RESULT internally records journal.records_written=29 at the moment the "
                "scientific comparison completed (last durable/complete stage "
                "098_gt_and_comparison_gate).  The diagnostic then performs a further "
                "post-RESULT-snapshot step: writing the RESULT artifact itself, journaled as "
                "stage 101_result_write (BEGIN + COMPLETE) = the 2 extra on-disk records, "
                "giving 31 total.  Hence JOURNAL_29_TO_31 = "
                "EXPECTED_POST_RESULT_SNAPSHOT_COMPLETION, not an anomaly."
            ),
        },

        # ---- Section 12: recorded conclusions --------------------------- #
        "recorded_conclusions": {
            "attempt_state": "CONSUMED_RESULT",
            "retry_permitted": False,
            "D61_repaired_and_reproduced": True,
            "G_bit_identical_reproduced": True,
            "D75_boundary_counts_unchanged": {
                "live_vs_self_f16_threshold_flip_count": 954,
                "self_f16_vs_phase27_f16_threshold_mismatch_count": 0,
                "live_vs_phase27_threshold_mismatch_count": 954,
                "n_pixels_generated_f16_eq_half_total": 2815,
                "n_measured_q_live_below_half_total": 954,
                "n_samples_live_f32_bit_equal_to_bound_f16": 0,
            },
            "v1_15_repair_policy": "POLICY_B",
            "journal_29_to_31_classification": journal_class,
            "post_run_14_pins_unchanged": all_pins_match,
            "TEST_accessed": False,
            "ROUTER_HOLDOUT_accessed": False,
            "phase36_completion": "NOT_COMPLETE_PENDING_V1_15",
            "phase37_status": "NOT_STARTED",
        },

        "prohibitions_observed": {
            "no_execution": True,
            "no_checkpoint_deserialization": True,
            "no_val_image_read": True,
            "no_val_gt_read": True,
            "no_test_read": True,
            "no_router_holdout_read": True,
            "no_perturbations": True,
            "no_v1_4_retry": True,
            "no_v1_15_created": True,
            "no_phase37_started": True,
            "no_frozen_content_modified": True,
        },

        "builder_source_sha256": sha256_file(Path(__file__).resolve()),
        "write_semantics": "WRITE_ONCE_O_CREAT_O_EXCL_FSYNC",
    }

    payload_bytes = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    write_once(OUT_PATH, payload_bytes)
    out_sha = sha256_file(OUT_PATH)

    print("ADJUDICATION_WRITTEN")
    print(f"path={OUT_PATH.relative_to(ROOT)}")
    print(f"bytes={len(payload_bytes)}")
    print(f"sha256={out_sha}")
    print(f"builder_sha256={payload['builder_source_sha256']}")
    print(f"all_14_pins_match={all_pins_match}")
    print(f"attempt_artifacts_match={attempt_ok}")
    print(f"prior_governance_artifacts_match={prior_ok}")
    print(f"scientific_targets_match={target_ok}")
    print(f"failure_absent={failure_absent}")
    print(f"journal_snapshot_records={journal_snapshot_records}")
    print(f"journal_29_to_31_classification={journal_class}")
    print("v1_15_repair_policy=POLICY_B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
