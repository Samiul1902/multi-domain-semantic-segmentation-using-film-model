"""Phase39 frozen model loaders (v1.0) — FROZEN DURING PHASE38.

B_phi (BARRBenefitRouterV1) and S_omega (BARRPostSafetyV1) are AST-extracted
from their frozen canonical source files, exactly as the consumed Phase36
pipeline does. Reproduces the frozen class identity without importing a
stale module surface.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ROUTER_SOURCE = "scripts/analysis/train_phase25d_router.py"
ROUTER_CLASS = "BARRBenefitRouterV1"
SOMEGA_SOURCE = "scripts/analysis/phase25f_execution_common.py"
SOMEGA_CLASS = "BARRPostSafetyV1"


def _extract_class(source_rel: str, class_name: str):
    import torch  # noqa: F401 -- required by the extracted class bodies
    import torch.nn as nn  # noqa: F401
    src = (ROOT / source_rel).read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            ns = {"__name__": "_phase39_" + class_name, "__builtins__": __builtins__}
            exec("import torch\nimport torch.nn as nn\n", ns)
            exec(compile(ast.Module(body=[node], type_ignores=[]), source_rel, "exec"), ns)
            return ns[class_name]
    raise RuntimeError(f"{class_name} not found in frozen source {source_rel}")


def load_router():
    return _extract_class(ROUTER_SOURCE, ROUTER_CLASS)()


def load_somega():
    return _extract_class(SOMEGA_SOURCE, SOMEGA_CLASS)()
