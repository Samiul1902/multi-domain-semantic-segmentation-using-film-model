"""Phase 14 clean-v3 — §7 evaluator binding (prospective hash of adapted evaluator + dependencies).

Records the SHA-256 of the adapted three-contrast evaluator and its transitive
dependency closure that defines metric/fusion semantics, plus the frozen clean-v3
operational config. No inference; pure hashing + governance artifact.
"""
import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "scripts" / "evaluation" / "evaluate_phase14_clean_v3_diagnostic.py"
GEN = PROJECT_ROOT / "scripts" / "audits" / "phase14_clean_v3_generate_global_reference.py"
AUDITS = PROJECT_ROOT / "reports" / "audits"

DEPS = [
    "src/analysis/oracle_roi.py",
    "src/data/regional_dataset.py",
    "src/data/transforms.py",
    "src/inference/kub_predict.py",
    "src/inference/predicted_roi.py",
    "src/inference/regional_evaluator.py",
    "src/metrics/object_metrics.py",
    "src/models/factory.py",
    "src/models/unet.py",
    "src/utils/checkpointing.py",
    "src/utils/manifest_guard.py",
    "src/utils/test_lock.py",
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    assert SRC.exists(), f"evaluator missing: {SRC}"
    evaluator_sha = sha256_file(SRC)
    gen_sha = sha256_file(GEN) if GEN.exists() else None
    dep_shas = {}
    for d in DEPS:
        dp = PROJECT_ROOT / d
        assert dp.exists(), f"dependency missing: {d}"
        dep_shas[d] = sha256_file(dp)

    binding = {
        "artifact": "phase14_clean_v3_evaluator_binding",
        "status": "BOUND_PROSPECTIVE",
        "evaluator": {
            "path": "scripts/evaluation/evaluate_phase14_clean_v3_diagnostic.py",
            "sha256": evaluator_sha,
        },
        "reference_generator": {
            "path": "scripts/audits/phase14_clean_v3_generate_global_reference.py",
            "sha256": gen_sha,
        },
        "dependency_sha256": dep_shas,
        "frozen_operational_config": {
            "oracle_downstream_margin": 0.20,
            "predicted_proposal_threshold": 0.10,
            "predicted_proposal_margin": 0.20,
            "predicted_proposal_top_k": 5,
            "predicted_proposal_nms_iou": 0.30,
            "final_fusion_threshold": 0.50,
            "fusion_mode": "MAX (DIRECT_REPLACEMENT_IN_PROPOSAL_UNION)",
            "global_threshold": 0.50,
        },
        "metric_fusion_semantics": "UNCHANGED from v2-era evaluate_phase14_diagnostic.py (verbatim copy, clean_v3 bindings only)",
        "population_binding_ref": "reports/audits/phase14_clean_v3_population_freeze.json",
        "checkpoint_binding_ref": "reports/audits/phase14_clean_v3_checkpoint_binding.json",
        "global_reference_ref": "reports/audits/phase14_clean_v3_global_reference_freeze.json",
        "governance_note": (
            "The adapted evaluator and its dependency closure are hashed prospectively. "
            "Post-binding modification of any listed file invalidates this binding and "
            "requires a new supervisor amendment. The evaluator must run exactly once (§8)."
        ),
    }
    out = AUDITS / "phase14_clean_v3_evaluator_binding.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(binding, f, indent=2)
    print(f"[bind] Wrote {out}")
    print(f"[bind] evaluator sha: {evaluator_sha}")
    print(f"[bind] deps hashed: {len(dep_shas)}")


if __name__ == "__main__":
    main()
