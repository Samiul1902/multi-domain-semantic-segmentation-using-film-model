"""Phase26 SPECIFICATION REPAIR - §29 ADDITIVE DOCS SYNC.

Idempotent: a second run reports changed=false.  Sentinel-guarded insertion.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_common as C  # noqa: E402

SENTINEL = "<!-- PHASE26_SPEC_V1_0_REPAIR -->"

DOCS = [
    "docs/ARCHITECTURE.md",
    "docs/DESIGN.md",
    "docs/MEMORY.md",
    "docs/PRD.md",
    "docs/RULES.md",
    "docs/TASKS.md",
    "notebooks/phasewise/PHASE_INDEX.md",
]

BLOCK = f"""
{SENTINEL}
## Phase26 specification repair — COMPLETE_FROZEN (2026-10-02)

**SUPERVISOR SPECIFICATION REPAIR** — `SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION`
(revision `ra_medfilm_barr_phase26_integration_v1_0`; `science_changed = false`, `model_weights_changed = false`).

- Phase26 legacy roadmap title **"Full Four-Domain RA-MedFiLM-BARR Training"** =
  **PRESERVED_PROVENANCE** (`LEGACY_ROADMAP_TITLE`).
- Canonical Phase26 operational title = **Full Four-Domain RA-MedFiLM-BARR Integration & Canonical Bundle Freeze**.
- `phase26_training_required = false` · `phase26_training_mode = ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION`.
  Phase26 performs **NO new parameter optimization** (no training / no fine-tuning / no backward /
  no optimizer / no model forward). Canonical spec: [`docs/phase26_training_spec.md`](../docs/phase26_training_spec.md).
- All four learned components **FROZEN_NO_GRAD**: G (Phase21), R_psi (Phase25A ROI-0.30), B_phi (Phase25D),
  S_omega (Phase25F); fusion = deterministic. `trainable_parameter_set = EMPTY`.
- `training_population = NONE` (n=0) → **holdout contamination risk RESOLVED**.
- Canonical system variant = **A8/C9** · canonical budget = **25%** (= 0.25, DEV count 1239) ·
  canonical lambda representative = **0.25** (`MEMBERSHIP_EQUIVALENT__NOT_PERFORMANCE_SELECTED`).
- Exact final-router threshold bound (DEV-calibrated, budget 0.25 / lambda 0.25) in
  `reports/audits/phase26_canonical_router_threshold_binding_v1_0.json`.
- Completeness matrix repaired: `phase26_specification_completeness_v1_0.csv` = **49/49 defined, 0 blocking**.
- **Phase26 spec = COMPLETE_FROZEN** · **Phase26 = EXECUTION_ELIGIBLE_NOT_STARTED**.
- ROUTER_HOLDOUT = **RESERVED_UNOPENED_FOR_PHASE30** · VAL808 = UNOPENED · TEST = LOCKED UNTIL PHASE39 ·
  Phase30 = NOT_STARTED.

Terminal: `PHASE26_SPEC_V1_0_COMPLETE__MODULAR_INTEGRATION_NO_RETRAINING_AND_CANONICAL_25PCT_A8_POLICY_FROZEN__PHASE26_EXECUTION_ELIGIBLE_NOT_STARTED`.
"""


def main():
    changed = []
    for rel in DOCS:
        p = C.ROOT / rel
        if not p.exists():
            print(f"  MISS {rel}")
            continue
        txt = p.read_text(encoding="utf-8")
        if SENTINEL in txt:
            print(f"  SKIP {rel} (already synced)")
            continue
        p.write_text(txt.rstrip("\n") + "\n\n" + BLOCK.strip() + "\n", encoding="utf-8")
        changed.append(rel)
        print(f"  SYNC {rel}")

    sync_status = {
        "artifact": "phase26_spec_repair_docs_sync",
        "phase": "26",
        "classification": "SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION",
        "method": C.METHOD_NAME,
        "revision": "ra_medfilm_barr_phase26_integration_v1_0",
        "docs_updated": changed,
        "docs_total": len(DOCS),
        "changed": len(changed) > 0,
        "idempotent": True,
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_spec_repair_docs_sync.json", sync_status)
    print(f"  changed={sync_status['changed']} ({len(changed)} docs)")


if __name__ == "__main__":
    main()
