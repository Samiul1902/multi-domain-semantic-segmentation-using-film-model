"""Phase D — GPU performance, reliability and reproducibility harness.

Every subcommand writes one JSON document under ``reports/performance/phase_d/``
and prints a short summary.  Nothing here trains a model on real data, scores a
protected split, or touches an institutional trust store.

Why a CLI rather than only a test module
---------------------------------------
Three of the measurements cannot run inside pytest on this host: the DataLoader
worker sweep spawns processes (Windows re-imports the calling module, so it needs
a ``__main__`` guard), the capacity search deliberately provokes OOM, and the
full sweep takes minutes.  Keeping them behind an explicit entry point means the
test suite stays fast and deterministic while the heavy measurement is still
reproducible by anyone with one command.

Evidence label
--------------
Every document this script writes carries ``evidence_class`` from
:mod:`src.research.performance.bench`, currently ``SYNTHETIC_BENCHMARK``.  No
number produced here is a real-data segmentation result.
"""
from __future__ import annotations

import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:                                  # pragma: no cover
    sys.path.insert(0, str(REPO))

OUTPUT_ROOT = REPO / "reports" / "performance" / "phase_d"
EVIDENCE_CLASS = "SYNTHETIC_BENCHMARK"


def _write(name: str, payload: Dict[str, Any]) -> Path:
    """Write one document atomically, through the Phase C writer."""
    from src.research.evaluation import provenance as PROV

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_ROOT / name
    PROV.atomic_write_json(path, payload)
    return path


def _environment() -> Dict[str, Any]:
    import torch

    return {"platform": platform.platform(), "python": platform.python_version(),
            "torch": torch.__version__, "cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version() if torch.cuda.is_available() else None,
            "device": (torch.cuda.get_device_name(0)
                       if torch.cuda.is_available() else "cpu"),
            "evidence_class": EVIDENCE_CLASS}


# --------------------------------------------------------------------------- #
# Git state
# --------------------------------------------------------------------------- #
def cmd_git(args: argparse.Namespace) -> int:
    """Record HEAD, branch and the changed-file list at report time."""
    import subprocess

    def git(*argv: str) -> str:
        try:
            return subprocess.run(["git", *argv], cwd=REPO, capture_output=True,
                                  text=True, check=False).stdout.strip()
        except OSError:                                   # pragma: no cover - no git
            return ""

    changed = [line for line in git("status", "--porcelain").splitlines() if line]
    doc = {"schema": "phase_d_git_state_v1", "evidence_class": EVIDENCE_CLASS,
           "head": git("rev-parse", "HEAD"),
           "commit": git("rev-parse", "HEAD"),
           "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
           "changed_files": changed,
           "n_changed_files": len(changed),
           "note": ("HEAD is captured before the Phase D commit; deliverable 13 records "
                    "the commit hash produced by this phase.")}
    path = _write("git.json", doc)
    print(f"git -> {path}")
    print(f"  HEAD {doc['head']} on {doc['branch']} ({len(changed)} changed paths)")
    return 0


# --------------------------------------------------------------------------- #
# §2 Benchmark
# --------------------------------------------------------------------------- #
def cmd_benchmark(args: argparse.Namespace) -> int:
    from src.research.performance import bench as B
    from src.research.evaluation import registry as REG

    seeds = [int(s) for s in args.seeds.split(",")]
    doc = B.full_sweep(seeds=seeds, device=args.device, warmup=args.warmup,
                       repeats=args.repeats,
                       batch_scaling=not args.no_batch_scaling,
                       precision=not args.no_precision)
    doc["environment"] = _environment()
    path = _write("benchmark.json", doc)

    print(f"benchmark -> {path}")
    print(f"  {'model':34} {'init':>8} {'forward':>9} {'pipeline':>9} "
          f"{'p95':>8} {'allocMiB':>9}")
    for record in doc["records"]:
        fwd = record["model_forward_ms"] or {}
        pipe = record["pipeline_ms"] or {}
        init = record["initialization_ms"] or {}
        mem = (record.get("memory") or {}).get("peak_allocated_mib")
        print(f"  {record['model_key']:34} "
              f"{(init.get('median') or 0):8.2f} "
              f"{(fwd.get('median') or 0):9.2f} "
              f"{(pipe.get('median') or 0):9.2f} "
              f"{(pipe.get('p95') or 0):8.2f} "
              f"{(mem or 0):9.1f}")
    print(f"  preprocessing {doc['preprocessing']['median']:.2f} ms")
    return 0


