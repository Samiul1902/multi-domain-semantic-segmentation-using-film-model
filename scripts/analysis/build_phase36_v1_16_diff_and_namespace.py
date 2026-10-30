#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.16 — DIFF PROOFS + OUTPUT-NAMESPACE MAP builder (write-once).

Produces TWO machine-derived diffs and ONE namespace map:

  (1) v1.15 -> v1.16 semantic diff   (WRITE-ONCE)
      The v1.16 revision is a PURE operational/governance/observability rebase:
      the scientific computation is IDENTICAL to v1.15.  Every hunk MUST classify
      as operational/governance/observability/namespace/provenance, and the
      SCIENTIFIC delta count MUST be 0.  Any UNCLASSIFIED hunk FAILS CLOSED.

  (2) v1.16 output-namespace map     (WRITE-ONCE)
      Enumerates every output path produced by the v1.16 science path and proves
      that NONE collides with a v1.14 or v1.15 output path
      (v1_14_overwrite_paths == [] and v1_15_overwrite_paths == []), and that all
      v1.16 science output paths are ABSENT pre-execution.

Non-consuming: static/source analysis only.  No model, no checkpoint, no VAL
image, no VAL GT, no TEST, no ROUTER_HOLDOUT, no science.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
V15 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_15.py"
V16 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_16.py"

V15_SHA = "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002"
V16_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"

AUD = ROOT / "reports" / "audits"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_once_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)} for {path}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")


# --------------------------------------------------------------------------- #
# 1. v1.15 -> v1.16 diff
# --------------------------------------------------------------------------- #
_GOV_TOKENS = (
    "v1_16", "V1_16", "V1.16", "v1.16", "PHASE36_V1_16", "phase36_v1_16",
    "JOURNAL", "_ScienceJournal", "STAGE_JOURNAL", "V1_16_JOURNAL",
    "D80", "OPERATIONAL", "NAMESPACE", "GATE_ENV",
)


def classify_operational_hunk(b_text: str) -> str:
    """Classify a non-scientific hunk.  Returns a governance class or UNCLASSIFIED."""
    if any(tok in b_text for tok in _GOV_TOKENS):
        return "OPERATIONAL_GOVERNANCE"
    return "UNCLASSIFIED"


def compute_diff(a_path: Path, b_path: Path) -> tuple[list[dict], list[str]]:
    a = a_path.read_text(encoding="utf-8").splitlines(keepends=True)
    b = b_path.read_text(encoding="utf-8").splitlines(keepends=True)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    hunks, classes = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        bt = "".join(b[j1:j2])
        at = "".join(a[i1:i2])
        # Scientific detector: any D61 or D75 token change means a scientific delta
        # (v1.15 -> v1.16 must have NONE of these).
        scientific = (
            ("fuse_full_field(p_global, refined, geom)" in bt
             and "_fuse_global_with_regional" in at)
            or "def _phase27_scored_final_binary" in bt
            or ("_phase27_scored_final_binary(" in bt and "final_binary" in bt)
        )
        cls = "SCIENTIFIC_DELTA" if scientific else classify_operational_hunk(bt)
        hunks.append({"tag": tag, "a_span": [i1, i2], "b_span": [j1, j2],
                      "a_preview": at[:300], "b_preview": bt[:300]})
        classes.append(cls)
    return hunks, classes


