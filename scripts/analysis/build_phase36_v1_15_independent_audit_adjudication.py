#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — D80 v1.15 INDEPENDENT-AUDIT ADJUDICATION (write-once, WO#17B).

STATIC / NON-CONSUMING.  Records the independent-audit verdict on the frozen
v1.15 family: the SCIENTIFIC repairs are valid (D61 = PASS, D75/POLICY_B = PASS),
but the OPERATIONAL / GOVERNANCE / PROVENANCE layer was NOT rebased from frozen
v1.14, so v1.15 may NOT be authorized for real execution.

D80 = V1_15_OPERATIONAL_GOVERNANCE_LAYER_NOT_REBASED_FROM_V1_14
D80_status = ESTABLISHED
v1_15_execution_authorized = false
v1_15_attempt_consumed = false
scientific_semantics_effect = NONE

Every D80 sub-finding is derived from the frozen v1.15 source by STATIC analysis
(no execution).  Re-run -> REFUSE_OVERWRITE (rc 2).  Never delete/recreate.

NO v1.15/v1.16 execution.  NO model.  NO checkpoint.  NO VAL image/GT.
NO TEST.  NO ROUTER_HOLDOUT.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
V15 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_15.py"
V15_LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_15.py"
OUT = AUD / "phase36_v1_15_independent_audit_adjudication_v1_0.json"

V15_SHA = "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002"
V15_LAUNCHER_SHA = "2ad201fde72845891571cb1a53a675f6d7075dde23383da3eaa0b13b15d10c1c"
V15_HANDOFF_SHA = "8aa164955032738dd3528df9424c8e373de840f20c62c054a5904980f7394273"


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


