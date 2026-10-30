#!/usr/bin/env python
"""WO#21A §3/§5/§6/§7 — BUILD the v1.22 LAUNCHER + SUPERVISOR + MANIFEST + BUNDLE.

MODE: NEW-REVISION PREPARATION ONLY.  NON-CONSUMING.

Creates NEW artifacts (v1.21 versions UNTOUCHED):

    scripts/analysis/launch_phase36_v1_22.py
    scripts/analysis/supervise_phase36_v1_22.py
    reports/audits/phase36_v1_22_runtime_source_integrity_manifest.json
    reports/audits/phase36_v1_22_launch_authority_sha.json
    reports/audits/phase36_v1_22_prelaunch_authority_bundle.json

LAUNCHER (D96 REPAIR — FIX ONLY THE REAL-DISPATCH CALL):
  * STRICT mechanical rebase of the frozen v1.21 launcher (v1.21 -> v1.22).
  * The default real-dispatch branch now calls the verifier DEFINED in the
    launcher — ``verify_v1_20_consumed_history()`` — instead of the UNDEFINED
    ``verify_v1_19_consumed_history()``.
  * The §10 consumed-history gate STILL binds the consumed v1.20 state
    (phase36_v1_20_interruption_adjudication_v1_0.json, SHA 31c29955...).

SUPERVISOR (D95 PRESERVED):
  * STRICT mechanical rebase of the frozen v1.21 supervisor (which ALREADY
    contains the D95 interruption-safety repair); ONLY the three literal frozen
    pins (launcher / bundle / launch-authority-file SHA) are re-pointed.

PIN RESOLUTION
--------------
All pins are fixed-width 64-hex literals; substituting one for another never
changes a file's BYTE LENGTH, so the builder converges in a few passes.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

L_V121 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_21.py"
S_V121 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_21.py"
E_V122 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_22.py"

L_V122 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_22.py"
S_V122 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_22.py"

MANIFEST_V122 = AUD / "phase36_v1_22_runtime_source_integrity_manifest.json"
LAUNCH_AUTH_V122 = AUD / "phase36_v1_22_launch_authority_sha.json"
BUNDLE_V122 = AUD / "phase36_v1_22_prelaunch_authority_bundle.json"

FROZEN_L_V121 = "0711fd79ca117dedaf8eae1eb024d0754033e0417c506bd748577fec73402208"
FROZEN_S_V121 = "7182d3c0f0147a0d09421a5d534ac876d9f38be87df765117a0b6f080edd7ac4"
FROZEN_E_V122 = "29d29da8a9514db464f2db45f06a1ccaabf65aa302c18cd53bbb7419e2fbbd2b"

# v1.21 chain SHAs (literal lines being replaced in the rebased supervisor).
V121_BUNDLE_SHA = "04e38ceb98fd25a19cb6b0f67e6e0044da12cd7411325f0a4ad6e94e93863a6a"
V121_AUTHFILE_SHA = "9b629074fc18b19d7f831b4ef301fdb18103f9a7ca8a496e992818308d88d525"

# v1.22 governance authorities bound by the launch-authority file.
P_V1_22_ATTESTATION = AUD / "phase36_v1_22_science_release_attestation.json"
P_V1_22_ADJUDICATION = AUD / "phase36_v1_22_adjudication_d85_d86_d87_d88.json"

V1_20_INTERRUPTION_ADJUDICATION_SHA = (
    "31c29955380c6ec75d18f747dec4f91332177ddabeccef40cb0cafa8b37f5b72")
V1_21_PRELAUNCH_DEFECT_ADJUDICATION_SHA = (
    "4c2bd8f78778d9e3661a2ee5a828dfa4ac159be0d36ffada15b74083ac061bb9")
D85_D88_D92_ADJUDICATION_SHA = "8ec45fe9dc3a9c5f20f284f206cf464f79115ff246b4805aab56c8b2c6141e42"

ZERO64 = "0" * 64


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha(Path(p).read_bytes())


def write_once(path: Path, data: bytes) -> str:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        w = 0
        while w < len(data):
            w += os.write(fd, data[w:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH: {path}")
    return sha(data)


def rebase(s: str) -> str:
    s = s.replace("v1.21", "v1.22")
    s = s.replace("V1.21", "V1.22")
    s = s.replace("v1_21", "v1_22")
    s = s.replace("V1_21", "V1_22")
    return s


# sanity: frozen inputs unchanged
assert sha_file(L_V121) == FROZEN_L_V121, "frozen v1.21 launcher SHA drift"
assert sha_file(S_V121) == FROZEN_S_V121, "frozen v1.21 supervisor SHA drift"
assert sha_file(E_V122) == FROZEN_E_V122, "v1.22 exec SHA drift"

# Prerequisite governance artifacts MUST exist BEFORE the chain (acyclic DAG).
for _p in (P_V1_22_ATTESTATION, P_V1_22_ADJUDICATION):
    if not _p.exists():
        print(f"FAIL_CLOSED: prerequisite governance artifact missing: {_p.name} "
              "(build it BEFORE the chain)", file=sys.stderr)
        sys.exit(3)

_IF_MAIN_MARKER = '\nif __name__ == "__main__":\n    sys.exit(main(sys.argv[1:]))\n'

# ---- D96: the exact undefined call we must eliminate ---------------------- #
_UNDEFINED_CALL = "_consumed = verify_v1_19_consumed_history()"
_DEFINED_CALL = "_consumed = verify_v1_20_consumed_history()"


def launcher_text() -> str:
    t = rebase(L_V121.read_text(encoding="utf-8"))

    # 1) re-point the execution-source pin.
    old_src = ('V1_22_SOURCE_SHA = '
               '"312886c68f056375adc3f091766777da9e1caa47c1d422673de67751e8df7b97"')
    assert old_src in t, "v1.22 SOURCE_SHA anchor missing"
    t = t.replace(old_src, f'V1_22_SOURCE_SHA = "{FROZEN_E_V122}"')

    # 2) D96 FIX: the real-dispatch branch must call the DEFINED verifier.
    assert _UNDEFINED_CALL in t, "D96 undefined-call anchor missing"
    t = t.replace(_UNDEFINED_CALL, _DEFINED_CALL)

    # 3) correct the stale inline comment above the gate (v1.19 -> v1.20).
    stale = ("    # §10 (v1.22): CONSUMED-HISTORY GATE — v1.19 is CONSUMED; v1.22 must\n"
             "    # not be mistaken for a clean-revision re-run. FAIL CLOSED on deviation.")
    fresh = ("    # §10 (v1.22): CONSUMED-HISTORY GATE — v1.20 is the LAST CONSUMED\n"
             "    # revision; v1.22 must not be mistaken for a clean-revision re-run.\n"
             "    # FAIL CLOSED on deviation.")
    if stale in t:
        t = t.replace(stale, fresh)

    # POST-CONDITION: the undefined symbol must be GONE from the whole file.
    assert "verify_v1_19_consumed_history" not in t, \
        "D96: undefined symbol still present after fix"
    assert "verify_v1_20_consumed_history" in t, \
        "D96: defined verifier missing after fix"
    return t


def supervisor_text(bundle_sha: str, authfile_sha: str, launcher_sha: str) -> str:
    s = rebase(S_V121.read_text(encoding="utf-8"))

    assert f'FROZEN_V1_22_LAUNCHER_SHA = "{FROZEN_L_V121}"' in s, "sup launcher pin anchor"
    assert f'FROZEN_V1_22_AUTHORITY_BUNDLE_SHA = "{V121_BUNDLE_SHA}"' in s, "sup bundle pin anchor"
    assert f'FROZEN_V1_22_LAUNCH_AUTHORITY_FILE_SHA = "{V121_AUTHFILE_SHA}"' in s, "sup authfile pin anchor"
    s = s.replace(f'FROZEN_V1_22_LAUNCHER_SHA = "{FROZEN_L_V121}"',
                  f'FROZEN_V1_22_LAUNCHER_SHA = "{launcher_sha}"')
    s = s.replace(f'FROZEN_V1_22_AUTHORITY_BUNDLE_SHA = "{V121_BUNDLE_SHA}"',
                  f'FROZEN_V1_22_AUTHORITY_BUNDLE_SHA = "{bundle_sha}"')
    s = s.replace(f'FROZEN_V1_22_LAUNCH_AUTHORITY_FILE_SHA = "{V121_AUTHFILE_SHA}"',
                  f'FROZEN_V1_22_LAUNCH_AUTHORITY_FILE_SHA = "{authfile_sha}"')

    # D95 must survive the rebase verbatim.
    for needle in ("_POPEN = subprocess.Popen",
                   "except KeyboardInterrupt",
                   "except BaseException",
                   "_terminate_child_tree(",
                   "UNOBSERVED_CHILD_TERMINATION",
                   "NORMAL_CHILD_COMPLETION",
                   "SUPERVISOR_INTERRUPTION",
                   "SUPERVISOR_INTERNAL_EXCEPTION"):
        assert needle in s, f"D95 marker lost in supervisor rebase: {needle!r}"
    return s


# --------------------------------------------------------------------------- #
# FIXED-POINT PIN RESOLUTION                                                    #
# --------------------------------------------------------------------------- #
V1_22_ATTESTATION_SHA = sha_file(P_V1_22_ATTESTATION)
V1_22_ADJUDICATION_SHA = sha_file(P_V1_22_ADJUDICATION)

launcher_sha = ZERO64
bundle_sha = ZERO64
authfile_sha = ZERO64

for _ in range(12):
    l_txt = launcher_text()
    l_bytes = l_txt.encode("utf-8")
    new_launcher_sha = sha(l_bytes)

    bundle_doc = {
        "artifact": "phase36_v1_22_prelaunch_authority_bundle",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "FINAL_PRELAUNCH_AUTHORITY_BUNDLE",
        "mode": "STATIC_NON_CONSUMING_GOVERNANCE_ONLY",
        "generated_utc": "2026-10-11T00:00:00Z",
        "authority_order": "ACYCLIC (A->B->C->D->E)",
        "supersedes_revision": "v1.21",
        "supervisor_sha256_present": False,
        "count_semantics": {
            "table_figure_target_count": 16,
            "total_reachable_write_target_count": 23,
            "unclassified_write_target_count": 0,
            "namespace_overlap_count": 0,
        },
        "v1_21_attempt_state": {
            "classification": "NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT",
            "defect": "D96",
            "attempt_consumed": False,
            "retry_permitted": False,
        },
        "v1_20_consumed_state": {
            "classification": "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT",
            "defect": "D95",
            "attempt_consumed": True,
            "retry_permitted": False,
        },
        "binds": {
            "v1_22_execution_source": {
                "path": "scripts/analysis/phase36_robustness_execution_v1_22.py",
                "sha256": FROZEN_E_V122,
            },
            "v1_22_launcher": {
                "path": "scripts/analysis/launch_phase36_v1_22.py",
                "sha256": new_launcher_sha,
                "role": "PINNED_BY_DEDICATED_LAUNCH_AUTHORITY_FILE",
            },
            "v1_22_runtime_manifest": {
                "path": "reports/audits/phase36_v1_22_runtime_source_integrity_manifest.json",
                "sha256": "PENDING_MANIFEST_SHA",
            },
            "v1_20_interruption_adjudication": {
                "path": "reports/audits/phase36_v1_20_interruption_adjudication_v1_0.json",
                "sha256": V1_20_INTERRUPTION_ADJUDICATION_SHA,
            },
            "v1_21_prelaunch_defect_adjudication": {
                "path": "reports/audits/phase36_v1_21_prelaunch_defect_adjudication_v1_0.json",
                "sha256": V1_21_PRELAUNCH_DEFECT_ADJUDICATION_SHA,
            },
        },
        "acyclicity": {
            "bundle_contains_supervisor_sha256": False,
            "bundle_contains_launch_authority_file_sha256": False,
            "note": ("The bundle binds exec/manifest/governance. It NEVER carries "
                     "the supervisor SHA (acyclic by construction). The launcher's "
                     "expected SHAs are read from a SEPARATELY-FROZEN launch-authority "
                     "constant file whose OWN raw bytes are pinned by the supervisor."),
        },
        "terminal": "PHASE36_V1_22_PRELAUNCH_AUTHORITY_BUNDLE_WRITTEN",
    }

    m121 = json.loads(
        (AUD / "phase36_v1_21_runtime_source_integrity_manifest.json").read_text("utf-8"))
    manifest_doc = json.loads(rebase(json.dumps(m121)))
    manifest_doc["artifact"] = "phase36_v1_22_runtime_source_integrity_manifest"
    manifest_doc["revision"] = "ra_medfilm_barr_phase36_robustness_v1_22"
    manifest_doc["execution_source"] = "scripts/analysis/phase36_robustness_execution_v1_22.py"
    manifest_doc["execution_source_sha256"] = FROZEN_E_V122
    manifest_doc["supersedes_revision"] = "v1.21"
    manifest_doc["v1_21_attempt_state"] = "NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT"
    manifest_doc["v1_20_consumed_state"] = "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT"
    manifest_doc["d95_supervisor_interruption_repair"] = True
    manifest_doc["d95_repair_class"] = (
        "V1_20_SUPERVISOR_RETURNS_ZERO_ON_UNOBSERVED_CHILD_TERMINATION")
    manifest_doc["d96_launcher_real_dispatch_call_repair"] = True
    manifest_doc["d96_repair_class"] = (
        "V1_21_REAL_DISPATCH_CALLS_UNDEFINED_V1_19_CONSUMED_HISTORY_VERIFIER")
    dep_ok = True
    for rel, exp in manifest_doc["dependencies"].items():
        obs = sha_file(ROOT / rel)
        manifest_doc["dependency_verification"][rel] = {
            "expected": exp, "observed": obs, "match": obs == exp}
        dep_ok = dep_ok and obs == exp
    ck_ok = True
    for rel, exp in manifest_doc["checkpoints"].items():
        obs = sha_file(ROOT / rel)
        manifest_doc["checkpoint_verification"][rel] = {
            "expected": exp, "observed": obs, "match": obs == exp}
        ck_ok = ck_ok and obs == exp
    manifest_doc["all_dependencies_match"] = dep_ok
    manifest_doc["all_checkpoints_match"] = ck_ok
    manifest_doc["launcher_sha256_present"] = False
    manifest_doc["d61_canonical_fusion_preserved"] = True
    manifest_doc["d75_policy_b_preserved"] = True
    manifest_doc["d93a_journal_helper_defined"] = True
    manifest_doc["scientific_delta_distinct_classes"] = []
    manifest_doc["generated_utc"] = "2026-10-11T00:00:00Z"
    manifest_doc["non_circular_chain"] = [
        "SUPERVISOR pins frozen v1.22 launcher SHA + prelaunch-authority-bundle SHA before dispatch",
        "LAUNCHER pins literal v1.22 execution SHA + this manifest SHA + the v1.22 PRELAUNCH AUTHORITY BUNDLE SHA",
        "EXECUTION SOURCE reads this manifest, verifies its own bytes vs execution_source_sha256",
        "EXECUTION SOURCE requires the launch-authority token PHASE36_V1_22_LAUNCH_AUTHORITY",
    ]
    manifest_bytes = (json.dumps(manifest_doc, indent=1) + "\n").encode("utf-8")
    manifest_sha = sha(manifest_bytes)
    if not (dep_ok and ck_ok):
        print("WARN: manifest dependency/checkpoint mismatch", file=sys.stderr)
    bundle_doc["binds"]["v1_22_runtime_manifest"]["sha256"] = manifest_sha

    bundle_bytes = (json.dumps(bundle_doc, indent=1) + "\n").encode("utf-8")
    new_bundle_sha = sha(bundle_bytes)

    auth_doc = {
        "artifact": "phase36_v1_22_launch_authority_sha",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "LAUNCH_AUTHORITY_CONSTANT",
        "launcher": "scripts\\analysis\\launch_phase36_v1_22.py",
        "launcher_sha256": new_launcher_sha,
        "prelaunch_authority_bundle": "reports\\audits\\phase36_v1_22_prelaunch_authority_bundle.json",
        "prelaunch_authority_bundle_sha256": new_bundle_sha,
        "runtime_manifest_sha256": manifest_sha,
        "execution_source_sha256": FROZEN_E_V122,
        "release_attestation_sha256": V1_22_ATTESTATION_SHA,
        "d85_d88_d92_adjudication_sha256": D85_D88_D92_ADJUDICATION_SHA,
        "d85_d88_adjudication_sha256": V1_22_ADJUDICATION_SHA,
        "v1_20_interruption_adjudication_sha256": V1_20_INTERRUPTION_ADJUDICATION_SHA,
        "v1_21_prelaunch_defect_adjudication_sha256": V1_21_PRELAUNCH_DEFECT_ADJUDICATION_SHA,
        "non_circular_note": ("The launcher reads its expected SHAs from this file; "
                              "the supervisor pins THIS FILE's raw bytes BEFORE Popen."),
        "terminal": "PHASE36_V1_22_LAUNCH_AUTHORITY_CONSTANT_WRITTEN",
    }
    auth_bytes = (json.dumps(auth_doc, indent=1) + "\n").encode("utf-8")
    new_authfile_sha = sha(auth_bytes)

    if (new_launcher_sha == launcher_sha and new_bundle_sha == bundle_sha
            and new_authfile_sha == authfile_sha):
        break
    launcher_sha, bundle_sha, authfile_sha = (
        new_launcher_sha, new_bundle_sha, new_authfile_sha)
else:
    print("FAIL_CLOSED: pin fixed point did not converge", file=sys.stderr)
    sys.exit(3)

s_txt = supervisor_text(bundle_sha, authfile_sha, launcher_sha)
s_bytes = s_txt.encode("utf-8")
supervisor_sha = sha(s_bytes)

# --------------------------------------------------------------------------- #
# WRITE (write-once)                                                            #
# --------------------------------------------------------------------------- #
results = {}
results["launcher"] = {
    "path": "scripts/analysis/launch_phase36_v1_22.py",
    "sha256": write_once(L_V122, l_bytes),
}
assert results["launcher"]["sha256"] == launcher_sha

results["supervisor"] = {
    "path": "scripts/analysis/supervise_phase36_v1_22.py",
    "sha256": write_once(S_V122, s_bytes),
}
results["manifest"] = {
    "path": str(MANIFEST_V122.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(MANIFEST_V122, manifest_bytes),
}
assert results["manifest"]["sha256"] == manifest_sha
results["bundle"] = {
    "path": str(BUNDLE_V122.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(BUNDLE_V122, bundle_bytes),
}
assert results["bundle"]["sha256"] == bundle_sha
results["launch_authority_file"] = {
    "path": str(LAUNCH_AUTH_V122.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(LAUNCH_AUTH_V122, auth_bytes),
}
assert results["launch_authority_file"]["sha256"] == authfile_sha

print(json.dumps({
    "built": results,
    "supervisor_sha256": supervisor_sha,
    "pins": {
        "v1_22_exec_sha256": FROZEN_E_V122,
        "v1_22_launcher_sha256": launcher_sha,
        "v1_22_manifest_sha256": manifest_sha,
        "v1_22_bundle_sha256": bundle_sha,
        "v1_22_launch_authority_file_sha256": authfile_sha,
    },
    "d96_fix": {
        "undefined_symbol_removed": "verify_v1_19_consumed_history",
        "defined_symbol_called": "verify_v1_20_consumed_history",
    },
    "fixed_point_converged": True,
}, indent=2))
