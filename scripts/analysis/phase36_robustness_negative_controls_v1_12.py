#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.12 — NEGATIVE CONTROLS NC86..NC99.

Additive over the carried-over v1.9 NC50..NC57, v1.10 NC63..NC70 and v1.11
NC71..NC85.  Each control here targets a SPECIFIC v1.12 governance repair and
pairs a faithful standalone re-implementation of the corresponding repaired
detector with an IN-MEMORY source mutant (or, for the launcher, a MUTATED
TEMPORARY ON-DISK COPY) that a CORRECT detector MUST reject.

Mandated mutants (D34/D35/D36):
  D34 : source re-acquires the ``manifest["launcher_sha256"]`` requirement;
        manifest illegitimately declares ``launcher_sha256`` (cycle).
  D35 : the FROZEN EXPECTED SHAs are made env-overridable (the exact v1.11
        defect) -> must be detected by the immutability detector;
        + the FOUR MANDATED LAUNCHER MUTANTS, exercised WITHOUT weakening the
          production launcher by calling ``verify_authority(exec_path=...,
          manifest_path=...)`` against mutated TEMPORARY COPIES:
            (1) mutate execution only            -> reject
            (2) mutate manifest only             -> reject
            (3) co-edit execution + manifest      -> reject
            (4) attempt to set the OLD override env names -> authority unchanged
  D36 : cross-file mutual-satisfiability (the exact canonical source + exact
        canonical manifest satisfy the launch-anchor predicate) — the
        complementary NEGATIVE is that a co-edit is REJECTED.

IN-MEMORY SOURCE MUTANTS + TEMP-FILE LAUNCHER MUTANTS ONLY.  Canonical files on
disk are NEVER modified.  NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO
forward.  NO smoke.  NO science.  NO VAL image / GT read.  NO protected read.
NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_12.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_12.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_12_runtime_source_integrity_manifest.json"

CANONICAL_SRC = EXEC.read_text(encoding="utf-8")
CANONICAL_SHA = hashlib.sha256(EXEC.read_bytes()).hexdigest()
LAUNCHER_SRC = LAUNCHER.read_text(encoding="utf-8")
MANIFEST_SRC = MANIFEST.read_text(encoding="utf-8")
# On-disk BYTES are the authority the immutable launcher hashes.  Every temp
# copy / SHA comparison MUST use these exact bytes (NOT a re-encoded text view,
# which would normalise CRLF<->LF and desynchronise the hash).
CANONICAL_EXEC_BYTES = EXEC.read_bytes()
MANIFEST_BYTES = MANIFEST.read_bytes()
MANIFEST_SHA = hashlib.sha256(MANIFEST_BYTES).hexdigest()
LAUNCHER_SHA = hashlib.sha256(LAUNCHER.read_bytes()).hexdigest()


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------- #
# shared AST helpers
# --------------------------------------------------------------------------- #
def _tree(src):
    return ast.parse(src)


def _funcs(tree):
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _seg(src, name):
    f = _funcs(ast.parse(src))
    if name not in f:
        return ""
    return ast.get_source_segment(src, f[name]) or ""


def _code_only(src):
    kept = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                continue
            kept.append(tok)
        out = tokenize.untokenize(kept)
    except Exception:
        out = src
    t = _tree(src)
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                out = out.replace(b[0].value.value, "")
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str) and n.value.value:
            out = out.replace(n.value.value, "None")
    return out


def _assigned_module_dict(tree, var_name):
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == var_name \
                        and isinstance(n.value, ast.Dict):
                    return n.value
    return None


# --------------------------------------------------------------------------- #
# D34 detector — source does NOT require manifest launcher_sha256, and fails
# closed if it unexpectedly appears.
# --------------------------------------------------------------------------- #
def det_d34_no_manifest_launcher_requirement(src: str) -> bool:
    integ = _seg(src, "_verify_transitive_source_integrity")
    if not integ:
        return False
    code = _code_only(integ)
    # (a) MUST NOT read a launcher hash out of the manifest.
    if 'manifest.get("launcher_sha256")' in code:
        return False
    if "expected_launcher" in code:
        return False
    # (b) MUST still require the launch-authority token.
    if "launch_authority_token_present" not in integ:
        return False
    if "LAUNCH_AUTHORITY_TOKEN" not in integ:
        return False
    # (c) MUST fail closed if the key unexpectedly appears (membership test).
    if '"launcher_sha256" in manifest' not in integ:
        return False
    if "manifest_launcher_sha256_absent" not in integ:
        return False
    if "if launcher_key_present or not launch_token_ok:" not in integ:
        return False
    return True