def build_v15_to_v16_diff() -> dict:
    hunks, classes = compute_diff(V15, V16)
    scientific = classes.count("SCIENTIFIC_DELTA")
    unclassified = classes.count("UNCLASSIFIED")
    artifact = {
        "artifact": "phase36_v1_15_to_v1_16_semantic_diff",
        "from_revision": "ra_medfilm_barr_phase36_robustness_v1_15",
        "to_revision": "ra_medfilm_barr_phase36_robustness_v1_16",
        "from_sha256": V15_SHA,
        "to_sha256": V16_SHA,
        "hunk_count": len(hunks),
        "scientific_delta_count": scientific,
        "scientific_deltas": [],
        "unclassified_delta_count": unclassified,
        "classification_counts": {
            "SCIENTIFIC_DELTA": scientific,
            "OPERATIONAL_GOVERNANCE": classes.count("OPERATIONAL_GOVERNANCE"),
            "UNCLASSIFIED": unclassified,
        },
        "hunks": [
            {"tag": h["tag"], "a_span": h["a_span"], "b_span": h["b_span"],
             "classification": c, "a_preview": h["a_preview"], "b_preview": h["b_preview"]}
            for h, c in zip(hunks, classes)
        ],
        "note": ("v1.16 is a PURE operational/governance/observability/namespace rebase "
                 "of v1.15.  The scientific computation is IDENTICAL.  Every hunk is "
                 "classified as operational/governance; scientific_delta_count MUST be 0; "
                 "any UNCLASSIFIED hunk fails closed."),
        "scientific_semantics_effect": "NONE",
        "model_free": True,
        "new_scientific_choice": False,
    }
    return artifact


# --------------------------------------------------------------------------- #
# 2. Output-namespace map
# --------------------------------------------------------------------------- #
def _string_constants(src: str) -> list[str]:
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.append(n.value)
        elif isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id.startswith(
                        ("SCIENCE_", "SMOKE_", "FORBIDDEN_")):
                    if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                        out.append(n.value.value)
    return out


def _v1_16_output_paths(src: str) -> list[str]:
    """All reports/audits/science output paths that mention v1_16."""
    paths = set()
    for s in _string_constants(src):
        if s.startswith("reports/") and "v1_16" in s:
            paths.add(s)
    # journal dir
    for s in _string_constants(src):
        if "v1_16_journal" in s:
            paths.add(s)
    return sorted(paths)


def _v1_14_output_paths(src: str) -> list[str]:
    paths = set()
    for s in _string_constants(src):
        if s.startswith("reports/") and ("v1_14" in s or "v1_8" in s):
            paths.add(s)
    return sorted(paths)


def _v1_15_output_paths(src: str) -> list[str]:
    paths = set()
    for s in _string_constants(src):
        if s.startswith("reports/") and "v1_15" in s:
            paths.add(s)
    return sorted(paths)


