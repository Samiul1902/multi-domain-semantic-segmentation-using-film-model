"""Architecture-drift guard for the frozen Phase-25 router and safety modules.

The canonical producers are top-level scripts that execute training on import, so
they cannot be imported.  ``src/models/barr/phase25_models.py`` is the single
reusable definition used by the FULL three-seed pipeline.

These tests extract the class *text* from the canonical scripts (the same way the
existing Phase-29/34/35 audit scripts do) and assert the two definitions are
identical.  Any drift on either side -- a changed width, a dropped LayerNorm, a
reordered activation, a different initialisation, a different normalisation rule
-- fails here.

The legacy scripts are never modified by these tests.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from src.models.barr import phase25_models as P

ROOT = Path(__file__).resolve().parents[1]
ROUTER_SCRIPT = ROOT / "scripts" / "analysis" / "train_phase25d_router.py"
SAFETY_SCRIPT = ROOT / "scripts" / "analysis" / "phase25f_execution_common.py"

pytestmark = pytest.mark.skipif(
    not (ROUTER_SCRIPT.exists() and SAFETY_SCRIPT.exists()),
    reason="canonical Phase-25 producers are not present",
)


# --------------------------------------------------------------------------- #
def _extract_class(path: Path, name: str, stop: str) -> str:
    """Return the source text of ``class <name>`` up to the ``stop`` marker."""
    text = path.read_text(encoding="utf-8")
    pattern = rf"class {name}\(nn\.Module\):.*?(?=\n{stop})"
    match = re.search(pattern, text, re.S)
    assert match is not None, f"could not extract {name} from {path.name}"
    return match.group(0)


def _canonical_router_class():
    src = _extract_class(ROUTER_SCRIPT, "BARRBenefitRouterV1", "def count_params")
    ns: dict = {"nn": nn, "torch": torch}
    exec(compile(src, str(ROUTER_SCRIPT), "exec"), ns)  # noqa: S102 - fixed repo source
    return ns["BARRBenefitRouterV1"], src


def _canonical_safety_class():
    text = SAFETY_SCRIPT.read_text(encoding="utf-8")
    src = _extract_class(SAFETY_SCRIPT, "BARRPostSafetyV1", "def count_params")
    # the class body references these two module-level constants
    feature_dim = int(re.search(r"^FEATURE_DIM = (\d+)", text, re.M).group(1))
    hidden = tuple(int(v) for v in
                   re.search(r"^HIDDEN = \((\d+), (\d+)\)", text, re.M).groups())
    ns: dict = {"nn": nn, "torch": torch, "np": np,
                "FEATURE_DIM": feature_dim, "HIDDEN": hidden}
    exec(compile(src, str(SAFETY_SCRIPT), "exec"), ns)  # noqa: S102 - fixed repo source
    return ns["BARRPostSafetyV1"], src


def _state_signature(model: nn.Module) -> list[tuple[str, tuple]]:
    return sorted((k, tuple(v.shape)) for k, v in model.state_dict().items())


# --------------------------------------------------------------------------- #
# B_phi
# --------------------------------------------------------------------------- #
def test_router_state_dict_matches_canonical_producer():
    canonical, _ = _canonical_router_class()
    assert _state_signature(P.BARRBenefitRouterV1()) == _state_signature(canonical())


def test_router_parameter_count_matches_canonical_producer():
    canonical, _ = _canonical_router_class()
    assert P.count_trainable_parameters(canonical()) == P.ROUTER_EXPECTED_PARAMETERS
    assert P.count_trainable_parameters(P.BARRBenefitRouterV1()) == P.ROUTER_EXPECTED_PARAMETERS


def test_router_forward_is_bit_identical_to_canonical_producer():
    canonical, _ = _canonical_router_class()
    torch.manual_seed(0)
    shared = P.BARRBenefitRouterV1().eval()
    legacy = canonical().eval()
    legacy.load_state_dict(shared.state_dict())

    x = torch.randn(17, P.ROUTER_NUMERIC_DIM)
    t = torch.randint(0, P.ROUTER_TASK_COUNT, (17,))
    with torch.no_grad():
        a = shared(x, t)
        b = legacy(x, t)
    assert a.shape == b.shape == (17,)
    assert torch.equal(a, b), "router forward diverged from the frozen producer"


def test_router_initialisation_matches_canonical_producer():
    """Same seed must give the same initial weights, not merely the same shapes."""
    canonical, _ = _canonical_router_class()
    torch.manual_seed(1234)
    shared = P.BARRBenefitRouterV1()
    torch.manual_seed(1234)
    legacy = canonical()
    for key, value in shared.state_dict().items():
        assert torch.equal(value, legacy.state_dict()[key]), f"init drift at {key}"


# --------------------------------------------------------------------------- #
# S_omega
# --------------------------------------------------------------------------- #
def test_safety_state_dict_matches_canonical_producer():
    canonical, _ = _canonical_safety_class()
    assert _state_signature(P.BARRPostSafetyV1()) == _state_signature(canonical())


def test_safety_parameter_count_matches_canonical_producer():
    canonical, _ = _canonical_safety_class()
    assert P.count_trainable_parameters(canonical()) == P.SAFETY_EXPECTED_PARAMETERS
    assert P.count_trainable_parameters(P.BARRPostSafetyV1()) == P.SAFETY_EXPECTED_PARAMETERS


def test_safety_forward_is_bit_identical_to_canonical_producer():
    canonical, _ = _canonical_safety_class()
    torch.manual_seed(0)
    shared = P.BARRPostSafetyV1().eval()
    legacy = canonical().eval()
    legacy.load_state_dict(shared.state_dict())

    x = torch.randn(11, P.SAFETY_FEATURE_DIM)
    with torch.no_grad():
        a, b = shared(x), legacy(x)
    assert a.shape == b.shape == (11,)
    assert torch.equal(a, b), "safety forward diverged from the frozen producer"


def test_safety_initialisation_matches_canonical_producer():
    canonical, _ = _canonical_safety_class()
    torch.manual_seed(1234)
    shared = P.BARRPostSafetyV1()
    torch.manual_seed(1234)
    legacy = canonical()
    for key, value in shared.state_dict().items():
        assert torch.equal(value, legacy.state_dict()[key]), f"init drift at {key}"


def test_safety_returns_a_raw_logit_not_a_probability():
    """The sigmoid belongs to the caller's threshold rule, never the module."""
    model = P.BARRPostSafetyV1().eval()
    with torch.no_grad():
        out = model(torch.randn(64, P.SAFETY_FEATURE_DIM))
    assert out.shape == (64,)
    assert (out < 0).any() and (out > 0).any(), "output is not a raw logit"


