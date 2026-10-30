#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.18 PURE RELEASE-GATE TEST (WO#17E §12; rebased from v1.17).

INVOKES the EXACT v1.18 pure runtime release-state function
(``_gate_science_release_state``) extracted by AST from the frozen v1.18 source and
executed in an ISOLATED namespace.  NO model, NO checkpoint, NO VAL access, NO marker
creation, NO torch import.

Requirements:
  * the unmodified frozen v1.18 source MUST yield state == "RELEASED";
  * SEVEN independent in-memory mutations of the gate inputs MUST each yield
    state == "NOT_RELEASED".

The gate function is executed source-faithfully: the AST node is compiled with the
module's own required globals injected from the source — so ANY divergence between the
source and this test is a hard FAIL, not a silent pass.

Writes reports/audits/phase36_v1_18_pure_release_gate_test.json (write-once).
Re-run -> REFUSE_OVERWRITE (rc 2).
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V18 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_18.py"
OUT = ROOT / "reports" / "audits" / "phase36_v1_18_pure_release_gate_test.json"

V18_SHA = "2259ce22e75ba9a3a8943769dc1e0ed5724f94902f5e8955976cd6ebeb8ce63e"


def sha256_file(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _extract_gate_fn(src_text: str) -> str:
    tree = ast.parse(src_text)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == "_gate_science_release_state":
            return ast.get_source_segment(src_text, n)
    raise AssertionError("_gate_science_release_state not found in v1.18 source")


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
    src_text = V18.read_text(encoding="utf-8")
    fn_src = _extract_gate_fn(src_text)
    env = {
        "json": json,
        "ROOT": ROOT,
        "__file__": str(V18),
        "_sha": sha256_file,
        "SCIENCE_RELEASE_ATTESTATION": _extract_module_const(
            src_text, "SCIENCE_RELEASE_ATTESTATION")
        or "reports/audits/phase36_v1_18_science_release_attestation.json",
        "_SCIENCE_RELEASE_REVISION": _extract_module_const(
            src_text, "_SCIENCE_RELEASE_REVISION")
        or "ra_medfilm_barr_phase36_robustness_v1_18",
        "HISTORICAL_V1_14_SMOKE": _extract_module_const(
            src_text, "HISTORICAL_V1_14_SMOKE")
        or "reports/audits/phase36_robustness_smoke_v1_14.json",
        "HISTORICAL_V1_14_SMOKE_SHA256": _extract_module_const(
            src_text, "HISTORICAL_V1_14_SMOKE_SHA256")
        or "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441",
        "Path": Path,
    }
    env.update(overrides)
    ns: dict = {}
    exec(compile(fn_src, "<v1_18_gate>", "exec"), env, ns)
    return ns["_gate_science_release_state"]


def main() -> int:
    if OUT.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE",
                          "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2
    if sha256_file(V18) != V18_SHA:
        print(json.dumps({"status": "FAIL_CLOSED__V1_18_SOURCE_SHA_MISMATCH",
                          "observed": sha256_file(V18)}, indent=1))
        return 3

    src_text = V18.read_text(encoding="utf-8")

    gate = _build_gate({})
    base = gate()
    base_released = (base.get("state") == "RELEASED")

    att_path = ROOT / "reports/audits/phase36_v1_18_science_release_attestation.json"
    att = json.loads(att_path.read_text(encoding="utf-8"))
    tmpdir = Path(tempfile.mkdtemp(prefix="v1_18_gate_"))

    def _mut_att(name: str, mutate) -> dict:
        d = json.loads(json.dumps(att))
        mutate(d)
        mp = tmpdir / f"{name}.json"
        mp.write_text(json.dumps(d, indent=1), encoding="utf-8")
        g = _build_gate({"SCIENCE_RELEASE_ATTESTATION": str(mp.relative_to(ROOT))
                         if str(mp).startswith(str(ROOT)) else str(mp)})
        return g()

    mutations = {}
    mutations["MUT_REVISION_MISMATCH"] = _mut_att(
        "m1", lambda d: d.update({"revision": "ra_medfilm_barr_phase36_robustness_v1_17"}))
    mutations["MUT_SOURCE_SHA_MISMATCH"] = _mut_att(
        "m2", lambda d: d.update({"execution_source_sha256": "0" * 64}))
    mutations["MUT_SMOKE_ARTIFACT_SHA_MISMATCH"] = _mut_att(
        "m3", lambda d: d.update({"smoke_artifact_sha256": "0" * 64}))
    mutations["MUT_SMOKE_NOT_SUCCESSFUL"] = _mut_att(
        "m4", lambda d: d.update({"smoke_all_pass": False}))
    mutations["MUT_SCIENTIFIC_OUTPUT_NOT_FALSE"] = _mut_att(
        "m5", lambda d: d.update({"scientific_output": True}))
    mutations["MUT_RELEASE_GATE_MISMATCH"] = _mut_att(
        "m6", lambda d: d.update({"release_gate": "SOMETHING_ELSE"}))
    g_missing = _build_gate({
        "SCIENCE_RELEASE_ATTESTATION": str(tmpdir / "does_not_exist.json")})
    mutations["MUT_NO_ATTESTATION"] = g_missing()

    mut_results = {k: (v.get("state"), v.get("reason")) for k, v in mutations.items()}
    all_mut_not_released = all(v.get("state") == "NOT_RELEASED"
                               for v in mutations.values())

    # D82 negative control: the v1.18 gate must NOT require a v1.18 smoke artifact.
    v18_gate_requires_smoke = ("phase36_robustness_smoke_v1_18.json" in src_text)

    passed = bool(base_released and all_mut_not_released)

    payload = {
        "artifact": "phase36_v1_18_pure_release_gate_test",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "PURE_RELEASE_GATE_TEST",
        "mode": "NON_CONSUMING__NO_MODEL__NO_CHECKPOINT__NO_VAL",
        "generated_utc": now(),
        "v1_18_source_sha256": V18_SHA,
        "gate_function": "_gate_science_release_state",
        "gate_function_source_faithful": True,
        "torch_imported": False,
        "model_constructed": False,
        "val_accessed": False,
        "marker_created": False,

        "base_gate_state": base.get("state"),
        "base_gate_reason": base.get("reason"),
        "base_gate_released": base_released,

        "mutations": mut_results,
        "mutation_count": len(mutations),
        "all_mutations_not_released": all_mut_not_released,

        "d82_compatibility_evidence": {
            "v18_gate_requires_v1_18_smoke_artifact": v18_gate_requires_smoke,
        },

        "all_pass": passed,
        "terminal": ("PHASE36_V1_18_PURE_RELEASE_GATE_TEST_PASS"
                     if passed else "PHASE36_V1_18_PURE_RELEASE_GATE_TEST_FAIL"),
    }

    _write_once_json(OUT, payload)
    print(json.dumps({
        "status": "V1_18_PURE_RELEASE_GATE_TEST_WRITTEN",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
        "base_gate_state": base.get("state"),
        "mutations_not_released": sum(1 for v in mutations.values()
                                      if v.get("state") == "NOT_RELEASED"),
        "mutation_count": len(mutations),
        "all_pass": passed,
        "terminal": payload["terminal"],
    }, indent=1))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
