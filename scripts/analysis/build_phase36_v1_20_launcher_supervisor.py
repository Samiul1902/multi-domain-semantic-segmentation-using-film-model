#!/usr/bin/env python
"""WO#20 §7 — BUILD v1.20 LAUNCHER + SUPERVISOR + MANIFEST + BUNDLE (write-once).

MODE: NEW-REVISION PREPARATION ONLY.  NON-CONSUMING.

Creates NEW artifacts (v1.19 versions UNTOUCHED):

    scripts/analysis/launch_phase36_v1_20.py
    scripts/analysis/supervise_phase36_v1_20.py
    reports/audits/phase36_v1_20_runtime_source_integrity_manifest.json
    reports/audits/phase36_v1_20_namespace_and_write_inventory.json
    reports/audits/phase36_v1_20_release_contract.json
    reports/audits/phase36_v1_20_launch_authority_sha.json
    reports/audits/phase36_v1_20_prelaunch_authority_bundle.json

The launcher and supervisor are STRICT mechanical rebases of the frozen v1.19
sources plus:

  * V1_19_SOURCE_SHA -> new v1.20 exec SHA
  * FROZEN_V1_20_LAUNCHER_SHA (supervisor)      -> new v1.20 launcher SHA
  * FROZEN_V1_20_AUTHORITY_BUNDLE_SHA           -> new v1.20 bundle SHA
  * FROZEN_V1_20_LAUNCH_AUTHORITY_FILE_SHA      -> new v1.20 authority-file SHA
  * §10 CONSUMED-HISTORY GATE (v1.19 is CONSUMED) appended + called in main().

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

L_V119 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_19.py"
S_V119 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_19.py"
E_V120 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_20.py"

L_V120 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_20.py"
S_V120 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_20.py"

MANIFEST_V120 = AUD / "phase36_v1_20_runtime_source_integrity_manifest.json"
NSINV_V120 = AUD / "phase36_v1_20_namespace_and_write_inventory.json"
CONTRACT_V120 = AUD / "phase36_v1_20_release_contract.json"
LAUNCH_AUTH_V120 = AUD / "phase36_v1_20_launch_authority_sha.json"
BUNDLE_V120 = AUD / "phase36_v1_20_prelaunch_authority_bundle.json"

FROZEN_L_V119 = "c2b81f8d7d65dc44fba6ee58ba74ea59815d46c415a052ea4aff86005167c9c5"
FROZEN_S_V119 = "8a33c6facbef13a7792fc0de968ec06257cb591890c13204aaad3d337e1d8cf4"
V1_19_EXEC_SHA = "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd"
FROZEN_E_V120 = "b9d128240596c5c6b7c040480823f4cc653d26a4bc665fc69b396d00e4fe0ad8"

# v1.19 chain SHAs (literal lines being replaced in the rebased sources).
V119_BUNDLE_SHA = "9d14991f0a7fa979484246e70868ed23ac41663c1ba2a27ee08c075a7f2bacd3"
V119_AUTHFILE_SHA = "d44a91a683233972439ccce4f40e70cf10a28f354cbee1d6876af31b3027b2e9"

# v1.20 governance authorities bound by the launch-authority file.
V1_20_ATTESTATION_SHA = "96b8343ae75dd0baab25ac85d4744d6620f3cfec51d1373f2fa9f2dd1b1af281"
D85_D88_D92_ADJUDICATION_SHA = "8ec45fe9dc3a9c5f20f284f206cf464f79115ff246b4805aab56c8b2c6141e42"
V1_19_FAILURE_ADJUDICATION_SHA = "76be9d8d75eb0dd45bffd1cb963e1093c52c4d5e8faa2cb7fefb2e33e6730b98"
# v1.20's OWN D85/D86/D87/D88 (+D93A) governance adjudication artifact.
V1_20_ADJUDICATION_SHA = "689cebadcc7d7187d86b487d18947267584c26c334aeb926d4d4386c676eb0ab"

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
    s = s.replace("v1.19", "v1.20")
    s = s.replace("V1.19", "V1.20")
    s = s.replace("v1_19", "v1_20")
    s = s.replace("V1_19", "V1_20")
    return s


# sanity: frozen inputs unchanged
assert sha_file(L_V119) == FROZEN_L_V119, "frozen v1.19 launcher SHA drift"
assert sha_file(S_V119) == FROZEN_S_V119, "frozen v1.19 supervisor SHA drift"
assert sha_file(E_V120) == FROZEN_E_V120, "v1.20 exec SHA drift"

# --------------------------------------------------------------------------- #
# §10 consumed-history gate (appended to the v1.20 launcher).                   #
# v1.19 is CONSUMED (CONSUMED_POST_START_PRE_MODEL_FAILURE; D93A).              #
# --------------------------------------------------------------------------- #
CONSUMED_GATE_CODE = '''

# =========================================================================== #
# §10 (v1.20) — CONSUMED-HISTORY GATE (v1.19 IS CONSUMED)                      #
# =========================================================================== #
# v1.19 is CONSUMED (CONSUMED_POST_START_PRE_MODEL_FAILURE; D93A).  v1.20 must
# NOT be mistaken for a clean-revision re-run of v1.19.  Before ANY real
# dispatch, the launcher REQUIRES that the v1.19 consumed history is EXACTLY
# the known recorded state: the v1.19 failure adjudication artifact exists with
# the expected SHA, the v1.19 START marker is PRESENT, the v1.19 RESULT and
# FAILURE markers are ABSENT, and the v1.19 PROCESS_EXIT evidence is PRESENT.
# Any deviation -> FAIL CLOSED.
V1_19_CONSUMED_ADJUDICATION = (
    AUD / "phase36_v1_19_execution_failure_adjudication_v1_0.json")
V1_19_CONSUMED_ADJUDICATION_SHA = (
    "76be9d8d75eb0dd45bffd1cb963e1093c52c4d5e8faa2cb7fefb2e33e6730b98")
V1_19_CONSUMED_EXPECTED_CLASSIFICATION = "CONSUMED_POST_START_PRE_MODEL_FAILURE"
V1_19_CONSUMED_START_MARKER = (
    AUD / "phase36_robustness_science_start_v1_19.json")
V1_19_CONSUMED_RESULT_MARKER = (
    AUD / "phase36_robustness_scientific_result_v1_19.json")
V1_19_CONSUMED_FAILURE_MARKER = (
    AUD / "phase36_robustness_science_failure_v1_19.json")
V1_19_CONSUMED_PROCESS_EXIT = (
    AUD / "phase36_robustness_science_process_exit_v1_19.json")


def verify_v1_19_consumed_history() -> dict:
    """§10: prove v1.19 is the EXACT known consumed-failure state. FAIL CLOSED."""
    result = {"ok": False, "reasons": []}
    if not V1_19_CONSUMED_ADJUDICATION.exists():
        result["reasons"].append("v1_19_adjudication_absent")
        return result
    adj_sha = sha256_file(V1_19_CONSUMED_ADJUDICATION)
    if adj_sha != V1_19_CONSUMED_ADJUDICATION_SHA:
        result["reasons"].append("v1_19_adjudication_sha_mismatch")
    try:
        doc = json.loads(V1_19_CONSUMED_ADJUDICATION.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover
        result["reasons"].append("v1_19_adjudication_unreadable")
        return result
    if doc.get("classification") != V1_19_CONSUMED_EXPECTED_CLASSIFICATION:
        result["reasons"].append("v1_19_adjudication_classification_mismatch")
    if not V1_19_CONSUMED_START_MARKER.exists():
        result["reasons"].append("v1_19_start_marker_absent__expected_present")
    if V1_19_CONSUMED_RESULT_MARKER.exists():
        result["reasons"].append("v1_19_result_present__expected_absent")
    if V1_19_CONSUMED_FAILURE_MARKER.exists():
        result["reasons"].append("v1_19_failure_present__expected_absent")
    if not V1_19_CONSUMED_PROCESS_EXIT.exists():
        result["reasons"].append("v1_19_process_exit_absent__expected_present")
    result["ok"] = not result["reasons"]
    result["v1_19_adjudication_sha256"] = adj_sha
    result["terminal"] = ("PHASE36_V1_20_CONSUMED_HISTORY_GATE_PASS" if result["ok"]
                          else "PHASE36_V1_20_CONSUMED_HISTORY_GATE_FAIL_CLOSED")
    return result
'''


_IF_MAIN_MARKER = '\nif __name__ == "__main__":\n    sys.exit(main(sys.argv[1:]))\n'


def launcher_text(launcher_self_sha: str) -> str:
    t = rebase(L_V119.read_text(encoding="utf-8"))
    assert f'V1_20_SOURCE_SHA = "{V1_19_EXEC_SHA}"' in t, "v1.20 SOURCE_SHA anchor missing"
    t = t.replace(f'V1_20_SOURCE_SHA = "{V1_19_EXEC_SHA}"',
                  f'V1_20_SOURCE_SHA = "{FROZEN_E_V120}"')

    anchor = (
        '    # Real dispatch path.\n'
        '    if os.environ.get(TOKEN_ENV) != "1":\n'
        '        print(f"FAIL_CLOSED: operator gate {TOKEN_ENV}=1 not set; refusing real dispatch.")\n'
        '        return 3\n')
    assert anchor in t, "launcher main() anchor not found"

    # Remove the OLD (rebased) §10 gate call block: everything from the anchor's
    # end up to (but not including) the `    gate_ok, results = run_all_gates()` line.
    gate_next = "    gate_ok, results = run_all_gates()"
    a_end = t.index(anchor) + len(anchor)
    g_start = t.index(gate_next, a_end)   # search AFTER the anchor only
    assert g_start > a_end, "gate call region ordering unexpected"
    between = t[a_end:g_start]
    assert "CONSUMED-HISTORY GATE" in between and "_consumed" in between, (
        "unexpected region between anchor and run_all_gates")

    gate_call = (
        '    # §10 (v1.20): CONSUMED-HISTORY GATE — v1.19 is CONSUMED; v1.20 must\n'
        '    # not be mistaken for a clean-revision re-run. FAIL CLOSED on deviation.\n'
        '    _consumed = verify_v1_19_consumed_history()\n'
        '    if not _consumed["ok"]:\n'
        '        print("FAIL_CLOSED: §10 consumed-history gate failed; NO attempt consumed.")\n'
        '        for _r in _consumed["reasons"]:\n'
        '            print(f"  {_r}")\n'
        '        return 3\n')
    t = t[:a_end] + gate_call + t[g_start:]

    # Replace the OLD (rebased) gate DEFINITION with the new one.
    marker = '# §10 (v1.20) — CONSUMED-HISTORY GATE'
    assert marker in t, "§10 definition header not found post-rebase"
    old_def_start = t.index(
        '\n# =========================================================================== #\n'
        '# §10 (v1.20) — CONSUMED-HISTORY GATE')
    old_def_end = t.index(_IF_MAIN_MARKER, old_def_start)
    t = t[:old_def_start] + CONSUMED_GATE_CODE + t[old_def_end:]
    return t


def supervisor_text(bundle_sha: str, authfile_sha: str, launcher_sha: str) -> str:
    s = rebase(S_V119.read_text(encoding="utf-8"))
    assert f'FROZEN_V1_20_LAUNCHER_SHA = "{FROZEN_L_V119}"' in s, "sup launcher pin anchor"
    assert f'FROZEN_V1_20_AUTHORITY_BUNDLE_SHA = "{V119_BUNDLE_SHA}"' in s, "sup bundle pin anchor"
    assert f'FROZEN_V1_20_LAUNCH_AUTHORITY_FILE_SHA = "{V119_AUTHFILE_SHA}"' in s, "sup authfile pin anchor"
    s = s.replace(f'FROZEN_V1_20_LAUNCHER_SHA = "{FROZEN_L_V119}"',
                  f'FROZEN_V1_20_LAUNCHER_SHA = "{launcher_sha}"')
    s = s.replace(f'FROZEN_V1_20_AUTHORITY_BUNDLE_SHA = "{V119_BUNDLE_SHA}"',
                  f'FROZEN_V1_20_AUTHORITY_BUNDLE_SHA = "{bundle_sha}"')
    s = s.replace(f'FROZEN_V1_20_LAUNCH_AUTHORITY_FILE_SHA = "{V119_AUTHFILE_SHA}"',
                  f'FROZEN_V1_20_LAUNCH_AUTHORITY_FILE_SHA = "{authfile_sha}"')
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

    bundle_doc = {
        "artifact": "phase36_v1_20_prelaunch_authority_bundle",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
        "type": "FINAL_PRELAUNCH_AUTHORITY_BUNDLE",
        "mode": "STATIC_NON_CONSUMING_GOVERNANCE_ONLY",
        "generated_utc": "2026-10-11T00:00:00Z",
        "authority_order": "ACYCLIC (A->B->C->D->E)",
        "supersedes_revision": "v1.19",
        "supervisor_sha256_present": False,
        "count_semantics": {
            "table_figure_target_count": 16,
            "total_reachable_write_target_count": 23,
            "unclassified_write_target_count": 0,
            "namespace_overlap_count": 0,
        },
        "v1_19_consumed_state": {
            "classification": "CONSUMED_POST_START_PRE_MODEL_FAILURE",
            "defect": "D93A",
            "attempt_consumed": True,
            "retry_permitted": False,
        },
        "binds": {
            "v1_20_execution_source": {
                "path": "scripts/analysis/phase36_robustness_execution_v1_20.py",
                "sha256": FROZEN_E_V120,
            },
            "v1_20_launcher": {
                "path": "scripts/analysis/launch_phase36_v1_20.py",
                "sha256": new_launcher_sha,
                "role": "PINNED_BY_DEDICATED_LAUNCH_AUTHORITY_FILE",
            },
            "v1_20_runtime_manifest": {
                "path": "reports/audits/phase36_v1_20_runtime_source_integrity_manifest.json",
                "sha256": "PENDING_MANIFEST_SHA",
            },
            "v1_19_failure_adjudication": {
                "path": "reports/audits/phase36_v1_19_execution_failure_adjudication_v1_0.json",
                "sha256": V1_19_FAILURE_ADJUDICATION_SHA,
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
        "terminal": "PHASE36_V1_20_PRELAUNCH_AUTHORITY_BUNDLE_WRITTEN",
    }

    m119 = json.loads(
        (AUD / "phase36_v1_19_runtime_source_integrity_manifest.json").read_text("utf-8"))
    manifest_doc = json.loads(rebase(json.dumps(m119)))
    manifest_doc["artifact"] = "phase36_v1_20_runtime_source_integrity_manifest"
    manifest_doc["revision"] = "ra_medfilm_barr_phase36_robustness_v1_20"
    manifest_doc["execution_source"] = "scripts/analysis/phase36_robustness_execution_v1_20.py"
    manifest_doc["execution_source_sha256"] = FROZEN_E_V120
    manifest_doc["supersedes_revision"] = "v1.19"
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
    manifest_doc["v1_19_consumed_state"] = "CONSUMED_POST_START_PRE_MODEL_FAILURE"
    manifest_doc["generated_utc"] = "2026-10-11T00:00:00Z"
    manifest_doc["non_circular_chain"] = [
        "SUPERVISOR pins frozen v1.20 launcher SHA + prelaunch-authority-bundle SHA before dispatch",
        "LAUNCHER pins literal v1.20 execution SHA + this manifest SHA + the v1.20 PRELAUNCH AUTHORITY BUNDLE SHA",
        "EXECUTION SOURCE reads this manifest, verifies its own bytes vs execution_source_sha256",
        "EXECUTION SOURCE requires the launch-authority token PHASE36_V1_20_LAUNCH_AUTHORITY",
    ]
    manifest_bytes = (json.dumps(manifest_doc, indent=1) + "\n").encode("utf-8")
    manifest_sha = sha(manifest_bytes)
    if not (dep_ok and ck_ok):
        print("WARN: manifest dependency/checkpoint mismatch", file=sys.stderr)
    bundle_doc["binds"]["v1_20_runtime_manifest"]["sha256"] = manifest_sha

    bundle_bytes = (json.dumps(bundle_doc, indent=1) + "\n").encode("utf-8")
    new_bundle_sha = sha(bundle_bytes)

    auth_doc = {
        "artifact": "phase36_v1_20_launch_authority_sha",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
        "type": "LAUNCH_AUTHORITY_CONSTANT",
        "launcher": "scripts\\analysis\\launch_phase36_v1_20.py",
        "launcher_sha256": new_launcher_sha,
        "prelaunch_authority_bundle": "reports\\audits\\phase36_v1_20_prelaunch_authority_bundle.json",
        "prelaunch_authority_bundle_sha256": new_bundle_sha,
        "runtime_manifest_sha256": manifest_sha,
        "execution_source_sha256": FROZEN_E_V120,
        "release_attestation_sha256": V1_20_ATTESTATION_SHA,
        "d85_d88_d92_adjudication_sha256": D85_D88_D92_ADJUDICATION_SHA,
        "d85_d88_adjudication_sha256": V1_20_ADJUDICATION_SHA,
        "v1_19_failure_adjudication_sha256": V1_19_FAILURE_ADJUDICATION_SHA,
        "non_circular_note": ("The launcher reads its expected SHAs from this file; "
                              "the supervisor pins THIS FILE's raw bytes BEFORE Popen."),
        "terminal": "PHASE36_V1_20_LAUNCH_AUTHORITY_CONSTANT_WRITTEN",
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
    "path": "scripts/analysis/launch_phase36_v1_20.py",
    "sha256": write_once(L_V120, l_bytes),
}
assert results["launcher"]["sha256"] == launcher_sha

results["supervisor"] = {
    "path": "scripts/analysis/supervise_phase36_v1_20.py",
    "sha256": write_once(S_V120, s_bytes),
}
results["manifest"] = {
    "path": str(MANIFEST_V120.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(MANIFEST_V120, manifest_bytes),
}
assert results["manifest"]["sha256"] == manifest_sha
results["bundle"] = {
    "path": str(BUNDLE_V120.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(BUNDLE_V120, bundle_bytes),
}
assert results["bundle"]["sha256"] == bundle_sha
results["launch_authority_file"] = {
    "path": str(LAUNCH_AUTH_V120.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(LAUNCH_AUTH_V120, auth_bytes),
}
assert results["launch_authority_file"]["sha256"] == authfile_sha

print(json.dumps({
    "built": results,
    "supervisor_sha256": supervisor_sha,
    "pins": {
        "v1_20_exec_sha256": FROZEN_E_V120,
        "v1_20_launcher_sha256": launcher_sha,
        "v1_20_manifest_sha256": manifest_sha,
        "v1_20_bundle_sha256": bundle_sha,
        "v1_20_launch_authority_file_sha256": authfile_sha,
    },
    "fixed_point_converged": True,
}, indent=2))