# --------------------------------------------------------------------------- #
# normalisation semantics
# --------------------------------------------------------------------------- #
def test_safety_normalisation_matches_canonical_producer():
    """FIT-only statistics, ddof=0, zero-sigma rule, one-hot left raw."""
    from src.research.full_pipeline.stages import safety_stage as S

    canonical, _ = _canonical_safety_class()
    text = SAFETY_SCRIPT.read_text(encoding="utf-8")
    numeric_idx = list(range(0, int(re.search(r"^FEATURE_DIM = (\d+)", text, re.M).group(1)) - 4))
    ns: dict = {"np": np, "NUMERIC_IDX": numeric_idx,
                "ONEHOT_IDX": list(range(len(numeric_idx), len(numeric_idx) + 4))}
    for fn in ("def fit_normalization", "def apply_normalization"):
        m = re.search(rf"{fn}\(.*?(?=\n\ndef |\n\n# ---)", text, re.S)
        assert m is not None, f"could not extract {fn}"
        exec(compile(m.group(0), str(SAFETY_SCRIPT), "exec"), ns)  # noqa: S102

    rng = np.random.default_rng(0)
    feats = rng.normal(size=(50, P.SAFETY_FEATURE_DIM)).astype(np.float32)
    feats[:, 3] = 3.0   # constant numeric column -> must be zeroed by the zero-sigma rule
    feats[:, 18] = 7.0  # one-hot column -> must stay raw

    mu_c, sig_c, const_c = ns["fit_normalization"](feats)
    mu_s, sig_s, const_s = S.fit_normalization(feats)
    assert np.allclose(mu_c, mu_s) and np.allclose(sig_c, sig_s)
    assert np.array_equal(const_c, const_s)

    out_c = ns["apply_normalization"](feats, mu_c, sig_c, const_c)
    out_s = S.apply_normalization(feats, mu_s, sig_s, const_s)
    assert np.allclose(out_c, out_s, atol=0, rtol=0), "normalisation drifted"
    assert np.all(out_s[:, 3] == 0.0), "constant numeric column was not zeroed"
    assert np.all(out_s[:, 18] == 7.0), "one-hot column was standardised"


# --------------------------------------------------------------------------- #
# the pipeline must not carry a second copy
# --------------------------------------------------------------------------- #
def test_stages_import_the_shared_definition():
    from src.research.full_pipeline.stages import router_stage, safety_stage

    assert router_stage.BARRBenefitRouterV1 is P.BARRBenefitRouterV1
    assert safety_stage.BARRPostSafetyV1 is P.BARRPostSafetyV1


def test_recipe_constants_agree_with_shared_module():
    from src.research.full_pipeline import recipe as R

    assert R.B_TOTAL_DIM == P.ROUTER_TOTAL_DIM
    assert tuple(R.B_HIDDEN) == tuple(P.ROUTER_HIDDEN)
    assert R.B_DROPOUT == P.ROUTER_DROPOUT
    assert R.B_EXPECTED_PARAMETERS == P.ROUTER_EXPECTED_PARAMETERS
    assert tuple(R.B_NORMALIZE_IDX) == tuple(P.ROUTER_SCALAR_NORMALIZE_IDX)

    assert R.S_FEATURE_DIM == P.SAFETY_FEATURE_DIM
    assert R.S_NUMERIC_DIM == P.SAFETY_NUMERIC_DIM
    assert R.S_ONEHOT_DIM == P.SAFETY_ONEHOT_DIM
    assert tuple(R.S_HIDDEN) == tuple(P.SAFETY_HIDDEN)
    assert R.S_EXPECTED_PARAMETERS == P.SAFETY_EXPECTED_PARAMETERS
