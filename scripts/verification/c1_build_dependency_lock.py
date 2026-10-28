"""Build the C1 dependency lock from the actually verified environment.

Read-only with respect to the environment: it inspects, it never installs.
Writes ``reports/planning/c1_launch_release_v1/c1_dependency_lock.json``.

Non-circular identity: ``dependency_identity_digest`` is
``sha256(canonical_json(lock_without_identity_block))``. The rule is written into
the lock itself so a third party can recompute it.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/planning/c1_launch_release_v1/c1_dependency_lock.json"

PYTORCH_INDEX = "https://download.pytorch.org/whl/cu124"
PYPI_INDEX = "https://pypi.org/simple"
IDENTITY_RULE = ("sha256(json.dumps(lock_without_identity_block,sort_keys=True,"
                 "separators=(',',':'),ensure_ascii=False,allow_nan=False))")

DIRECT = {
    "torch", "torchvision", "numpy", "pandas", "matplotlib", "scikit-learn",
    "tqdm", "pyyaml", "scikit-image", "tensorboard", "seaborn", "ipython",
    "nbformat", "nbclient", "ipykernel",
}

WORKSPACE_LOCAL = [
    {"import_root": "src", "kind": "repository_package",
     "note": "imported from the repository root; not installed as a distribution"},
    {"import_root": "scripts", "kind": "repository_package",
     "note": "scripts/training/phase21_common.py supplies the per-image Dice/IoU metric"},
]


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def freeze() -> dict:
    raw = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    out = {}
    for line in raw.strip().splitlines():
        if "==" in line and not line.startswith("-"):
            name, _, version = line.partition("==")
            out[name.strip()] = version.strip()
    return out


def main() -> int:
    import torch

    installed = freeze()
    packages = []
    for name in sorted(installed, key=str.lower):
        version = installed[name]
        cuda_local = "+cu" in version
        packages.append({
            "name": name,
            "version": version,
            "index": PYTORCH_INDEX if cuda_local else PYPI_INDEX,
            "provenance": "pytorch_cu124_wheel_index" if cuda_local else "pypi",
            "direct": name.lower() in {d.lower() for d in DIRECT},
        })

    lock = {
        "schema": 1,
        "scope": "C1_FILM_ATTRIBUTION_V1",
        "study_id": "C1_FILM_ATTRIBUTION_V1",
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable": sys.executable,
            "requires_python": ">=3.10",
        },
        "platform": {"system": platform.system(), "machine": platform.machine(),
                     "release": platform.release()},
        "cuda": {
            "torch_version": str(torch.__version__),
            "torch_cuda_build": torch.version.cuda,
            "cudnn_version": torch.backends.cudnn.version(),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "device_capability": list(torch.cuda.get_device_capability(0))
            if torch.cuda.is_available() else None,
        },
        "indexes": {"pytorch_cu124": PYTORCH_INDEX, "pypi": PYPI_INDEX},
        "install_order": [
            f"pip install torch=={installed.get('torch')} torchvision=={installed.get('torchvision')} --index-url {PYTORCH_INDEX}",
            "pip install <remaining pinned packages> --index-url " + PYPI_INDEX,
        ],
        "workspace_local": WORKSPACE_LOCAL,
        "package_count": len(packages),
        "packages": packages,
        "reconstruction_status": {
            "clean_install_verified": False,
            "statement": ("The environment was inspected, not reconstructed. Clean-install "
                          "reproducibility is NOT claimed; the pins are the verified "
                          "installed set."),
        },
        "provenance_note": ("Versions were read from the live virtual environment with "
                            "pip freeze; no package was installed, upgraded or replaced."),
        "identity_rule": IDENTITY_RULE,
    }
    digest = hashlib.sha256(canonical(lock)).hexdigest()
    lock["identity"] = {"dependency_identity_digest": digest, "rule": IDENTITY_RULE}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"packages={len(packages)} direct={sum(1 for p in packages if p['direct'])}")
    print(f"dependency_identity_digest={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