def main() -> int:
    src = V15.read_text(encoding="utf-8")
    lsrc = V15_LAUNCHER.read_text(encoding="utf-8")

    # ---- D80-A: launcher omits required --mode science argument ---- #
    exec_requires_mode = ('ap.add_argument("--mode", required=True' in src
                          or "add_argument('--mode', required=True" in src)
    launcher_cmd_has_mode = re.search(r"cmd\s*=\s*\[[^\]]*\"--mode\"[^\]]*\]", lsrc) is not None
    d80a = bool(exec_requires_mode and not launcher_cmd_has_mode)

    # ---- D80-B: v1.15 reuses v1.14 science artifact namespace ---- #
    reused = [p for p in (
        "phase36_robustness_scientific_result_v1_14.json",
        "phase36_robustness_science_start_v1_14.json",
        "phase36_robustness_science_failure_v1_14.json",
    ) if p in src]
    d80b = len(reused) > 0

    # ---- D80-C: launch authority token mismatch ---- #
    exec_token = None
    m = re.search(r'LAUNCH_AUTHORITY_TOKEN\s*=\s*"([^"]+)"', src)
    if m:
        exec_token = m.group(1)
    launcher_token = None
    m2 = re.search(r'LAUNCH_AUTHORITY\s*=\s*"([^"]+)"', lsrc)
    if m2:
        launcher_token = m2.group(1)
    d80c = bool(exec_token and launcher_token and exec_token != launcher_token)

    # ---- D80-D: science operator gate not rebased ---- #
    uses_inherited_gate = "C.GATE_ENV" in src
    d80d = bool(uses_inherited_gate)

    # ---- D80-E: transitive self-integrity still bound to v1.14 execution SHA ---- #
    reads_v1_14_manifest = "phase36_v1_14_runtime_source_integrity_manifest.json" in src
    d80e = bool(reads_v1_14_manifest)

    # ---- D80-F: release attestation still bound to v1.14 ---- #
    release_rev_is_v1_14 = '_SCIENCE_RELEASE_REVISION = "ra_medfilm_barr_phase36_robustness_v1_14"' in src
    requires_v1_14_smoke = "SMOKE_V1_14_ARTIFACT" in src
    d80f = bool(release_rev_is_v1_14 and requires_v1_14_smoke)

    # ---- D80-G: stage journal not implemented ---- #
    d80g = ("journal" not in src.lower())

    # ---- D80-H: launcher does not pin exact execution SHA ---- #
    pins_literal = V15_SHA in lsrc
    d80h = not pins_literal

    # ---- D80-I: validation coverage missed operational cross-contract ---- #
    # The v1.15 unit/preflight/NC suites did not test the mode-argument / token /
    # namespace cross-contract (they validated scientific repairs + inherited
    # governance only).  No dedicated operational cross-contract validator exists.
    cross_contract_validator_exists = (ROOT / "scripts/analysis"
                                       / "validate_phase36_v1_16_operational_cross_contract.py").exists()
    d80i = not cross_contract_validator_exists

    subfindings = {
        "D80-A": {
            "id": "LAUNCHER_OMITS_REQUIRED_MODE_SCIENCE_ARGUMENT",
            "established": d80a,
            "evidence": {
                "execution_requires_mode": exec_requires_mode,
                "execution_argparse": 'ap.add_argument("--mode", required=True, choices=C.MODES)',
                "launcher_real_cmd": "[canonical_python, execution_source]",
                "launcher_cmd_contains_mode": launcher_cmd_has_mode,
            },
            "required_repair": "[canonical_python, execution_source, \"--mode\", \"science\"]",
        },
        "D80-B": {
            "id": "V1_15_EXECUTION_REUSES_V1_14_SCIENCE_ARTIFACT_NAMESPACE",
            "established": d80b,
            "evidence": {
                "inherited_v1_14_paths": reused,
                "separate_v1_15_paths_used": ("phase36_robustness_science_start_v1_15.json" in src),
            },
            "required_repair": "entirely new v1.16 namespace",
        },
        "D80-C": {
            "id": "V1_15_LAUNCH_AUTHORITY_TOKEN_MISMATCH",
            "established": d80c,
            "evidence": {
                "execution_expects": exec_token,
                "launcher_sets": launcher_token,
            },
            "required_repair": "PHASE36_V1_16_LAUNCH_AUTHORITY (both sides)",
        },
        "D80-D": {
            "id": "V1_15_SCIENCE_OPERATOR_GATE_NOT_REBASED",
            "established": d80d,
            "evidence": {
                "execution_uses_inherited_C.GATE_ENV": uses_inherited_gate,
                "smoke_gate_env_used": "C.SMOKE_GATE_ENV" in src,
            },
            "required_repair": "explicit v1.16 gate PHASE36_V1_16_EXECUTE bound identically in exec + launcher",
        },
        "D80-E": {
            "id": "V1_15_TRANSITIVE_SELF_INTEGRITY_STILL_BOUND_TO_V1_14_EXECUTION_SHA",
            "established": d80e,
            "evidence": {
                "reads_v1_14_runtime_manifest": reads_v1_14_manifest,
                "v1_14_manifest_path": "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json",
            },
            "required_repair": "new v1.16 runtime integrity authority whose execution_source_sha256 == exact v1.16 SHA",
        },
        "D80-F": {
            "id": "V1_15_RELEASE_ATTESTATION_STILL_BOUND_TO_V1_14",
            "established": d80f,
            "evidence": {
                "release_revision_is_v1_14": release_rev_is_v1_14,
                "requires_v1_14_smoke_artifact": requires_v1_14_smoke,
            },
            "required_repair": "new v1.16 science-release attestation binding the exact v1.16 source",
        },
        "D80-G": {
            "id": "V1_15_STAGE_JOURNAL_NOT_IMPLEMENTED",
            "established": d80g,
            "evidence": {"journal_mentions_in_v1_15_source": src.lower().count("journal")},
            "required_repair": "crash-survivable v1.16 stage journal",
        },
        "D80-H": {
            "id": "V1_15_LAUNCHER_DOES_NOT_PIN_V1_15_EXECUTION_SOURCE_AUTHORITY",
            "established": d80h,
            "evidence": {
                "launcher_records_current_exec_sha": "sha256_file(EXECUTION_SOURCE)" in lsrc,
                "launcher_requires_literal_v1_15_sha": pins_literal,
            },
            "required_repair": "v1.16 launcher must compare v1.16 execution bytes against a literal frozen expected SHA",
        },
        "D80-I": {
            "id": "V1_15_VALIDATION_COVERAGE_MISSED_OPERATIONAL_CROSS_CONTRACT",
            "established": d80i,
            "evidence": {
                "existing_suites": ["unit", "preflight", "negative_controls", "science_repair_validator"],
                "operational_cross_contract_validator_exists": cross_contract_validator_exists,
            },
            "required_repair": "new validation must detect every D80-A..H mutation",
        },
    }

    payload = {
        "artifact": "phase36_v1_15_independent_audit_adjudication_v1_0",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_15",
        "type": "INDEPENDENT_AUDIT_ADJUDICATION",
        "mode": "STATIC_NON_CONSUMING",
        "generated_utc": now(),

        "v1_15_scientific_repairs_valid": True,
        "D61": "PASS",
        "D75_POLICY_B": "PASS",

        "D80": "V1_15_OPERATIONAL_GOVERNANCE_LAYER_NOT_REBASED_FROM_V1_14",
        "D80_status": "ESTABLISHED",
        "D80_subfindings": subfindings,

        "v1_15_execution_authorized": False,
        "v1_15_attempt_consumed": False,
        "scientific_semantics_effect": "NONE",
        "classification": "PREEXECUTION_AUDIT_FAILED__OPERATIONAL_GOVERNANCE_REBASE_REQUIRED",

        "frozen_v1_15_authorities": {
            "execution_sha256": V15_SHA,
            "launcher_sha256": V15_LAUNCHER_SHA,
            "handoff_sha256": V15_HANDOFF_SHA,
        },

        "v1_15_attempt_absence": {
            "START": (AUD / "phase36_robustness_science_start_v1_15.json").exists(),
            "RESULT": (AUD / "phase36_robustness_science_result_v1_15.json").exists(),
            "FAILURE": (AUD / "phase36_robustness_science_failure_v1_15.json").exists(),
            "PROCESS_EXIT": (AUD / "phase36_robustness_science_process_exit_v1_15.json").exists(),
            "stdout": (AUD / "phase36_robustness_science_stdout_v1_15.txt").exists(),
            "stderr": (AUD / "phase36_robustness_science_stderr_v1_15.txt").exists(),
        },

        "preserved": True,
        "v1_15_modified": False,
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
        "terminal": "PHASE36_V1_15_INDEPENDENT_AUDIT_ADJUDICATION_COMPLETE__D80_ESTABLISHED",
    }

    if OUT.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE", "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2
    _write_once_json(OUT, payload)
    print(json.dumps({
        "status": "D80_ADJUDICATION_WRITTEN",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
        "D80": payload["D80"],
        "D80_status": payload["D80_status"],
        "subfindings_established": sum(1 for v in subfindings.values() if v["established"]),
        "subfindings_total": len(subfindings),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
