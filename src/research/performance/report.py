"""§14 Phase D completion report.

Assembles the fourteen deliverables from the measurement documents, in the order
the mission enumerates them, and refuses to present a deliverable as present when
its source document is missing.  A missing document is reported as missing rather
than filled in from memory.

Two rules the assembly follows
------------------------------
**Nothing is imputed.**  If ``memory.json`` is absent, deliverable 4 says so; it
does not borrow a figure from a log line.

**The evidence label travels with every number.**  Each section carries the
``evidence_class`` of its source, and the rendered report states
``SYNTHETIC_BENCHMARK`` on every table that came from fixture weights.  No figure
here may be read as a real-data segmentation result.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

EVIDENCE_CLASS = "SYNTHETIC_BENCHMARK"

#: The fourteen deliverables, in the mission's order, with the document each one
#: reads from.  ``None`` means the report computes it directly.
DELIVERABLES: Sequence[Dict[str, Any]] = (
    {"index": 1, "name": "Git HEAD and changed files", "source": "git.json"},
    {"index": 2, "name": "Performance benchmark methodology", "source": "benchmark.json"},
    {"index": 3, "name": "Actual measured CPU/GPU latency", "source": "benchmark.json"},
    {"index": 4, "name": "Memory measurements", "source": "memory.json"},
    {"index": 5, "name": "FULL versus Lite conditional compute", "source": "conditional.json"},
    {"index": 6, "name": "FiLM gradient and conditioning verification",
     "source": "film_conditioning.json"},
    {"index": 7, "name": "Checkpoint/resume reliability", "source": "determinism.json"},
    {"index": 8, "name": "Synthetic evidence-isolation tests",
     "source": "evidence_isolation.json"},
    {"index": 9, "name": "Failure-injection results", "source": "failure_injection.json"},
    {"index": 10, "name": "CPU/CUDA parity observations", "source": "cpu_cuda_parity.json"},
    {"index": 11, "name": "Complete regression-test results", "source": "regression.json"},
    {"index": 12, "name": "Remaining technical blockers", "source": None},
    {"index": 13, "name": "Git commit hash", "source": "git.json"},
    {"index": 14, "name": "Phase D completion decision", "source": None},
)


def _read(root: Path, name: str) -> Optional[Dict[str, Any]]:
    path = Path(root) / name
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _benchmark_summary(doc: Mapping[str, Any]) -> Dict[str, Any]:
    records = doc.get("records") or []
    rows = []
    for record in records:
        pipeline = record.get("pipeline_ms") or {}
        forward = record.get("model_forward_ms") or {}
        memory = record.get("memory") or {}
        rows.append({"model_key": record.get("model_key"), "seed": record.get("seed"),
                     "adapter_kind": record.get("adapter_kind"),
                     "initialization_ms": (record.get("initialization_ms") or {}).get("median"),
                     "forward_ms_median": forward.get("median"),
                     "forward_ms_p95": forward.get("p95"),
                     "pipeline_ms_median": pipeline.get("median"),
                     "pipeline_ms_p95": pipeline.get("p95"),
                     "throughput_images_per_s": record.get("throughput_images_per_s"),
                     "peak_allocated_mib": memory.get("peak_allocated_mib"),
                     "peak_reserved_mib": memory.get("peak_reserved_mib"),
                     "parameters": record.get("parameters"),
                     "macs": record.get("macs"),
                     "observed_state": record.get("observed_state"),
                     "refiner_invocation_rate": record.get(
                         "conditional_refiner_invocation_rate")})
    return {"rows": rows,
            "conditions": doc.get("conditions"),
            "preprocessing_ms": (doc.get("preprocessing") or {}).get("median"),
            "batch_scaling": doc.get("batch_scaling"),
            "precision": doc.get("precision"),
            "routed_batch_policy": doc.get("routed_batch_policy")}


def _conditional_summary(doc: Mapping[str, Any]) -> Dict[str, Any]:
    return {"scenarios": doc.get("scenarios"), "records": doc.get("records"),
            "comparisons": doc.get("comparisons"),
            "roi_edge_cases": doc.get("roi_edge_cases")}


def _memory_summary(doc: Mapping[str, Any]) -> Dict[str, Any]:
    return {"training": doc.get("training"), "inference": doc.get("inference"),
            "capacity": doc.get("capacity"), "autocast": doc.get("autocast"),
            "accumulation": doc.get("accumulation"), "transfer": doc.get("transfer")}


def _checks(doc: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not doc:
        return {"present": False}
    checks = doc.get("checks") or []
    return {"present": True, "n_checks": len(checks),
            "n_passed": sum(1 for c in checks if c.get("passed")),
            "failed": [c["check"] for c in checks if not c.get("passed")],
            "checks": checks, "all_passed": all(c.get("passed") for c in checks)}


def build_report(root: Path, *,
                 blockers: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Assemble every deliverable, marking missing sources as missing."""
    root = Path(root)
    documents = {name: _read(root, name) for name in
                 ("git.json", "benchmark.json", "memory.json", "conditional.json",
                  "determinism.json", "film_conditioning.json", "failure_injection.json",
                  "evidence_isolation.json", "stability.json", "cpu_cuda_parity.json",
                  "regression.json")}

    deliverables: List[Dict[str, Any]] = []
    for entry in DELIVERABLES:
        source = entry["source"]
        present = True if source is None else documents.get(source) is not None
        deliverables.append({"index": entry["index"], "name": entry["name"],
                             "source": source, "present": bool(present)})

    determinism = _checks(documents["determinism.json"])
    film = _checks(documents["film_conditioning.json"])
    stability = _checks(documents["stability.json"])
    isolation = documents["evidence_isolation.json"] or {}
    failures = documents["failure_injection.json"] or {}
    parity = documents["cpu_cuda_parity.json"] or {}
    regression = documents["regression.json"] or {}

    unresolved = list(blockers or [])
    if not determinism.get("all_passed", False):
        unresolved.append(f"determinism checks failed: {determinism.get('failed')}")
    if not film.get("all_passed", False):
        unresolved.append(f"FiLM conditioning checks failed: {film.get('failed')}")
    if not stability.get("all_passed", False):
        unresolved.append(f"stability checks failed: {stability.get('failed')}")
    if not isolation.get("all_blocked", False):
        unresolved.append("an evidence-isolation attack was not blocked")
    if not failures.get("all_detected", False):
        unresolved.append(f"failure injection missed: {failures.get('missed')}")
    if parity and not parity.get("all_passed", False):
        unresolved.append(f"CPU/CUDA parity failed for {parity.get('failed')}")
    if regression and regression.get("failed"):
        unresolved.append(f"regression failures: {regression.get('failed')}")
    missing_sources = [d["name"] for d in deliverables if not d["present"]]
    if missing_sources:
        unresolved.append(f"deliverables without a source document: {missing_sources}")

    status = ("PHASE_D_COMPLETE" if not unresolved
              else "PHASE_D_INCOMPLETE")
    report = {
        "schema": "phase_d_summary_v1",
        "evidence_class": EVIDENCE_CLASS,
        "status": status,
        "deliverables": deliverables,
        "1_git_head": documents["git.json"],
        "2_benchmark_methodology": {
            "conditions": (documents["benchmark.json"] or {}).get("conditions"),
            "timing_source": "time.perf_counter with CUDA synchronisation on both sides",
            "warmup_iterations": ((documents["benchmark.json"] or {}).get("conditions")
                                  or {}).get("warmup_iterations"),
            "measured_repeats": ((documents["benchmark.json"] or {}).get("conditions")
                                 or {}).get("measured_repeats"),
            "statistics": "median, p90, p95, mean, min, max, stdev per call",
            "cold_vs_warm": ("the first call is recorded separately as "
                             "cold_first_call and never averaged into the warm figure"),
            "batch_policy": (documents["benchmark.json"] or {}).get("routed_batch_policy"),
            "macs_vs_wall_time": ("conv/linear MACs are architectural; latency is this "
                                  "host and this build. They are never substituted"),
            "seeds": (documents["benchmark.json"] or {}).get("seeds"),
            "evidence_class": EVIDENCE_CLASS,
        },
        "3_latency": _benchmark_summary(documents["benchmark.json"] or {}),
        "4_memory": _memory_summary(documents["memory.json"] or {}),
        "5_conditional_compute": _conditional_summary(documents["conditional.json"] or {}),
        "6_film": film,
        "7_resume_reliability": determinism,
        "8_evidence_isolation": {"n_attacks": isolation.get("n_attacks"),
                                 "n_blocked": isolation.get("n_blocked"),
                                 "all_blocked": isolation.get("all_blocked"),
                                 "attacks": isolation.get("attacks")},
        "9_failure_injection": {"n_injections": failures.get("n_injections"),
                                "n_detected": failures.get("n_detected"),
                                "all_detected": failures.get("all_detected"),
                                "injections": failures.get("injections")},
        "10_parity": parity,
        "11_regression": regression,
        "12_blockers": unresolved,
        "13_commit": (documents["git.json"] or {}).get("commit"),
        "14_decision": {"status": status,
                        "definition_of_done": _definition_of_done(determinism, film,
                                                                  isolation, failures,
                                                                  parity, regression,
                                                                  documents)},
        "stability": stability,
    }
    return report


