"""Phase 25B -- fail-closed entry gate.

Verifies the authorized predecessor state (canonical Phase25A after the
ROI-threshold adjudication) and the locks that Phase25B must inherit.

FAIL CLOSED: any disagreement aborts with a non-zero exit and a
DATA_PROTOCOL_VIOLATION style terminal.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"

EXPECTED = {
    "predecessor_terminal": (
        "PHASE25A_CANONICAL_RERUN_COMPLETE__ROI_PROPOSAL_THRESHOLD_0P30__"
        "SEGMENTATION_OUTPUT_THRESHOLD_0P50__PHASE25B_ELIGIBLE_NOT_STARTED"
    ),
    "phase25a_classification": "CANONICAL_PHASE25A_AFTER_THRESHOLD_ADJUDICATION",
    "phase25a_notebook_sha256": "fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd",
    "phase21_global_sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "phase25a_final_refiner_sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "roi_proposal_threshold": 0.30,
    "segmentation_output_threshold": 0.50,
    "router_development_n": 4957,
    "router_holdout_n": 875,
    "action_available_n": 4957,
    "action_unavailable_n": 0,
    "superseded_classification": "NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50",
    "split_manifest_sha256": "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555",
}

PHASE21_CKPT = ROOT / "checkpoints" / "phase21_global_medfilm_fourdomain_seed42_clean_v3" / "best.pt"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    checks: list[dict] = []

    def chk(name: str, ok: bool, detail=None) -> bool:
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        return bool(ok)

    ptr_path = AUD / "phase25a_canonical_governance_pointer.json"
    ptr = jload(ptr_path)
    can = ptr.get("canonical", {})
    sup = ptr.get("superseded", {})

    chk("canonical_gov_pointer_exists", ptr_path.exists(), str(ptr_path))
    chk("canonical_classification",
        can.get("classification") == EXPECTED["phase25a_classification"],
        can.get("classification"))

    nb = ROOT / can.get("notebook", "")
    chk("canonical_notebook_sha256",
        nb.exists() and sha(nb) == EXPECTED["phase25a_notebook_sha256"],
        sha(nb) if nb.exists() else None)

    chk("roi_proposal_threshold_0p30",
        can.get("roi_proposal_threshold") == EXPECTED["roi_proposal_threshold"],
        can.get("roi_proposal_threshold"))
    chk("segmentation_output_threshold_0p50",
        can.get("segmentation_output_threshold") == EXPECTED["segmentation_output_threshold"],
        can.get("segmentation_output_threshold"))

    # ambiguous bare threshold fields
    ambiguous = []
    for src_name, src in (("pointer_canonical", can), ("pointer_superseded", sup)):
        for k, v in src.items():
            if k == "roi_proposal_threshold" or k == "segmentation_output_threshold":
                continue
            if "threshold" == k or k.endswith("_threshold") and isinstance(v, (int, float)):
                ambiguous.append(f"{src_name}.{k}={v}")
    chk("ambiguous_threshold_fields_zero", len(ambiguous) == 0, ambiguous)

    ref = ROOT / can.get("checkpoint_root", "") / "final" / "final.pt"
    chk("canonical_final_refiner_sha256",
        ref.exists() and sha(ref) == EXPECTED["phase25a_final_refiner_sha256"],
        sha(ref) if ref.exists() else None)

    chk("phase21_global_checkpoint_sha256",
        PHASE21_CKPT.exists() and sha(PHASE21_CKPT) == EXPECTED["phase21_global_sha256"],
        sha(PHASE21_CKPT) if PHASE21_CKPT.exists() else None)

    prov = jload(AUD / "phase25a_roi030_cache_provenance.json")
    chk("router_development_n_4957",
        prov.get("population_n") == EXPECTED["router_development_n"], prov.get("population_n"))
    chk("canonical_action_available_4957",
        prov.get("action_available_n") == EXPECTED["action_available_n"],
        prov.get("action_available_n"))
    chk("canonical_action_unavailable_0",
        prov.get("action_unavailable_global_empty_n") == EXPECTED["action_unavailable_n"],
        prov.get("action_unavailable_global_empty_n"))

    chk("superseded_run_is_noncanonical",
        sup.get("classification") == EXPECTED["superseded_classification"],
        sup.get("classification"))
    chk("superseded_scientific_use_allowed_false",
        sup.get("scientific_use_allowed") is False, sup.get("scientific_use_allowed"))
    chk("superseded_preserved_on_disk",
        (ROOT / sup.get("checkpoint_root", "")).exists(), sup.get("checkpoint_root"))

    # split / holdout population
    split = ROOT / "reports" / "audits" / "phase24_router_split_manifest.csv"
    chk("router_split_manifest_sha256",
        split.exists() and sha(split) == EXPECTED["split_manifest_sha256"],
        sha(split) if split.exists() else None)
    holdout_n = None
    if split.exists():
        import csv
        with split.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        holdout_n = sum(1 for r in rows if str(r.get("split_role", "")).upper() == "ROUTER_HOLDOUT")
        dev_n = sum(1 for r in rows if str(r.get("split_role", "")).upper() == "ROUTER_DEVELOPMENT")
    else:
        dev_n = None
    chk("router_holdout_n_875", holdout_n == EXPECTED["router_holdout_n"], holdout_n)
    chk("router_development_manifest_n_4957", dev_n == EXPECTED["router_development_n"], dev_n)

    # not-started guards.
    # NOTE: this gate's own output (phase25b_entry_gate.json) is a self-reference and is
    # excluded. We test for SUBSTANTIVE prior Phase25B work only: a feature cache, an
    # extraction script, a notebook, or a training/experiment tree.
    def _substantive(pattern: str) -> list:
        hits = []
        for p in ROOT.glob(pattern):
            s = str(p).replace("\\", "/")
            if ".venv" in s or "/.git/" in s:
                continue
            if s.endswith("reports/audits/phase25b_entry_gate.json"):
                continue
            if s.endswith("scripts/analysis/run_phase25b_entry_gate.py"):
                continue
            hits.append(s)
        return hits

    prior_cache = _substantive("data_cache/phase25b*")
    prior_nb = _substantive("notebooks/**/phase_25b*")
    prior_exp = _substantive("experiments/phase25b*")
    prior_ckpt = _substantive("checkpoints/phase25b*")
    prior_trainer = _substantive("scripts/**/train_phase25b*")
    chk("phase25b_previously_not_started",
        not any([prior_cache, prior_nb, prior_exp, prior_ckpt, prior_trainer]),
        {"cache": prior_cache, "notebook": prior_nb, "experiments": prior_exp,
         "checkpoints": prior_ckpt, "trainer": prior_trainer})
    chk("phase25c_previously_not_started",
        not any(_substantive("data_cache/phase25c*") + _substantive("notebooks/**/phase_25c*")
                + _substantive("experiments/phase25c*") + _substantive("checkpoints/phase25c*")))
    chk("no_benefit_router_artifact",
        len([p for p in ROOT.glob("**/*benefit_router*") if ".venv" not in str(p)]) == 0)
    chk("no_paired_gain_table",
        len([p for p in ROOT.glob("**/*paired_gain*") if ".venv" not in str(p)]) == 0)

    # predecessor terminal
    fz = jload(AUD / "phase25a_canonical_final_freeze.json")
    chk("predecessor_terminal_exact",
        fz.get("terminal") == EXPECTED["predecessor_terminal"], fz.get("terminal"))

    n_fail = sum(1 for c in checks if not c["passed"])
    status = "PHASE25B_ENTRY_GATE_PASS" if n_fail == 0 else "PHASE25B_ENTRY_GATE_FAIL"

    out = {
        "artifact": "phase25b_entry_gate",
        "phase": "25B",
        "purpose": "fail-closed verification of the authorized Phase25A predecessor state",
        "expected": EXPECTED,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "checks": checks,
        "verdict": status,
        "fail_closed": n_fail == 0,
        "phase25b_started": False,
        "test_reads": 0,
        "holdout_outcomes_read": 0,
        "val_outcome_reads": 0,
    }
    AUD.mkdir(parents=True, exist_ok=True)
    (AUD / "phase25b_entry_gate.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: {c['detail']}")
    print()
    print(f"{len(checks) - n_fail}/{len(checks)} PASS")
    print(status)
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
