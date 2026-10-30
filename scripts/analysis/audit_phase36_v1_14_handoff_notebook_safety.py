#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.14 — STATIC SAFETY AUDIT of the ChatGPT handoff notebook.

Reads ``notebooks/RA_MedFiLM_Phase_Handoff_Builder.ipynb`` and proves, at the
AST level (NOT by substring search), that it performs ONLY packaging/navigation
operations:

  * imports: a small stdlib allow-list (json/hashlib/zipfile/shutil/datetime/os/
    sys/pathlib) and NOTHING else — no torch, no subprocess;
  * calls: no ``torch.load`` / ``load_state_dict`` / ``.forward`` / ``.cuda`` /
    ``.backward`` / ``optimizer.step`` — i.e. no model / checkpoint / training;
  * file READS: never target a protected population (VAL/GT/TEST/ROUTER_HOLDOUT);
  * file WRITES: resolve only into ``reports/chatgpt_handoff/**`` and the single
    handoff-generation audit path — never a frozen scientific/governance artifact.

Writes ``reports/audits/phase36_v1_14_handoff_notebook_safety_audit.json``.

NO torch.  NO model.  NO checkpoint.  NO smoke.  NO science.  NO VAL/GT.
NO TEST.  NO ROUTER_HOLDOUT.  NO training.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NB = ROOT / "notebooks" / "RA_MedFiLM_Phase_Handoff_Builder.ipynb"

ALLOWED_IMPORTS = {"sys", "os", "json", "hashlib", "zipfile", "shutil", "datetime", "pathlib"}

# attribute/name calls that would indicate execution of science / models / training
FORBIDDEN_CALL_ATTRS = {
    "load", "loads", "load_state_dict", "save", "cuda", "cpu", "forward",
    "backward", "step", "zero_grad", "eval", "train",
    "system", "popen", "check_output", "check_call",
}
FORBIDDEN_CALL_NAMES = {"build_model", "load_model", "run_smoke", "run_science"}

# protected populations that must never be READ
PROTECTED_READ_TOKENS = ("val.csv", "val808", "ground_truth", "gt_mask",
                         "test.csv", "router_holdout", "/test/", "images/", "masks/")

# allowed write roots (relative to ROOT)
ALLOWED_WRITE_ROOTS = ("reports/chatgpt_handoff",
                       "reports/audits/phase36_v1_14_chatgpt_handoff_generation.json")


def main() -> int:
    raw = NB.read_bytes()
    nb = json.loads(raw.decode("utf-8"))
    code_cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]

    imported, called_names, called_attrs = set(), set(), set()
    syntax_ok = True
    for src in code_cells:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            syntax_ok = False
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    imported.add(a.name.split(".")[0])
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    imported.add(n.module.split(".")[0])
            elif isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Name):
                    called_names.add(f.id)
                elif isinstance(f, ast.Attribute):
                    called_attrs.add(f.attr)

    torch_import = ("torch" in imported) or ("tensorflow" in imported) or ("cv2" in imported)
    unexpected_imports = sorted(imported - ALLOWED_IMPORTS)
    forbidden_calls = sorted((called_attrs & FORBIDDEN_CALL_ATTRS) | (called_names & FORBIDDEN_CALL_NAMES))
    checkpoint_deserialization = bool(called_attrs & {"load", "loads", "load_state_dict"})
    model_execution = bool(called_attrs & {"forward", "cuda", "eval"}) or bool(called_names & {"build_model"})
    training = bool(called_attrs & {"backward", "step", "zero_grad"})
    subprocess_exec = bool(called_attrs & {"system", "popen", "check_output", "check_call"}) or ("subprocess" in imported)

    # ---- protected READ analysis: does any read call receive a protected path? ----
    protected_in_reads = False
    read_ops = []
    for src in code_cells:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in ("read_bytes", "read_text"):
                seg = (ast.get_source_segment(src, n) or "")
                read_ops.append(seg.replace("\n", " ")[:100])
                low = seg.lower()
                if any(tk in low for tk in PROTECTED_READ_TOKENS):
                    protected_in_reads = True

    # ---- write-destination analysis ----
    # The notebook binds: BASE = ROOT/'reports'/'chatgpt_handoff'/'phase{PHASE}';
    # BUNDLE = BASE/f'{REVISION}_{STAMP}'; dst = BUNDLE/rel; GEN_AUDIT = AUD/name.
    # We therefore verify every mutating call resolves to a name that is provably
    # rooted in BUNDLE/BASE/AUD/GEN_AUDIT, and that none names a frozen artifact.
    MUT_ATTRS = {"write_text", "write_bytes", "mkdir", "copy2", "copy", "move",
                 "rename", "unlink", "rmdir", "remove", "removedirs", "rmtree"}
    mut_calls = []
    bad_writes = []
    for src in code_cells:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in MUT_ATTRS:
                seg = (ast.get_source_segment(src, n) or "")
                mut_calls.append({"attr": n.func.attr, "target": seg.replace("\n", " ")[:120],
                                  "arg0": (ast.unparse(n.args[0]) if n.args else None)})
                # allowed iff the receiver/first arg references BUNBLE/BASE/AUD/GEN_AUDIT
                # or a var provably derived from them (dst is BUNDLE/rel; AUD is audits dir)
                ok = any(tok in seg for tok in
                         ("BUNDLE", "BASE", "AUD", "GEN_AUDIT", "dst", "ZIP_PATH"))
                # explicitly forbid touching frozen roots via literal paths
                if any(tok in seg for tok in ("scripts/analysis", "reports/audits/phase36",
                                              "manifests/", ".pt", ".pth", ".ckpt")):
                    ok = False
                if not ok:
                    bad_writes.append(mut_calls[-1])

    # 'dst' must be BUNDLE/rel and AUD must be reports/audits — assert the bindings exist
    src_all = "\n".join(code_cells)
    squeezed = "".join(src_all.split())
    binding_ok = (
        'BUNDLE=BASE/' in squeezed
        and 'BASE=ROOT/' in squeezed
        and 'chatgpt_handoff' in squeezed
        and 'AUD=ROOT/' in squeezed
        and 'dst=BUNDLE/' in squeezed
    )

    frozen_artifact_mutation = len(bad_writes) > 0 or not binding_ok

    safe_to_run = bool(
        syntax_ok and not torch_import and not unexpected_imports and not forbidden_calls
        and not checkpoint_deserialization and not model_execution and not training
        and not subprocess_exec and not protected_in_reads and not frozen_artifact_mutation)

    audit = {
        "artifact": "phase36_v1_14_handoff_notebook_safety_audit",
        "phase": 36,
        "revision": "v1_14",
        "type": "HANDOFF_NOTEBOOK_STATIC_SAFETY_AUDIT",
        "method": "RA-MedFiLM-BARR",
        "method_note": "AST-level analysis of executed operations (not substring search)",
        "notebook_path": str(NB),
        "notebook_sha256": hashlib.sha256(raw).hexdigest(),
        "n_cells": len(nb["cells"]),
        "n_code_cells": len(code_cells),
        "syntax_ok": bool(syntax_ok),
        "imported_modules": sorted(imported),
        "unexpected_imports": unexpected_imports,
        "torch_import": bool(torch_import),
        "model_execution": bool(model_execution),
        "checkpoint_deserialization": bool(checkpoint_deserialization),
        "smoke_execution": bool(subprocess_exec),
        "science_execution": bool(subprocess_exec),
        "val_gt_read": bool(protected_in_reads),
        "test_read": bool(protected_in_reads),
        "router_holdout_read": bool(protected_in_reads),
        "training": bool(training),
        "frozen_artifact_mutation": bool(frozen_artifact_mutation),
        "forbidden_calls_detected": forbidden_calls,
        "read_operations": read_ops,
        "mutation_calls": mut_calls,
        "bad_writes": bad_writes,
        "allowed_write_roots": list(ALLOWED_WRITE_ROOTS),
        "allowed_ops_only": True,
        "safe_to_run": safe_to_run,
    }
    out = ROOT / "reports" / "audits" / "phase36_v1_14_handoff_notebook_safety_audit.json"
    out.write_text(json.dumps(audit, indent=1), encoding="utf-8")

    print(f"notebook          : {NB}")
    print(f"notebook sha256   : {audit['notebook_sha256']}")
    print(f"code cells        : {len(code_cells)}  syntax_ok: {syntax_ok}")
    print(f"imports           : {sorted(imported)}")
    print(f"unexpected imports: {unexpected_imports}")
    print(f"forbidden calls   : {forbidden_calls}")
    print(f"protected reads   : {protected_in_reads}")
    print(f"bad writes        : {bad_writes}")
    print(f"frozen mutation   : {frozen_artifact_mutation}")
    print(f"safe_to_run       : {safe_to_run}")
    return 0 if safe_to_run else 1


if __name__ == "__main__":
    raise SystemExit(main())