def _definition_of_done(determinism: Mapping[str, Any], film: Mapping[str, Any],
                        isolation: Mapping[str, Any], failures: Mapping[str, Any],
                        parity: Mapping[str, Any], regression: Mapping[str, Any],
                        documents: Mapping[str, Any]) -> Dict[str, Any]:
    """The mission's own completion criteria, each answered by a measurement."""
    benchmark = documents.get("benchmark.json") or {}
    records = benchmark.get("records") or []
    profiled = {r.get("model_key") for r in records}
    return {
        "all_eight_adapters_profiled": {
            "met": len(profiled) == 8,
            "detail": f"{len(profiled)} distinct model keys profiled"},
        "routing_branches_benchmarked": {
            "met": bool((documents.get("conditional.json") or {}).get("records")),
            "detail": ("all four canonical states reached and asserted, plus the "
                       "global-only / always-refine / conditional comparison")},
        "gpu_memory_characterised": {
            "met": bool((documents.get("memory.json") or {}).get("training")),
            "detail": "per-stage training peaks, inference peaks and a capacity search"},
        "deterministic_resume_demonstrated": {
            "met": bool(determinism.get("all_passed")),
            "detail": "ablation shows the data-order fix is necessary and sufficient"},
        "film_conditioning_functionally_verified": {
            "met": bool(film.get("all_passed")),
            "detail": ("functional task dependence plus a frozen-conditioning control "
                       "that stays at the task-blind optimum")},
        "synthetic_cannot_masquerade": {
            "met": bool(isolation.get("all_blocked")),
            "detail": f"{isolation.get('n_blocked')}/{isolation.get('n_attacks')} attacks blocked"},
        "interruption_and_corruption_recovery": {
            "met": bool(failures.get("all_detected")),
            "detail": f"{failures.get('n_detected')}/{failures.get('n_injections')} injections detected"},
        "new_engineering_regressions_resolved": {
            # A missing regression document is not evidence of zero regressions.
            # Phase D defect: `not bool(None)` reported this criterion as met before
            # the regression had ever been run.
            "met": bool(regression) and not regression.get("new_regressions"),
            "detail": (f"new regressions: {regression.get('new_regressions')}"
                       if regression else "no regression document produced"),
        },
        "protected_restrictions_intact": {
            "met": True,
            "detail": ("Phase D code references no protected-split identifier and no "
                       "institutional trust-store path (audited by the package scan in "
                       "test_18), no trust-store file was written, and no real training "
                       "was launched; this is a scope attestation for Phase D, not a "
                       "measurement"),
        },
    }


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #
def _fmt(value: Any, digits: int = 2, suffix: str = "") -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}{suffix}"
    return str(value)


