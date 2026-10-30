"""
Phase 19 driver — Multi-Domain Dataset Harmonization (Stage B).

Produces every Phase-19 artifact deterministically. No training, no optimizer,
no backward pass, no checkpoint, no TEST access.

Run:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe scripts/analysis/run_phase19_harmonization.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import multidomain_harmonization as H  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402


def main() -> int:
    print("=" * 78)
    print("PHASE 19 — MULTI-DOMAIN DATASET HARMONIZATION (Stage B)")
    print("=" * 78)

    lock = verify_test_lock(str(ROOT))
    print(f"TEST lock verified: count={lock['test_sample_count']} sha={lock['full_test_sha256'][:16]}...")

    audits = ROOT / "reports/audits"
    tables = ROOT / "reports/tables"
    figs = ROOT / "reports/figures/phase19_harmonization"
    audits.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)

    produced: dict[str, str] = {}

    # ---- measurement caches -------------------------------------------------
    img = H.build_image_measurements(ROOT, tables / "phase19_image_measurements.csv")
    print(f"image measurements: {len(img)} rows (TRAIN+VAL, full population)")
    msk = H.build_mask_measurements(ROOT, tables / "phase19_mask_measurements.csv")
    print(f"mask measurements : {len(msk)} rows (deterministic per-domain sample)")

    # ---- tables -------------------------------------------------------------
    produced["phase19_image_measurements.csv"] = H.write_csv(
        tables / "phase19_image_measurements.csv", img)
    produced["phase19_mask_measurements.csv"] = H.write_csv(
        tables / "phase19_mask_measurements.csv", msk)
    produced["phase19_dataset_inventory.csv"] = H.write_csv(
        tables / "phase19_dataset_inventory.csv", H.dataset_inventory(ROOT))
    produced["phase19_task_id_registry.csv"] = H.write_csv(
        tables / "phase19_task_id_registry.csv", H.task_id_registry(ROOT))
    produced["phase19_metadata_governance.csv"] = H.write_csv(
        tables / "phase19_metadata_governance.csv", H.metadata_governance())
    produced["phase19_harmonized_schema.csv"] = H.write_csv(
        tables / "phase19_harmonized_schema.csv", H.harmonized_schema())
    produced["phase19_phase20_entry_criteria.csv"] = H.write_csv(
        tables / "phase19_phase20_entry_criteria.csv", H.phase20_entry_criteria(ROOT))
    produced["phase19_group_key_availability.csv"] = H.write_csv(
        tables / "phase19_group_key_availability.csv", H.group_key_availability(ROOT))

    # ---- contracts ----------------------------------------------------------
    produced["phase19_preprocessing_contract.json"] = H.write_json(
        audits / "phase19_preprocessing_contract.json", H.preprocessing_contract(ROOT))
    produced["phase19_evaluation_contract.json"] = H.write_json(
        audits / "phase19_evaluation_contract.json", H.evaluation_contract())
    produced["phase19_legacy_evidence_reuse_map.json"] = H.write_json(
        audits / "phase19_legacy_evidence_reuse_map.json", H.legacy_evidence_reuse_map())
    produced["phase19_leakage_safeguards.json"] = H.write_json(
        audits / "phase19_leakage_safeguards.json", H.leakage_safeguards(ROOT))

    # ---- loader smoke test --------------------------------------------------
    smoke = H.loader_smoke_test(ROOT)
    produced["phase19_loader_smoke_test.json"] = H.write_json(
        audits / "phase19_loader_smoke_test.json", smoke)
    print(f"loader smoke test : all_checks_passed={smoke['all_checks_passed']} "
          f"test_rejected(dataset/loader)={smoke['test_rejected_by_dataset']}/{smoke['test_rejected_by_loader']}")

    # ---- figures ------------------------------------------------------------
    fig_shas = H.build_all_figures(ROOT, figs)
    print(f"figures           : {len(fig_shas)} written to {figs.relative_to(ROOT)}")

    # ---- protocol -----------------------------------------------------------
    protocol = H.harmonization_protocol(ROOT)
    protocol["artifacts"] = produced
    protocol["figures"] = fig_shas
    protocol["loader_smoke_test_summary"] = {
        "all_checks_passed": smoke["all_checks_passed"],
        "test_rejected_by_dataset": smoke["test_rejected_by_dataset"],
        "test_rejected_by_loader": smoke["test_rejected_by_loader"],
    }
    produced["phase19_multidomain_harmonization_protocol.json"] = H.write_json(
        audits / "phase19_multidomain_harmonization_protocol.json", protocol)

    print()
    print("=" * 78)
    print("ARTIFACTS")
    print("=" * 78)
    for name, digest in produced.items():
        print(f"  {digest}  {name}")
    print()
    print(f"terminal state: {protocol['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