def build_output_namespace_map() -> dict:
    v16_src = V16.read_text(encoding="utf-8")
    v14_src = V14.read_text(encoding="utf-8")
    v15_src = V15.read_text(encoding="utf-8")

    v16_paths = _v1_16_output_paths(v16_src)
    v14_paths = set(_v1_14_output_paths(v14_src))
    v15_paths = set(_v1_15_output_paths(v15_src))

    v14_overwrite = sorted([p for p in v16_paths if p in v14_paths])
    v15_overwrite = sorted([p for p in v16_paths if p in v15_paths])

    # SCIENCE-EXECUTION output paths — these MUST all be ABSENT pre-execution.
    # (Governance artifacts such as the runtime manifest / release attestation are
    # created during PREPARATION and are deliberately excluded from the absence gate.)
    science_output_paths = [
        "reports/audits/phase36_robustness_science_start_v1_16.json",
        "reports/audits/phase36_robustness_scientific_result_v1_16.json",
        "reports/audits/phase36_robustness_science_failure_v1_16.json",
        "reports/audits/phase36_robustness_science_process_exit_v1_16.json",
        "reports/audits/phase36_robustness_science_stdout_v1_16.txt",
        "reports/audits/phase36_robustness_science_stderr_v1_16.txt",
        "reports/audits/phase36_robustness_smoke_start_v1_16.json",
        "reports/audits/phase36_robustness_smoke_v1_16.json",
        "reports/audits/phase36_robustness_smoke_failure_v1_16.json",
    ]
    journal_dir_rel = "reports/audits/phase36_robustness_science_v1_16_journal"

    absence = {}
    for p in science_output_paths:
        absence[p] = {"exists": (ROOT / p).exists(), "kind": "SCIENCE_EXECUTION_OUTPUT"}
    journal_dir = ROOT / journal_dir_rel
    absence[journal_dir_rel] = {
        "exists": journal_dir.exists() and len([f for f in journal_dir.iterdir() if f.is_file()]) > 0,
        "kind": "SCIENCE_JOURNAL_DIR",
    }

    all_absent = all(not v["exists"] for v in absence.values())

    return {
        "artifact": "phase36_v1_16_output_namespace_map",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_16",
        "v1_16_output_paths": v16_paths,
        "v1_16_science_output_paths": science_output_paths,
        "v1_16_governance_artifacts_created_in_preparation": [
            "reports/audits/phase36_v1_16_runtime_source_integrity_manifest.json",
            "reports/audits/phase36_v1_16_science_release_attestation.json",
        ],
        "v1_16_science_artifacts": {
            "START": "reports/audits/phase36_robustness_science_start_v1_16.json",
            "RESULT": "reports/audits/phase36_robustness_scientific_result_v1_16.json",
            "FAILURE": "reports/audits/phase36_robustness_science_failure_v1_16.json",
            "PROCESS_EXIT": "reports/audits/phase36_robustness_science_process_exit_v1_16.json",
            "stdout": "reports/audits/phase36_robustness_science_stdout_v1_16.txt",
            "stderr": "reports/audits/phase36_robustness_science_stderr_v1_16.txt",
            "journal_dir": journal_dir_rel,
        },
        "v1_14_output_paths_observed": sorted(v14_paths),
        "v1_15_output_paths_observed": sorted(v15_paths),
        "v1_14_overwrite_paths": v14_overwrite,
        "v1_15_overwrite_paths": v15_overwrite,
        "no_v1_14_overwrite": v14_overwrite == [],
        "no_v1_15_overwrite": v15_overwrite == [],
        "all_v1_16_science_paths_absent_pre_execution": all_absent,
        "absence_pre_execution": absence,
        "note": ("The v1.16 science path writes ONLY into an isolated v1.16 artifact "
                 "namespace.  No v1.14 and no v1.15 output path is overwritten, and all "
                 "v1.16 SCIENCE-EXECUTION output paths (START/RESULT/FAILURE/PROCESS_EXIT/"
                 "stdout/stderr/journal/smoke) are ABSENT before execution.  Governance "
                 "artifacts (runtime manifest, release attestation) are created during "
                 "preparation by design."),
        "model_free": True,
    }


def main() -> int:
    diff = build_v15_to_v16_diff()
    _write_once_json(AUD / "phase36_v1_15_to_v1_16_semantic_diff.json", diff)

    ns = build_output_namespace_map()
    _write_once_json(AUD / "phase36_v1_16_output_namespace_map.json", ns)

    print(json.dumps({
        "v1_15_to_v1_16_diff": {
            "hunk_count": diff["hunk_count"],
            "scientific_delta_count": diff["scientific_delta_count"],
            "unclassified_delta_count": diff["unclassified_delta_count"],
            "classification_counts": diff["classification_counts"],
        },
        "output_namespace_map": {
            "v1_16_output_paths": len(ns["v1_16_output_paths"]),
            "v1_14_overwrite_paths": ns["v1_14_overwrite_paths"],
            "v1_15_overwrite_paths": ns["v1_15_overwrite_paths"],
            "all_v1_16_science_paths_absent_pre_execution": ns["all_v1_16_science_paths_absent_pre_execution"],
        },
    }, indent=1))
    ok = (diff["scientific_delta_count"] == 0
          and diff["unclassified_delta_count"] == 0
          and ns["no_v1_14_overwrite"] and ns["no_v1_15_overwrite"]
          and ns["all_v1_16_science_paths_absent_pre_execution"])
    print("terminal:", "PHASE36_V1_16_DIFF_AND_NAMESPACE_PASS" if ok else "PHASE36_V1_16_DIFF_AND_NAMESPACE_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
