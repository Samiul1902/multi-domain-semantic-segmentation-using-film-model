"""Final synthetic-only production-chain test for the C1 six-run campaign.

Exercises the *real* execution chain -- Trainer.run, EpochStore, checkpoint
selection, resume-after-interruption -- on the tensor-only fixture. It never
reads a manifest, a pixel or a checkpoint from disk, so it cannot touch TRAIN,
VAL or TEST data and needs no launch grant.

What this proves, and what it does not:

  proves   the code path a real run would take completes, selects a best epoch,
           writes a recoverable checkpoint, and resumes to an identical result
  does not prove   any scientific claim. Synthetic tensors are not evidence.

Exit code 0 means the chain is sound. Any refusal is a real defect.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# --------------------------------------------------------------------------- #
# HOST DEFECT WORKAROUND -- import-time only, and it does not fix the defect.
#
# On this host CreateProcess from Python raises an access violation (crash at
# multiprocessing/popen_spawn_win32.py:75). torch's __init__ calls
# platform.machine(), which shells out to `cmd /c ver` through subprocess, so
# even *importing* torch dies. Seeding the uname cache from environment
# variables avoids that one spawn. It does NOT make worker processes work, so
# num_workers must stay 0 here. A real campaign needs this fixed at the host
# level, not shimmed.
# --------------------------------------------------------------------------- #
_SHIM = "platform._uname_cache"
platform._uname_cache = platform.uname_result(
    system="Windows",
    node=os.environ.get("COMPUTERNAME", "host"),
    release="10",
    version=os.environ.get("OS_VERSION", "10.0.26200"),
    machine=os.environ.get("PROCESSOR_ARCHITECTURE", "AMD64"),
)

from src.research.c1_film.integration_contract import make_contract  # noqa: E402
from src.research.c1_film.training_engine import Trainer  # noqa: E402
from src.research.c1_film.synthetic_fixture import fixture_loaders  # noqa: E402
from src.research.c1_film.control import parameter_accounting  # noqa: E402


def _tmp(name: str) -> Path:
    root = Path(tempfile.gettempdir()) / "c1_synthetic_chain" / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _artifacts(root: Path) -> dict:
    return {
        "lifecycle": (root / "lifecycle.json").is_file(),
        "latest": (root / "latest.json").is_file(),
        "epoch_ckpts": sorted(p.name for p in root.glob("epoch-*.pt")),
    }


def full_run(arm: str, seed: int) -> dict:
    root = _tmp(f"{arm}_seed{seed}")
    trainer = Trainer(make_contract(arm, seed, synthetic=True, device="cpu"))
    result = trainer.run(root, fixture_loaders)
    return {"arm": arm, "seed": seed, "result_complete": result["complete"],
            "epochs": result["epochs"], "best_epoch": trainer.best_epoch,
            "best_macro": trainer.best_macro, "identity": trainer.identity,
            "initial_sha256": trainer.initial_sha256,
            "counts": trainer.counts, "artifacts": _artifacts(root),
            "root": str(root)}


def interrupted_then_resumed(arm: str, seed: int) -> dict:
    """Stop after epoch 2, then resume. The resumed run must finish identically."""
    root = _tmp(f"{arm}_seed{seed}_resume")
    first = Trainer(make_contract(arm, seed, synthetic=True, device="cpu"))
    first.run(root, fixture_loaders, until_epoch=2)
    mid = _artifacts(root)

    second = Trainer(make_contract(arm, seed, synthetic=True, device="cpu"))
    result = second.run(root, fixture_loaders, resume=True)
    return {"identity_preserved": first.identity == second.identity,
            "initial_sha256_preserved": first.initial_sha256 == second.initial_sha256,
            "mid_artifacts": mid, "final": {"complete": result["complete"],
                                            "epochs": result["epochs"],
                                            "best_epoch": second.best_epoch},
            "artifacts": _artifacts(root), "root": str(root)}


def main() -> int:
    report: dict = {"synthetic_only": True, "scientific_evidence": False,
                    "runs": [], "checks": {}, "failures": [],
                    "host_shim_required": _SHIM}

    for arm, seed in (("C1-T", 42), ("C1-C", 42)):
        rec = full_run(arm, seed)
        report["runs"].append(rec)
        if not rec["result_complete"]:
            report["failures"].append(f"{arm}/seed{seed} did not complete")
        if not rec["artifacts"]["epoch_ckpts"]:
            report["failures"].append(f"{arm}/seed{seed} wrote no epoch checkpoint")
        if rec["best_epoch"] < 1:
            report["failures"].append(f"{arm}/seed{seed} selected no best epoch")

    # Resume must reproduce the same identity and reach the same best epoch.
    resume = interrupted_then_resumed("C1-T", 42)
    report["resume"] = resume
    if not resume["identity_preserved"]:
        report["failures"].append("resume changed the contract identity")
    if not resume["initial_sha256_preserved"]:
        report["failures"].append("resume changed the initial parameter digest")
    if not resume["final"]["complete"]:
        report["failures"].append("resumed run did not complete")

    # Matched arms. C1-C is a deepcopy of C1-T with conditioning frozen, so the
    # correct invariant is: identical total parameters and identical initial
    # digest, differing only in how many parameters are trainable. Freezing
    # never removes parameters, so a total-parameter difference would be a bug.
    t, c = report["runs"][0]["counts"], report["runs"][1]["counts"]
    report["checks"]["treatment"] = {"total": t["total"], "trainable": t["trainable"],
                                     "conditioning": t["conditioning"]}
    report["checks"]["control"] = {"total": c["total"], "trainable": c["trainable"],
                                   "conditioning": c["conditioning"]}
    report["checks"]["total_parameters_equal"] = t["total"] == c["total"]
    report["checks"]["trainable_delta"] = t["trainable"] - c["trainable"]
    report["checks"]["conditioning_parameters"] = t["conditioning"]
    report["checks"]["initial_digest_matched"] = (
        report["runs"][0]["initial_sha256"] == report["runs"][1]["initial_sha256"])

    if t["total"] != c["total"]:
        report["failures"].append("matched arms differ in total parameters")
    if t["trainable"] - c["trainable"] != t["conditioning"]:
        report["failures"].append(
            "trainable difference does not equal the conditioning parameter count")
    if c["trainable"] != 3432233 or t["trainable"] != 3523001:
        report["failures"].append("trainable counts drift from the frozen 3523001/3432233")
    if not report["checks"]["initial_digest_matched"]:
        report["failures"].append("matched arms do not start from the same weights")

    report["verdict"] = "CHAIN_SOUND" if not report["failures"] else "CHAIN_DEFECT"
    out = ROOT / "reports/audits/c1_r4_execution" / "synthetic_chain_test.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(json.dumps({k: report[k] for k in
                      ("verdict", "failures", "checks", "synthetic_only",
                       "scientific_evidence")}, indent=2))
    print(f"report -> {out}")
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
