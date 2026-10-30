"""Post-Phase24 repair -- dimension contract + router parameter recheck (section 8/9).

Records the pre-router dimension contract and independently recomputes the
closed-form parameter count of the ALREADY FROZEN v1.1 router architecture.
No router is instantiated.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
SPEC = AUD / "phase24_exact_implementation_spec.json"


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    spec = jload(SPEC)
    router = spec.get("router", {})
    declared = router.get("expected_parameter_count_closed_form")

    # Independent closed-form recomputation from the frozen v1.1 architecture string:
    #   Linear(218,128) -> LayerNorm(128) -> SiLU -> Dropout(0.10)
    #   Linear(128,64)  -> LayerNorm(64)  -> SiLU -> Dropout(0.10)
    #   Linear(64,1)
    #   task embedding n_tasks=4, embedding_dim=16
    emb = 4 * 16
    l1_w, l1_b = 218 * 128, 128
    ln1 = 128 * 2
    l2_w, l2_b = 128 * 64, 64
    ln2 = 64 * 2
    l3_w, l3_b = 64 * 1, 1
    total_with_ln = emb + (l1_w + l1_b) + ln1 + (l2_w + l2_b) + ln2 + (l3_w + l3_b)
    total_without_ln = emb + (l1_w + l1_b) + (l2_w + l2_b) + (l3_w + l3_b)

    breakdown = {
        "task_embedding_4x16": emb,
        "Linear_218_128_W": l1_w, "Linear_218_128_b": l1_b,
        "LayerNorm_128": ln1,
        "Linear_128_64_W": l2_w, "Linear_128_64_b": l2_b,
        "LayerNorm_64": ln2,
        "Linear_64_1_W": l3_w, "Linear_64_1_b": l3_b,
    }

    discrepancy = (total_with_ln != declared)
    # Which variant reproduces the declared value?
    variant_matches = []
    if total_with_ln == declared:
        variant_matches.append("LayerNorm affine ENABLED + 4x16 embedding")
    if total_without_ln == declared:
        variant_matches.append("LayerNorm affine DISABLED (elementwise_affine=False) "
                               "+ 4x16 embedding")
    if (total_with_ln - emb) == declared:
        variant_matches.append("LayerNorm ENABLED, task embedding EXCLUDED")
    if (total_without_ln - emb) == declared:
        variant_matches.append("LayerNorm DISABLED, task embedding EXCLUDED")

    out = {
        "artifact": "phase24_router_feature_dimension_contract_v1_2",
        "phase": "24",
        "revision": "ra_medfilm_barr_narrowed_v1_2",
        "classification": "SPECIFICATION_COMPLETENESS_ONLY",
        "science_changed": False,
        "dimension_contract": {
            "deep_features": 192,
            "scalar_features": 10,
            "phase25b_numeric_matrix": 202,
            "task_id_metadata": "retained separately (not embedded in Phase25B)",
            "future_phase25d_task_embedding": 16,
            "future_router_input": 218,
            "task_embedding_materialized_in_phase25b": False,
        },
        "dimension_checks": {
            "deep_192": 6 * 32 == 192,
            "phase25b_202": 192 + 10 == 202,
            "future_218": 202 + 16 == 218,
        },
        "v1_1_router_architecture": {
            "input_dim": 218,
            "layers": ["Linear(218,128)", "LayerNorm(128)", "SiLU", "Dropout(0.10)",
                       "Linear(128,64)", "LayerNorm(64)", "SiLU", "Dropout(0.10)",
                       "Linear(64,1)"],
            "task_conditioning": {"n_tasks": 4, "embedding_dim": 16},
        },
        "parameter_recheck": {
            "declared_in_v1_1": declared,
            "recomputed_with_layernorm_affine": total_with_ln,
            "recomputed_without_layernorm_affine": total_without_ln,
            "breakdown": breakdown,
            "discrepancy": discrepancy,
            "delta": (total_with_ln - declared) if discrepancy else 0,
            "variants_reproducing_declared": variant_matches,
        },
        "discrepancy_present": discrepancy,
        "discrepancy_policy": "REPORTED, NOT SILENTLY REPAIRED",
        "hidden_widths_modified": False,
        "router_instantiated": False,
        "verdict": ("ROUTER_PARAM_COUNT_CONSISTENT" if not discrepancy
                    else "ROUTER_PARAM_COUNT_DISCREPANCY_REPORTED"),
        "test_reads": 0,
    }
    (AUD / "phase24_router_feature_dimension_contract_v1_2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    print("=== dimension contract ===")
    for k, v in out["dimension_contract"].items():
        print(f"  {k:38s}= {v}")
    print()
    print("=== router parameter recheck (no instantiation) ===")
    print(f"  declared in v1.1                        = {declared}")
    print(f"  recomputed (LayerNorm affine on)        = {total_with_ln}")
    print(f"  recomputed (LayerNorm affine off)       = {total_without_ln}")
    print(f"  discrepancy                             = {discrepancy} (delta {total_with_ln - declared})")
    print(f"  variants reproducing declared           = {variant_matches}")
    print()
    print(out["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