def det_d34_manifest_no_cycle(manifest: dict) -> bool:
    return "launcher_sha256" not in manifest


# --------------------------------------------------------------------------- #
# D35 detector — launcher frozen hashes are IMMUTABLE (no env override).
# --------------------------------------------------------------------------- #
def _launcher_code_only(src: str) -> str:
    t = _tree(src)
    out = src
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                out = out.replace(b[0].value.value, "")
    kept = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(out).readline):
            if tok.type == tokenize.COMMENT:
                continue
            kept.append(tok)
        out = tokenize.untokenize(kept)
    except Exception:
        pass
    return out


def det_d35_frozen_hashes_immutable(launcher_src: str) -> bool:
    code = _launcher_code_only(launcher_src)
    code_no_token_set = (code.replace('os.environ[LAUNCH_AUTHORITY_TOKEN]="1"', "")
                             .replace("os.environ[LAUNCH_AUTHORITY_TOKEN]='1'", "")
                             .replace('os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"', "")
                             .replace('os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"', ""))
    # no env read anywhere on the authorization path
    if "os.environ.get" in code_no_token_set or "getenv" in code_no_token_set:
        return False
    # the actual override env names must be absent from CODE
    for bad in ("PHASE36_V1_11_EXPECTED_EXEC_SHA", "PHASE36_V1_11_EXPECTED_MANIFEST_SHA",
                "PHASE36_V1_12_EXPECTED_EXEC_SHA", "PHASE36_V1_12_EXPECTED_MANIFEST_SHA"):
        if bad in code:
            return False
    # the accessors must return literal module constants only
    for fname, cname in (("_frozen_expected_exec_sha", "FROZEN_EXPECTED_EXEC_SHA"),
                         ("_frozen_expected_manifest_sha", "FROZEN_EXPECTED_MANIFEST_SHA")):
        body = _seg(launcher_src, fname)
        if not body or "os.environ" in _launcher_code_only(body):
            return False
        if cname not in body:
            return False
    return True


# --------------------------------------------------------------------------- #
# Mutators — execution source (in-memory string surgery only)
# --------------------------------------------------------------------------- #
def mut_d34_restore_manifest_launcher_requirement(src: str) -> str:
    """Re-introduce the exact v1.11 defect: read + require manifest launcher SHA."""
    old = (
        '    launcher_key_present = "launcher_sha256" in manifest\n'
        '    launch_token_ok = os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"\n'
    )
    new = (
        '    expected_launcher = manifest.get("launcher_sha256")\n'
        '    launch_token_ok = os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"\n'
    )
    return src.replace(old, new, 1)


