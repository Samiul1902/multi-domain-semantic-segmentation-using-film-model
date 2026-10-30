"""Synthetic-fixture tests for the EXT-03 completion-summary generator v1.1.

NO training, NO model inference, NO real dataset access. Fixtures are synthetic
registries plus tiny `torch.save`d dictionaries written into a temporary
directory; nothing outside `tempfile.mkdtemp()` is created or modified.

Each case asserts a specific fail-closed code, so the suite proves the v1.1
guards actually fire rather than merely existing.

Run:
    python scripts/analysis/tests/test_ext03_completion_summary_v1_1.py
Exit code 0 iff every case behaves as specified.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
GEN_PATH = REPO / "scripts" / "analysis" / "ext03_matrix_completion_summary_v1_1.py"

_spec = importlib.util.spec_from_file_location("ext03_gen_v11", GEN_PATH)
gen = importlib.util.module_from_spec(_spec)
sys.modules["ext03_gen_v11"] = gen
_spec.loader.exec_module(gen)

ARCHS = gen.ARCHS
SEEDS = gen.SEEDS
RESULTS: list[tuple[str, bool, str]] = []


def build_fixture(root: Path, mutate=None) -> tuple[Path, Path]:
    """Create a synthetic registry + runs tree. Returns (registry_path, runs_dir)."""
    runs = root / "runs"
    reg = {"runs": {}}
    for ai, a in enumerate(ARCHS):
        for si, s in enumerate(SEEDS):
            rid = f"{a}_seed{s}"
            bm = 0.50 + 0.01 * si + 0.001 * ai
            be = 20 + 5 * si
            ce = min(gen.MAX_EPOCHS, be + gen.PATIENCE)
            d = runs / rid
            d.mkdir(parents=True, exist_ok=True)
            p = d / "best.pt"
            torch.save({"model": {}, "epoch": be, "macro": bm}, p)
            reg["runs"][rid] = {
                "run_id": rid,
                "architecture": a,
                "seed": s,
                "status": "COMPLETE",
                "best_metric": bm,
                "best_epoch": be,
                "current_epoch": ce,
                "checkpoint_sha": hashlib.sha256(p.read_bytes()).hexdigest(),
                "resume_count": 0,
                "lr_used": None,
                "lr_source": None,
                "start_time": "synthetic",
                "completion_time": "synthetic",
            }
    if mutate is not None:
        mutate(reg)
    rp = root / "registry.json"
    rp.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    return rp, runs


def expect_abort(name: str, code: str, mutate, tamper=None) -> None:
    root = Path(tempfile.mkdtemp(prefix="ext03v11_"))
    try:
        rp, runs = build_fixture(root, mutate)
        if tamper is not None:
            tamper(runs)
        try:
            gen.build_summary({}, runs, rp, GEN_PATH)
        except gen.AuditAbort as exc:
            ok = exc.code == code
            RESULTS.append((name, ok, f"got {exc.code}" + ("" if ok else f", expected {code}")))
            return
        except Exception as exc:  # unexpected failure type
            RESULTS.append((name, False, f"unexpected {type(exc).__name__}: {exc}"))
            return
        RESULTS.append((name, False, f"no abort raised, expected {code}"))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def case_happy_path() -> None:
    root = Path(tempfile.mkdtemp(prefix="ext03v11_"))
    try:
        rp, runs = build_fixture(root)
        s = gen.build_summary({}, runs, rp, GEN_PATH)

        ok = len(s["per_run"]) == 15
        detail = [f"per_run={len(s['per_run'])}"]

        ranked = [r["architecture"] for r in s["family_ranking"]]
        ok &= ranked == sorted(ARCHS, key=lambda a: -s["families"][a]["mean_macro_dice"])
        detail.append(f"ranking={ranked}")

        ok &= all(v["sd_convention"] == "sample_standard_deviation_n_minus_1"
                  for v in s["families"].values())
        ok &= s["constants"]["sd_convention"] == "sample_standard_deviation_n_minus_1"

        from datetime import datetime
        dt = datetime.fromisoformat(s["generated_utc"])
        ok &= dt.tzinfo is not None
        detail.append(f"utc={s['generated_utc']}")

        ok &= len(s["binding"]["registry_sha256"]) == 64
        ok &= len(s["binding"]["generator_sha256"]) == 64
        ok &= s["access_statements"]["reads_under_test_manifest"] == 0
        ok &= s["access_statements"]["reads_under_router_holdout"] == 0
        ok &= all("forbidden" not in p.lower() for p in s["access_statements"]["files_read"])

        for a in ARCHS:
            vals = [r["best_macro_dice"] for r in s["per_run"] if r["architecture"] == a]
            ok &= abs(s["families"][a]["mean_macro_dice"] - sum(vals) / 3) < 1e-12
            ok &= abs(s["families"][a]["sd_macro_dice"] - math.sqrt(
                sum((v - sum(vals) / 3) ** 2 for v in vals) / 2)) < 1e-12

        RESULTS.append(("happy_path_all_guards_pass", bool(ok), "; ".join(detail)))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def case_write_once() -> None:
    root = Path(tempfile.mkdtemp(prefix="ext03v11_"))
    try:
        p = root / "out.json"
        gen._write_once(p, b"first")
        try:
            gen._write_once(p, b"second")
            RESULTS.append(("write_once_json_refuses_second_write", False, "second write succeeded"))
        except gen.AuditAbort as exc:
            ok = exc.code == "E_OUTPUT_EXISTS" and p.read_bytes() == b"first"
            RESULTS.append(("write_once_json_refuses_second_write", ok, exc.code))
        c = root / "out.csv"
        gen._write_once(c, b"a")
        try:
            gen._write_once(c, b"b")
            RESULTS.append(("write_once_csv_refuses_second_write", False, "second write succeeded"))
        except gen.AuditAbort as exc:
            ok = exc.code == "E_OUTPUT_EXISTS" and c.read_bytes() == b"a"
            RESULTS.append(("write_once_csv_refuses_second_write", ok, exc.code))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def case_forbidden_read() -> None:
    root = Path(tempfile.mkdtemp(prefix="ext03v11_"))
    try:
        bad = root / "manifests" / "phase4_v2" / "test.csv"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("x", encoding="utf-8")
        try:
            gen._read(bad)
            RESULTS.append(("forbidden_read_blocked", False, "read succeeded"))
        except gen.AuditAbort as exc:
            RESULTS.append(("forbidden_read_blocked", exc.code == "E_FORBIDDEN_READ", exc.code))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    case_happy_path()
    case_write_once()
    case_forbidden_read()

    expect_abort("sha_absent_null", "E_SHA_ABSENT",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("checkpoint_sha", None))
    expect_abort("sha_absent_key_deleted", "E_SHA_ABSENT",
                 lambda r: r["runs"]["unet_seed42"].pop("checkpoint_sha"))
    expect_abort("sha_absent_empty_string", "E_SHA_ABSENT",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("checkpoint_sha", ""))
    expect_abort("sha_malformed_short", "E_SHA_MALFORMED",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("checkpoint_sha", "abc123"))
    expect_abort("sha_malformed_uppercase", "E_SHA_MALFORMED",
                 lambda r: r["runs"]["unet_seed42"].__setitem__(
                     "checkpoint_sha", r["runs"]["unet_seed42"]["checkpoint_sha"].upper()))
    expect_abort("status_not_complete", "E_STATUS",
                 lambda r: r["runs"]["unetpp_seed123"].__setitem__("status", "RUNNING"))
    expect_abort("architecture_mismatch", "E_ARCH",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("architecture", "unetpp"))
    expect_abort("seed_mismatch_in_entry", "E_SEED",
                 lambda r: r["runs"]["unet_seed123"].__setitem__("seed", 7))
    expect_abort("run_missing", "E_RUN_MISSING",
                 lambda r: r["runs"].pop("segformer_b0_seed3407"))
    expect_abort("run_unexpected", "E_RUN_UNEXPECTED",
                 lambda r: r["runs"].__setitem__("unet_seed999", dict(r["runs"]["unet_seed42"], run_id="unet_seed999")))
    expect_abort("stopping_rule_violated", "E_STOPPING_RULE",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("current_epoch", 99))
    expect_abort("best_epoch_gt_current", "E_BEST_EPOCH_GT_CURRENT",
                 lambda r: (r["runs"]["unet_seed42"].__setitem__("best_epoch", 50),
                            r["runs"]["unet_seed42"].__setitem__("current_epoch", 40)))
    expect_abort("metric_out_of_range_high", "E_METRIC_RANGE",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("best_metric", 1.5))
    expect_abort("metric_zero", "E_METRIC_RANGE",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("best_metric", 0.0))
    expect_abort("metric_nan", "E_METRIC_RANGE",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("best_metric", float("nan")))
    expect_abort("metric_not_a_number", "E_METRIC_TYPE",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("best_metric", "0.62"))
    expect_abort("checkpoint_absent", "E_CHECKPOINT_ABSENT", lambda r: None,
                 tamper=lambda runs: (runs / "unet_seed42" / "best.pt").unlink())
    expect_abort("checkpoint_sha_mismatch", "E_CHECKPOINT_SHA_MISMATCH", lambda r: None,
                 tamper=lambda runs: (runs / "unet_seed42" / "best.pt").write_bytes(b"tampered"))
    expect_abort("checkpoint_epoch_mismatch", "E_CKPT_EPOCH_MISMATCH",
                 lambda r: (r["runs"]["unet_seed42"].__setitem__("best_epoch", 21),
                            r["runs"]["unet_seed42"].__setitem__("current_epoch", 36)))
    expect_abort("checkpoint_macro_mismatch", "E_CKPT_MACRO_MISMATCH",
                 lambda r: r["runs"]["unet_seed42"].__setitem__("best_metric", 0.7777))

    width = max(len(n) for n, _, _ in RESULTS)
    passed = 0
    for name, ok, detail in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
        passed += 1 if ok else 0
    print()
    print(f"{passed}/{len(RESULTS)} cases passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
