"""Shared analysis-only guard for the ReMedFiLM notebooks.

Import and call `install()` before any other analysis code. The guard is
enforcement, not convention:

  * `sys.addaudithook` blocks process launches and writes outside the report dir,
  * the protected TEST manifest cannot be read,
  * `torch.optim.*` constructors and `Module.train(True)` raise.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(r"D:\Softfors\jup")
REPORT = REPO / "full_doc_report"

PROTECTED_READS = {(REPO / "manifests/phase4_v3/test.csv").resolve()}
BLOCKED_EVENTS = {"subprocess.Popen", "os.system", "os.exec", "os.spawn",
                  "os.posix_spawn", "os.startfile", "pty.spawn"}
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC


class AnalysisOnlyViolation(RuntimeError):
    """Raised when a cell attempts a non-analysis operation."""


_installed = False


def _audit(event, args, _blocked=frozenset(BLOCKED_EVENTS),
           _protected=frozenset(PROTECTED_READS),
           _report=str(REPORT), _flags=_WRITE_FLAGS, _path=Path):
    if event in _blocked:
        raise AnalysisOnlyViolation(f"blocked process launch: {event}")
    if event == "open":
        path, mode, flags = args
        try:
            p = _path(path).resolve()
        except Exception:
            return
        if str(p) in {str(x) for x in _protected}:
            raise AnalysisOnlyViolation(f"protected TEST manifest access: {p}")
        writing = False
        if isinstance(mode, str):
            writing = any(c in mode for c in "wax+")
        if isinstance(flags, int) and flags & _flags:
            writing = True
        if writing and _report not in str(p.parent) and str(p) != _report:
            raise AnalysisOnlyViolation(f"write outside full_doc_report: {p}")


def install() -> bool:
    """Install the guard once and return True."""
    global _installed
    if _installed:
        return True
    sys.addaudithook(_audit)
    try:
        import torch
        import torch.optim as optim

        def _no_optimiser(*a, **k):
            raise AnalysisOnlyViolation("optimiser construction is forbidden (analysis only)")

        for name in ("SGD", "Adam", "AdamW", "RMSprop", "Adagrad"):
            if hasattr(optim, name):
                setattr(optim, name, _no_optimiser)
        _orig_train = torch.nn.Module.train

        def _guarded_train(self, mode=True):
            if mode:
                raise AnalysisOnlyViolation("Module.train(True) is forbidden (analysis only)")
            return _orig_train(self, False)

        torch.nn.Module.train = _guarded_train
    except ImportError:
        pass
    _installed = True
    return True


def require() -> bool:
    return True


def self_test() -> list[tuple[str, str]]:
    """Run negative controls; returns (name, verdict) pairs."""
    results = []
    try:
        import torch
        for name, ctor in (("optimiser construction", torch.optim.Adam),
                           ("AdamW construction", torch.optim.AdamW)):
            try:
                ctor([])
                results.append((name, "NOT BLOCKED"))
            except AnalysisOnlyViolation:
                results.append((name, "blocked"))
    except ImportError:
        pass
    try:
        (REPO / "manifests/phase4_v3/test.csv").open("rb").read(1)
        results.append(("TEST manifest read", "NOT BLOCKED"))
    except AnalysisOnlyViolation:
        results.append(("TEST manifest read", "blocked"))
    except FileNotFoundError:
        results.append(("TEST manifest read", "blocked (file absent)"))
    try:
        (REPO / "reports" / "_guard_probe.txt").open("w").write("x")
        results.append(("write outside report dir", "NOT BLOCKED"))
    except AnalysisOnlyViolation:
        results.append(("write outside report dir", "blocked"))
    return results
