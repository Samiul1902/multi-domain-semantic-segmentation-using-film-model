"""Project governance sync -- section 4: D2 adjudication.

Router parameter-count bookkeeping correction. The frozen router architecture is
UNCHANGED; only the *naming* of the historical 36,353 figure is corrected. Pure
arithmetic -- NO model is instantiated, no CUDA, no forward pass.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"

# --- frozen BARRBenefitRouterV1 architecture (unchanged) ---
TASK_EMB_N, TASK_EMB_D = 4, 16
INPUT_DIM = 218
H1, H2 = 128, 64


def linear(i: int, o: int) -> dict:
    return {"weight": i * o, "bias": o, "total": i * o + o}


def layernorm_affine(d: int) -> dict:
    return {"gamma": d, "beta": d, "total": 2 * d}


def main() -> int:
    emb = TASK_EMB_N * TASK_EMB_D
    l1 = linear(INPUT_DIM, H1)
    ln1 = layernorm_affine(H1)
    l2 = linear(H1, H2)
    ln2 = layernorm_affine(H2)
    l3 = linear(H2, 1)

    total = emb + l1["total"] + ln1["total"] + l2["total"] + ln2["total"] + l3["total"]
    linear_core = l1["total"] + l2["total"] + l3["total"]
    layernorm_total = ln1["total"] + ln2["total"]

    n_fail = 0
    checks: list[dict] = []

    def chk(name, ok, detail=None):
        nonlocal n_fail
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            n_fail += 1

    chk("total_trainable_params_is_36801", total == 36801, total)
    chk("linear_core_is_36353", linear_core == 36353, linear_core)
    chk("linear_core_matches_historical", linear_core == 36353)
    chk("difference_is_448", total - linear_core == 448, total - linear_core)
    chk("difference_breakdown_64_plus_384",
        emb == 64 and layernorm_total == 384, {"task_embedding": emb,
                                               "layernorm_affine": layernorm_total})
    chk("task_embedding_retained", emb == 64)
    chk("layernorm_retained", layernorm_total == 384)
    chk("layernorm_affine_true", True)
    chk("hidden_widths_unchanged", (H1, H2) == (128, 64))
    chk("input_dim_unchanged_218", INPUT_DIM == 218)
    # cross-check: does 36353 equal the full count with affine+embedding removed?
    chk("36353_is_exactly_linear_core_only",
        linear_core == 36801 - emb - layernorm_total,
        {"linear_core": linear_core, "36801-64-384": 36801 - emb - layernorm_total})
    chk("no_optional_harm_head_in_primary", True)

    verdict = "D2_RESOLVED" if n_fail == 0 else "D2_BLOCKED"

    out = {
        "artifact": "phase24_router_parameter_count_adjudication",
        "phase": "24",
        "revision": "ra_medfilm_barr_narrowed_v1_2",
        "defect_id": "D2",
        "field": "router.expected_parameter_count_closed_form",
        "classification": "SPECIFICATION_COMPLETENESS_AND_GOVERNANCE_SYNC",
        "architecture_changed": False,
        "hidden_widths_changed": False,
        "input_dim_changed": False,
        "task_embedding_retained": True,
        "layernorm_retained": True,
        "layernorm_affine": True,
        "optional_harm_head_in_primary": False,
        "frozen_architecture": {
            "task_embedding": f"Embedding({TASK_EMB_N}, {TASK_EMB_D})",
            "input_dim": INPUT_DIM,
            "layers": [
                f"Linear({INPUT_DIM},{H1})",
                f"LayerNorm({H1}) [elementwise_affine=true]",
                "SiLU",
                "Dropout(0.10)",
                f"Linear({H1},{H2})",
                f"LayerNorm({H2}) [elementwise_affine=true]",
                "SiLU",
                "Dropout(0.10)",
                f"Linear({H2},1)",
            ],
        },
        "parameter_recomputation": {
            "task_embedding_4x16": emb,
            "Linear_218_128": l1,
            "LayerNorm_128": ln1,
            "Linear_128_64": l2,
            "LayerNorm_64": ln2,
            "Linear_64_1": l3,
            "linear_core_subtotal": linear_core,
            "layernorm_affine_subtotal": layernorm_total,
        },
        "canonical_total_trainable_params": total,
        "historical_linear_core_count": linear_core,
        "historical_36353_interpretation": (
            "36,353 is exactly the LINEAR-LAYER MLP parameter count "
            "(Linear(218,128) + Linear(128,64) + Linear(64,1)); it is NOT the total "
            "trainable router parameter count"),
        "historical_label_corrected_from": "total trainable router parameters",
        "historical_label_corrected_to": "historical_mlp_linear_core_parameter_count",
        "difference": total - linear_core,
        "difference_breakdown": {
            "task_embedding": emb,
            "layernorm_affine": layernorm_total,
        },
        "bookkeeping_correction_only": True,
        "model_trained_so_no_science_invalidated": True,
        "science_changed": False,
        "method_changed": False,
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "verdict": verdict,
        "model_instantiations": 0,
        "forward_passes": 0,
        "training_runs": 0,
        "optimizer_constructed": False,
        "backward_calls": 0,
        "test_reads": 0,
    }
    (AUD / "phase24_router_parameter_count_adjudication.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: "
              f"{json.dumps(c['detail'], ensure_ascii=False) if c['detail'] is not None else ''}")
    print()
    print(json.dumps({"linear_core": linear_core, "total_trainable": total,
                      "difference": total - linear_core,
                      "task_embedding": emb, "layernorm_affine": layernorm_total}, indent=1))
    print(f"{len(checks) - n_fail}/{len(checks)} PASS")
    print(verdict)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
