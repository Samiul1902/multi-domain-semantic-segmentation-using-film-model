"""Builder: Phase36 v1.4 result-adjudication RECONCILIATION v1.1 (D76 / D77 / D78).

STATIC / EXISTING-EVIDENCE ONLY.

Additive reconciliation of three governance/provenance defects found in the frozen
v1.4 result-adjudication v1.0 family:

  D76 = JOURNAL_SNAPSHOT_FINAL_COUNT_FIELDS_SEMANTICALLY_INVERTED
  D77 = RESULT_ADJUDICATION_BUILDER_VALIDATION_NOT_FAIL_CLOSED
  D78 = D75_SCORING_SOURCE_PROVENANCE_NOT_DURABLY_CONTENT_BOUND

This builder is FAIL-CLOSED: it computes every required authority check and ABORTS
(nonzero, NO artifact written) if ANY required check fails.  The frozen v1.0
adjudication and its builder are NEVER modified.

Prohibitions: NO model run / checkpoint deserialization / VAL image read / VAL GT read /
TEST / ROUTER_HOLDOUT / perturbation / metric execution / v1.4 retry / v1.15
implementation / v1.15 execution / Phase37.  Raw-byte SHA-256 only (Path.read_bytes()).
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

OUT_PATH = (
    AUDIT_DIR
    / "phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_v1_1.json"
)

FROZEN_ADJUDICATION = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_v1_0.json",
    "912cb24e4b27dcc7d66310b36db2154180411ec52d79d19c767aa708220b9b36",
)
FROZEN_BUILDER = (
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_v1_0.py",
    "8c95a6f6c3d9f3735169256d9c6f06bd538ed5ebbba8afb8a96ed72b2e81baf7",
)

# 7 source + 7 governance = 14 v1.4 family pins.
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
FAILURE_REL = "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_4.json"

PRIOR_ARTIFACTS = {
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
    "phase27_final_prob": (
        "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy",
        "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf",
    ),
    "phase27_global_prob": (
        "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy",
        "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13",
    ),
    "phase27_score_csv": (
        "reports/tables/phase27_val808_per_sample_scores.csv",
        "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12",
    ),
}

# Section 7/9: exact scoring-source authorities (path, sha256, span).
SCORING_SOURCES = {
    "phaseA": (
        "scripts/analysis/run_phase27_exec_phaseA.py",
        "ac0ffbdadbfe60349061a926f5a664716a3a3690ac3a90c21a35802263975841",
        "full_field_binary_from_prob",
        "L19, L109, L245-246, L298, L349, L382, L385",
    ),
    "phaseB": (
        "scripts/analysis/run_phase27_exec_phaseB.py",
        "35800e39d9220e638adbb640bd25e18bc14da5298d9bed4a603f2f0dec64cf37",
        "phase B scored loop / g_bin,f_bin",
        "L66, L110-117, L129-133, L142-147",
    ),
    "v1_14": (
        "scripts/analysis/phase36_robustness_execution_v1_14.py",
        "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5",
        "_evaluate_clean_sample",
        "L372, L2391, L2413-2414, L2418-2420",
    ),
}

HISTORICAL_WRONG_SCORE_SHA_PREFIX = "08417a17d"
EXPECTED_JOURNAL_N = 31
EXPECTED_RESULT_SNAPSHOT_N = 29
EXPECTED_CHAIN = "v1_4_29980_2026-10-10T09:56:09Z"
POST_SNAPSHOT_RECORDS = [
    "029_101_result_write__BEGIN.json",
    "030_101_result_write__COMPLETE.json",
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    return sha256_bytes(p.read_bytes())


def check_pins(pins: dict) -> tuple[dict, bool]:
    out = {}
    all_ok = True
    for k, (rel, exp) in pins.items():
        actual = sha256_file(ROOT / rel)
        ok = actual == exp
        all_ok = all_ok and ok
        out[k] = {"path": rel, "sha256_expected": exp, "sha256_actual": actual, "match": ok}
    return out, all_ok


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
        raise IOError(f"post-write size mismatch {st.st_size} != {len(payload)}")


def evaluate_gate(override_expected: dict | None = None) -> dict:
    """Compute ALL required authority checks.  Returns a result dict.

    `override_expected` (used ONLY by negative controls) may mutate one expected
    hash to prove the gate genuinely refuses to write under mismatch.
    """
    ov = override_expected or {}

    def exp(key, default):
        return ov.get(key, default)

    frozen_adj = sha256_file(ROOT / FROZEN_ADJUDICATION[0])
    frozen_bld = sha256_file(ROOT / FROZEN_BUILDER[0])

    checks: dict[str, bool] = {}
    checks["frozen_adjudication_exact"] = frozen_adj == exp(
        "frozen_adjudication", FROZEN_ADJUDICATION[1]
    )
    checks["frozen_builder_exact"] = frozen_bld == exp("frozen_builder", FROZEN_BUILDER[1])

    src_map, src_ok = check_pins(SOURCE_PINS)
    gov_map, gov_ok = check_pins(GOVERNANCE_PINS)
    n_family = len(SOURCE_PINS) + len(GOVERNANCE_PINS)
    # NOTE: SOURCE_PINS and GOVERNANCE_PINS share the keys preflight /
    # negative_controls, so they MUST be counted as disjoint groups — never merged.
    n_src_ok = sum(1 for v in src_map.values() if v["match"])
    n_gov_ok = sum(1 for v in gov_map.values() if v["match"])
    n_family_ok = n_src_ok + n_gov_ok
    checks["v1_4_family_14_14_pins_exact"] = (
        src_ok and gov_ok and n_src_ok == len(SOURCE_PINS) and n_gov_ok == len(GOVERNANCE_PINS)
    )

    att_map, att_ok = check_pins(ATTEMPT_ARTIFACTS)
    checks["START_exact"] = att_map["START"]["match"]
    checks["RESULT_exact"] = att_map["RESULT"]["match"]
    checks["PROCESS_EXIT_exact"] = att_map["PROCESS_EXIT"]["match"]
    checks["STDOUT_exact"] = att_map["STDOUT"]["match"]
    checks["STDERR_exact"] = att_map["STDERR"]["match"]
    checks["FAILURE_absent"] = not (ROOT / FAILURE_REL).exists()

    prior_map, prior_ok = check_pins(PRIOR_ARTIFACTS)
    checks["D72_exact"] = prior_map["D72_attestation"]["match"]
    checks["D73_D74_reconciliation_exact"] = prior_map["D73_D74_reconciliation"]["match"]

    tgt_map, tgt_ok = check_pins(SCIENTIFIC_TARGETS)
    checks["phase27_final_prob_exact"] = tgt_map["phase27_final_prob"]["match"]
    checks["phase27_global_prob_exact"] = tgt_map["phase27_global_prob"]["match"]
    checks["phase27_score_csv_exact"] = tgt_map["phase27_score_csv"]["match"]
    # Positive guard: the bound score CSV sha must equal the canonical good constant
    # AND must NOT begin with the historical wrong prefix.
    _score_sha = tgt_map["phase27_score_csv"]["sha256_actual"] or ""
    checks["historical_wrong_score_sha_not_introduced"] = (
        _score_sha == "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
        and not _score_sha.startswith(exp("wrong_sha_prefix", HISTORICAL_WRONG_SCORE_SHA_PREFIX))
    )

    # Journal.
    journal_files = sorted(p.name for p in JOURNAL_DIR.iterdir() if p.is_file())
    n_journal = len(journal_files)
    checks["journal_count_exactly_31"] = n_journal == exp("journal_n", EXPECTED_JOURNAL_N)

    journal_sha = {}
    chains = set()
    for name in journal_files:
        p = JOURNAL_DIR / name
        journal_sha[name] = sha256_file(p)
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            rec = {}
        chains.add(rec.get("attempt_id"))
    checks["single_attempt_chain"] = (len(chains) == 1) and (
        EXPECTED_CHAIN in chains
    )
    checks["029_result_write_BEGIN_exact"] = (
        POST_SNAPSHOT_RECORDS[0] in journal_files
    ) and exp("j029", True)
    checks["030_result_write_COMPLETE_exact"] = (
        POST_SNAPSHOT_RECORDS[1] in journal_files
    ) and exp("j030", True)

    # Scoring sources.
    src_bindings = {}
    for key, (rel, exp_sha, func, span) in SCORING_SOURCES.items():
        actual = sha256_file(ROOT / rel)
        ok = actual == ov.get("scoring_" + key, exp_sha)
        src_bindings[key] = {
            "path": rel,
            "sha256": actual,
            "sha256_expected": exp_sha,
            "relevant_function": func,
            "relevant_line_span": span,
            "match": ok,
        }
        checks[f"scoring_source_{key}_exact"] = ok

    gate_pass = all(checks.values())
    return {
        "frozen_adjudication_sha256": frozen_adj,
        "frozen_builder_sha256": frozen_bld,
        "source_pins": src_map,
        "governance_pins": gov_map,
        "attempt_artifacts": att_map,
        "prior_artifacts": prior_map,
        "scientific_targets": tgt_map,
        "n_family_pins": n_family,
        "n_family_pins_ok": n_family_ok,
        "journal_files": journal_files,
        "journal_sha256": journal_sha,
        "journal_chains": sorted(str(c) for c in chains),
        "scoring_sources": src_bindings,
        "checks": checks,
        "gate_pass": gate_pass,
    }


def derive_scoring_semantics(ev: dict) -> dict:
    """Mechanically assert the scoring semantics from the BOUND source SHAs.

    Assertions are only marked established when the corresponding source pin matched,
    so POLICY_B can never be asserted on an unbound/absent source.
    """
    s = ev["scoring_sources"]
    phaseA_ok = s["phaseA"]["match"]
    phaseB_ok = s["phaseB"]["match"]
    v114_ok = s["v1_14"]["match"]

    phase27_scored = (
        "PERSISTED_F16__RECAST_F32__THRESHOLD_0_50" if (phaseA_ok and phaseB_ok) else "NOT_ESTABLISHED"
    )
    v114_scored = "LIVE_F32__THRESHOLD_0_50" if v114_ok else "NOT_ESTABLISHED"
    phaseA_live = "LIVE_F32__THRESHOLD_0_50" if phaseA_ok else "NOT_ESTABLISHED"

    policy = (
        "POLICY_B"
        if (phase27_scored == "PERSISTED_F16__RECAST_F32__THRESHOLD_0_50"
            and v114_scored == "LIVE_F32__THRESHOLD_0_50")
        else "NOT_ESTABLISHED"
    )
    d78 = (
        "D75_SCORING_SOURCE_PROVENANCE_BOUND" if policy == "POLICY_B"
        else "D75_SCORING_SOURCE_PROVENANCE_NOT_ESTABLISHED"
    )
    return {
        "phase27_historical_scored_representation": phase27_scored,
        "phase27_phase_a_live_binary_representation": phaseA_live,
        "v1_14_clean_scored_representation": v114_scored,
        "v1_15_repair_policy": policy,
        "policy_B_is_historically_faithful": policy == "POLICY_B",
        "D78": d78,
    }


def build_payload(ev: dict) -> dict:
    sem = derive_scoring_semantics(ev)
    s = ev["scoring_sources"]
    checks = ev["checks"]
    n_journal = len(ev["journal_files"])

    return {
        "artifact_kind": (
            "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_4_RESULT_ADJUDICATION_RECONCILIATION"
        ),
        "revision": "v1.1",
        "decision_ids": ["D76", "D77", "D78"],
        "purpose": (
            "Additive reconciliation of three governance/provenance defects in the frozen "
            "v1.4 result-adjudication v1.0 family: D76 journal field-semantics inversion, "
            "D77 non-fail-closed builder, D78 un-bound D75 scoring-source provenance. "
            "STATIC / existing-evidence only. Preserves all established scientific conclusions."
        ),
        "execution_scope": "STATIC_NON_CONSUMING_EXISTING_EVIDENCE_ONLY",
        "supersedes": None,
        "amends": (
            "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_v1_0.json"
        ),

        # ---- Section 2: frozen family (never modified) ------------------ #
        "frozen_family": {
            "adjudication": {
                "path": FROZEN_ADJUDICATION[0],
                "sha256_expected": FROZEN_ADJUDICATION[1],
                "sha256_actual": ev["frozen_adjudication_sha256"],
                "match": checks["frozen_adjudication_exact"],
            },
            "builder": {
                "path": FROZEN_BUILDER[0],
                "sha256_expected": FROZEN_BUILDER[1],
                "sha256_actual": ev["frozen_builder_sha256"],
                "match": checks["frozen_builder_exact"],
            },
            "overwritten": False,
            "edited": False,
        },

        # ---- Section 3: preserved scientific conclusions ---------------- #
        "D61": "PRESERVED",
        "D75": "PRESERVED",
        "preserved_scientific_conclusions": {
            "attempt_state": "CONSUMED_RESULT",
            "retry_permitted": False,
            "D61_CANONICAL_FUSION_REPAIR_PROOF": "ESTABLISHED",
            "PHASE27_FINAL_AUTHORITY_REPRODUCED_BIT_IDENTICALLY_VAL808": True,
            "final_f16_bit_identical_all": True,
            "total_f16_element_mismatch_count": 0,
            "n_samples_with_any_f16_difference": 0,
            "D75_live_vs_self_f16_threshold_flips": 954,
            "self_f16_vs_phase27_f16_threshold_mismatches": 0,
            "G_persisted_f16_authority": "BIT_IDENTICAL",
            "v1_4_retry": "FORBIDDEN",
            "Phase36": "NOT_COMPLETE_PENDING_V1_15",
            "Phase37": "NOT_STARTED",
        },

        # ---- Section 4: D76 --------------------------------------------- #
        "D76": "JOURNAL_SNAPSHOT_FINAL_COUNT_FIELDS_SEMANTICALLY_INVERTED",
        "D76_status": "RECONCILED",
        "d76_reconciled": True,
        "d76_old_fields": {
            "journal_snapshot_records": 31,
            "journal_final_records": 29,
        },
        "d76_corrected_semantics": {
            "journal_result_snapshot_records": 29,
            "journal_final_on_disk_records": 31,
        },
        "journal_result_snapshot_records": EXPECTED_RESULT_SNAPSHOT_N,
        "journal_final_on_disk_records": n_journal,
        "n_post_snapshot_records": n_journal - EXPECTED_RESULT_SNAPSHOT_N,
        "post_snapshot_records": POST_SNAPSHOT_RECORDS,
        "post_snapshot_records_present": [
            r in ev["journal_files"] for r in POST_SNAPSHOT_RECORDS
        ],
        "post_snapshot_record_sha256": {
            r: ev["journal_sha256"].get(r) for r in POST_SNAPSHOT_RECORDS
        },
        "journal_29_to_31_classification": "EXPECTED_POST_RESULT_SNAPSHOT_COMPLETION",
        "journal_classification_preserved": "EXPECTED_POST_RESULT_SNAPSHOT_COMPLETION",
        "journal_single_attempt_chain": checks["single_attempt_chain"],
        "journal_attempt_chains": ev["journal_chains"],
        "journal_n_records": n_journal,
        "d76_chronology": (
            "RESULT-internal snapshot: records_written=29 (stage 098_gt_and_comparison_gate). "
            "Post-snapshot stage 101_result_write (BEGIN 029 + COMPLETE 030) adds 2 records, "
            "giving 31 final on-disk.  The v1.0 field NAMES were semantically inverted: it "
            "labelled 31 as the 'snapshot' and 29 as the 'final'."
        ),

        # ---- Section 5/6: D77 ------------------------------------------- #
        "D77": "RESULT_ADJUDICATION_BUILDER_VALIDATION_NOT_FAIL_CLOSED",
        "D77_status": "RECONCILED",
        "d77_established": True,
        "original_builder_fail_closed": False,
        "new_reconciliation_builder_fail_closed": True,
        "D77_scientific_semantics_effect": "NONE_FOR_EXISTING_FROZEN_ARTIFACT",
        "D77_governance_effect": "YES",
        "D77_reason": (
            "The frozen v1.0 builder computes all_pins_match / attempt_ok / prior_ok / "
            "target_ok / failure_absent (L218-224) but writes the artifact (L502-503 "
            "write_once) with NO gate on those booleans.  The actual frozen v1.0 artifact "
            "records all-match=true evidence, so the defect does not reverse the existing "
            "result; but the builder would not have failed closed under an input mismatch."
        ),
        "D77_frozen_builder_evidence": {
            "computes_booleans_lines": "L218-L224",
            "ungated_write_lines": "L502-L503",
            "gate_between_present": False,
        },

        # ---- Section 7/8/9: D78 ----------------------------------------- #
        "D78": sem["D78"],
        "D78_status": "RECONCILED" if sem["D78"].endswith("_BOUND") else "NOT_ESTABLISHED",
        "Phase27_PhaseA_source_path": s["phaseA"]["path"],
        "Phase27_PhaseA_source_sha256": s["phaseA"]["sha256"],
        "Phase27_PhaseA_relevant_lines": s["phaseA"]["relevant_line_span"],
        "Phase27_PhaseA_relevant_function": s["phaseA"]["relevant_function"],
        "Phase27_PhaseB_source_path": s["phaseB"]["path"],
        "Phase27_PhaseB_source_sha256": s["phaseB"]["sha256"],
        "Phase27_PhaseB_relevant_lines": s["phaseB"]["relevant_line_span"],
        "Phase27_PhaseB_relevant_function": s["phaseB"]["relevant_function"],
        "v1_14_source_path": s["v1_14"]["path"],
        "v1_14_source_sha256": s["v1_14"]["sha256"],
        "v1_14_relevant_lines": s["v1_14"]["relevant_line_span"],
        "v1_14_relevant_function": s["v1_14"]["relevant_function"],
        "scoring_source_bindings": s,
        "phase27_historical_scored_representation": sem["phase27_historical_scored_representation"],
        "phase27_phase_a_live_binary_representation": sem["phase27_phase_a_live_binary_representation"],
        "v1_14_clean_scored_representation": sem["v1_14_clean_scored_representation"],
        "phaseA_binary_pngs_are_not_authoritative_scoring_representation": True,
        "D78_mechanical_derivation": {
            "phaseB_step1_persisted_caches_loaded": (
                "run_phase27_exec_phaseB.py L129-130: gp = np.load(CACHE27/"
                "phase27_val808_global_prob_f16.npy); fp = np.load(CACHE27/"
                "phase27_val808_final_prob_f16.npy)"
            ),
            "phaseB_step2_stored_dtype_authority_float16": (
                "the loaded arrays carry the persisted float16 dtype (filenames ..._f16.npy; "
                "Phase-A wrote them via np.lib.format.open_memmap(..., dtype=np.float16) L245-246 / "
                "final_prob_f16[gi] = ...astype(np.float16) L385)"
            ),
            "phaseB_step3_elementwise_recast_to_float32": (
                "L142-143: np.asarray(gp[i], dtype=np.float32) / np.asarray(fp[i], dtype=np.float32)"
            ),
            "phaseB_step4_binary_via_ge_0_50": (
                "L142-143: (... >= SEG).astype(np.uint8), where SEG = 0.50 (L66)"
            ),
            "phaseB_step5_binary_used_for_gt_metric_scoring": (
                "L145-147: g_dice = canon_dice(g_bin, gt_bin); f_dice = canon_dice(f_bin, gt_bin) "
                "— the Phase-B binary IS the GT-scored representation (hash barrier L110-117)"
            ),
            "phaseA_separate_behavior": (
                "run_phase27_exec_phaseA.py L19 (header): 'Binary decisions are taken in float32 "
                "BEFORE any float16 storage cast.'  L382: fbin = full_field_binary_from_prob("
                "np.asarray(p_final, dtype=np.float32)); L385 persists final_prob_f16.  Phase-A "
                "_final.png masks use live-f32 and are NOT the authoritative Phase-B scoring "
                "representation."
            ),
            "v1_14_behavior": (
                "phase36_robustness_execution_v1_14.py L2413-2414: final_prob = np.asarray("
                "out['final_probability'], dtype=np.float32); final_binary = (final_prob >= "
                "SEGMENTATION_OUTPUT_THRESHOLD) — live-f32 threshold at 0.50 (L372)."
            ),
        },

        # ---- Section 10/11: policy -------------------------------------- #
        "v1_15_repair_policy": sem["v1_15_repair_policy"],
        "policy_B_is_historically_faithful": sem["policy_B_is_historically_faithful"],
        "policy_A_definition": "retain live-f32 thresholding (v1.14 clean scoring)",
        "policy_B_definition": (
            "p_final_scored = p_final_live.astype(np.float16).astype(np.float32); "
            "then threshold p_final_scored >= 0.50, applied uniformly to clean and "
            "perturbed Phase36 conditions."
        ),
        "policy_B_representation_only": True,
        "policy_B_does_not_alter": [
            "live p_final construction", "G", "router", "ROI", "B_phi", "R_psi",
            "S_omega", "routing state", "safety state", "fusion math",
            "proposal geometry", "perturbation generation", "model checkpoints",
            "network inference", "sample order",
        ],
        "policy_B_implementation_defined_not_executed": {
            "p_scored_f16": "np.asarray(p_final_live, dtype=np.float32).astype(np.float16)",
            "p_scored": "p_scored_f16.astype(np.float32)",
            "binary": "p_scored >= np.float32(0.50)",
        },

        # ---- Effects / state -------------------------------------------- #
        "scientific_semantics_effect": "NONE",
        "governance_provenance_effect": "YES",
        "v1_4_retry_permitted": False,
        "v1_15_created": False,
        "v1_15_executed": False,
        "Phase36_complete": False,
        "Phase36": "NOT_COMPLETE_PENDING_V1_15",
        "Phase37": "NOT_STARTED",
        "TEST_accessed": False,
        "ROUTER_HOLDOUT_accessed": False,

        # ---- Section 14: fail-closed evidence --------------------------- #
        "fail_closed_gate": {
            "all_required_checks": checks,
            "all_required_checks_pass": ev["gate_pass"],
            "n_checks": len(checks),
            "n_checks_pass": sum(1 for v in checks.values() if v),
            "write_precondition": "ALL_REQUIRED_CHECKS_PASS",
            "aborts_before_write_on_failure": True,
        },

        # ---- Ancestor binding ------------------------------------------- #
        "ancestor_binding": {
            "n_family_pins": ev["n_family_pins"],
            "n_family_pins_ok": ev["n_family_pins_ok"],
            "source_pins": ev["source_pins"],
            "governance_pins": ev["governance_pins"],
            "attempt_artifacts": ev["attempt_artifacts"],
            "prior_artifacts": ev["prior_artifacts"],
            "scientific_targets": ev["scientific_targets"],
            "all_frozen_ancestors_unchanged": (
                ev["gate_pass"]
                and ev["n_family_pins_ok"] == ev["n_family_pins"]
                and checks["frozen_adjudication_exact"]
                and checks["frozen_builder_exact"]
            ),
        },

        "prohibitions_observed": {
            "no_v1_4_retry": True, "no_model_execution": True,
            "no_checkpoint_deserialization": True, "no_val_image_read": True,
            "no_val_gt_read": True, "no_test": True, "no_router_holdout": True,
            "no_perturbations": True, "no_metric_execution": True,
            "no_v1_15_implementation": True, "no_v1_15_execution": True,
            "no_phase37": True, "no_overwrite_of_v1_0_adjudication": True,
            "no_overwrite_of_v1_0_builder": True,
            "historical_wrong_phase27_score_sha_not_introduced": True,
        },

        "builder_source_sha256": sha256_file(Path(__file__).resolve()),
        "write_semantics": "WRITE_ONCE_O_CREAT_O_EXCL_FSYNC_FAIL_CLOSED",
    }


def main(argv: list[str]) -> int:
    # Optional negative-control mode: --negate <key> forces one expected hash to fail.
    override = None
    if len(argv) >= 3 and argv[1] == "--negate":
        override = {argv[2]: "0" * 64}

    if OUT_PATH.exists():
        print(f"REFUSE_OVERWRITE: {OUT_PATH} already exists")
        return 2

    ev = evaluate_gate(override)

    if not ev["gate_pass"]:
        print("FAIL_CLOSED: one or more required authority checks failed; NO artifact written.")
        for k, v in ev["checks"].items():
            if not v:
                print(f"  FAILED_CHECK {k}")
        return 3

    payload = build_payload(ev)
    payload_bytes = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    # Re-assert gate immediately before the write.
    if not all(ev["checks"].values()):
        print("FAIL_CLOSED_AT_WRITE: refusing to write")
        return 3

    write_once(OUT_PATH, payload_bytes)
    out_sha = sha256_file(OUT_PATH)

    print("RECONCILIATION_WRITTEN")
    print(f"path={OUT_PATH.relative_to(ROOT)}")
    print(f"bytes={len(payload_bytes)}")
    print(f"sha256={out_sha}")
    print(f"builder_sha256={payload['builder_source_sha256']}")
    print(f"frozen_adjudication_sha256={ev['frozen_adjudication_sha256']}")
    print(f"frozen_builder_sha256={ev['frozen_builder_sha256']}")
    print(f"gate_checks_pass={ev['gate_pass']} n={len(ev['checks'])}")
    print(f"D76_status=RECONCILED journal_result_snapshot_records={EXPECTED_RESULT_SNAPSHOT_N} "
          f"journal_final_on_disk_records={len(ev['journal_files'])}")
    print("D77_status=RECONCILED original_builder_fail_closed=False new_builder_fail_closed=True")
    print(f"D78={payload['D78']}")
    print(f"v1_15_repair_policy={payload['v1_15_repair_policy']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
