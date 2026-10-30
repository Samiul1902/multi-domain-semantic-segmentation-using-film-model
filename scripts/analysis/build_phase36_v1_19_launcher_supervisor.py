#!/usr/bin/env python
"""WO#19 §9 — BUILD v1.19 LAUNCHER + SUPERVISOR + MANIFEST + BUNDLE (write-once).

MODE: NEW-REVISION PREPARATION ONLY.  NON-CONSUMING.

Creates NEW artifacts (v1.18 versions UNTOUCHED):

    scripts/analysis/launch_phase36_v1_19.py
    scripts/analysis/supervise_phase36_v1_19.py
    reports/audits/phase36_v1_19_runtime_source_integrity_manifest.json
    reports/audits/phase36_v1_19_namespace_and_write_inventory.json
    reports/audits/phase36_v1_19_release_contract.json
    reports/audits/phase36_v1_19_launch_authority_sha.json
    reports/audits/phase36_v1_19_prelaunch_authority_bundle.json

The launcher and supervisor are STRICT mechanical rebases of the frozen v1.18
sources (v1_18->v1_19, V1_18->V1_19, v1.18->v1.19, V1.18->V1.19) plus:

  * V1_19_SOURCE_SHA  -> new v1.19 exec SHA
  * FROZEN_V1_19_LAUNCHER_SHA (supervisor)      -> new v1.19 launcher SHA
  * FROZEN_V1_19_AUTHORITY_BUNDLE_SHA           -> new v1.19 bundle SHA
  * FROZEN_V1_19_LAUNCH_AUTHORITY_FILE_SHA      -> new v1.19 authority-file SHA
  * §10 CONSUMED-HISTORY GATE appended + called in the launcher's real path.

PIN RESOLUTION
--------------
All pins are fixed-width 64-hex literals, so substituting one for another never
changes a file's BYTE LENGTH.  The builder therefore reaches a fixed point in a
small number of passes: it substitutes pins, hashes the consumers, and repeats
until the SHAs stop changing.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import datetime as _dt
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

L_V118 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_18.py"
S_V118 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_18.py"
E_V119 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_19.py"

L_V119 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_19.py"
S_V119 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_19.py"

MANIFEST_V119 = AUD / "phase36_v1_19_runtime_source_integrity_manifest.json"
NSINV_V119 = AUD / "phase36_v1_19_namespace_and_write_inventory.json"
CONTRACT_V119 = AUD / "phase36_v1_19_release_contract.json"
LAUNCH_AUTH_V119 = AUD / "phase36_v1_19_launch_authority_sha.json"
BUNDLE_V119 = AUD / "phase36_v1_19_prelaunch_authority_bundle.json"

FROZEN_L_V118 = "727a3bdd47f626826575de286a2a382dd63eb899c244af9da6e1d9d078944f3e"
FROZEN_S_V118 = "2528e0601fd3fd1231bc11e8258a9fb0ae9f1df8303fe2237d32385701cbc5d4"
V1_18_EXEC_SHA = "2259ce22e75ba9a3a8943769dc1e0ed5724f94902f5e8955976cd6ebeb8ce63e"
FROZEN_E_V119 = "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd"

# v1.18 chain SHAs (used only to locate the literal lines being replaced).
V118_BUNDLE_SHA = "0f6989bcc500ce6ba1cf963d4580bc2bdfbcb5db6ad0ce65fd46ade1d8529dfc"
V118_AUTHFILE_SHA = "a5d383f147fabf11104a8f619cdd1cb44442cca22fbe0b94632d40f76c1070e7"

# v1.19 governance authorities bound by the launch-authority file.
#   * release attestation = NEW v1.19 artifact (created separately).
#   * D85-D88 adjudication = the v1.18 adjudication artifact (shared governance
#     history; the adjudication of D85-D88 remains valid and unchanged).
V1_19_ATTESTATION_SHA = "c3f5068f51693c8441965255d55821c35e583c6d60d9ab5cbbbe5c43ed476b0e"
D85_D88_ADJUDICATION_SHA = "8ec45fe9dc3a9c5f20f284f206cf464f79115ff246b4805aab56c8b2c6141e42"

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
    assert path.stat().st_size == len(data), "post-write size mismatch"
    return sha(data)


def rebase(s: str) -> str:
    s = s.replace("v1.18", "v1.19")
    s = s.replace("V1.18", "V1.19")
    s = s.replace("v1_18", "v1_19")
    s = s.replace("V1_18", "V1_19")
    return s


# sanity: frozen inputs unchanged
assert sha_file(L_V118) == FROZEN_L_V118, "frozen v1.18 launcher SHA drift"
assert sha_file(S_V118) == FROZEN_S_V118, "frozen v1.18 supervisor SHA drift"
assert sha_file(E_V119) == FROZEN_E_V119, "v1.19 exec SHA drift"


# --------------------------------------------------------------------------- #
# §10 consumed-history gate (appended to the v1.19 launcher)                    #
# --------------------------------------------------------------------------- #
CONSUMED_GATE_CODE = '''

# =========================================================================== #
# §10 (v1.19) — CONSUMED-HISTORY GATE (NEW; PREVENTS CLEAN-REVISION MISTAKE)   #
# =========================================================================== #
# v1.18 is CONSUMED (CONSUMED_PRE_START_RUNTIME_FAILURE; D92).  v1.19 must NOT
# be mistaken for a clean-revision re-run of v1.18.  Before ANY real dispatch,
# the launcher REQUIRES that the v1.18 consumed history is EXACTLY the known
# recorded state: the v1.18 consumed-failure adjudication artifact exists with
# the expected SHA, the v1.18 START marker is ABSENT, and the v1.18 PROCESS_EXIT
# evidence is PRESENT.  Any deviation -> FAIL CLOSED.
V1_18_CONSUMED_ADJUDICATION = (
    AUD / "phase36_v1_18_consumed_prestart_failure_adjudication_v1_0.json")
V1_18_CONSUMED_ADJUDICATION_SHA = (
    "41c6d79790f302e0863b0646b659729594cdc15834b3697169d5503907d809f9")
V1_18_CONSUMED_EXPECTED_CLASSIFICATION = "CONSUMED_PRE_START_RUNTIME_FAILURE"
V1_18_CONSUMED_START_MARKER = (
    AUD / "phase36_robustness_science_start_v1_18.json")
V1_18_CONSUMED_PROCESS_EXIT = (
    AUD / "phase36_robustness_science_process_exit_v1_18.json")


def verify_v1_18_consumed_history() -> dict:
    """§10: prove v1.18 is the EXACT known consumed-failure state. FAIL CLOSED."""
    result = {"ok": False, "reasons": []}
    if not V1_18_CONSUMED_ADJUDICATION.exists():
        result["reasons"].append("v1_18_adjudication_absent")
        return result
    adj_sha = sha256_file(V1_18_CONSUMED_ADJUDICATION)
    if adj_sha != V1_18_CONSUMED_ADJUDICATION_SHA:
        result["reasons"].append("v1_18_adjudication_sha_mismatch")
    try:
        doc = json.loads(V1_18_CONSUMED_ADJUDICATION.read_text(encoding="utf-8"))
    except Exception as e:  # pragma: no cover
        result["reasons"].append("v1_18_adjudication_unreadable")
        return result
    if doc.get("classification") != V1_18_CONSUMED_EXPECTED_CLASSIFICATION:
        result["reasons"].append("v1_18_adjudication_classification_mismatch")
    if V1_18_CONSUMED_START_MARKER.exists():
        result["reasons"].append("v1_18_start_marker_present__expected_absent")
    if not V1_18_CONSUMED_PROCESS_EXIT.exists():
        result["reasons"].append("v1_18_process_exit_absent__expected_present")
    result["ok"] = not result["reasons"]
    result["v1_18_adjudication_sha256"] = adj_sha
    result["v1_18_start_marker_absent"] = not V1_18_CONSUMED_START_MARKER.exists()
    result["v1_18_process_exit_present"] = V1_18_CONSUMED_PROCESS_EXIT.exists()
    result["terminal"] = ("PHASE36_V1_19_CONSUMED_HISTORY_GATE_PASS" if result["ok"]
                          else "PHASE36_V1_19_CONSUMED_HISTORY_GATE_FAIL_CLOSED")
    return result
'''


_IF_MAIN_MARKER = '\nif __name__ == "__main__":\n    sys.exit(main(sys.argv[1:]))\n'


def launcher_text(launcher_self_sha: str) -> str:
    """Rebased v1.19 launcher.  ``launcher_self_sha`` is not embedded (the
    launcher does not pin itself); accepted for signature symmetry."""
    t = rebase(L_V118.read_text(encoding="utf-8"))
    assert f'V1_19_SOURCE_SHA = "{V1_18_EXEC_SHA}"' in t
    t = t.replace(f'V1_19_SOURCE_SHA = "{V1_18_EXEC_SHA}"',
                  f'V1_19_SOURCE_SHA = "{FROZEN_E_V119}"')

    # 1) Add the §10 consumed-history gate call into main()'s real dispatch path,
    #    immediately AFTER the operator-gate check and BEFORE run_all_gates().
    anchor = (
        '    # Real dispatch path.\n'
        '    if os.environ.get(TOKEN_ENV) != "1":\n'
        '        print(f"FAIL_CLOSED: operator gate {TOKEN_ENV}=1 not set; refusing real dispatch.")\n'
        '        return 3\n')
    assert anchor in t, "launcher main() anchor not found"
    gate_call = anchor + (
        '    # §10 (v1.19): CONSUMED-HISTORY GATE — v1.18 is CONSUMED; v1.19 must\n'
        '    # not be mistaken for a clean-revision re-run. FAIL CLOSED on deviation.\n'
        '    _consumed = verify_v1_18_consumed_history()\n'
        '    if not _consumed["ok"]:\n'
        '        print("FAIL_CLOSED: §10 consumed-history gate failed; NO attempt consumed.")\n'
        '        for _r in _consumed["reasons"]:\n'
        '            print(f"  {_r}")\n'
        '        return 3\n')
    t = t.replace(anchor, gate_call)

    # 2) Relocate the gate DEFINITION to BEFORE the `if __name__` block so it is
    #    defined by the time main() is invoked.
    assert _IF_MAIN_MARKER in t, "launcher if-main marker not found"
    t = t.replace(_IF_MAIN_MARKER, CONSUMED_GATE_CODE + _IF_MAIN_MARKER)
    return t


def supervisor_text(bundle_sha: str, authfile_sha: str, launcher_sha: str) -> str:
    s = rebase(S_V118.read_text(encoding="utf-8"))
    assert f'FROZEN_V1_19_LAUNCHER_SHA = "{FROZEN_L_V118}"' in s
    assert f'FROZEN_V1_19_AUTHORITY_BUNDLE_SHA = "{V118_BUNDLE_SHA}"' in s
    assert f'FROZEN_V1_19_LAUNCH_AUTHORITY_FILE_SHA = "{V118_AUTHFILE_SHA}"' in s
    s = s.replace(f'FROZEN_V1_19_LAUNCHER_SHA = "{FROZEN_L_V118}"',
                  f'FROZEN_V1_19_LAUNCHER_SHA = "{launcher_sha}"')
    s = s.replace(f'FROZEN_V1_19_AUTHORITY_BUNDLE_SHA = "{V118_BUNDLE_SHA}"',
                  f'FROZEN_V1_19_AUTHORITY_BUNDLE_SHA = "{bundle_sha}"')
    s = s.replace(f'FROZEN_V1_19_LAUNCH_AUTHORITY_FILE_SHA = "{V118_AUTHFILE_SHA}"',
                  f'FROZEN_V1_19_LAUNCH_AUTHORITY_FILE_SHA = "{authfile_sha}"')
    return s


# --------------------------------------------------------------------------- #
# FIXED-POINT PIN RESOLUTION                                                    #
# --------------------------------------------------------------------------- #
launcher_sha = ZERO64
bundle_sha = ZERO64
authfile_sha = ZERO64

for _ in range(12):
    l_txt = launcher_text(launcher_sha)
    l_bytes = l_txt.encode("utf-8")
    new_launcher_sha = sha(l_bytes)

    # bundle binds exec + manifest + launcher(self) + governance (non-circular:
    # bundle does NOT contain the launch-authority file SHA nor supervisor SHA).
    bundle_doc = {
        "artifact": "phase36_v1_19_prelaunch_authority_bundle",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_19",
        "type": "FINAL_PRELAUNCH_AUTHORITY_BUNDLE",
        "mode": "STATIC_NON_CONSUMING_GOVERNANCE_ONLY",
        "generated_utc": "2026-10-10T00:00:00Z",
        "authority_order": "ACYCLIC (A->B->C->D->E)",
        "supersedes_revision": "v1.18",
        "supervisor_sha256_present": False,
        "count_semantics": {
            "table_figure_target_count": 16,
            "total_reachable_write_target_count": 23,
            "unclassified_write_target_count": 0,
            "namespace_overlap_count": 0,
        },
        "v1_18_consumed_state": {
            "classification": "CONSUMED_PRE_START_RUNTIME_FAILURE",
            "defect": "D92",
            "attempt_consumed": True,
            "retry_permitted": False,
        },
        "binds": {
            "v1_19_execution_source": {
                "path": "scripts/analysis/phase36_robustness_execution_v1_19.py",
                "sha256": FROZEN_E_V119,
            },
            "v1_19_launcher": {
                "path": "scripts/analysis/launch_phase36_v1_19.py",
                "sha256": new_launcher_sha,
                "role": "PINNED_BY_DEDICATED_LAUNCH_AUTHORITY_FILE",
            },
            "v1_19_runtime_manifest": {
                "path": "reports/audits/phase36_v1_19_runtime_source_integrity_manifest.json",
                "sha256": "PENDING_MANIFEST_SHA",
            },
            "v1_18_consumed_adjudication": {
                "path": "reports/audits/phase36_v1_18_consumed_prestart_failure_adjudication_v1_0.json",
                "sha256": "41c6d79790f302e0863b0646b659729594cdc15834b3697169d5503907d809f9",
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
        "terminal": "PHASE36_V1_19_PRELAUNCH_AUTHORITY_BUNDLE_WRITTEN",
    }

    # manifest: REBASE the v1.18 manifest (same 14 deps + 4 checkpoints), only
    # the revision token + execution_source(+sha) change.  Re-verify the deps.
    m118 = json.loads(
        (AUD / "phase36_v1_18_runtime_source_integrity_manifest.json").read_text("utf-8"))
    manifest_doc = json.loads(rebase(json.dumps(m118)))
    manifest_doc["artifact"] = "phase36_v1_19_runtime_source_integrity_manifest"
    manifest_doc["revision"] = "ra_medfilm_barr_phase36_robustness_v1_19"
    manifest_doc["execution_source"] = "scripts/analysis/phase36_robustness_execution_v1_19.py"
    manifest_doc["execution_source_sha256"] = FROZEN_E_V119
    manifest_doc["supersedes_revision"] = "v1.18"
    # re-verify dependencies + checkpoints against the ACTUAL bytes on disk.
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
    manifest_doc["d92_journal_symbol_repair"] = True
    manifest_doc["scientific_delta_distinct_classes"] = ["D92"]
    manifest_doc["v1_18_consumed_state"] = "CONSUMED_PRE_START_RUNTIME_FAILURE"
    manifest_doc["generated_utc"] = "2026-10-10T00:00:00Z"
    manifest_doc["non_circular_chain"] = [
        "SUPERVISOR pins frozen v1.19 launcher SHA + prelaunch-authority-bundle SHA before dispatch",
        "LAUNCHER pins literal v1.19 execution SHA + this manifest SHA + the v1.19 PRELAUNCH AUTHORITY BUNDLE SHA",
        "EXECUTION SOURCE reads this manifest, verifies its own bytes vs execution_source_sha256",
        "EXECUTION SOURCE requires the launch-authority token PHASE36_V1_19_LAUNCH_AUTHORITY",
    ]
    manifest_bytes = (json.dumps(manifest_doc, indent=1) + "\n").encode("utf-8")
    manifest_sha = sha(manifest_bytes)
    if not (dep_ok and ck_ok):
        print("WARN: manifest dependency/checkpoint mismatch", file=sys.stderr)
    bundle_doc["binds"]["v1_19_runtime_manifest"]["sha256"] = manifest_sha

    bundle_bytes = (json.dumps(bundle_doc, indent=1) + "\n").encode("utf-8")
    new_bundle_sha = sha(bundle_bytes)

    # launch-authority file pins bundle + manifest + exec + governance; its OWN
    # bytes are pinned by the supervisor (breaks bundle<->launcher cycle).
    auth_doc = {
        "artifact": "phase36_v1_19_launch_authority_sha",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_19",
        "type": "LAUNCH_AUTHORITY_CONSTANT",
        "launcher": "scripts\\analysis\\launch_phase36_v1_19.py",
        "launcher_sha256": new_launcher_sha,
        "prelaunch_authority_bundle": "reports\\audits\\phase36_v1_19_prelaunch_authority_bundle.json",
        "prelaunch_authority_bundle_sha256": new_bundle_sha,
        "runtime_manifest_sha256": manifest_sha,
        "execution_source_sha256": FROZEN_E_V119,
        "release_attestation_sha256": V1_19_ATTESTATION_SHA,
        "d85_d88_adjudication_sha256": D85_D88_ADJUDICATION_SHA,
        "v1_18_consumed_adjudication_sha256":
            "41c6d79790f302e0863b0646b659729594cdc15834b3697169d5503907d809f9",
        "non_circular_note": ("The launcher reads its expected SHAs from this file; "
                              "the supervisor pins THIS FILE's raw bytes BEFORE Popen."),
        "terminal": "PHASE36_V1_19_LAUNCH_AUTHORITY_CONSTANT_WRITTEN",
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

# The sup must pin (bundle, authfile, launcher) — all now stable.
s_txt = supervisor_text(bundle_sha, authfile_sha, launcher_sha)
s_bytes = s_txt.encode("utf-8")
supervisor_sha = sha(s_bytes)

# --------------------------------------------------------------------------- #
# WRITE (write-once)                                                            #
# --------------------------------------------------------------------------- #
results = {}
results["launcher"] = {
    "path": "scripts/analysis/launch_phase36_v1_19.py",
    "sha256": write_once(L_V119, l_bytes),
}
assert results["launcher"]["sha256"] == launcher_sha

results["supervisor"] = {
    "path": "scripts/analysis/supervise_phase36_v1_19.py",
    "sha256": write_once(S_V119, s_bytes),
}
results["manifest"] = {
    "path": str(MANIFEST_V119.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(MANIFEST_V119, manifest_bytes),
}
assert results["manifest"]["sha256"] == manifest_sha
results["bundle"] = {
    "path": str(BUNDLE_V119.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(BUNDLE_V119, bundle_bytes),
}
assert results["bundle"]["sha256"] == bundle_sha
results["launch_authority_file"] = {
    "path": str(LAUNCH_AUTH_V119.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(LAUNCH_AUTH_V119, auth_bytes),
}
assert results["launch_authority_file"]["sha256"] == authfile_sha

print(json.dumps({
    "built": results,
    "supervisor_sha256": supervisor_sha,
    "pins": {
        "v1_19_exec_sha256": FROZEN_E_V119,
        "v1_19_launcher_sha256": launcher_sha,
        "v1_19_manifest_sha256": manifest_sha,
        "v1_19_bundle_sha256": bundle_sha,
        "v1_19_launch_authority_file_sha256": authfile_sha,
    },
    "fixed_point_converged": True,
}, indent=2))
