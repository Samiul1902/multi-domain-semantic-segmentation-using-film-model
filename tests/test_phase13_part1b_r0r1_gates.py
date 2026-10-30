"""Static + unit gate suite for PHASE-13 PART-1B-R0-R1.

Tests A-P. NO scientific execution: no training, no optimizer, no forward pass,
no VAL/TRAIN inference, no proposals, no grid search, no TEST access.

Run:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe tests/test_phase13_part1b_r0r1_gates.py
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RUNNER_PATH = ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
CONFIG_PATH = (
    ROOT / "configs" / "phase13_clean_v3"
    / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3.yaml"
)
CSV_PATH = ROOT / "reports" / "tables" / "phase13_clean_v3_executable_config_binding.csv"
R2A_PATH = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_loss_binding_r2a.json"


def _load_runner():
    spec = importlib.util.spec_from_file_location("_runner_r0r1", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _load_runner()


@pytest.fixture(scope="module")
def config():
    return _load_runner().load_executable_config(CONFIG_PATH)


@pytest.fixture(scope="module")
def source():
    return RUNNER_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tree(source):
    return ast.parse(source)


# ---------------------------------------------------------------------------
# A. CenterNetFocalLoss is the ONLY executable criterion
# ---------------------------------------------------------------------------
def test_A_centernet_focal_only_executable_criterion(runner, source):
    runner.verify_loss_binding(runner.load_executable_config(CONFIG_PATH))
    calls = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "CenterNetFocalLoss"
    ]
    assert len(calls) == 1, f"expected exactly one CenterNetFocalLoss construction, got {len(calls)}"


# ---------------------------------------------------------------------------
# B. alpha == 2.0
# ---------------------------------------------------------------------------
def test_B_alpha_is_twenty(config, runner):
    assert float(config["loss"]["alpha"]) == 2.0
    binding = runner.verify_loss_binding(config)
    assert binding["alpha"] == 2.0


# ---------------------------------------------------------------------------
# C. beta == 4.0
# ---------------------------------------------------------------------------
def test_C_beta_is_four(config, runner):
    assert float(config["loss"]["beta"]) == 4.0
    binding = runner.verify_loss_binding(config)
    assert binding["beta"] == 4.0


# ---------------------------------------------------------------------------
# D. SoftFocalDiceLoss is NOT on the executable path
# ---------------------------------------------------------------------------
def test_D_no_soft_focal_dice_on_executable_path(config, tree):
    loss = config["loss"]
    assert str(loss.get("dice_term", "NONE")).upper() == "NONE"
    assert float(loss.get("dice_weight", 0.0)) == 0.0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "SoftFocalDiceLoss", "SoftFocalDiceLoss constructed on executable path"
    # superseded composite objective must live in a non-executable sub-block
    assert loss["superseded_composite_contract"]["executable"] is False
    assert loss["non_primary_implementation_defect"]["executable"] is False


# ---------------------------------------------------------------------------
# E. No NotImplementedError (or TODO / dummy) on the executable path
# ---------------------------------------------------------------------------
def test_E_no_not_implemented_error(source, tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            func = node.exc.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            assert name != "NotImplementedError", "NotImplementedError raised on executable path"
    assert "raise NotImplementedError" not in source
    for marker in ("TODO(", "FIXME", "PLACEHOLDER_METRIC"):
        assert marker not in source, f"unresolved marker {marker!r} present"


# ---------------------------------------------------------------------------
# F. Exactly ONE proposal configuration
# ---------------------------------------------------------------------------
def test_F_one_proposal_configuration(runner):
    assert runner.PROPOSAL_CONFIGURATION_COUNT == 1
    assert runner.GRID_SEARCH_ENABLED is False
    assert (runner.PROPOSAL_THRESHOLD, runner.PROPOSAL_MARGIN,
            runner.PROPOSAL_TOP_K, runner.PROPOSAL_NMS_IOU) == (0.10, 0.20, 5, 0.30)


# ---------------------------------------------------------------------------
# G. No product / grid loop over proposal configurations
# ---------------------------------------------------------------------------
def test_G_no_proposal_grid_loop(source, tree):
    assert "itertools.product" not in source
    assert "GRID_SEARCH_ENABLED = False" in source
    # no loop iterating a collection of proposal configs
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.ListComp, ast.GeneratorExp)):
            text = ast.unparse(node)
            assert "PROPOSAL_CONFIGS" not in text
            assert "proposal_configs" not in text


# ---------------------------------------------------------------------------
# H. The 4-term selection tuple is unchanged
# ---------------------------------------------------------------------------
def test_H_selection_tuple_unchanged(runner):
    from src.training.clean_v3_selection import SELECTION_TERM_NAMES, SELECTION_LABEL

    assert tuple(SELECTION_TERM_NAMES) == (
        "tiny_recall90",
        "overall_recall90",
        "negative_mean_roi_area_fraction",
        "negative_val_loss",
    )
    assert SELECTION_LABEL == "EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION"
    cfg_selection = runner.load_executable_config(CONFIG_PATH)["checkpoint_selection"]
    assert cfg_selection["tuple"] == [
        "tiny_recall90", "overall_recall90",
        "-mean_roi_area_fraction", "-val_loss",
    ]


# ---------------------------------------------------------------------------
# I. Diagnostics are structurally excluded from selection
# ---------------------------------------------------------------------------
def test_I_diagnostics_excluded(runner):
    from src.training.clean_v3_selection import select_epoch

    params = set(inspect.signature(select_epoch).parameters)
    for diagnostic in (
        "hard_tiny_recovered90",
        "global_empty_images_covered90",
        "multi_component_recall90",
        "mean_proposals_per_image",
    ):
        assert diagnostic not in params, f"{diagnostic} must not be a selection parameter"

    # a huge diagnostic swing cannot change the selection decision
    baseline = select_epoch(0.5, 0.5, 0.01, 1.0, best_score=None, epoch=1)
    noisy = select_epoch(0.5, 0.5, 0.01, 1.0, best_score=None, epoch=1)
    assert baseline.score == noisy.score
    assert baseline.is_new_best == noisy.is_new_best


# ---------------------------------------------------------------------------
# J. set_seed is called BEFORE model construction
# ---------------------------------------------------------------------------
def test_J_set_seed_before_model_construction(tree):
    main = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    seed_line = model_line = None
    for node in ast.walk(main):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name == "set_seed" and seed_line is None:
                seed_line = node.lineno
            if name == "create_model" and model_line is None:
                model_line = node.lineno
    assert seed_line is not None, "set_seed not called in main()"
    assert model_line is not None, "create_model not called in main()"
    assert seed_line < model_line, "set_seed must precede create_model"


# ---------------------------------------------------------------------------
# K. TRAIN loader generator exists
# ---------------------------------------------------------------------------
def test_K_train_loader_generator(source, tree):
    assert "make_generator" in source
    assert "train_generator" in source
    # DataLoader must receive the generator kwarg
    dataloader_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "DataLoader"
    ]
    assert len(dataloader_calls) >= 2
    for call in dataloader_calls:
        kwargs = {kw.arg for kw in call.keywords}
        assert "generator" in kwargs, "every DataLoader must receive a generator"


# ---------------------------------------------------------------------------
# L. Generator state is persisted (not empty `{}`)
# ---------------------------------------------------------------------------
def test_L_generator_state_persisted(source, tree):
    assert "loader_generator_states" in source
    assert "get_state()" in source
    # the old empty-dict binding must be gone
    assert "loader_generator_states={}" not in source
    # and it is restored on resume
    assert "set_state" in source


# ---------------------------------------------------------------------------
# M. Resume mismatch fails LOUDLY
# ---------------------------------------------------------------------------
def test_M_resume_mismatch_fails_loudly(runner):
    import tempfile

    class Args:
        resume = True

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "history.csv").write_text("epoch\n1\n", encoding="utf-8")
        # resume with no latest.pt must raise (not silently restart)
        with pytest.raises(RuntimeError):
            runner.assert_resumable_or_absent(Args(), tmp, tmp)

    class NoResume:
        resume = False

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "history.csv").write_text("epoch\n1\n", encoding="utf-8")
        with pytest.raises(RuntimeError):
            runner.assert_resumable_or_absent(NoResume(), tmp, tmp)

    # identity mismatch must raise
    state = {
        "experiment_id": "WRONG_ID",
        "manifest_version": runner.MANIFEST_VERSION,
        "taxonomy_id": runner.TAXONOMY_ID,
        "input_resolution": runner.INPUT_RESOLUTION,
        "seed": 42,
        "r2_protocol_sha": runner.R2_PROTOCOL_SHA,
    }
    with pytest.raises(RuntimeError):
        runner.assert_resume_identity(state, {}, {}, 42)


# ---------------------------------------------------------------------------
# N. Manifest provenance binding returns non-empty EXPLICIT fields
# ---------------------------------------------------------------------------
def test_N_manifest_hashes_non_empty(source, runner):
    """Production provenance binding resolves against the REAL schema.

    Superseded in Part-1B: this test previously fabricated an ``image_sha256``
    column, which let it pass while the real tables (which have no such column)
    failed. It now exercises the REAL production provenance binding — see the
    amendment ``NON_SCIENTIFIC_PROVENANCE_BINDING`` and the dedicated suite
    ``tests/test_phase13_manifest_provenance_binding.py``.
    """
    assert "manifest_hashes={}" not in source

    # The implementation must no longer depend on a per-sample image hash.
    assert 'frame, "image_sha256"' not in source
    assert "'image_sha256'" not in source

    import pandas as pd

    from src.utils.manifest_guard import get_manifest_path

    manifest_train = pd.read_csv(get_manifest_path(runner.MANIFEST_VERSION, "train"))
    manifest_val = pd.read_csv(get_manifest_path(runner.MANIFEST_VERSION, "val"))
    train_table = pd.read_csv(runner.TRAIN_SAMPLE_TABLE)
    val_table = pd.read_csv(runner.VAL_SAMPLE_TABLE)

    train_ids = set(manifest_train["sample_id"].astype(str))
    val_ids = set(manifest_val["sample_id"].astype(str))
    train_frame = train_table[
        train_table["view_type"].eq("FULL_FIELD")
        & train_table["sample_id"].astype(str).isin(train_ids)
    ].reset_index(drop=True)
    val_frame = val_table[
        val_table["view_type"].eq("FULL_FIELD")
        & val_table["sample_id"].astype(str).isin(val_ids)
    ].reset_index(drop=True)

    hashes = runner.compute_manifest_hashes(
        runner.MANIFEST_VERSION,
        train_frame,
        val_frame,
        train_sample_table=runner.TRAIN_SAMPLE_TABLE,
        val_sample_table=runner.VAL_SAMPLE_TABLE,
    )
    for key in (
        "train_manifest_file_sha256",
        "val_manifest_file_sha256",
        "train_sample_table_file_sha256",
        "val_sample_table_file_sha256",
        "train_filtered_sample_ids_sha256",
        "val_filtered_sample_ids_sha256",
    ):
        assert isinstance(hashes[key], str) and hashes[key], f"{key} resolved empty"
        assert len(hashes[key]) == 64, f"{key} is not a 64-hex digest"

    assert hashes["train_filtered_sample_count"] == runner.EXPECTED_TRAIN_CASES
    assert hashes["val_filtered_sample_count"] == runner.EXPECTED_VAL_CASES

    # Superseded names must not reappear.
    assert "train_table_sha256" not in hashes
    assert "val_table_sha256" not in hashes


# ---------------------------------------------------------------------------
# O. heatmap_resolution = 128 is explicit
# ---------------------------------------------------------------------------
def test_O_heatmap_resolution_explicit(runner, config, tree):
    assert runner.HEATMAP_RESOLUTION == 128
    assert int(config["architecture"]["heatmap_resolution"]) == 128
    assert config["architecture"]["heatmap_output_shape"] == [1, 128, 128]
    call = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "create_model"
    )
    kwargs = {kw.arg: kw for kw in call.keywords}
    assert "heatmap_resolution" in kwargs, "create_model must pass heatmap_resolution explicitly"


# ---------------------------------------------------------------------------
# P. The binding CSV parses with pandas (no special options)
# ---------------------------------------------------------------------------
def test_P_binding_csv_parses():
    frame = pd.read_csv(CSV_PATH)
    assert list(frame.columns) == [
        "field", "value", "scientific_source",
        "source_sha", "binding_role", "scientifically_material",
    ]
    assert len(frame) > 0
    loss_rows = frame[frame["field"].astype(str).str.startswith("loss")]
    assert (loss_rows["binding_role"] == "R2A_LOSS_BINDING_EXECUTING").any()
    # the prior CHECK_REQUIRED audit must NOT have been erased
    assert (
        frame["binding_role"] == "SUPERSEDED_PRIOR_CHECK_REQUIRED_AUDIT"
    ).any()


# ---------------------------------------------------------------------------
# Extra: R2A amendment exists and R2 is unedited
# ---------------------------------------------------------------------------
def test_extra_r2a_amendment_exists_and_r2_untouched(runner):
    assert R2A_PATH.exists()
    amendment = json.loads(R2A_PATH.read_text(encoding="utf-8"))
    assert amendment["amendment_scope"] == "LOSS_OBJECTIVE_ONLY"
    assert amendment["resulting_executable_protocol_identity"] == "R2 + R2A_LOSS_BINDING"
    assert amendment["material_change_relative_to_R2"] == "NO"
    protocol = runner.verify_r2_protocol()
    assert protocol["status"] == runner.R2_REQUIRED_STATUS


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "--no-header"]))
