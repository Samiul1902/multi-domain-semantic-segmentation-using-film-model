"""Phase27 EXECUTION - safe class extraction shim.

Two canonical Phase25 modules define their model classes alongside a
module-level training/execution body:

    scripts/analysis/train_phase25d_router.py          (runs Phase25D training on import)
    scripts/analysis/phase25f_execution_common.py      (imports a spec-common module)

Importing them directly would execute that body (and, for Phase25D, retrain).
This shim extracts ONLY the class definitions by parsing the source, compiling a
module containing just the requested definitions plus a controlled stub preamble,
so no training / no execution side effect occurs.

Used by the Phase27 execution to obtain ``BARRBenefitRouterV1`` and
``BARRPostSafetyV1`` without any import-time side effect.
"""
from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")


def _stubbed_import(name):
    """Return a stub module for heavyweight/irrelevant imports."""
    m = types.ModuleType(name)
    return m


def extract_class(src_path: Path, class_names, extra_imports=()):
    """Compile and exec ONLY the named classes from ``src_path``.

    The returned namespace contains the requested classes.  Any module-level
    statement that is not a class definition (or a harmless import) is skipped, so
    no training loop, no file write and no model construction runs.
    """
    src = Path(src_path).read_text(encoding="utf-8")
    tree = ast.parse(src)

    needed_imports = []
    class_nodes = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            needed_imports.append(node)
        elif isinstance(node, ast.ImportFrom):
            needed_imports.append(node)
        elif isinstance(node, ast.ClassDef) and node.name in class_names:
            class_nodes[node.name] = node

    missing = [c for c in class_names if c not in class_nodes]
    if missing:
        raise RuntimeError(f"class(es) not found in {src_path}: {missing}")

    ns: dict = {"__name__": "_phase27_class_shim_" + Path(src_path).stem}
    for imp in needed_imports:
        try:
            code = ast.Module(body=[imp], type_ignores=[])
            exec(compile(code, str(src_path), "exec"), ns)
        except Exception:  # noqa: BLE001 - unrelated imports may be heavyweight
            continue
    # safe builtins / libs the classes need
    for lib in ("torch", "numpy", "math"):
        if lib not in ns:
            try:
                ns[lib] = __import__(lib)
            except Exception:  # noqa: BLE001
                pass
    for name in class_names:
        code = ast.Module(body=[class_nodes[name]], type_ignores=[])
        exec(compile(code, str(src_path), "exec"), ns)
    return ns


def get_benefit_router():
    ns = extract_class(ROOT / "scripts/analysis/train_phase25d_router.py",
                       ["BARRBenefitRouterV1"])
    return ns["BARRBenefitRouterV1"]


def get_post_safety():
    """Phase25F's BARRPostSafetyV1 lives in phase25f_execution_common.py.

    That module's body imports phase25f_spec_repair_common (safe) and defines the
    class; extract the class directly and supply the two frozen module constants it
    needs (FEATURE_DIM, HIDDEN) from the file's own header.
    """
    path = ROOT / "scripts/analysis/phase25f_execution_common.py"
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    ns: dict = {"__name__": "_phase27_shim_post_safety"}
    ns["torch"] = __import__("torch")
    ns["nn"] = ns["torch"].nn
    ns["np"] = __import__("numpy")
    # lift the small module-level constants the class constructor needs
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in ("FEATURE_DIM", "HIDDEN", "NUMERIC_IDX", "ONEHOT_IDX") for t in targets):
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BARRPostSafetyV1":
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
            return ns["BARRPostSafetyV1"]
    raise RuntimeError("BARRPostSafetyV1 not found")


if __name__ == "__main__":
    R = get_benefit_router()
    S = get_post_safety()
    r = R()
    s = S()
    print("BARRBenefitRouterV1 params:", sum(p.numel() for p in r.parameters()))
    print("BARRPostSafetyV1 params:", sum(p.numel() for p in s.parameters()))