# --------------------------------------------------------------------------- #
# §3 Conditional computation
# --------------------------------------------------------------------------- #
def cmd_conditional(args: argparse.Namespace) -> int:
    from src.research.performance import conditional as C

    seeds = [int(s) for s in args.seeds.split(",")]
    doc = C.benchmark_all_scenarios(device=args.device, seeds=seeds,
                                    warmup=args.warmup, repeats=args.repeats)
    doc["environment"] = _environment()
    path = _write("conditional.json", doc)

    print(f"conditional -> {path}")
    for record in doc["records"]:
        counts = record["component_invocations"]
        print(f"  {record['model_key']:6} {record['scenario']:15} "
              f"{record['observed_state']:20} "
              f"{record['branch_latency_ms']['median']:7.2f} ms  "
              f"G{counts.get('global', 0)} R{counts.get('router', 0)} "
              f"F{counts.get('refiner', 0)} S{counts.get('safety', 0)}")
    for comp in doc["comparisons"]:
        print(f"  {comp['model_key']:6} global {comp['global_only_ms']['median']:.2f} "
              f"always {comp['always_refine_ms']['median']:.2f} "
              f"conditional {comp['conditional_ms']['median']:.2f} ms  "
              f"effective MAC {comp['effective_macs_per_image']} "
              f"of {comp['macs_if_always_refine']}")
    return 0


# --------------------------------------------------------------------------- #
# §4 Memory
# --------------------------------------------------------------------------- #
def cmd_memory(args: argparse.Namespace) -> int:
    from src.research.performance import memory as M

    batches = tuple(int(b) for b in args.batches.split(","))
    doc = M.memory_report(device=args.device, batches=batches, steps=args.steps)
    doc["environment"] = _environment()
    # The transfer measurement always runs: workers=0 pinned and unpinned are the two
    # configurations that isolate host-to-device cost from worker spawn. --workers only
    # ADDS a worker configuration; it must not gate the measurement, or --transfer-batches
    # is silently ignored (Phase D defect: batches stayed at the library default of 6).
    modes = [(0, False), (0, True)]
    if args.workers:
        modes.append((int(args.workers), True))
    doc["transfer"] = [M.dataloader_overhead(workers=w, pin_memory=p,
                                             batches=args.transfer_batches,
                                             device=args.device)
                       for w, p in modes]
    path = _write("memory.json", doc)

    print(f"memory -> {path}")
    for row in doc["training"]:
        print(f"  {row['stage']:8} batch {row['batch']:2} "
              f"alloc {row['peak_allocated_mib']:8.1f} "
              f"reserved {row['peak_reserved_mib']:8.1f} MiB")
    for row in doc["inference"]:
        print(f"  infer {row['model_key']:26} "
              f"alloc {row['peak_allocated_mib']:8.1f} "
              f"reserved {row['peak_reserved_mib']:8.1f} MiB")
    for row in doc["capacity"]:
        print(f"  capacity {row['stage']:8} max batch {row['max_batch']}")
    return 0


# --------------------------------------------------------------------------- #
# §5 Determinism
# --------------------------------------------------------------------------- #
def cmd_determinism(args: argparse.Namespace) -> int:
    from src.research.performance import determinism as D

    doc = D.reproducibility_report(device=args.device, seed=args.seed)
    doc["environment"] = _environment()
    path = _write("determinism.json", doc)
    print(f"determinism -> {path}")
    for check in doc["checks"]:
        print(f"  {'PASS' if check['passed'] else 'FAIL'}  {check['check']}: "
              f"{check['detail']}")
    return 0


# --------------------------------------------------------------------------- #
# §6 FiLM conditioning
# --------------------------------------------------------------------------- #
def cmd_film(args: argparse.Namespace) -> int:
    from src.research.performance import film as F

    doc = F.film_report(device=args.device, seed=args.seed)
    doc["environment"] = _environment()
    path = _write("film_conditioning.json", doc)
    print(f"film -> {path}")
    for check in doc["checks"]:
        print(f"  {'PASS' if check['passed'] else 'FAIL'}  {check['check']}: "
              f"{check['detail']}")
    return 0


