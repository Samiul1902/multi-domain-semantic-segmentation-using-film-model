"""Phase 25A — FAIL-CLOSED ENTRY GATE.

First implementation/training phase after the Phase-24 freeze. Verifies every
declared predecessor before ANY implementation or training work begins.

FAIL CLOSED: any mismatch aborts with a non-zero exit code and writes a gate
artifact recording the failure. Predecessor scientific state is NEVER silently
repaired.

Writes:
    reports/audits/phase25a_entry_gate.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25a_entry_gate.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()

# --- frozen expected values (from the Phase-24 v1.1 repair) ------------------
EXPECTED_TERMINAL = ("PHASE24_SPEC_COMPLETENESS_REPAIR_COMPLETE__"
                     "RA_MEDFILM_BARR_V1_1_FROZEN__PHASE25_ELIGIBLE_NOT_STARTED")
EXPECTED_NB_SHA = "612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef"
EXPECTED_METHOD = "RA-MedFiLM-BARR"
EXPECTED_ARCH = "ra_medfilm_barr_narrowed_v1_1"
EXPECTED_SEED = 42
EXPECTED_DEV = 4957
EXPECTED_HOLDOUT = 875
EXPECTED_GLOBAL_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
EXPECTED_P22_PROTOCOL_SHA = "9d620d6c85276e1a9a086ec60172cdef3b94dc58fe8288222378d196dd4609b7"
EXPECTED_SPLIT_MANIFEST_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"
EXPECTED_SPEC_COMPLETENESS = "PHASE24_SPEC_COMPLETENESS_REPAIR_PASS"

GLOBAL_CKPT = ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
NB = (ROOT / "notebooks/phasewise/phase_24_architecture_spec"
      / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
SPLIT_MANIFEST = AUD / "phase24_router_split_manifest.csv"
P22_PROTOCOL = AUD / "phase22_diagnostic_protocol.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def j(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def rows(p: Path) -> list[dict]:
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


checks: list[dict] = []


def chk(name: str, ok: bool, observed=None, expected=None) -> bool:
    entry = {"check": name, "pass": bool(ok)}
    if observed is not None:
        entry["observed"] = observed
    if expected is not None:
        entry["expected"] = expected
    checks.append(entry)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}"
          + (f"  observed={observed!r}" if (not ok and observed is not None) else ""))
    return bool(ok)


print("=" * 78)
print("PHASE 25A — FAIL-CLOSED ENTRY GATE")
print("=" * 78)

# 1. Phase-24 v1.1 exact implementation specification exists ------------------
ex_path = AUD / "phase24_exact_implementation_spec.json"
ex = j(ex_path)
chk("phase24_v1_1_exact_spec_exists", ex_path.exists() and bool(ex),
    observed=str(ex_path.exists()))

# 2. specification-completeness audit PASS ------------------------------------
scr = j(AUD / "phase24_spec_completeness_repair.json")
chk("phase24_spec_completeness_audit_pass",
    scr.get("verdict") == EXPECTED_SPEC_COMPLETENESS and int(scr.get("n_failed", 1)) == 0,
    observed=scr.get("verdict"), expected=EXPECTED_SPEC_COMPLETENESS)

# 3. Phase-24 v1.1 notebook SHA matches exactly -------------------------------
nb_sha = sha(NB) if NB.exists() else "MISSING"
chk("phase24_notebook_sha_exact", nb_sha == EXPECTED_NB_SHA,
    observed=nb_sha, expected=EXPECTED_NB_SHA)

# 4-6. method name / architecture revision / seed -----------------------------
chk("method_name", ex.get("method_name") == EXPECTED_METHOD,
    observed=ex.get("method_name"), expected=EXPECTED_METHOD)
chk("architecture_revision", ex.get("architecture_id") == EXPECTED_ARCH,
    observed=ex.get("architecture_id"), expected=EXPECTED_ARCH)
chk("master_development_seed", int(ex.get("split_seed", -1)) == EXPECTED_SEED,
    observed=ex.get("split_seed"), expected=EXPECTED_SEED)

# 7-8. ROUTER_DEVELOPMENT / ROUTER_HOLDOUT populations ------------------------
sm = rows(SPLIT_MANIFEST) if SPLIT_MANIFEST.exists() else []
dev = [r for r in sm if r.get("split_role") == "ROUTER_DEVELOPMENT"]
hold = [r for r in sm if r.get("split_role") == "ROUTER_HOLDOUT"]
chk("router_development_exists_n_4957", len(dev) == EXPECTED_DEV,
    observed=len(dev), expected=EXPECTED_DEV)
chk("router_holdout_exists_n_875", len(hold) == EXPECTED_HOLDOUT,
    observed=len(hold), expected=EXPECTED_HOLDOUT)

# 9. group overlap between DEV / HOLDOUT == 0 ---------------------------------
dev_groups = {r["group_key"] for r in dev}
hold_groups = {r["group_key"] for r in hold}
chk("group_overlap_dev_holdout_zero", len(dev_groups & hold_groups) == 0,
    observed=len(dev_groups & hold_groups), expected=0)

# 10-11. overlap with VAL / TEST == 0 ----------------------------------------
bpe = j(AUD / "phase24_benefit_data_protocol_exact.json")
chk("overlap_with_val_zero",
    bool(bpe.get("phase22_val_overlap_zero")) and int(bpe.get("mask_reads", -1)) == 0,
    observed=bpe.get("phase22_val_overlap_zero"), expected=True)
chk("overlap_with_test_zero", bool(bpe.get("test_overlap_zero")),
    observed=bpe.get("test_overlap_zero"), expected=True)

# 12. ROUTER_HOLDOUT outcomes read == 0 --------------------------------------
chk("router_holdout_outcomes_read_zero",
    int(bpe.get("holdout_outcomes_read", -1)) == 0,
    observed=bpe.get("holdout_outcomes_read"), expected=0)

# 13-14. frozen Phase-21 checkpoint exists + SHA ------------------------------
g_sha = sha(GLOBAL_CKPT) if GLOBAL_CKPT.exists() else "MISSING"
chk("phase21_checkpoint_exists", GLOBAL_CKPT.exists(), observed=str(GLOBAL_CKPT.exists()))
chk("phase21_checkpoint_sha_matches", g_sha == EXPECTED_GLOBAL_SHA,
    observed=g_sha, expected=EXPECTED_GLOBAL_SHA)

# 15. Phase-25 modules previously started == 0 -------------------------------
chk("phase25_modules_previously_started_zero",
    int(ex.get("phase25_started_phase25a", 0) if False else
        int(scr.get("phase25_modules_started", 0))) == 0,
    observed=scr.get("phase25_modules_started"), expected=0)
chk("phase24_declared_phase25_not_started", ex.get("phase25_started") is False,
    observed=ex.get("phase25_started"), expected=False)

# 16. TEST counters all zero --------------------------------------------------
tl = j(AUD / "phase24_spec_repair_freeze.json")
tl_b = tl.get("bindings", {})
chk("test_lock_closed", tl_b.get("test_lock") == "CLOSED",
    observed=tl_b.get("test_lock"), expected="CLOSED")
ne = j(AUD / "phase24_no_execution_audit.json")
test_zero = (int(ne.get("test_reads", -1)) == 0
             and int(ne.get("test_image_reads", -1)) == 0
             and int(ne.get("test_mask_reads", -1)) == 0
             and int(ne.get("test_inference_calls", -1)) == 0
             and int(ne.get("test_visualizations", -1)) == 0)
chk("test_counters_all_zero", test_zero,
    observed={k: ne.get(k) for k in ("test_reads", "test_image_reads", "test_mask_reads",
                                     "test_inference_calls", "test_visualizations")},
    expected=0)

# 17. predecessor terminal ----------------------------------------------------
chk("phase24_repair_terminal_matches", tl.get("terminal_state") == EXPECTED_TERMINAL,
    observed=tl.get("terminal_state"), expected=EXPECTED_TERMINAL)

# 18. split manifest SHA (frozen binding) ------------------------------------
sm_sha = sha(SPLIT_MANIFEST) if SPLIT_MANIFEST.exists() else "MISSING"
chk("split_manifest_sha_matches", sm_sha == EXPECTED_SPLIT_MANIFEST_SHA,
    observed=sm_sha, expected=EXPECTED_SPLIT_MANIFEST_SHA)

# 19. Phase-22 protocol SHA (predecessor science) ----------------------------
p22_sha = sha(P22_PROTOCOL) if P22_PROTOCOL.exists() else "MISSING"
chk("phase22_protocol_sha_matches", p22_sha == EXPECTED_P22_PROTOCOL_SHA,
    observed=p22_sha, expected=EXPECTED_P22_PROTOCOL_SHA)

# 20. no Phase-25A artifacts already present (this gate runs first) ----------
pre_existing = [p.name for p in [
    AUD / "phase25a_final_freeze.json",
    AUD / "phase25a_training_run_registry.json",
] if p.exists()]
chk("no_phase25a_training_artifacts_preexisting", len(pre_existing) == 0,
    observed=pre_existing, expected=[])

n_pass = sum(1 for c in checks if c["pass"])
n_fail = len(checks) - n_pass
verdict = ("PHASE25A_ENTRY_GATE_PASS" if n_fail == 0
           else "PHASE25A_ENTRY_GATE_FAIL")

out = {
    "artifact": "phase25a_entry_gate",
    "phase": "25A",
    "purpose": "fail-closed verification of every declared predecessor before the "
               "first implementation/training phase after the Phase-24 freeze",
    "predecessor_terminal": EXPECTED_TERMINAL,
    "architecture_id": EXPECTED_ARCH,
    "method_name": EXPECTED_METHOD,
    "master_development_seed": EXPECTED_SEED,
    "n_checks": len(checks),
    "n_passed": n_pass,
    "n_failed": n_fail,
    "verdict": verdict,
    "training_may_start": n_fail == 0,
    "fail_closed": True,
    "predecessor_scientific_state_repaired": False,
    "checks": checks,
    "generated_utc": UTC,
    "test_reads": 0,
}
AUD.mkdir(parents=True, exist_ok=True)
(AUD / "phase25a_entry_gate.json").write_text(json.dumps(out, indent=1) + "\n",
                                              encoding="utf-8")

print("-" * 78)
print(f"entry gate: {n_pass}/{len(checks)} PASS -> {verdict}")
print(f"wrote {AUD / 'phase25a_entry_gate.json'}")
if n_fail:
    print("FAIL-CLOSED: refusing to proceed to Phase-25A implementation.")
    sys.exit(2)
print("PHASE25A_ENTRY_GATE_PASS")
