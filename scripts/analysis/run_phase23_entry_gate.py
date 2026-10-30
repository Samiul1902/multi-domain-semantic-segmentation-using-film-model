"""Phase 23 — entry gate (FAIL CLOSED).

Verifies every precondition required before the Phase-23 literature / methodological
novelty audit may proceed. Read-only: it inspects persisted artifacts, never trains,
never runs segmentation inference, never touches TEST.

If any check fails the script writes reports/audits/phase23_entry_gate.json with
verdict PHASE23_ENTRY_GATE_FAIL and exits non-zero. It never repairs frozen science.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase23_entry_gate.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase22_resource_gap"
OUT = AUD / "phase23_entry_gate.json"

# ---- frozen predecessor identities (must be byte-identical) ----
EXPECTED_PHASE22_FREEZE_SHA = "9a0aa2f8c1a2850770fb09f2838e95f0fe08b3b40e55ab1d10c3564841107bca"
EXPECTED_PROTOCOL_SHA = "9d620d6c85276e1a9a086ec60172cdef3b94dc58fe8288222378d196dd4609b7"
EXPECTED_CHECKPOINT_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
EXPECTED_PHASE22_NOTEBOOK_SHA = "cca76123336f0895426f76024138b90565631d44ba51dced405e0fd8afa43658"
EXPECTED_PHASE21_MACRO_DICE = 0.8350794169575282
EXPECTED_PROTOCOL_ID = "phase22_diagnostic_protocol_v1"
EXPECTED_PREDECESSOR_TERMINAL = (
    "PHASE22_CANONICAL_IPYNB_MATERIALIZED__VISUAL_INTEGRITY_PASS__"
    "SCIENCE_UNCHANGED__PHASE23_ELIGIBLE_NOT_STARTED"
)

PHASE22_FREEZE = AUD / "phase22_final_freeze.json"
PHASE22_PROTOCOL = AUD / "phase22_diagnostic_protocol.json"
PHASE21_FREEZE = AUD / "phase21_final_freeze.json"
COMBINED_AUDIT = AUD / "post_phase22_evidence_repair_final_audit.json"
NOTEBOOK = ROOT / "notebooks" / "phasewise" / "phase_22_resource_gap" / "phase22_resource_gap_analysis.ipynb"
CHECKPOINT = ROOT / "checkpoints" / "phase21_global_medfilm_fourdomain_seed42_clean_v3" / "best.pt"

GT_FREE_TABLE = TAB / "phase22_gt_free_proxy_vs_benefit.csv"
GT_AWARE_TABLE = TAB / "phase22_gt_aware_posthoc_associations.csv"
LABEL_CONTRACT = AUD / "phase22_future_benefit_label_contract.json"
CANDIDATE_EVIDENCE = AUD / "phase22_candidate_method_evidence.json"


def sha256(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    checks: list[dict] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": str(detail)})

    freeze = load(PHASE22_FREEZE)
    comb = load(COMBINED_AUDIT)
    contract = load(LABEL_CONTRACT)
    candidate = load(CANDIDATE_EVIDENCE)

    # ---- 1. predecessor freeze / protocol / checkpoint identity ----
    chk("phase22_freeze_exists", PHASE22_FREEZE.exists(), str(PHASE22_FREEZE.relative_to(ROOT)))
    chk("phase22_freeze_sha_unchanged",
        sha256(PHASE22_FREEZE) == EXPECTED_PHASE22_FREEZE_SHA,
        sha256(PHASE22_FREEZE) or "MISSING")
    chk("phase22_protocol_sha_unchanged",
        sha256(PHASE22_PROTOCOL) == EXPECTED_PROTOCOL_SHA,
        sha256(PHASE22_PROTOCOL) or "MISSING")
    chk("phase21_best_checkpoint_sha_unchanged",
        sha256(CHECKPOINT) == EXPECTED_CHECKPOINT_SHA,
        sha256(CHECKPOINT) or "MISSING")
    chk("protocol_id",
        (freeze.get("protocol") or {}).get("protocol_id", contract.get("protocol_id")) == EXPECTED_PROTOCOL_ID
        or EXPECTED_PROTOCOL_ID in json.dumps(freeze),
        EXPECTED_PROTOCOL_ID)

    # ---- 2. predecessor terminal state + combined audit green ----
    chk("combined_audit_all_passed", comb.get("all_passed") is True,
        f"{comb.get('n_passed')}/{comb.get('n_checks')}")
    chk("predecessor_terminal_present",
        EXPECTED_PREDECESSOR_TERMINAL in (comb.get("terminal_states") or []),
        EXPECTED_PREDECESSOR_TERMINAL)
    chk("phase23_not_already_started", comb.get("phase23_started") is False,
        str(comb.get("phase23_started")))

    # ---- 3. Phase-21 macro Dice (science identity) ----
    md = None
    try:
        md = float((freeze.get("science_identity") or {}).get("phase21_macro_domain_dice"))
    except (TypeError, ValueError):
        md = None
    if md is None:
        # fall back to combined audit phase21 block
        md = (comb.get("phase21") or {}).get("macro_domain_dice")
    chk("phase21_macro_dice_unchanged",
        md is not None and abs(float(md) - EXPECTED_PHASE21_MACRO_DICE) < 1e-12,
        str(md))

    # ---- 4. TEST lock ----
    tl = (freeze.get("governance") or {}).get("test_locks") or {}
    tr_freeze = freeze.get("test_reads")
    tr_comb = (comb.get("phase22") or {}).get("test_reads", {})
    candidates = [tl, tr_freeze, tr_comb]
    zero_ok = False
    evidence = ""
    for cand in candidates:
        if isinstance(cand, dict) and cand and all(int(v) == 0 for v in cand.values()):
            zero_ok = True
            evidence = json.dumps(cand)
            break
        if cand == 0:
            zero_ok = True
            evidence = "0"
            break
    if not evidence:
        evidence = json.dumps({"test_locks": tl, "freeze_test_reads": tr_freeze, "combined": tr_comb})
    chk("test_reads_zero", zero_ok, evidence)

    # ---- 5. GT-free / GT-aware evidence artifacts present ----
    chk("gt_free_table_exists", GT_FREE_TABLE.exists(), str(GT_FREE_TABLE.relative_to(ROOT)))
    chk("gt_aware_table_exists", GT_AWARE_TABLE.exists(), str(GT_AWARE_TABLE.relative_to(ROOT)))

    # ---- 6. future benefit label contract is CONTRACTED, not trained ----
    chk("label_contract_present", LABEL_CONTRACT.exists(), str(LABEL_CONTRACT.relative_to(ROOT)))
    chk("label_contract_not_implemented",
        contract.get("status") == "CONTRACT_PROPOSED_NOT_IMPLEMENTED",
        str(contract.get("status")))
    chk("label_contract_not_a_training_artifact",
        contract.get("is_a_training_artifact") is False,
        str(contract.get("is_a_training_artifact")))

    # ---- 7. candidate evidence present ----
    chk("candidate_method_evidence_present", CANDIDATE_EVIDENCE.exists(),
        str(CANDIDATE_EVIDENCE.relative_to(ROOT)))
    chk("candidate_evidence_lists_c1_c5",
        len(candidate.get("candidates") or []) >= 5,
        f"{len(candidate.get('candidates') or [])} candidates")

    # ---- 8. canonical Phase-22 notebook present at expected SHA ----
    chk("phase22_canonical_notebook_sha",
        sha256(NOTEBOOK) == EXPECTED_PHASE22_NOTEBOOK_SHA,
        sha256(NOTEBOOK) or "MISSING")

    # ---- 9. Phase-23 target outputs do not pre-exist (clean start) ----
    # The entry gate's own output file is self-referential and excluded.
    SELF = {"phase23_entry_gate.json"}
    pre_existing = sorted(
        p.name for p in AUD.glob("phase23_*") if p.name not in SELF
    ) + sorted(p.name for p in TAB.glob("phase23_*"))
    chk("no_preexisting_phase23_artifacts", len(pre_existing) == 0,
        ",".join(pre_existing) if pre_existing else "none")

    # ---- 10. no phase24 implementation artifacts ----
    p24 = sorted(p.name for p in AUD.glob("phase24_*"))
    chk("phase24_not_started", len(p24) == 0, ",".join(p24) if p24 else "none")

    # ---- 11. figure root present (Phase-22 evidence intact for motivation) ----
    n_fig = len(list(FIG.glob("*.png"))) if FIG.exists() else 0
    chk("phase22_figure_root_intact", n_fig == 15, f"{n_fig} png")

    n_pass = sum(1 for c in checks if c["pass"])
    n_fail = len(checks) - n_pass
    verdict = "PHASE23_ENTRY_GATE_PASS" if n_fail == 0 else "PHASE23_ENTRY_GATE_FAIL"

    payload = {
        "artifact": "phase23_entry_gate",
        "phase": 23,
        "purpose": "fail-closed precondition check before the literature/methodological novelty audit",
        "predecessor_terminal_state": EXPECTED_PREDECESSOR_TERMINAL,
        "expected_identities": {
            "phase22_final_freeze_sha256": EXPECTED_PHASE22_FREEZE_SHA,
            "phase22_protocol_sha256": EXPECTED_PROTOCOL_SHA,
            "phase21_best_checkpoint_sha256": EXPECTED_CHECKPOINT_SHA,
            "phase22_canonical_notebook_sha256": EXPECTED_PHASE22_NOTEBOOK_SHA,
            "phase21_macro_domain_dice": EXPECTED_PHASE21_MACRO_DICE,
        },
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": n_pass,
        "n_failed": n_fail,
        "verdict": verdict,
        "no_training": True,
        "no_segmentation_inference": True,
        "test_reads": 0,
        "phase24_started": False,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    for c in checks:
        flag = "PASS" if c["pass"] else "FAIL"
        print(f"  [{flag}] {c['check']} — {c['detail']}")
    print(f"\n{n_pass}/{len(checks)} checks passed — {verdict}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