# --------------------------------------------------------------------------- #
# §7 Failure injection
# --------------------------------------------------------------------------- #
def cmd_failures(args: argparse.Namespace) -> int:
    from src.research.performance import failures as FL

    doc = FL.failure_report(workdir=OUTPUT_ROOT / "_failure_injection")
    doc["environment"] = _environment()
    path = _write("failure_injection.json", doc)
    print(f"failures -> {path}")
    for row in doc["injections"]:
        print(f"  {'DETECTED' if row['detected'] else 'MISSED  '}  "
              f"{row['stage']:24} via {row['detected_by']}: {row['detail'][:90]}")
    print(f"  {doc['n_detected']}/{doc['n_injections']} detected")
    return 0


# --------------------------------------------------------------------------- #
# §8 Evidence isolation
# --------------------------------------------------------------------------- #
def cmd_isolation(args: argparse.Namespace) -> int:
    from src.research.performance import isolation as ISO

    doc = ISO.run_all_attacks(OUTPUT_ROOT / "_isolation_attacks")
    doc["environment"] = _environment()
    path = _write("evidence_isolation.json", doc)
    print(f"isolation -> {path}")
    for row in doc["attacks"]:
        print(f"  {'BLOCKED' if row['blocked'] else 'MISSED '}  {row['attack']:26} "
              f"via {row['blocked_by']}")
    print(f"  {doc['n_blocked']}/{doc['n_attacks']} blocked")
    return 0


# --------------------------------------------------------------------------- #
# §10 Stability, §11 parity
# --------------------------------------------------------------------------- #
def cmd_stability(args: argparse.Namespace) -> int:
    from src.research.performance import stability as S

    doc = S.stability_report(device=args.device, seed=args.seed,
                             cycles=args.cycles)
    doc["environment"] = _environment()
    path = _write("stability.json", doc)
    print(f"stability -> {path}")
    for check in doc["checks"]:
        print(f"  {'PASS' if check['passed'] else 'FAIL'}  {check['check']}: "
              f"{check['detail']}")
    return 0


def cmd_parity(args: argparse.Namespace) -> int:
    from src.research.performance import stability as S

    doc = S.parity_report(device=args.device, seed=args.seed)
    doc["environment"] = _environment()
    path = _write("cpu_cuda_parity.json", doc)
    print(f"parity -> {path}")
    for row in doc["records"]:
        print(f"  {row['model_key']:26} shape {row['shape_match']} "
              f"finite {row['both_finite']} max|d| {row['max_abs_difference']:.3e} "
              f"bin agree {row['binary_agreement']:.4f} "
              f"state {row['state_agreement']}")
    return 0


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# §13 Regression
# --------------------------------------------------------------------------- #
#: The §13 targeted set.  Each entry is one of the areas the mission enumerates.
TARGETED_SUITE = {
    "FULL pipeline": ["tests/test_full_pipeline.py"],
    "Lite pipeline": ["tests/test_lite_pipeline.py", "tests/test_ra_medfilm_barr_lite.py",
                      "tests/test_lite_evaluation.py"],
    "Architecture drift": ["tests/test_phase25_architecture_drift.py"],
    "Stage 6": ["tests/test_stage6_baselines.py", "tests/test_stage6_integration.py"],
    "Phase C evaluation": ["tests/test_evaluation_phase_c.py"],
    "Dataset and ROI": ["tests/test_oracle_roi.py", "tests/test_predicted_roi.py",
                        "tests/test_kub_dataset.py"],
    "Metrics and statistics": ["tests/test_evaluation_metrics.py",
                               "tests/test_segmentation_metrics.py",
                               "tests/test_object_metrics.py"],
    "Checkpoint recovery": ["tests/test_checkpointing.py"],
    "CUDA memory": ["tests/test_phase08_infrastructure.py"],
    "FiLM conditioning": ["tests/test_c1_film_preparation.py",
                          "tests/test_phase10_models.py"],
    "Evidence-class separation": ["tests/test_performance_phase_d.py",
                                  "tests/test_rc2_missing_store_isolation.py"],
}

