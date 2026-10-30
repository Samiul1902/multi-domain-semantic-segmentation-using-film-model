#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0d MODEL-FREE rank-contract unit tests for the repaired Grad-CAM target scalar.

This script is MODEL-FREE and CPU-ONLY. It MUST NOT and DOES NOT:
  * construct GlobalMedFiLM or B_phi;
  * torch.load any checkpoint;
  * execute any model on CUDA;
  * read any dataset;
  * read any real persisted p_global array.

It exercises the REAL repaired helper imported from
`scripts/analysis/phase35_interpretability_execution_v1_0d.py` (so the tested object is the exact
object that scientific Grad-CAM and the smoke path call).

A separate, clearly-labelled reproduction test calls the FROZEN DEFECTIVE v1.0b helper on a tiny CPU
tensor to document `PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY`. That call involves no
model, no checkpoint, no autograd and no data; it is defect documentation, not execution.

Writes reports/audits/phase35_gradcam_target_rank_unit_v1_0d.json (write-once).

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_gradcam_target_rank_unit_v1_0d.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import phase35_interpretability_execution_v1_0d as D          # noqa: E402  (repaired helper)
import phase35_interpretability_execution_v1_0b as V0B        # noqa: E402  (defective helper, repro only)

AUD = ROOT / "reports" / "audits"
OUT = AUD / "phase35_gradcam_target_rank_unit_v1_0d.json"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0d"

RESULTS = []


def rec(name, expected, observed, ok, note=""):
    RESULTS.append(OrderedDict([("test", name), ("expected", expected), ("observed", observed),
                                ("pass", bool(ok)), ("note", note)]))
    return bool(ok)


def expect_raise(fn, *args, **kwargs):
    """Return (raised: bool, exc_type: str|None, message: str|None)."""
    try:
        fn(*args, **kwargs)
    except Exception as e:                                   # noqa: BLE001 (fail-closed contract)
        return True, type(e).__name__, str(e)
    return False, None, None