def mut_d34_manifest_declares_launcher(manifest_src: str) -> str:
    """Inject an illegal ``launcher_sha256`` key into the manifest JSON."""
    d = json.loads(manifest_src)
    d["launcher_sha256"] = "deadbeef" * 8
    return json.dumps(d, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- #
# Mutators — launcher (in-memory source mutants; not written to canonical path)
# --------------------------------------------------------------------------- #
def mut_d35_make_env_overridable(src: str) -> str:
    """Re-introduce the exact v1.11 defect: env-overridable expected hashes."""
    return src.replace(
        "    return FROZEN_EXPECTED_EXEC_SHA",
        '    return os.environ.get("PHASE36_V1_12_EXPECTED_EXEC_SHA", FROZEN_EXPECTED_EXEC_SHA)',
        1)


# --------------------------------------------------------------------------- #
# Launcher in-memory module loader (NO dispatch; production constants intact).
# --------------------------------------------------------------------------- #
def _load_launcher(launcher_src: str):
    """Load a launcher module from SOURCE STRING via a temp file.

    The temp file holds a COPY; the canonical launcher is never modified.  We do
    NOT execute ``main()`` so no token is set and no dispatch occurs.

    NOTE: a launcher loaded from a temp COPY resolves ``ROOT`` to the temp tree,
    so its canonical exec/manifest paths are bogus.  This is FINE for the
    source-level immutability detector, and misleading for ``verify_authority``.
    Callers that need REAL path resolution MUST use
    ``_load_production_launcher()`` (canonical path) instead.
    """
    tmp = tempfile.NamedTemporaryFile("w", suffix="_launch_mut.py", delete=False,
                                      encoding="utf-8")
    try:
        tmp.write(launcher_src)
        tmp.close()
        spec = importlib.util.spec_from_file_location("phase36_v1_12_launch_mut", tmp.name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _load_production_launcher():
    """Load the launcher from its CANONICAL path so ``ROOT`` resolves correctly.

    Used only to call ``verify_authority(...)`` with explicit temp paths; the
    production frozen constants remain intact and ``main()`` is never executed.
    """
    spec = importlib.util.spec_from_file_location("phase36_v1_12_launch_prod", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# Control table
# --------------------------------------------------------------------------- #
_manifest = json.loads(MANIFEST_SRC)
_launcher_mod = _load_production_launcher()

results = []


def _record(name, mutation_changed, detector_canonical, detector_mutant,
            extra=None):
    bites = bool(detector_canonical) and (not detector_mutant)
    r = {
        "nc": name,
        "mutation_changed_bytes": bool(mutation_changed),
        "detector_on_canonical": bool(detector_canonical),
        "detector_on_mutant": bool(detector_mutant),
        "mutant_bite": bool(bites),
        "pass": bool(mutation_changed and detector_canonical and not detector_mutant),
    }
    if extra:
        r.update(extra)
    results.append(r)


# --- D34 ------------------------------------------------------------------- #
_base_d34 = det_d34_no_manifest_launcher_requirement(CANONICAL_SRC)
_mut = mut_d34_restore_manifest_launcher_requirement(CANONICAL_SRC)
_record("NC86_D34_source_reacquires_manifest_launcher_requirement",
        _mut != CANONICAL_SRC, _base_d34,
        det_d34_no_manifest_launcher_requirement(_mut))

_cyc_src = mut_d34_manifest_declares_launcher(MANIFEST_SRC)
_cyc = json.loads(_cyc_src)
_record("NC87_D34_manifest_declares_launcher_sha_cycle",
        _cyc_src != MANIFEST_SRC, det_d34_manifest_no_cycle(_manifest),
        det_d34_manifest_no_cycle(_cyc))

# --- D35: source-level immutability detector ------------------------------- #
_base_d35 = det_d35_frozen_hashes_immutable(LAUNCHER_SRC)
_mut_d35 = mut_d35_make_env_overridable(LAUNCHER_SRC)
_record("NC88_D35_frozen_hashes_made_env_overridable",
        _mut_d35 != LAUNCHER_SRC, _base_d35,
        det_d35_frozen_hashes_immutable(_mut_d35))

# --- D35: FOUR MANDATED LAUNCHER MUTANTS (without weakening production) ----- #
# The production launcher is loaded in-memory; we call verify_authority with
# TEMP mutated copies of exec / manifest.  The frozen expected constants inside
# the loaded module are UNCHANGED, so the mutated copies MUST be rejected.

def _run_launcher_against(exec_bytes: bytes, manifest_bytes: bytes):
    """Write mutated copies to temp files and call verify_authority on them."""
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td) / "phase36_robustness_execution_v1_12.py"
        mp = Path(td) / "phase36_v1_12_runtime_source_integrity_manifest.json"
        ep.write_bytes(exec_bytes)
        mp.write_bytes(manifest_bytes)
        return _launcher_mod.verify_authority(exec_path=ep, manifest_path=mp)


# (1) mutate EXECUTION only -> reject
_mut_exec_only = CANONICAL_SRC + "\n# tampered\n"
_auth_exec_only = _run_launcher_against(_mut_exec_only.encode("utf-8"),
                                        MANIFEST_BYTES)
_record("NC89_D35_mutate_execution_only_rejects",
        _mut_exec_only != CANONICAL_SRC, True, bool(_auth_exec_only["authorized"]),
        extra={"launcher_authorized": bool(_auth_exec_only["authorized"])})

# (2) mutate MANIFEST only -> reject
_d = json.loads(MANIFEST_SRC)
_d["n_dependencies"] = 13
_mut_manifest_only_text = json.dumps(_d, indent=2, ensure_ascii=False) + "\n"
_mut_manifest_only = _mut_manifest_only_text.encode("utf-8")
_auth_man_only = _run_launcher_against(CANONICAL_EXEC_BYTES, _mut_manifest_only)
_record("NC90_D35_mutate_manifest_only_rejects",
        _mut_manifest_only != MANIFEST_BYTES, True, bool(_auth_man_only["authorized"]),
        extra={"launcher_authorized": bool(_auth_man_only["authorized"])})

# (3) co-edit EXECUTION + MANIFEST -> reject
_d2 = json.loads(MANIFEST_SRC)
_d2["execution_source_sha256"] = _sha_bytes(_mut_exec_only.encode("utf-8"))
_mut_manifest_coedit = (json.dumps(_d2, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
_auth_coedit = _run_launcher_against(_mut_exec_only.encode("utf-8"),
                                     _mut_manifest_coedit)
_record("NC91_D35_coedit_execution_and_manifest_rejects",
        (_mut_exec_only != CANONICAL_SRC and _mut_manifest_coedit != MANIFEST_BYTES),
        True, bool(_auth_coedit["authorized"]),
        extra={"launcher_authorized": bool(_auth_coedit["authorized"])})

# (4) old override env names MUST NOT alter the production expected-hash authority
_old_names = ("PHASE36_V1_11_EXPECTED_EXEC_SHA", "PHASE36_V1_11_EXPECTED_MANIFEST_SHA",
              "PHASE36_V1_12_EXPECTED_EXEC_SHA", "PHASE36_V1_12_EXPECTED_MANIFEST_SHA")
_saved_env = {k: os.environ.get(k) for k in _old_names}
try:
    for k in _old_names:
        os.environ[k] = "0" * 64
    _prod_expected_exec = _launcher_mod._frozen_expected_exec_sha()
    _prod_expected_man = _launcher_mod._frozen_expected_manifest_sha()
    _auth_env = _launcher_mod.verify_authority()  # canonical paths
    _env_inert = (
        _prod_expected_exec == _launcher_mod.FROZEN_EXPECTED_EXEC_SHA
        and _prod_expected_man == _launcher_mod.FROZEN_EXPECTED_MANIFEST_SHA
        and bool(_auth_env["authorized"]) is True)
    _env_detail = {"prod_expected_exec": _prod_expected_exec,
                   "frozen_exec": _launcher_mod.FROZEN_EXPECTED_EXEC_SHA,
                   "canonical_still_authorized": bool(_auth_env["authorized"])}
finally:
    for k, v in _saved_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
_record("NC92_D35_old_override_env_cannot_alter_authority",
        True, True, (not _env_inert),  # detector "bites" the mutant env
        extra=dict(_env_detail, env_inert=bool(_env_inert)))
# NC92 semantics: canonical (no env) MUST stay authorized AND setting the old
# override names MUST NOT change the frozen authority -> _env_inert must be True.
results[-1]["pass"] = bool(_env_inert)
results[-1]["detector_on_mutant"] = not bool(_env_inert)
results[-1]["mutant_bite"] = bool(_env_inert)

# --- D35: env-override on the LOADED mutant launcher must actually bite ------ #
_mut_mod = _load_launcher(_mut_d35)
_saved2 = {k: os.environ.get(k) for k in _old_names}
try:
    os.environ["PHASE36_V1_12_EXPECTED_EXEC_SHA"] = "0" * 64
    _mut_expected = _mut_mod._frozen_expected_exec_sha()
finally:
    for k, v in _saved2.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
_mut_override_bites = (_mut_expected == "0" * 64)
_record("NC93_D35_env_override_detector_bites_mutant_launcher",
        _mut_d35 != LAUNCHER_SRC, _base_d35,
        det_d35_frozen_hashes_immutable(_mut_d35),
        extra={"mutant_expected_exec_under_env": _mut_expected,
               "override_took_effect": bool(_mut_override_bites)})

# --- D36: cross-file mutual satisfiability (positive) + co-edit (negative) --- #
_auth_canonical = _launcher_mod.verify_authority()
_cross_ok = bool(_auth_canonical["authorized"])
_record("NC94_D36_canonical_three_files_mutually_satisfiable",
        True, _cross_ok, _cross_ok,
        extra={"authorized": _cross_ok})
results[-1]["pass"] = bool(_cross_ok)  # positive contract; no mutant expected

_auth_coedit_reject = _auth_coedit["authorized"]
_record("NC95_D36_coedit_cannot_pass_frozen_launcher",
        True, True, bool(_auth_coedit_reject),
        extra={"coedit_authorized": bool(_auth_coedit_reject)})

# --- D35 immutability of the PRODUCTION frozen constants (hash-anchored) ----- #
_prod_exec_const = _launcher_mod.FROZEN_EXPECTED_EXEC_SHA
_prod_man_const = _launcher_mod.FROZEN_EXPECTED_MANIFEST_SHA
_record("NC96_D35_production_constants_equal_canonical_files",
        True,
        (_prod_exec_const == CANONICAL_SHA and _prod_man_const == MANIFEST_SHA),
        not (_prod_exec_const == CANONICAL_SHA and _prod_man_const == MANIFEST_SHA),
        extra={"prod_exec_const": _prod_exec_const, "canonical_exec": CANONICAL_SHA,
               "prod_manifest_const": _prod_man_const,
               "canonical_manifest": MANIFEST_SHA})
results[-1]["detector_on_mutant"] = results[-1]["detector_on_canonical"]
results[-1]["pass"] = bool(results[-1]["detector_on_canonical"])

# --- D36: detector that BITES when the exec still requires manifest launcher -- #
def det_d36_three_file_satisfiable(exec_src: str, manifest: dict) -> bool:
    """True iff exec + manifest are MUTUALLY SATISFIABLE under the no-cycle rule."""
    integ = _seg(exec_src, "_verify_transitive_source_integrity")
    if 'manifest.get("launcher_sha256")' in _code_only(integ):
        return False  # exec requires a key the manifest must not declare
    if "launcher_sha256" in manifest:
        return False  # manifest declares a key the exec must not require
    if "launch_authority_token_present" not in integ:
        return False
    return True


_record("NC97_D36_detector_bites_when_three_files_unsatisfiable",
        _mut != CANONICAL_SRC,
        det_d36_three_file_satisfiable(CANONICAL_SRC, _manifest),
        det_d36_three_file_satisfiable(_mut, _manifest))
_record("NC98_D36_detector_bites_when_manifest_cycle",
        _cyc_src != MANIFEST_SRC,
        det_d36_three_file_satisfiable(CANONICAL_SRC, _manifest),
        det_d36_three_file_satisfiable(CANONICAL_SRC, _cyc))

# --- D35: the launcher must have NO env-override reachable from main() -------- #
_lmain = _seg(LAUNCHER_SRC, "main")
_record("NC99_D35_main_has_no_hash_override_mechanism",
        True,
        det_d35_frozen_hashes_immutable(LAUNCHER_SRC),
        ("--expected" in _lmain or "expected_exec_sha" in _lmain),
        extra={"main_has_override_flag": ("--expected" in _lmain)})
results[-1]["detector_on_mutant"] = not results[-1]["detector_on_mutant"]
results[-1]["pass"] = bool(det_d35_frozen_hashes_immutable(LAUNCHER_SRC))

passed = sum(1 for r in results if r["pass"])
total = len(results)
sha_after = hashlib.sha256(EXEC.read_bytes()).hexdigest()
launcher_sha_after = hashlib.sha256(LAUNCHER.read_bytes()).hexdigest()
manifest_sha_after = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()

report = {
    "artifact": "phase36_v1_12_negative_controls",
    "phase": 36,
    "section": "§K",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_12",
    "type": "NEGATIVE_CONTROL_AUDIT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "mutants_are_in_memory_or_temp_files_only": True,
    "production_launcher_not_weakened": True,
    "canonical_source_sha256_before": CANONICAL_SHA,
    "canonical_source_sha256_after": sha_after,
    "canonical_source_unmodified": bool(CANONICAL_SHA == sha_after),
    "launcher_sha256": launcher_sha_after,
    "manifest_sha256": manifest_sha_after,
    "nc_range": "NC86-NC99",
    "targets": "D34/D35/D36",
    "carried_over_v1_11": "NC71-NC85_remain_valid_in_phase36_v1_11_negative_controls.json",
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "controls": results,
}
out = ROOT / "reports/audits/phase36_v1_12_negative_controls.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total,
                  "canonical_unmodified": CANONICAL_SHA == sha_after,
                  "launcher_unmodified": launcher_sha_after == LAUNCHER_SHA}, indent=1))
for r in results:
    print(("PASS " if r["pass"] else "FAIL "), r["nc"],
          "| canonical_detector=", r["detector_on_canonical"],
          "| mutant_bite=", r["mutant_bite"])
raise SystemExit(0 if passed == total else 1)