#: How each known non-passing test is classified.  Anything absent from this map
#: defaults to ``new_regression``, so an unexpected failure can never be quietly
#: absorbed into a benign category.
CLASSIFICATION = {
    "tests/test_c1_launch_rc2.py::ProductionUnprovisionedTests::test_default_production_store_is_absent":
        ("environmental",
         "asserts the production trust store is ABSENT; on this host it exists and is "
         "internally self-consistent, so the gate refuses the authorization payload at "
         "signature verification instead. A stale host fact, not a code defect. The "
         "store was not modified and the check was not weakened; see "
         "tests/test_rc2_missing_store_isolation.py"),
}

_SUMMARY = re.compile(
    r"(?:(?P<failed>\d+) failed)?[, ]*"
    r"(?:(?P<passed>\d+) passed)?[, ]*"
    r"(?:(?P<skipped>\d+) skipped)?[, ]*"
    r"(?:(?P<xfailed>\d+) xfailed)?[, ]*"
    r"(?:(?P<error>\d+) error)?")


def _run_pytest(paths: List[str], *, basetemp: str, extra: Optional[List[str]] = None,
                timeout: int = 7200) -> Dict[str, Any]:
    """Run pytest and parse its summary, without hiding anything."""
    import re as _re
    import subprocess

    argv = [sys.executable, "-m", "pytest", "-q", "--no-header", "-rfE",
            f"--basetemp={basetemp}", "-p", "no:cacheprovider", *paths]
    if extra:
        argv.extend(extra)
    completed = subprocess.run(argv, cwd=REPO, capture_output=True, text=True,
                               timeout=timeout, check=False)
    stdout = completed.stdout or ""

    def _named(prefix: str) -> List[str]:
        return [line.split(" ", 1)[1].split(" - ")[0].strip()
                for line in stdout.splitlines() if line.startswith(prefix)]

    failed_tests = _named("FAILED ")
    # An ERROR is not a pass.  Without -rE pytest reports only the count, so the
    # errored test could never be named or classified — it would simply vanish
    # behind a non-zero "error" tally.
    errored_tests = _named("ERROR ")
    counts = {"failed": 0, "passed": 0, "skipped": 0, "xfailed": 0, "error": 0}
    parsed = False
    for line in reversed(stdout.splitlines()):
        match = _SUMMARY.search(line.strip())
        if match and any(match.group(k) for k in counts):
            for key in counts:
                value = match.group(key)
                if value:
                    counts[key] = int(value)
            parsed = True
            break
    # A collection error (or an interrupted run) exits non-zero with no summary line.
    # Returning 0 passed / 0 failed there would report a broken run as a clean one,
    # so the anomaly is carried explicitly and surfaced in the document.
    anomaly = None
    if completed.returncode != 0 and not parsed:
        anomaly = (f"pytest exited {completed.returncode} without a parseable summary; "
                   f"tail: {' | '.join(stdout.strip().splitlines()[-3:]) or '(no stdout)'}")
    elif completed.returncode not in (0, 1) and parsed:
        anomaly = (f"pytest exited {completed.returncode} (interrupted or internal error) "
                   f"despite a summary line")
    return {"counts": counts, "failed_tests": failed_tests,
            "errored_tests": errored_tests,
            "returncode": completed.returncode,
            "parsed": parsed,
            "anomaly": anomaly,
            "tail": "\n".join(stdout.strip().splitlines()[-6:]),
            "stderr_tail": "\n".join((completed.stderr or "").strip().splitlines()[-4:])}