def main():
    import torch
    gen = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    logits = torch.arange(16, dtype=torch.float32).reshape(1, 1, 4, 4)
    assert tuple(logits.shape) == (1, 1, 4, 4)
    assert logits.device.type == "cpu"
    assert not logits.requires_grad

    # ---------------- Test 1: non-empty rank-2 mask ----------------
    m1 = torch.zeros(4, 4, dtype=torch.bool)
    m1[0:2, 0:2] = True
    sel = logits[0, 0][m1].tolist()
    t1 = D.gradcam_target_scalar_rank_safe(logits, m1)
    rec("T1_nonempty_rank2_mask", 2.5, float(t1), float(t1) == 2.5,
        note=f"selected values {sel}; mean = 2.5; returns 0-dim tensor")

    # ---------------- Test 2: empty mask -> full-field fallback ----------------
    m2 = torch.zeros(4, 4, dtype=torch.bool)
    t2 = D.gradcam_target_scalar_rank_safe(logits, m2)
    rec("T2_empty_mask_full_field_fallback", 7.5, float(t2), float(t2) == 7.5,
        note="mean over the full [0,0,4,4] foreground plane")

    # ---------------- Test 3: spatial mismatch must fail closed ----------------
    m3 = torch.zeros(3, 4, dtype=torch.bool)
    raised, etype, msg = expect_raise(D.gradcam_target_scalar_rank_safe, logits, m3)
    rec("T3_spatial_mismatch_rejected", "fail_closed", {"raised": raised, "exc": etype},
        raised, note=msg or "")

    # ---------------- Test 4: rank mismatch must fail closed ----------------
    m4 = torch.zeros(1, 1, 4, 4, dtype=torch.bool)
    raised, etype, msg = expect_raise(D.gradcam_target_scalar_rank_safe, logits, m4)
    rec("T4_rank4_mask_rejected", "fail_closed", {"raised": raised, "exc": etype},
        raised, note=(msg or "") + " | the scientific contract is deliberately rank 2")

    # ---------------- Test 5: non-Boolean mask must fail closed ----------------
    m5f = torch.zeros(4, 4, dtype=torch.float32)
    r5f, e5f, msg5f = expect_raise(D.gradcam_target_scalar_rank_safe, logits, m5f)
    rec("T5a_float_mask_rejected", "fail_closed", {"raised": r5f, "exc": e5f}, r5f, note=msg5f or "")
    m5i = torch.zeros(4, 4, dtype=torch.int64)
    r5i, e5i, msg5i = expect_raise(D.gradcam_target_scalar_rank_safe, logits, m5i)
    rec("T5b_integer_mask_rejected", "fail_closed", {"raised": r5i, "exc": e5i}, r5i, note=msg5i or "")

    # ---------------- Additional logits-contract tests ----------------
    m_ok = torch.zeros(4, 4, dtype=torch.bool)
    m_ok[0, 0] = True
    r6, e6, msg6 = expect_raise(D.gradcam_target_scalar_rank_safe,
                                torch.zeros(4, 4, dtype=torch.float32), m_ok)
    rec("T6_logits_rank3_rejected", "fail_closed", {"raised": r6, "exc": e6}, r6, note=msg6 or "")
    r7, e7, msg7 = expect_raise(D.gradcam_target_scalar_rank_safe,
                                torch.zeros(2, 1, 4, 4, dtype=torch.float32), m_ok)
    rec("T7_logits_batch2_rejected", "fail_closed", {"raised": r7, "exc": e7}, r7, note=msg7 or "")
    r8, e8, msg8 = expect_raise(D.gradcam_target_scalar_rank_safe,
                                torch.zeros(1, 2, 4, 4, dtype=torch.float32), m_ok)
    rec("T8_logits_channels2_rejected", "fail_closed", {"raised": r8, "exc": e8}, r8, note=msg8 or "")

    # ---------------- numpy rank-2 bool mask is accepted (canonical representation) ----------------
    import numpy as np
    m_np = np.zeros((4, 4), dtype=bool)
    m_np[0:2, 0:2] = True
    t9 = D.gradcam_target_scalar_rank_safe(logits, m_np)
    rec("T9_numpy_rank2_bool_mask_accepted", 2.5, float(t9), float(t9) == 2.5,
        note="rank-2 numpy Boolean is the canonical mask representation")

    # ---------------- DEFECT REPRODUCTION (frozen defective helper; model-free) ----------------
    raised, etype, msg = expect_raise(V0B.gradcam_target_scalar, logits, m1)
    rec("D1_frozen_v1_0b_logits_mask_indexing_reproduced", "IndexError", {"raised": raised,
                                                                          "exc": etype},
        raised and etype == "IndexError",
        note=(msg or "") + " | frozen v1.0b `logits[mask]` on rank-4 logits with a rank-2 mask")

    n_total = len(RESULTS)
    n_failed = sum(1 for r in RESULTS if not r["pass"])
    all_pass = n_failed == 0

    artifact = OrderedDict([
        ("artifact", "phase35_gradcam_target_rank_unit_v1_0d"),
        ("phase", 35), ("section", "\u00A7G"), ("method", "RA-MedFiLM-BARR"), ("revision", REVISION),
        ("classification", "MODEL_FREE_CPU_TENSOR_UNIT_TESTS__NOT_SCIENTIFIC_EXECUTION"),
        ("tested_object", {
            "module": "scripts/analysis/phase35_interpretability_execution_v1_0d.py",
            "function": "gradcam_target_scalar_rank_safe",
            "is_the_scientific_and_smoke_helper": True,
        }),
        ("defect_reproduction_target", {
            "module": "scripts/analysis/phase35_interpretability_execution_v1_0b.py",
            "function": "gradcam_target_scalar",
            "defect_id": "PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY",
        }),
        ("device", "cpu"), ("dtype", "float32"), ("cuda_used", False),
        ("results", RESULTS), ("n_tests", n_total), ("n_failed", n_failed),
        ("all_pass", all_pass),
        ("execution_counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0),
            ("model_forwards", 0), ("model_autograd_calls", 0), ("gradcam_executions", 0),
            ("router_attribution_executions", 0), ("raw_val_reads", 0),
            ("real_persisted_p_global_reads", 0), ("gt_reads", 0),
            ("router_holdout_reads", 0), ("test_reads", 0), ("training_steps", 0),
            ("model_free_cpu_unit_tests", n_total),
        ])),
        ("generated_utc", gen),
    ])
    if OUT.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {OUT}")
    OUT.write_text(json.dumps(artifact, indent=1) + "\n", encoding="utf-8")
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()

    print("=== PHASE35 v1.0d MODEL-FREE GRAD-CAM TARGET RANK UNIT TESTS ===")
    print("device: cpu | cuda used: False | models constructed: 0 | checkpoints loaded: 0")
    for r in RESULTS:
        print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['test']:46s} "
              f"expected={r['expected']} observed={r['observed']}")
    print(f"TOTAL: {n_total} tests, {n_failed} failed | all_pass: {all_pass}")
    print(f"{sha}  {OUT.relative_to(ROOT)}")
    return 0 if all_pass else 3


if __name__ == "__main__":
    raise SystemExit(main())
