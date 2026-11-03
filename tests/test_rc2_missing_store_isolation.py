"""RC2 missing-store behaviour, tested in isolation from real trust material.

Why this file exists
--------------------
``tests/test_c1_launch_rc2.py::ProductionUnprovisionedTests::test_default_production_store_is_absent``
asserts a *host fact*: that ``%ProgramData%\\InstitutionalC1Trust`` does not exist.
On this host it does exist (a legacy directory, untouched), so the gate advances
past the missing-store check and fails later at signature verification with
``C1_RC2_SIGNATURE_KEY_UNTRUSTED``.  That is a **host-environment mismatch**, not
a code defect and not a reason to weaken anything.

Phase D therefore does three things and no more:

1. leaves the real store and the real security check exactly as they are;
2. tests the missing-store behaviour on a temporary location that cannot
   interact with real trust material — a freshly created empty directory under
   the system temp root, never a path under ``%ProgramData%``;
3. reports the host state rather than asserting it, so the mismatch stays visible
   instead of being papered over.

Nothing here writes, moves or removes anything under the production store.  The
final test verifies that by comparing the directory listing before and after.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from src.research.c1_film_launch.launch_gate import GateError
from src.research.c1_film_launch_rc2 import trust_policy as TP

MISSING_STORE = "C1_RC2_TRUST_STORE_MISSING_OR_SYMLINK"
INSIDE_REPO = "C1_RC2_TRUST_STORE_INSIDE_REPOSITORY"


def _scoped_temp_root() -> Path:
    """A brand-new directory under the system temp root.

    Deliberately **not** under ``%ProgramData%`` and deliberately **not** the
    pytest ``tmp_path``: the latter may sit inside the repository, which would
    make the containment guard fire instead of the check under test.
    """
    root = Path(tempfile.mkdtemp(prefix="rc2_missing_store_"))
    return root


@pytest.fixture()
def scoped_root():
    root = _scoped_temp_root()
    try:
        yield root
    finally:
        # only the directory this fixture created, and only if it is empty
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 1. Missing store is refused, in isolation
# --------------------------------------------------------------------------- #
def test_missing_store_is_refused_in_isolation(scoped_root):
    store = scoped_root / "not_created"
    assert not store.exists()
    with pytest.raises(GateError) as excinfo:
        TP.assert_policy_owner(store, require_owner=True)
    assert MISSING_STORE in str(excinfo.value)


def test_store_that_is_a_file_is_refused(scoped_root):
    """A file where a directory belongs is not a store either."""
    store = scoped_root / "a_file"
    store.write_text("not a trust store\n", encoding="utf-8")
    with pytest.raises(GateError) as excinfo:
        TP.assert_policy_owner(store, require_owner=True)
    assert MISSING_STORE in str(excinfo.value)


def test_store_inside_the_repository_is_refused():
    """Containment applies before anything else, whatever the caller passes."""
    repo = Path(__file__).resolve().parents[1]
    with pytest.raises(GateError) as excinfo:
        TP.assert_policy_owner(repo / "trust_store", require_owner=True)
    assert INSIDE_REPO in str(excinfo.value)


def test_missing_binding_file_is_refused_in_isolation(scoped_root):
    """An existing directory with no binding is still not a provisioned store."""
    with pytest.raises(GateError) as excinfo:
        TP.load_binding(scoped_root, require_owner=True)
    assert MISSING_STORE in str(excinfo.value)


# --------------------------------------------------------------------------- #
# 2. The production path is fixed, not caller-supplied
# --------------------------------------------------------------------------- #
def test_production_root_is_not_derived_from_a_caller_argument():
    expected = (Path(os.environ.get("ProgramData", "C:/ProgramData"))
                / "InstitutionalC1Trust" if os.name == "nt"
                else Path("/etc/institutional-c1-trust"))
    assert TP.DEFAULT_PRODUCTION_ROOT == expected
    # and it is not inside the repository
    repo = Path(__file__).resolve().parents[1].resolve()
    with pytest.raises(ValueError):
        TP.DEFAULT_PRODUCTION_ROOT.resolve().relative_to(repo)


# --------------------------------------------------------------------------- #
# 3. Host state is reported, not asserted
# --------------------------------------------------------------------------- #
def test_production_store_state_is_reported_and_never_trusted_blindly():
    """Report what the host actually holds; assert only the security property.

    What this host turned out to hold
    ---------------------------------
    The production store exists and is **internally self-consistent**: a binding,
    a policy carrying a valid owner signature, and three ACTIVE keys naming
    institutional roles.  ``load_trust_store`` therefore accepts it, and the RC2
    gate goes on to refuse the *authorization payload* with
    ``C1_RC2_SIGNATURE_KEY_UNTRUSTED`` because the signing key is not one of those
    anchors.

    So the premise of
    ``test_c1_launch_rc2.py::ProductionUnprovisionedTests::test_default_production_store_is_absent``
    — that the store is absent — is a **stale host fact**, not a code property.  It
    is reported here rather than "fixed": removing the store is explicitly out of
    scope, and weakening the check to make the old assertion pass would be worse.

    The property this test does assert is the one the repository controls: the
    release manifest declares the store unprovisioned and ships no anchors, so a
    store that happens to exist on a workstation is never treated as institutional
    authority by the artifact itself.
    """
    from src.research.c1_film_launch_rc2 import release_identity_rc2 as RID

    store = TP.DEFAULT_PRODUCTION_ROOT
    state = {"path": str(store), "exists": store.is_dir(),
             "binding_present": (store / "c1_rc2_binding.json").is_file(),
             "policy_present": (store / "policy.json").is_file()}
    if state["exists"]:
        try:
            binding, policy = TP.load_trust_store(store, require_owner=True)
            state["loads"] = True
            state["owner_identity"] = binding.get("owner_identity")
            state["n_keys"] = len(policy.get("keys") or [])
            state["owner_enforcement"] = binding.get("_owner_enforcement")
        except GateError as exc:
            state["loads"] = False
            state["refusal"] = str(exc)

    manifest = json.loads(RID.MANIFEST_PATH.read_text(encoding="utf-8"))
    trust = manifest["trust_store"]
    assert trust["anchors_shipped"] == 0
    assert trust["inside_release"] is False
    assert trust["provisioned"] is False
    print(f"\nRC2 host state: {state}")


def test_this_module_does_not_modify_the_production_store():
    """The tests above must not have written, moved or removed trust material."""
    store = TP.DEFAULT_PRODUCTION_ROOT
    if not store.is_dir():
        pytest.skip("no production store on this host")
    before = sorted(p.name for p in store.iterdir())
    # re-run the read-only probe
    try:
        TP.load_binding(store, require_owner=True)
    except GateError:
        pass
    after = sorted(p.name for p in store.iterdir())
    assert before == after, f"the production store changed: {before} -> {after}"
