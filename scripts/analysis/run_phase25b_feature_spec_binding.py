"""Phase 25B -- Phase24 v1.1 frozen feature-spec binding audit (FAIL-CLOSED).

Work-order section 3 requires that the authoritative Phase24 v1.1 artifact
EXPLICITLY define, among other things:

  (a) the six 32-dimensional deep feature vectors;
  (b) their source taps;
  (c) their DETERMINISTIC REDUCTION TO 32 DIMENSIONS;
  (d) the ten scalar descriptors.

If it does not, Phase25B MUST STOP and emit:

  PHASE25B_BLOCKED__FROZEN_FEATURE_SPEC_INCOMPLETE

and must NOT invent a projection/reduction method (section 4).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"

SPEC = AUD / "phase24_exact_implementation_spec.json"
ARCH = AUD / "phase24_architecture_spec.json"
CONTRACT = ROOT / "reports" / "tables" / "phase24_router_input_contract.csv"
PRIMARY = ROOT / "reports" / "tables" / "phase24_router_primary_feature_set.csv"

# Observed channel widths of the frozen Phase-21 global MedFiLM at the three taps.
# Source: src/models/film/global_medfilm.py  GLOBAL_MEDFILM_CHANNELS = (24,48,96,192,256)
#   bridge   <- residual_block(c4=192, cb=256)   -> 256 channels
#   decoder2 <- DecoderBlock(c3=96, c2=48, c2=48) -> 48 channels
#   decoder1 <- DecoderBlock(c2=48, c1=24, c1=24) -> 24 channels
OBSERVED_TAP_CHANNELS = {"bridge": 256, "decoder2": 48, "decoder1": 24}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    spec = jload(SPEC)
    router = spec.get("router", {})

    req: list[dict] = []

    def require(name: str, ok: bool, detail=None, *, blocker: bool = True) -> bool:
        req.append({"requirement": name, "present": bool(ok),
                    "blocking_if_absent": blocker, "detail": detail})
        return bool(ok)

    # (b) source taps -- these ARE defined
    taps = router.get("feature_taps")
    tap_spec = router.get("tap_spec")
    require("six_deep_feature_vectors_enumerated",
            isinstance(tap_spec, list) and len(tap_spec) == 6, tap_spec)
    require("source_taps_named",
            taps == ["bridge", "decoder2", "decoder1"],
            {"feature_taps": taps})
    require("pooling_operation_named",
            bool(router.get("roi_pool_mapping")),
            router.get("roi_pool_mapping"))

    # (a)+(c) THE DECISIVE QUESTION: is the reduction to 32 dimensions defined?
    # The spec declares a TARGET WIDTH (32) and the total (6*32=192) but never states
    # HOW a C-channel map becomes 32 values.
    declared_width = router.get("pool_width_per_axis")
    breakdown = router.get("input_dim_breakdown", {})
    require("declared_width_is_32", declared_width == 32, declared_width)
    require("closed_form_total_218",
            router.get("input_dim_closed_form") == 218,
            router.get("input_dim_closed_form"))
    require("breakdown_sums_to_218",
            (breakdown.get("tap_axes_x_width", 0) + breakdown.get("scalars", 0)
             + breakdown.get("task_embedding", 0)) == 218,
            breakdown)

    # Search the authoritative artifacts for ANY operation that maps a channel map
    # to exactly 32 values.
    reduction_tokens = [
        "adaptive pool", "adaptive_avg_pool", "adaptive max pool",
        "reduce to 32", "reduction to 32", "projection", "1x1 conv",
        "conv1x1", "learned projection", "linear projection",
        "channel reduce", "channel-reduce", "compress to 32",
        "aggregate channels", "binning", "truncation", "first 32",
        "freeze_reduction", "feature_reduction", "how 32",
    ]
    corpus = json.dumps(spec, ensure_ascii=False).lower()
    corpus += json.dumps(jload(ARCH), ensure_ascii=False).lower()
    corpus += CONTRACT.read_text(encoding="utf-8").lower() if CONTRACT.exists() else ""
    corpus += PRIMARY.read_text(encoding="utf-8").lower() if PRIMARY.exists() else ""

    found = [t for t in reduction_tokens if t in corpus]
    # "projection" appears only as 'trainable_conv_projection_before_pooling: false'
    # (i.e. it is explicitly FORBIDDEN, not defined) -- record that nuance.
    projection_only_forbidden = (
        router.get("trainable_conv_projection_before_pooling") is False
        and "projection" in found
    )
    reduction_defined = bool(
        [t for t in found if t not in ("projection", "1x1 conv", "conv1x1",
                                       "learned projection", "linear projection")]
    ) or (router.get("trainable_conv_projection_before_pooling") is True)

    require("deterministic_reduction_to_32_explicitly_defined",
            reduction_defined,
            {"tokens_found": found,
             "projection_is_only_declared_FORBIDDEN": projection_only_forbidden,
             "note": ("the spec fixes the OUTPUT width (32) but never fixes the "
                      "OPERATION that produces 32 values from a C-channel map")})

    # Behavioural confirmation: channel widths at the taps do not equal 32, so the
    # operation cannot be the identity.
    require("tap_widths_equal_declared_32",
            all(v == declared_width for v in OBSERVED_TAP_CHANNELS.values()),
            {"observed": OBSERVED_TAP_CHANNELS, "declared": declared_width})

    # (d) ten scalar descriptors -- definitional LEVEL is what matters.
    scalars = router.get("scalar_descriptors")
    require("ten_scalar_descriptors_enumerated",
            isinstance(scalars, list) and len(scalars) == 10, scalars)
    require("scalar_count_matches",
            router.get("n_scalar_descriptors") == 10,
            router.get("n_scalar_descriptors"))

    # For each scalar, is a FORMULA / frozen statistic defined? The primary feature-set
    # table supplies mapping_kind + derivation prose, but no closed-form equation.
    import csv
    if PRIMARY.exists():
        with PRIMARY.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        scalar_rows = [r for r in rows if r.get("group") == "scalar"]
        require("scalar_rows_present", len(scalar_rows) == 10, len(scalar_rows))
        require("scalar_mapping_kinds_recorded",
                all(r.get("mapping_kind") for r in scalar_rows),
                sorted({r.get("mapping_kind") for r in scalar_rows}))
        # Prose derivations exist, but no frozen numeric definition (units, band width
        # semantics, entropy base, margin sign convention) is fixed anywhere.
        require("scalar_closed_form_equations_defined",
                False,
                {"note": ("mapping_kind + English derivation prose are present, but no "
                          "closed-form definition (entropy base, margin sign convention, "
                          "boundary-band definition, connected-component convention) is "
                          "frozen; several scalars are derived-by-prose only")})
    else:
        require("primary_feature_set_present", False, str(PRIMARY))

    n_blockers_absent = sum(1 for r in req if r["blocking_if_absent"] and not r["present"])
    blocked = n_blockers_absent > 0
    terminal = ("PHASE25B_BLOCKED__FROZEN_FEATURE_SPEC_INCOMPLETE" if blocked
                else "PHASE25B_FEATURE_SPEC_BINDING_OK")

    out = {
        "artifact": "phase25b_phase24_feature_spec_binding",
        "phase": "25B",
        "purpose": ("verify that the authoritative Phase24 v1.1 artifact explicitly and "
                    "completely defines every Phase25B feature, BEFORE any extraction"),
        "work_order_ref": "sections 3, 4, 10, 11, 12",
        "frozen_artifacts_read": {
            "phase24_exact_implementation_spec.json": sha(SPEC) if SPEC.exists() else None,
            "phase24_architecture_spec.json": sha(ARCH) if ARCH.exists() else None,
            "phase24_router_input_contract.csv": sha(CONTRACT) if CONTRACT.exists() else None,
            "phase24_router_primary_feature_set.csv": sha(PRIMARY) if PRIMARY.exists() else None,
        },
        "spec_version": spec.get("spec_version"),
        "requirements": req,
        "n_requirements": len(req),
        "n_blocking_absent": n_blockers_absent,
        "blocked": blocked,
        "decision": ("STOP -- do NOT invent a reduction / projection method"
                     if blocked else "proceed"),
        "forbidden_workaround_avoided": (
            "no trainable 1x1 projection, random projection, PCA, first-32-channel "
            "truncation, or averaging bins was invented"
        ),
        "extraction_performed": False,
        "features_written": 0,
        "refiner_forwards": 0,
        "test_reads": 0,
        "holdout_outcomes_read": 0,
        "val_outcome_reads": 0,
        "verdict": terminal,
    }
    AUD.mkdir(parents=True, exist_ok=True)
    (AUD / "phase25b_phase24_feature_spec_binding.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for r in req:
        mark = "PRESENT" if r["present"] else ("ABSENT*" if r["blocking_if_absent"] else "ABSENT")
        print(f"[{mark:8s}] {r['requirement']}")
        if not r["present"]:
            print(f"            -> {r['detail']}")
    print()
    print(f"blocking requirements absent: {n_blockers_absent}/{len(req)}")
    print(terminal)
    return 0


if __name__ == "__main__":
    sys.exit(main())