def cmd_regression(args: argparse.Namespace) -> int:
    """Run the targeted set, then the broad suite when asked, and classify failures."""
    # A FRESH, explicitly scoped basetemp per run.  Reusing one directory across runs
    # is the stale-temp hazard §12 warns about: an interrupted run leaves fixtures
    # behind, and pytest then reports teardown errors ("assert not self._finalizers")
    # that belong to the harness, not to the tests.  Observed in Phase D: a reused
    # basetemp turned 34 clean passes into 34 errors.
    import time as _time

    stamp = _time.strftime("%Y%m%d_%H%M%S")
    basetemp = str(REPO / "_tmp" / f"phase_d_regression_{stamp}")
    Path(basetemp).mkdir(parents=True, exist_ok=True)

    targeted = _run_pytest(sorted({p for group in TARGETED_SUITE.values() for p in group}),
                           basetemp=basetemp)
    by_area: Dict[str, Any] = {}
    for index, (area, paths) in enumerate(TARGETED_SUITE.items()):
        # index-based, not hash-based: hash() is salted per process, so two areas
        # could in principle share a directory and cross-contaminate each other.
        by_area[area] = _run_pytest(paths, basetemp=f"{basetemp}_area{index:02d}")

    broad = None
    if args.broad:
        broad = _run_pytest(["tests"], basetemp=f"{basetemp}_broad")

    anomalies = {name: result["anomaly"]
                 for name, result in [("targeted", targeted),
                                      *[(f"area:{a}", r) for a, r in by_area.items()],
                                      *([("broad", broad)] if broad else [])]
                 if result.get("anomaly")}

    failures = list(targeted["failed_tests"])
    if broad:
        failures.extend(broad["failed_tests"])
    # Errored tests are classified alongside failures: a teardown or collection
    # error is a non-pass and must be named, not left inside a bare count.
    errored = list(targeted.get("errored_tests") or [])
    if broad:
        errored.extend(broad.get("errored_tests") or [])
    classification: Dict[str, Any] = {}
    new_regressions: List[str] = []
    for test in dict.fromkeys(failures):
        category, reason = CLASSIFICATION.get(
            test, ("new_regression", "unexpected: not a known pre-existing condition"))
        classification[test] = {"category": category, "reason": reason}
        if category == "new_regression":
            new_regressions.append(test)
    for test in dict.fromkeys(errored):
        if test in classification:
            continue
        category, reason = CLASSIFICATION.get(
            test, ("new_regression",
                   "errored (not failed): the test did not complete"))
        classification[test] = {"category": category, "reason": reason}
        if category == "new_regression":
            new_regressions.append(test)

    doc = {
        "schema": "phase_d_regression_v1",
        "evidence_class": EVIDENCE_CLASS,
        "targeted": targeted,
        "by_area": {area: result["counts"] for area, result in by_area.items()},
        "broad": broad,
        "passed": (broad or targeted)["counts"]["passed"],
        "failed": (broad or targeted)["counts"]["failed"],
        "skipped": (broad or targeted)["counts"]["skipped"],
        "xfailed": (broad or targeted)["counts"]["xfailed"],
        "failed_tests": failures,
        "errored_tests": errored,
        "classification": classification,
        "new_regressions": new_regressions,
        "pre_existing_defects": [t for t, c in classification.items()
                                 if c["category"] == "pre_existing_defect"],
        "environmental": [t for t, c in classification.items()
                          if c["category"] == "environmental"],
        "basetemp": basetemp,
        "anomalies": anomalies,
        "note": ("Failures are classified explicitly; anything not in the known map is "
                 "reported as a new regression rather than absorbed. An unparseable or "
                 "interrupted run is recorded in anomalies instead of being counted as "
                 "a clean pass."),
    }
    path = _write("regression.json", doc)
    print(f"regression -> {path}")
    print(f"  targeted: {targeted['counts']}")
    if broad:
        print(f"  broad:    {broad['counts']}")
    for test, info in classification.items():
        print(f"  {info['category']:20} {test}")
    for name, anomaly in anomalies.items():
        print(f"  ANOMALY {name}: {anomaly}")
    print(f"  new regressions: {len(new_regressions)}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from src.research.performance import report as RP

    doc = RP.build_report(OUTPUT_ROOT)
    path = _write("phase_d_summary.json", doc)
    markdown = RP.render_markdown(doc)
    md_path = OUTPUT_ROOT / "phase_d_completion_report.md"
    from src.research.evaluation import provenance as PROV

    PROV.atomic_write_text(md_path, markdown)
    print(f"report -> {path}")
    print(f"         {md_path}")
    print(f"  status: {doc['status']}")
    for item in doc["deliverables"]:
        print(f"  {'OK  ' if item['present'] else 'MISS'}  {item['index']:2d}. {item['name']}")
    for blocker in doc["12_blockers"]:
        print(f"  BLOCKER: {blocker}")
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    """Run the whole harness with one set of defaults.

    ``all`` is parsed by a bare subparser, so it has none of the per-command
    options; the defaults are filled in here rather than read off ``args`` with
    ``getattr`` everywhere.
    """
    merged = argparse.Namespace(
        device=getattr(args, "device", "cuda"),
        seed=getattr(args, "seed", 42),
        seeds=getattr(args, "seeds", "42,123,3407"),
        warmup=getattr(args, "warmup", 5),
        repeats=getattr(args, "repeats", 30),
        no_batch_scaling=False, no_precision=False,
        batches=getattr(args, "batches", "1,2,4"),
        steps=getattr(args, "steps", 2),
        workers=getattr(args, "workers", None),
        transfer_batches=getattr(args, "transfer_batches", 24),
        cycles=getattr(args, "cycles", 12),
        broad=getattr(args, "broad", False))
    steps = [cmd_git, cmd_benchmark, cmd_conditional, cmd_memory, cmd_determinism,
             cmd_film, cmd_failures, cmd_isolation, cmd_stability, cmd_parity,
             cmd_regression, cmd_report]
    for step in steps:
        code = step(merged)
        if code:
            return code
    return 0


# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase D performance, reliability and reproducibility harness")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
        p.add_argument("--device", default="cuda")
        p.add_argument("--seed", type=int, default=42)
        return p

    p = common(sub.add_parser("benchmark", help="§2 eight-model benchmark"))
    p.add_argument("--seeds", default="42,123,3407")
    p.add_argument("--warmup", type=int, default=5)
    p.add_argument("--repeats", type=int, default=30)
    p.add_argument("--no-batch-scaling", action="store_true")
    p.add_argument("--no-precision", action="store_true")
    p.set_defaults(func=cmd_benchmark)

    p = common(sub.add_parser("conditional", help="§3 routing scenarios"))
    p.add_argument("--seeds", default="42,123,3407")
    p.add_argument("--warmup", type=int, default=5)
    p.add_argument("--repeats", type=int, default=20)
    p.set_defaults(func=cmd_conditional)

    p = common(sub.add_parser("memory", help="§4 memory characterisation"))
    p.add_argument("--batches", default="1,2,4")
    p.add_argument("--steps", type=int, default=2)
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--transfer-batches", type=int, default=24)
    p.set_defaults(func=cmd_memory)

    common(sub.add_parser("determinism", help="§5 determinism and resume")).set_defaults(
        func=cmd_determinism)
    common(sub.add_parser("film", help="§6 FiLM conditioning")).set_defaults(func=cmd_film)
    common(sub.add_parser("failures", help="§7 failure injection")).set_defaults(
        func=cmd_failures)
    common(sub.add_parser("isolation", help="§8 evidence isolation")).set_defaults(
        func=cmd_isolation)
    p = common(sub.add_parser("stability", help="§10 resource stability"))
    p.add_argument("--cycles", type=int, default=12)
    p.set_defaults(func=cmd_stability)
    common(sub.add_parser("parity", help="§11 CPU/CUDA parity")).set_defaults(
        func=cmd_parity)
    sub.add_parser("report", help="assemble the Phase D summary").set_defaults(
        func=cmd_report)
    sub.add_parser("git", help="record HEAD and changed files").set_defaults(func=cmd_git)
    p = sub.add_parser("regression", help="§13 targeted and broad regression")
    p.add_argument("--broad", action="store_true", help="also run the whole tests/ tree")
    p.set_defaults(func=cmd_regression)
    p = common(sub.add_parser("all", help="run every subcommand in order"))
    p.add_argument("--seeds", default="42,123,3407")
    p.add_argument("--warmup", type=int, default=5)
    p.add_argument("--repeats", type=int, default=30)
    p.add_argument("--batches", default="1,2,4")
    p.add_argument("--steps", type=int, default=2)
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--cycles", type=int, default=12)
    p.add_argument("--broad", action="store_true")
    p.set_defaults(func=cmd_all)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