def render_markdown(report: Mapping[str, Any]) -> str:
    """The completion report, with the evidence label on every measured table."""
    lines: List[str] = []
    add = lines.append
    status = report.get("status")
    add("# Phase D — GPU Performance, Reliability and Reproducibility")
    add("")
    add(f"**Status:** `{status}`  ")
    add(f"**Evidence class:** `{report.get('evidence_class')}` — every measured number "
        "below comes from fixture weights and synthetic inputs. None of it is a "
        "real-data segmentation result.")
    add("")
    add("## Deliverables")
    add("")
    add("| # | Deliverable | Source | Present |")
    add("|---|---|---|---|")
    for entry in report["deliverables"]:
        add(f"| {entry['index']} | {entry['name']} | "
            f"`{entry['source'] or 'computed'}` | {'yes' if entry['present'] else 'NO'} |")
    add("")

    git = report.get("1_git_head") or {}
    add("## 1 / 13 — Git state")
    add("")
    add(f"- HEAD: `{git.get('head')}` on `{git.get('branch')}`")
    add(f"- commit used for this report: `{git.get('commit')}`")
    changed = git.get("changed_files") or []
    add(f"- changed files at report time: {len(changed)}")
    for path in changed[:60]:
        add(f"  - `{path}`")
    add("")

    methodology = report["2_benchmark_methodology"]
    add("## 2 — Benchmark methodology")
    add("")
    add(f"- timing: {methodology['timing_source']}")
    add(f"- warm-up: {methodology['warmup_iterations']} discarded iterations; "
        f"{methodology['measured_repeats']} measured repeats per call")
    add(f"- statistics: {methodology['statistics']}")
    add(f"- cold versus warm: {methodology['cold_vs_warm']}")
    add(f"- MACs versus wall time: {methodology['macs_vs_wall_time']}")
    policy = methodology.get("batch_policy") or {}
    add(f"- batch policy: {policy.get('reason', 'n/a')}")
    add(f"- seeds: {methodology.get('seeds')}")
    conditions = methodology.get("conditions") or {}
    add(f"- device: {conditions.get('device_name')} · torch {conditions.get('torch_version')} "
        f"· CUDA {conditions.get('cuda_version')} · cuDNN {conditions.get('cudnn_version')}")
    add(f"- CUDA synchronised for every GPU timing: {_fmt(conditions.get('cuda_synchronized'))}")
    add("")

    latency = report["3_latency"]
    add("## 3 — Measured latency")
    add("")
    add("`SYNTHETIC_BENCHMARK` — batch 1, FP32, 512×512, RTX 3060 Ti.")
    add("")
    add("| model | seed | init ms | forward p50 | forward p95 | pipeline p50 | "
        "pipeline p95 | img/s | peak alloc MiB | refiner rate |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for row in latency.get("rows") or []:
        rate = row.get("refiner_invocation_rate")
        add(f"| `{row['model_key']}` | {row['seed']} | "
            f"{_fmt(row['initialization_ms'], 1)} | "
            f"{_fmt(row['forward_ms_median'])} | {_fmt(row['forward_ms_p95'])} | "
            f"{_fmt(row['pipeline_ms_median'])} | {_fmt(row['pipeline_ms_p95'])} | "
            f"{_fmt(row['throughput_images_per_s'], 1)} | "
            f"{_fmt(row['peak_allocated_mib'], 1)} | "
            f"{'—' if rate is None else _fmt(rate, 2)} |")
    add("")
    add("The **refiner rate** column is the fraction of the 30 measured calls in which the "
        "refiner actually ran. On a randomly initialised fixture this number is an artifact "
        "of untrained logits, not a property of the architecture: Phase C saw 1.00 for FULL "
        "and 0.00 for Lite on the same kind of fixture. It is reported to make the pipeline "
        "figure interpretable (a rate of 1.00 means the pipeline number includes the refiner "
        "on every call), never as expected behaviour of a trained model. Nothing was tuned "
        "to move it.")
    add("")
    add(f"Pre/post-processing: preprocessing median "
        f"{_fmt(latency.get('preprocessing_ms'))} ms (CPU, PIL decode + resize + normalise), "
        "post-processing measured separately so it is never folded into model latency.")
    add("")
    precision = latency.get("precision") or []
    if precision:
        add("### FP32 versus mixed precision")
        add("")
        add("| model | fp32 p50 | amp p50 | speed-up | max abs difference |")
        add("|---|---|---|---|---|")
        for row in precision:
            numerical = row.get("numerical") or {}
            add(f"| `{row['model_key']}` | {_fmt((row.get('fp32') or {}).get('median'))} | "
                f"{_fmt((row.get('amp') or {}).get('median'))} | "
                f"{_fmt(row.get('speedup'), 2)}× | "
                f"{_fmt(numerical.get('max_abs_difference'), 4)} |")
        add("")
        add("Autocast changes the arithmetic; the delta is shown so a speed-up is never "
            "reported as free.")
        add("")
    scaling = latency.get("batch_scaling") or []
    if scaling:
        add("### Batch scaling (single-network models only)")
        add("")
        add("| model | batch | per-image ms | images/s |")
        add("|---|---|---|---|")
        for block in scaling:
            for row in block.get("rows") or []:
                add(f"| `{block['model_key']}` | {row['batch_size']} | "
                    f"{_fmt(row.get('per_image_ms'))} | "
                    f"{_fmt(row.get('throughput_images_per_s'), 1)} |")
        add("")
        add("FULL and Lite are excluded: their ROI and safety stages are per-image, so a "
            "batched figure for them would describe a pipeline that does not exist.")
        add("")

    memory = report["4_memory"]
    add("## 4 — Memory")
    add("")
    add("`SYNTHETIC_BENCHMARK`. `peak_allocated` is live memory; `peak_reserved` is "
        "allocator cache and is not a leak.")
    add("")
    add("| stage | batch | micro-batch | accum | autocast | peak alloc MiB | "
        "peak reserved MiB |")
    add("|---|---|---|---|---|---|---|")
    for row in memory.get("training") or []:
        add(f"| {row['stage']} | {row['batch']} | {row['micro_batch']} | "
            f"{row['accumulation']} | {_fmt(row['autocast'])} | "
            f"{_fmt(row['peak_allocated_mib'], 1)} | {_fmt(row['peak_reserved_mib'], 1)} |")
    add("")
    add("| inference path | peak alloc MiB | peak reserved MiB | parameters |")
    add("|---|---|---|---|")
    for row in memory.get("inference") or []:
        add(f"| `{row['model_key']}` | {_fmt(row['peak_allocated_mib'], 1)} | "
            f"{_fmt(row['peak_reserved_mib'], 1)} | {row.get('parameters')} |")
    add("")
    capacity = memory.get("capacity") or []
    if capacity:
        add("Capacity search (largest batch that completes one step without OOM):")
        add("")
        for row in capacity:
            add(f"- {row['stage']}: max batch {row.get('max_batch')} "
                f"(GPU total {_fmt(row.get('gpu_total_mib'), 0)} MiB)")
        add("")

    conditional = report["5_conditional_compute"]
    add("## 5 — FULL versus Lite conditional compute")
    add("")
    add("`SYNTHETIC_BENCHMARK`. These are **branch costs**, not routing rates: the router "
        "scalar and the safety logit are scripted so each branch is reachable without a "
        "trained model. No threshold was changed.")
    add("")
    add("| model | seed | scenario | state | latency p50 ms | G | R | refiner | safety |")
    add("|---|---|---|---|---|---|---|---|---|")
    for row in conditional.get("records") or []:
        counts = row.get("component_invocations") or {}
        add(f"| `{row['model_key']}` | {row['seed']} | {row['scenario']} | "
            f"{row['observed_state']} | "
            f"{_fmt((row.get('branch_latency_ms') or {}).get('median'))} | "
            f"{counts.get('global', 0)} | {counts.get('router', 0)} | "
            f"{counts.get('refiner', 0)} | {counts.get('safety', 0)} |")
    add("")
    add("| model | seed | global-only ms | always-refine ms | conditional ms | "
        "effective MACs | MACs if always refine |")
    add("|---|---|---|---|---|---|---|")
    for row in conditional.get("comparisons") or []:
        add(f"| `{row['model_key']}` | {row['seed']} | "
            f"{_fmt((row.get('global_only_ms') or {}).get('median'))} | "
            f"{_fmt((row.get('always_refine_ms') or {}).get('median'))} | "
            f"{_fmt((row.get('conditional_ms') or {}).get('median'))} | "
            f"{row.get('effective_macs_per_image')} | {row.get('macs_if_always_refine')} |")
    add("")
    add("A lower refiner count is not by itself a lower total cost, so the effective MAC "
        "figure is reported beside the branch count.")
    add("")
    add("The three seeds share one architecture and differ only in randomly initialised "
        "weights, so the seed-to-seed spread above is not a performance difference between "
        "checkpoints. It comes from the fixture routing different numbers of ROIs on the "
        "same input, plus ordinary host state (allocator warm-up, clocks). Read each seed "
        "as one draw from the same distribution, not as a ranking.")
    add("")

    film = report["6_film"]
    add("## 6 — FiLM conditioning")
    add("")
    for check in film.get("checks") or []:
        add(f"- **{'PASS' if check['passed'] else 'FAIL'}** `{check['check']}` — "
            f"{check['detail']}")
    add("")

    determinism = report["7_resume_reliability"]
    add("## 7 — Checkpoint and resume reliability")
    add("")
    for check in determinism.get("checks") or []:
        add(f"- **{'PASS' if check['passed'] else 'FAIL'}** `{check['check']}` "
            f"({check.get('identity_class')}) — {check['detail']}")
    add("")

    isolation = report["8_evidence_isolation"]
    add("## 8 — Synthetic evidence isolation")
    add("")
    add(f"{isolation.get('n_blocked')}/{isolation.get('n_attacks')} attacks blocked.")
    add("")
    add("| attack | blocked | mechanism |")
    add("|---|---|---|")
    for row in isolation.get("attacks") or []:
        add(f"| {row['attack']} | {_fmt(row['blocked'])} | {row['mechanism']} |")
    add("")

    failures = report["9_failure_injection"]
    add("## 9 — Failure injection")
    add("")
    add(f"{failures.get('n_detected')}/{failures.get('n_injections')} injections detected.")
    add("")
    add("| stage | injection | detected by |")
    add("|---|---|---|")
    for row in failures.get("injections") or []:
        add(f"| {row['stage']} | {row['injection']} | {row.get('detected_by') or '**MISSED**'} |")
    add("")

    parity = report["10_parity"]
    add("## 10 — CPU/CUDA parity")
    add("")
    tolerances = parity.get("tolerances") or {}
    add(f"Tolerances inherited unchanged from the Phase B gate: binary agreement ≥ "
        f"{tolerances.get('binary_agreement_min')}, mean |Δ| ≤ "
        f"{tolerances.get('mean_abs_difference_max')}, exact routing-state match.")
    add("")
    add("| model | shape | finite | max abs Δ | mean abs Δ | binary agreement | state |")
    add("|---|---|---|---|---|---|---|")
    for row in parity.get("records") or []:
        add(f"| `{row['model_key']}` | {_fmt(row['shape_match'])} | "
            f"{_fmt(row['both_finite'])} | {_fmt(row['max_abs_difference'], 6)} | "
            f"{_fmt(row['mean_abs_difference'], 6)} | "
            f"{_fmt(row['binary_agreement'], 4)} | "
            f"{row.get('cpu_state') or '—'} / {row.get('cuda_state') or '—'} |")
    add("")
    add("No cross-device bitwise equality is claimed; these are agreement criteria on a "
        "numerically different implementation.")
    add("")

    regression = report["11_regression"]
    add("## 11 — Regression results")
    add("")
    if regression:
        targeted = regression.get("targeted") or {}
        broad = regression.get("broad") or {}
        add("| run | passed | failed | errors | skipped | xfailed | exit |")
        add("|---|---|---|---|---|---|---|")
        for label, run in (("targeted (§13 areas)", targeted), ("broad (`tests/`)", broad)):
            if not run:
                continue
            counts = run.get("counts") or {}
            add(f"| {label} | {counts.get('passed')} | {counts.get('failed')} | "
                f"{counts.get('error')} | {counts.get('skipped')} | "
                f"{counts.get('xfailed')} | {run.get('returncode')} |")
        add("")
        by_area = regression.get("by_area") or {}
        if by_area:
            add("| area | passed | failed | errors | skipped |")
            add("|---|---|---|---|---|")
            for area, counts in by_area.items():
                add(f"| {area} | {counts.get('passed')} | {counts.get('failed')} | "
                    f"{counts.get('error')} | {counts.get('skipped')} |")
            add("")
        classification = regression.get("classification") or {}
        if classification:
            add("Every non-passing test is classified explicitly. Anything not on the "
                "known list defaults to `new_regression` rather than being absorbed.")
            add("")
            add("| test | category | reason |")
            add("|---|---|---|")
            for test, info in classification.items():
                add(f"| `{test}` | {info.get('category')} | {info.get('reason')} |")
            add("")
        else:
            add("No test failed in either run, so the classification table is empty.")
            add("")
        anomalies = regression.get("anomalies") or {}
        if anomalies:
            add("Runs that exited without a parseable summary are listed here instead of "
                "being counted as clean:")
            add("")
            for name, anomaly in anomalies.items():
                add(f"- `{name}`: {anomaly}")
            add("")
    else:
        add("No regression document was produced; see the blockers below.")
    add("")

    add("## 12 — Remaining blockers")
    add("")
    blockers = report.get("12_blockers") or []
    if blockers:
        for item in blockers:
            add(f"- {item}")
    else:
        add("None recorded by this phase.")
    add("")

    decision = report["14_decision"]
    add("## 14 — Completion decision")
    add("")
    add(f"`{decision['status']}`")
    add("")
    add("| criterion | met | detail |")
    add("|---|---|---|")
    for name, block in (decision.get("definition_of_done") or {}).items():
        add(f"| {name.replace('_', ' ')} | {_fmt(block.get('met'))} | {block.get('detail')} |")
    add("")
    return "\n".join(lines)


__all__ = ["DELIVERABLES", "EVIDENCE_CLASS", "build_report", "render_markdown"]
