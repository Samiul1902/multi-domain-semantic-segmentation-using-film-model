#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.14 — LAUNCHER CO-EDIT NEGATIVE CONTROL (on-disk artifact).

Produces ``reports/audits/phase36_v1_14_launcher_co_edit_negative_control.json``.

It demonstrates, WITHOUT weakening the production launcher, that a source+manifest
CO-EDIT cannot pass the IMMUTABLE frozen launcher: the canonical launcher module is
loaded in-memory (production frozen constants intact, ``main()`` never executed),
and ``verify_authority(exec_path=..., manifest_path=...)`` is called against TEMP
mutated copies (exec mutated, manifest re-pointed at the mutated exec).  It MUST
return ``authorized=False``.

It also records the three other mandated mutants (exec-only, manifest-only,
old-override-env inert), so the artifact is a complete D35 mutant ledger.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_14.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"

EXEC_BYTES = EXEC.read_bytes()
MANIFEST_BYTES = MANIFEST.read_bytes()
EXEC_SHA = hashlib.sha256(EXEC_BYTES).hexdigest()
MANIFEST_SHA = hashlib.sha256(MANIFEST_BYTES).hexdigest()


def _load_production_launcher():
    spec = importlib.util.spec_from_file_location("phase36_v1_14_launch_coedit", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_production_launcher()
FROZEN_EXEC = mod.FROZEN_EXPECTED_EXEC_SHA
FROZEN_MANIFEST = mod.FROZEN_EXPECTED_MANIFEST_SHA


def _verify(exec_bytes: bytes, manifest_bytes: bytes) -> dict:
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td) / "phase36_robustness_execution_v1_14.py"
        mp = Path(td) / "phase36_v1_14_runtime_source_integrity_manifest.json"
        ep.write_bytes(exec_bytes)
        mp.write_bytes(manifest_bytes)
        return mod.verify_authority(exec_path=ep, manifest_path=mp)


# canonical control (must authorize)
_auth_canon = mod.verify_authority()

# (1) mutate execution only
_mut_exec = EXEC_BYTES + b"\n# tampered\n"
_auth_exec = _verify(_mut_exec, MANIFEST_BYTES)

# (2) mutate manifest only
_d = json.loads(MANIFEST_BYTES.decode("utf-8"))
_d["n_dependencies"] = 13
_mut_man = (json.dumps(_d, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
_auth_man = _verify(EXEC_BYTES, _mut_man)

# (3) co-edit exec + manifest (manifest re-points at the mutated exec)
_d2 = json.loads(MANIFEST_BYTES.decode("utf-8"))
_d2["execution_source_sha256"] = hashlib.sha256(_mut_exec).hexdigest()
_mut_man_co = (json.dumps(_d2, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
_auth_co = _verify(_mut_exec, _mut_man_co)

# (4) old override env names MUST be inert
_old = ("PHASE36_V1_11_EXPECTED_EXEC_SHA", "PHASE36_V1_11_EXPECTED_MANIFEST_SHA",
        "PHASE36_V1_14_EXPECTED_EXEC_SHA", "PHASE36_V1_14_EXPECTED_MANIFEST_SHA")
_saved = {k: os.environ.get(k) for k in _old}
try:
    for k in _old:
        os.environ[k] = "0" * 64
    _frozen_exec_under_env = mod._frozen_expected_exec_sha()
    _frozen_man_under_env = mod._frozen_expected_manifest_sha()
    _auth_env = mod.verify_authority()
finally:
    for k, v in _saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

env_inert = (_frozen_exec_under_env == FROZEN_EXEC
             and _frozen_man_under_env == FROZEN_MANIFEST
             and _frozen_exec_under_env != "0" * 64)

report = {
    "artifact": "phase36_v1_14_launcher_co_edit_negative_control",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_14",
    "type": "LAUNCHER_NEGATIVE_CONTROL",
    "model_free": True,
    "protected_population_read": False,
    "production_launcher_weakened": False,
    "production_launcher_sha256": hashlib.sha256(LAUNCHER.read_bytes()).hexdigest(),
    "canonical_execution_sha256": EXEC_SHA,
    "canonical_manifest_sha256": MANIFEST_SHA,
    "frozen_expected_exec_sha256": FROZEN_EXEC,
    "frozen_expected_manifest_sha256": FROZEN_MANIFEST,
    "canonical_pair_authorized": bool(_auth_canon.get("authorized")),
    "mutants": {
        "execution_only": {
            "mutated_exec_sha256": hashlib.sha256(_mut_exec).hexdigest(),
            "authorized": bool(_auth_exec.get("authorized")),
            "rejected": not bool(_auth_exec.get("authorized")),
        },
        "manifest_only": {
            "mutated_manifest_sha256": hashlib.sha256(_mut_man).hexdigest(),
            "authorized": bool(_auth_man.get("authorized")),
            "rejected": not bool(_auth_man.get("authorized")),
        },
        "co_edit_exec_and_manifest": {
            "mutated_exec_sha256": hashlib.sha256(_mut_exec).hexdigest(),
            "mutated_manifest_sha256": hashlib.sha256(_mut_man_co).hexdigest(),
            "authorized": bool(_auth_co.get("authorized")),
            "rejected": not bool(_auth_co.get("authorized")),
        },
        "old_override_env_names": {
            "names": list(_old),
            "frozen_exec_under_env": _frozen_exec_under_env,
            "frozen_manifest_under_env": _frozen_man_under_env,
            "canonical_authorized_under_env": bool(_auth_env.get("authorized")),
            "env_inert": bool(env_inert),
        },
    },
    "all_mutants_rejected": bool(
        not _auth_exec.get("authorized")
        and not _auth_man.get("authorized")
        and not _auth_co.get("authorized")
        and bool(_auth_canon.get("authorized"))
        and env_inert),
}
out = ROOT / "reports/audits/phase36_v1_14_launcher_co_edit_negative_control.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"all_mutants_rejected": report["all_mutants_rejected"],
                  "canonical_authorized": report["canonical_pair_authorized"]}, indent=1))
raise SystemExit(0 if report["all_mutants_rejected"] else 1)
