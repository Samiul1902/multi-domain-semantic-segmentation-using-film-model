#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.17 PURE RELEASE-GATE READ-ONLY VERIFIER (WO#17D §3).

NO-WRITE verifier.  Executes the EXACT pure v1.17 runtime release-state function
(``_gate_science_release_state``) extracted by AST from the FROZEN v1.17 source,
against the FROZEN release attestation, and prints the runtime release state.

DIFFERENCE FROM validate_phase36_v1_17_pure_release_gate.py:
  * This verifier writes NO artifact of any kind (no report, no temp artifact in
    the repo).  It is safe to run repeatedly and NEVER overwrites anything.
  * It also READS the already-written mutation-test artifact and confirms every
    required mutation returned NOT_RELEASED.

Requires:
  * runtime_release_state == RELEASED
  * the existing mutation-test artifact reports all mutations NOT_RELEASED

Exit codes: 0 = PASS, 1 = gate not RELEASED, 2 = mutation artifact inconsistent,
            3 = v1.17 source SHA mismatch (fail-closed).
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V17 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_17.py"
ATTESTATION = ROOT / "reports" / "audits" / "phase36_v1_17_science_release_attestation.json"
MUTATION_ARTIFACT = ROOT / "reports" / "audits" / "phase36_v1_17_pure_release_gate_test.json"

V17_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"


def sha256_file(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def _extract_gate_fn(src_text: str) -> str:
    tree = ast.parse(src_text)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == "_gate_science_release_state":
            return ast.get_source_segment(src_text, n)
    raise AssertionError("_gate_science_release_state not found in v1.17 source")


def _extract_module_const(src_text: str, name: str):
    tree = ast.parse(src_text)
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name:
            try:
                return ast.literal_eval(n.value)
            except Exception:
                return None
    return None


def _build_gate(overrides: dict):
    src_text = V17.read_text(encoding="utf-8")
    fn_src = _extract_gate_fn(src_text)
    env = {
        "json": json,
        "ROOT": ROOT,
        "__file__": str(V17),
        "_sha": sha256_file,
        "SCIENCE_RELEASE_ATTESTATION": _extract_module_const(
            src_text, "SCIENCE_RELEASE_ATTESTATION")
        or "reports/audits/phase36_v1_17_science_release_attestation.json",
        "_SCIENCE_RELEASE_REVISION": _extract_module_const(
            src_text, "_SCIENCE_RELEASE_REVISION")
        or "ra_medfilm_barr_phase36_robustness_v1_17",
        "HISTORICAL_V1_14_SMOKE": _extract_module_const(src_text, "HISTORICAL_V1_14_SMOKE")
        or "reports/audits/phase36_robustness_smoke_v1_14.json",
        "HISTORICAL_V1_14_SMOKE_SHA256": _extract_module_const(
            src_text, "HISTORICAL_V1_14_SMOKE_SHA256")
        or "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441",
        "Path": Path,
    }
    env.update(overrides)
    ns: dict = {}
    exec(compile(fn_src, "<v1_17_gate_ro>", "exec"), env, ns)
    return ns["_gate_science_release_state"]


def main() -> int:
    if sha256_file(V17) != V17_SHA:
        print(json.dumps({"status": "FAIL_CLOSED__V1_17_SOURCE_SHA_MISMATCH",
                          "observed": sha256_file(V17)}, indent=1))
        return 3

    # Execute the EXACT gate against the FROZEN attestation (no writes anywhere).
    gate = _build_gate({})
    base = gate()
    released = (base.get("state") == "RELEASED")

    # Read the EXISTING mutation-test artifact (never rewritten).
    mut_artifact_present = MUTATION_ARTIFACT.exists()
    mut = json.loads(MUTATION_ARTIFACT.read_text(encoding="utf-8")) \
        if mut_artifact_present else {}
    mut_states = mut.get("mutations", {})

    def _state_of(v):
        # Mutation values are recorded as either {"state": ...} or [state, reason].
        if isinstance(v, dict):
            return v.get("state")
        if isinstance(v, (list, tuple)) and v:
            return v[0]
        return v

    all_mut_not_released = (bool(mut_states)
                            and all(_state_of(v) == "NOT_RELEASED"
                                    for v in mut_states.values()))
    mut_artifact_consistent = (mut.get("all_mutations_not_released") is True
                               and all_mut_not_released)

    result = {
        "artifact": "phase36_v1_17_pure_release_gate_readonly_verification",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_17",
        "type": "PURE_RELEASE_GATE_READONLY_VERIFICATION",
        "mode": "NO_WRITE__NO_MODEL__NO_CHECKPOINT__NO_VAL",
        "wrote_any_artifact": False,
        "v1_17_source_sha256": sha256_file(V17),
        "attestation_sha256": sha256_file(ATTESTATION),
        "runtime_release_state": base.get("state"),
        "runtime_release_reason": base.get("reason"),
        "runtime_release_state_released": released,
        "mutation_test_artifact_present": mut_artifact_present,
        "mutation_test_artifact_sha256": sha256_file(MUTATION_ARTIFACT),
        "mutation_test_all_mutations_not_released": mut.get("all_mutations_not_released"),
        "mutation_states": {k: _state_of(v) for k, v in mut_states.items()},
        "mutation_artifact_consistent": mut_artifact_consistent,
        "all_pass": bool(released and mut_artifact_consistent),
    }
    print(json.dumps(result, indent=1))

    if not released:
        print("terminal: PHASE36_V1_17_PURE_RELEASE_GATE_READONLY_FAIL__NOT_RELEASED")
        return 1
    if not mut_artifact_consistent:
        print("terminal: PHASE36_V1_17_PURE_RELEASE_GATE_READONLY_FAIL__MUTATION_ARTIFACT_INCONSISTENT")
        return 2
    print("terminal: PHASE36_V1_17_PURE_RELEASE_GATE_READONLY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
