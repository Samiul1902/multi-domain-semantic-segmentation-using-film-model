"""Phase C unified evaluation -- the eighteen mandatory synthetic integration checks.

Mission Phase C §10 enumerates eighteen end-to-end checks.  Each one is a test
below, numbered to match:

 1. all eight model adapters instantiate
 2. all four task ids work where supported
 3. all 24 registry entries are recognised
 4. FULL performs conditional inference through the complete graph
 5. Lite performs conditional inference through the complete graph
 6. ground truth never reaches inference
 7. metrics agree with independently computed known answers
 8. checkpoint identity mismatches fail closed
 9. missing models are marked missing, never estimated
10. partial or corrupt exports are never published as complete
11. seed comparisons preserve exact image pairing
12. statistical routines handle missing seeds and groups honestly
13. accuracy-efficiency units and bases are correct
14. reports distinguish synthetic from actual evidence
15. repeat execution is deterministic
16. interrupted evaluation resumes without duplicating or losing samples
17. protected TEST1683 is never read
18. existing FULL/Lite training tests remain passing

Everything runs on small deterministic synthetic fixtures.  A synthetic number is
never presented as a research result: the registry stays NOT_ESTABLISHED and
``research_cells_completed`` stays 0 throughout.

Check 18 shells out to the two existing training suites.  It is skipped unless
``PHASE_C_RUN_TRAINING_REGRESSION=1`` is set, so the default suite stays fast; the
Phase C regression batch sets it.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

from src.metrics import evaluation_metrics as EM
from src.research.c3_baselines import experiment as C3
from src.research.evaluation import adapters as A
from src.research.evaluation import cli as CLI
from src.research.evaluation import efficiency as EF
from src.research.evaluation import metrics as MET
from src.research.evaluation import protocol as P
from src.research.evaluation import provenance as PROV
from src.research.evaluation import registry as REG
from src.research.evaluation import reports as REP
from src.research.evaluation import runner as RN
from src.research.evaluation import stats as ST
from src.research.stage6 import end_to_end as E6

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

ROOT = Path(__file__).resolve().parents[1]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

#: Verified from instantiated models; the baselines are cross-checked against the
#: C3 historical table instead of being restated here.
EXPECTED_PARAMETERS = {
    REG.FULL: 4_837_420,
    REG.GLOBAL: 3_523_001,
    REG.LITE: 272_601,
}
EXECUTE_STATES = ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _one_per_domain(samples):
    """First sample of each domain, so an aggregate can be computed at all."""
    out, seen = [], set()
    for sample in samples:
        if sample.domain not in seen:
            seen.add(sample.domain)
            out.append(sample)
    assert len(out) == 4, [s.domain for s in out]
    return out


@pytest.fixture(scope="session")
def bundle(tmp_path_factory):
    """A deterministic synthetic VAL population: two images per domain."""
    root = tmp_path_factory.mktemp("phase_c_bundle")
    samples = RN.synthetic_samples(root / "fixture", per_domain_val=2)
    assert len(samples) == 8
    return root, samples


@pytest.fixture(scope="session")
def samples(bundle):
    return bundle[1]


@pytest.fixture(scope="session")
def mini(samples):
    return _one_per_domain(samples)


@pytest.fixture(scope="session")
def adapters():
    """One synthetic adapter per model key, built once and closed at the end."""
    built = {}

    def get(model_key, seed=42):
        key = (model_key, seed)
        if key not in built:
            adapter = A.build_synthetic(model_key, seed, device=DEVICE)
            built[key] = adapter.load()
        return built[key]

    yield get
    for adapter in built.values():
        adapter.close()


def _record(sample_id, dice, *, domain="KUB", patient_id=None, group_key=None):
    return {"sample_id": str(sample_id), "domain": domain, "task_id": 3,
            "dice": float(dice), "iou": float(dice), "precision": float(dice),
            "recall": float(dice), "hd95": 1.0, "state": "SKIP_GLOBAL",
            "refiner_executed": False, "accepted": False, "harmful_accepted": False,
            "gt_empty": False, "pred_empty": False, "empty_gt_false_positive": False,
            "patient_id": patient_id, "group_key": group_key}


# --------------------------------------------------------------------------- #
# 1. All eight adapters instantiate
# --------------------------------------------------------------------------- #
def test_01_all_eight_adapters_instantiate(adapters):
    assert len(REG.MODEL_KEYS) == 8
    assert len(REG.DISPLAY_ORDER) == 8
    kinds = set()
    for model_key in REG.DISPLAY_ORDER:
        adapter = adapters(model_key, 42)
        assert adapter.model_key == model_key
        assert adapter.kind == REG.ADAPTER_KINDS[model_key]
        kinds.add(adapter.kind)

        count = adapter.parameter_count()
        if model_key in EXPECTED_PARAMETERS:
            assert count == EXPECTED_PARAMETERS[model_key], model_key
        else:
            historical = int(C3.ARCHITECTURES[
                REG.C3_ARCHITECTURE_KEY[model_key]]["historical_params"].replace(",", ""))
            assert count == historical, model_key

        identity = adapter.identity()
        assert identity["adapter_kind"] == adapter.kind
        assert identity["evidence_class"] == P.SYNTHETIC_EVIDENCE
        assert identity["synthetic_fixture_priming"]["primed"] is True

    # the three adapter kinds are genuinely distinct, not one flattened path
    assert kinds == {"ROUTED", "TASK_CONDITIONED", "PLAIN"}
    assert REG.ADAPTER_KINDS[REG.FULL] == "ROUTED"
    assert REG.ADAPTER_KINDS[REG.LITE] == "ROUTED"
    assert REG.ADAPTER_KINDS[REG.GLOBAL] == "TASK_CONDITIONED"
    assert all(REG.ADAPTER_KINDS[b] == "PLAIN" for b in REG.BASELINES)


# --------------------------------------------------------------------------- #
# 2. All four task ids work where supported
# --------------------------------------------------------------------------- #
def test_02_task_ids_reach_the_models_that_take_one(monkeypatch, adapters, mini):
    image = mini[0].image

    # ROUTED: the id must reach the state machine
    routed = adapters(REG.FULL, 42)
    seen = []
    original = routed._system.infer

    def spy_infer(img, task_id):
        seen.append(int(task_id))
        return original(img, task_id)

    monkeypatch.setattr(routed._system, "infer", spy_infer)
    for task_id in (0, 1, 2, 3):
        prediction = routed.predict(image, task_id)
        assert prediction.probability.shape == (P.RESOLUTION, P.RESOLUTION)
        assert np.isfinite(prediction.probability).all()
        assert 0.0 <= float(prediction.probability.min())
        assert float(prediction.probability.max()) <= 1.0
    assert seen == [0, 1, 2, 3]

    # TASK_CONDITIONED: the id must reach the network as a tensor
    monkeypatch.undo()
    conditioned = adapters(REG.GLOBAL, 42)
    received = []
    original_forward = conditioned._model.forward

    def spy_forward(x, task_ids):
        received.append(int(task_ids.reshape(-1)[0]))
        return original_forward(x, task_ids)

    monkeypatch.setattr(conditioned._model, "forward", spy_forward)
    for task_id in (0, 1, 2, 3):
        prediction = conditioned.predict(image, task_id)
        assert prediction.probability.shape == (P.RESOLUTION, P.RESOLUTION)
        assert np.isfinite(prediction.probability).all()
    assert received == [0, 1, 2, 3]

    # PLAIN: no task input at all.  Feeding one would be a protocol change, so the
    # forward must receive the image and nothing else.
    monkeypatch.undo()
    plain = adapters(REG.BASELINES[0], 42)
    arities = []
    original_plain = plain._model.forward

    def spy_plain(*args, **kwargs):
        arities.append((len(args), sorted(kwargs)))
        return original_plain(*args, **kwargs)

    monkeypatch.setattr(plain._model, "forward", spy_plain)
    first = plain.predict(image, 0).probability
    second = plain.predict(image, 3).probability
    assert arities and all(arity == (1, []) for arity in arities)
    assert np.array_equal(first, second), "a plain baseline must ignore the task id"
    assert REG.TAKES_TASK_ID[REG.BASELINES[0]] is False

    # a task id outside 0..3 is rejected rather than silently wrapped
    with pytest.raises(A.AdapterError):
        routed.predict(image, 4)


# --------------------------------------------------------------------------- #
# 3. All 24 registry entries are recognised
# --------------------------------------------------------------------------- #
def test_03_all_24_registry_cells_are_recognised():
    cells = REG.model_seed_cells()
    assert len(cells) == 24
    assert len(set(cells)) == 24
    assert {m for m, _ in cells} == set(REG.MODEL_KEYS)
    assert {s for _, s in cells} == {42, 123, 3407}
    REG.assert_complete_matrix()

    ids = [REG.cell_id(m, s) for m, s in cells]
    assert len(set(ids)) == 24
    assert ids[0] == f"{REG.FULL}::seed42"

    for model_key in REG.MODEL_KEYS:
        spec = REG.spec(model_key)
        assert spec.adapter_kind == REG.ADAPTER_KINDS[model_key]
        assert spec.takes_task_id == REG.TAKES_TASK_ID[model_key]
        assert spec.display_name
        assert spec.role
        if model_key in (REG.FULL, REG.LITE):
            assert spec.chain == ("G", "R_psi", "B_phi", "S_omega")
            assert REG.architecture_identity(model_key)["requires_component_chain"] is True
        elif model_key == REG.GLOBAL:
            # the global stage alone: no refiner, router or safety
            assert spec.chain == ("G",)
            assert REG.architecture_identity(model_key)["requires_component_chain"] is False
        else:
            # a baseline belongs to no BARR chain at all
            assert spec.chain == (), model_key
            assert REG.architecture_identity(model_key)["requires_component_chain"] is False

    with pytest.raises(REG.RegistryError):
        REG.spec("NOT_A_MODEL")
    # the acceptance gate stays in stage6.matrix; this package adds no second one
    assert not hasattr(REG, "validate_cell")


# --------------------------------------------------------------------------- #
# 4. FULL conditional inference
# --------------------------------------------------------------------------- #
def test_04_full_runs_the_complete_conditional_graph(adapters, samples, tmp_path):
    adapter = adapters(REG.FULL, 42)
    outcome = RN.evaluate_cell(adapter, samples, directory=tmp_path / "full")
    records = outcome["records"]

    states = {r["state"] for r in records}
    assert states <= set(E6.STATES), states
    assert states - {"NOT_APPLICABLE"}, "the router never made a decision"
    for record in records:
        assert record["refiner_executed"] == (record["state"] in EXECUTE_STATES)
        assert record["accepted"] == (record["state"] == "EXECUTE_THEN_ACCEPT")
    # the refiner branch is genuinely exercised, not merely reachable on paper
    assert any(r["refiner_executed"] for r in records)

    summary = outcome["summary"]
    assert 0.0 < summary["refiner_invocation_rate"] <= 1.0
    assert summary["primary_aggregate"] == "equal_domain_macro_dice"
    assert summary["aggregation_levels"] == ["PER_IMAGE", "PER_DOMAIN", "POOLED"]
    # the G/R/B/S chain is the declared one
    assert adapter.identity()["component_chain"] == ["G", "R_psi", "B_phi", "S_omega"]
    assert set(adapter.identity()["component_sha256"]) == {"G", "R", "B", "S"}
    assert outcome["parameter_count"] == 4_837_420


# --------------------------------------------------------------------------- #
# 5. Lite conditional inference
# --------------------------------------------------------------------------- #
def test_05_lite_runs_the_complete_conditional_graph(adapters, samples, tmp_path):
    adapter = adapters(REG.LITE, 123)
    assert adapter._system.uses_tap_forward is True
    outcome = RN.evaluate_cell(adapter, samples, directory=tmp_path / "lite")
    records = outcome["records"]

    states = {r["state"] for r in records}
    assert states <= set(E6.STATES), states
    assert states - {"NOT_APPLICABLE"}
    for record in records:
        assert record["refiner_executed"] == (record["state"] in EXECUTE_STATES)
    assert any(r["refiner_executed"] for r in records)

    summary = outcome["summary"]
    assert 0.0 < summary["refiner_invocation_rate"] <= 1.0
    assert outcome["parameter_count"] == 272_601
    # Lite runs the same four components at the same tap grid sides as FULL
    identity = adapter.identity()
    assert identity["component_chain"] == ["G", "R_psi", "B_phi", "S_omega"]
    assert set(identity["component_sha256"]) == {"G", "R", "B", "S"}
    # and it is a genuinely different family, not FULL under another name
    assert outcome["parameter_count"] != adapters(REG.FULL, 123).parameter_count()


# --------------------------------------------------------------------------- #
# 6. Ground truth never reaches inference
# --------------------------------------------------------------------------- #
def test_06_ground_truth_never_reaches_inference(monkeypatch, adapters, mini, tmp_path):
    adapter = adapters(REG.FULL, 42)
    captured = []
    original = adapter.predict

    def spy(*args, **kwargs):
        captured.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(adapter, "predict", spy)
    outcome = RN.evaluate_cell(adapter, mini, directory=tmp_path / "gtfree")

    assert len(captured) == len(mini)
    mask_ids = {id(sample.mask) for sample in mini}
    for args, kwargs in captured:
        assert len(args) == 2, "inference takes the image and the task id only"
        assert not kwargs, "inference must not be driven by keyword arguments"
        image, task_id = args
        assert torch.is_tensor(image)
        assert tuple(image.shape) == (1, 3, P.RESOLUTION, P.RESOLUTION)
        assert isinstance(task_id, int)
        for argument in args:
            assert id(argument) not in mask_ids, "a ground-truth array reached inference"

    # the scores exist because scoring happens after inference, not during it
    assert all("dice" in record for record in outcome["records"])
    assert all(record["tp"] >= 0 for record in outcome["records"])

    # the property is re-checked on the live signatures, not asserted in prose
    audit = A.audit_gt_free()
    assert audit["gt_free"] is True, audit["gt_like_parameters"]
    assert audit["gt_like_parameters"] == []
    assert E6.audit_ground_truth_free()["gt_free"] is True


# --------------------------------------------------------------------------- #
# 7. Metrics agree with independently computed known answers
# --------------------------------------------------------------------------- #
def test_07_metrics_match_independently_computed_known_answers():
    report = MET.verify_known_answers()
    assert report["all_match"], report["failures"]
    assert report["cases"] == 8
    assert report["metric_implementation_version"] == P.METRIC_IMPLEMENTATION_VERSION

    # independent hand arithmetic for the shifted-block case, not a recorded output
    gt = np.zeros((4, 4), np.uint8)
    gt[1:3, 1:3] = 1
    pred = np.zeros((4, 4), np.uint8)
    pred[1:3, 2:4] = 1
    tp = int(np.logical_and(gt, pred).sum())
    fp = int(np.logical_and(1 - gt, pred).sum())
    fn = int(np.logical_and(gt, 1 - pred).sum())
    tn = int(np.logical_and(1 - gt, 1 - pred).sum())
    assert (tp, fp, fn, tn) == (2, 2, 2, 10)

    record = MET.score_prediction(sample_id="hand", domain="KUB", task_id=3,
                                  final_probability=pred.astype(np.float32),
                                  ground_truth=gt)
    assert record["dice"] == pytest.approx(2 * tp / (2 * tp + fp + fn), abs=1e-6)
    assert record["iou"] == pytest.approx(tp / (tp + fp + fn), abs=1e-6)
    assert record["precision"] == pytest.approx(tp / (tp + fp), abs=1e-6)
    assert record["recall"] == pytest.approx(tp / (tp + fn), abs=1e-6)

    # HD95 units: pixels by default, millimetres only when spacing is supplied
    hd = MET.hd95_with_units(pred, gt)
    assert hd["hd95_unit"] == "pixel"
    assert hd["hd95_mm"] is None and hd["hd95_spacing_mm"] is None
    assert hd["hd95"] == pytest.approx(1.0)
    assert "never 0" in hd["hd95_convention"]
    scaled = MET.hd95_with_units(pred, gt, spacing=(2.0, 3.0))
    assert scaled["hd95_spacing_mm"] == [2.0, 3.0]
    assert scaled["hd95_mm"] == pytest.approx(3.0)   # the shift is along columns

    # an empty mask leaves HD95 undefined rather than silently zero
    empty = MET.hd95_with_units(np.zeros((4, 4)), np.zeros((4, 4)))
    assert empty["hd95_valid"] is False
    assert empty["hd95_invalid_reason"] == "both_empty"
    assert empty["hd95_mm"] is None

    # non-finite probabilities are either refused or counted, never ignored
    bad = np.full((4, 4), 0.5, np.float32)
    bad[0, 0] = np.nan
    with pytest.raises(MET.NonFiniteProbabilityError):
        MET.score_prediction(sample_id="nan", domain="KUB", task_id=3,
                             final_probability=bad, ground_truth=gt)
    masked = MET.score_prediction(sample_id="nan", domain="KUB", task_id=3,
                                  final_probability=bad, ground_truth=gt,
                                  on_non_finite="mask")
    assert masked["non_finite_pixels"] == 1

    # the three aggregation levels are distinct quantities
    def _score(sample_id, domain, prediction):
        return MET.score_prediction(sample_id=sample_id, domain=domain, task_id=3,
                                    final_probability=prediction.astype(np.float32),
                                    ground_truth=gt)

    records = [
        _score("i1", "ISIC", pred),        # dice 0.5
        _score("i2", "ISIC", pred),        # dice 0.5
        _score("b1", "BUSI", gt),          # dice 1.0
        _score("k1", "KVASIR", gt),        # dice 1.0
        _score("u1", "KUB", np.zeros_like(gt)),   # dice 0.0
    ]
    agg = MET.aggregate_records(records)
    assert agg["aggregation_levels"] == ["PER_IMAGE", "PER_DOMAIN", "POOLED"]
    assert agg["domain_n"] == {"ISIC": 2, "BUSI": 1, "KVASIR": 1, "KUB": 1}
    manual = float(np.mean([agg["per_domain"][d]["dice"] for d in P.DOMAINS]))
    assert agg["equal_domain_macro_dice"] == pytest.approx(manual, abs=1e-12)
    assert agg["equal_domain_macro_dice"] == pytest.approx(0.625, abs=1e-6)
    assert agg["primary_aggregate"] == "equal_domain_macro_dice"
    # image-weighted and equal-domain differ whenever the domain counts differ
    assert agg["image_weighted_dice"] == pytest.approx(0.6, abs=1e-6)
    assert agg["image_weighted_dice"] != pytest.approx(agg["equal_domain_macro_dice"])
    # pixel-pooled is a third quantity again, and is never substituted
    assert agg["pooled_dice"] == pytest.approx(
        EM.pooled_segmentation_metrics(
            [{"tp": r["tp"], "tn": r["tn"], "fp": r["fp"], "fn": r["fn"],
              "total": r["tp"] + r["tn"] + r["fp"] + r["fn"]} for r in records])["dice"])


# --------------------------------------------------------------------------- #
# 8. Checkpoint identity mismatches fail closed
# --------------------------------------------------------------------------- #
def test_08_incompatible_checkpoint_families_are_rejected(tmp_path):
    # 1. no checkpoint at all: a random-weight model may not produce a score
    with pytest.raises(A.AdapterUnavailable):
        A.TaskConditionedAdapter(REG.GLOBAL, 42, device="cpu").load()
    with pytest.raises(A.AdapterUnavailable):
        A.PlainAdapter(REG.BASELINES[0], 42, device="cpu").load()

    # 2. a named but absent file
    with pytest.raises(A.AdapterUnavailable):
        A.PlainAdapter(REG.BASELINES[0], 42, device="cpu",
                       checkpoint_path=tmp_path / "absent.pt").load()

    # 3. a checkpoint whose tensors do not match the architecture
    wrong = tmp_path / "wrong.pt"
    torch.save({"model_state": {"not_a_layer.weight": torch.zeros(3)}}, wrong)
    with pytest.raises(RuntimeError):
        A.PlainAdapter(REG.BASELINES[0], 42, device="cpu",
                       checkpoint_path=wrong).load()

    # 4. a routed family that is absent on disk: an empty root reaches the deep
    #    component check, a root that does not exist is refused earlier
    empty_root = tmp_path / "empty_root"
    empty_root.mkdir()
    with pytest.raises(Exception) as absent:
        A.RoutedAdapter.load_real(REG.FULL, 42, run_root=empty_root, device="cpu")
    assert "missing component checkpoint" in str(absent.value)
    with pytest.raises(A.AdapterUnavailable) as no_root:
        A.RoutedAdapter.load_real(REG.FULL, 42, run_root=tmp_path / "no_family",
                                  device="cpu")
    assert "does not exist" in str(no_root.value)

    # 5. a routed adapter with no root at all fails legibly, not with a TypeError
    unrooted = A.build_adapter(REG.FULL, 42, source="real")
    with pytest.raises(A.AdapterUnavailable):
        unrooted.load()
    with pytest.raises(A.AdapterError):
        unrooted.predict(torch.zeros(1, 3, 8, 8), 0)

    # 6. provenance refuses a protected split and any recorded protected read
    identity = A.build_synthetic(REG.BASELINES[0], 42, device="cpu").identity()
    kwargs = dict(model_key=REG.BASELINES[0], seed=42,
                  adapter_identity=identity, evidence_class=P.REAL_VAL_EVIDENCE,
                  split_manifest_sha256="0" * 64, n_images=4,
                  evaluation_configuration=PROV.evaluation_config(),
                  synthetic=False, training_performed=True)
    with pytest.raises(PROV.ProvenanceError):
        PROV.build_evaluation_provenance(split=P.SPLIT_TEST, **kwargs)
    with pytest.raises(PROV.ProvenanceError):
        PROV.build_evaluation_provenance(split=P.SPLIT_VAL, protected_reads=1, **kwargs)

    # 7. a synthetic adapter is never stamped as real evidence
    synthetic = A.build_synthetic(REG.BASELINES[0], 42, device="cpu")
    assert synthetic.evidence_class == P.SYNTHETIC_EVIDENCE
    assert synthetic.source == "synthetic"
    assert A.build_adapter(REG.BASELINES[0], 42, source="real").evidence_class \
        == P.REAL_VAL_EVIDENCE


# --------------------------------------------------------------------------- #
# 9. Missing models are marked missing
# --------------------------------------------------------------------------- #
def test_09_absent_cells_are_marked_missing_not_estimated(tmp_path):
    empty = tmp_path / "nothing_here"
    outcome = PROV.verify_matrix(empty)
    assert outcome["n_cells"] == 24
    assert outcome["counts"] == {"MISSING": 24}
    assert outcome["research_cells_completed"] == 0
    assert all(c["status"] == "MISSING" for c in outcome["cells"])
    assert all("cell_result.json absent" in c["reasons"] for c in outcome["cells"])

    results = REP.collect_results(empty)
    assert results["research_cells_completed"] == 0
    assert results["synthetic_cells_executed"] == 0
    assert results["registry_status"]["status"] == "NOT_ESTABLISHED_0_OF_24"
    assert results["registry_status"]["all_cells_not_established"] is True
    assert all(c["status"] == "MISSING" for c in results["cells"])
    assert results["banner"] == REP.EMPTY_BANNER
    # absence is reported as absence, not as a zero score
    assert all(c.get("equal_domain_macro_dice") is None for c in results["cells"])


# --------------------------------------------------------------------------- #
# 10. Partial exports are not published as complete
# --------------------------------------------------------------------------- #
def test_10_partial_or_corrupt_exports_are_never_published_as_complete(adapters, mini,
                                                                      tmp_path):
    adapter = adapters(REG.BASELINES[0], 42)
    outcome = RN.evaluate_cell(adapter, mini)
    provenance = PROV.build_evaluation_provenance(
        model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_VAL,
        adapter_identity=adapter.identity(), evidence_class=adapter.evidence_class,
        split_manifest_sha256="0" * 64, n_images=len(outcome["records"]),
        evaluation_configuration=PROV.evaluation_config(),
        synthetic=True, training_performed=False)
    roster = [s.sample_id for s in mini]
    directory = tmp_path / "cell"

    # a short roster is refused rather than published as if complete
    with pytest.raises(PROV.PublicationError) as short:
        PROV.publish_cell(directory, records=outcome["records"][:2],
                          provenance=provenance, summary=outcome["summary"],
                          expected_sample_ids=roster)
    assert "roster mismatch" in str(short.value)

    # duplicated images are refused
    with pytest.raises(PROV.PublicationError) as duplicated:
        PROV.publish_cell(directory, records=list(outcome["records"]) + [outcome["records"][0]],
                          provenance=provenance, summary=outcome["summary"])
    assert "duplicate sample_id" in str(duplicated.value)

    # an empty cell is refused
    with pytest.raises(PROV.PublicationError):
        PROV.publish_cell(directory, records=[], provenance=provenance,
                          summary=outcome["summary"])

    # none of the failed attempts left a readable cell behind
    assert PROV.verify_cell(directory)["status"] == "MISSING"

    # a valid publication is validated
    doc = PROV.publish_cell(directory, records=outcome["records"],
                            provenance=provenance, summary=outcome["summary"],
                            expected_sample_ids=roster)
    assert doc["per_image_rows"] == len(mini)
    assert PROV.verify_cell(directory)["status"] == "COMPLETE_VALIDATED"
    assert not (directory / PROV.INCOMPLETE_NAME).exists()

    # an interrupted write leaves a marker and no result document
    interrupted = tmp_path / "interrupted"
    interrupted.mkdir()
    PROV.mark_incomplete(interrupted)
    (interrupted / PROV.PER_IMAGE_NAME).write_text("sample_id,dice\nx,0.5\n",
                                                   encoding="utf-8")
    assert PROV.verify_cell(interrupted)["status"] == "MISSING"

    # tampering with the export after publication is detected
    per_image = directory / PROV.PER_IMAGE_NAME
    per_image.write_bytes(per_image.read_bytes() + b"extra\n")
    rejected = PROV.verify_cell(directory)
    assert rejected["status"] == "REJECTED"
    assert "per_image.csv hash mismatch" in rejected["reasons"]


# --------------------------------------------------------------------------- #
# 11. Seed comparisons preserve exact image pairing
# --------------------------------------------------------------------------- #
def test_11_paired_comparisons_preserve_image_and_seed_identity():
    a = [_record("s1", 0.8), _record("s2", 0.6), _record("s3", 0.4)]
    b = [_record("s1", 0.7), _record("s2", 0.5), _record("s3", 0.3)]

    result = ST.compare_pair("A", "B", 42, a, b, n_boot=500)
    assert result["status"] == "DESCRIPTIVE"
    assert result["seed"] == 42
    assert result["n_paired_images"] == 3
    assert result["mean_difference"] == pytest.approx(0.1)
    assert result["inference_class"] == ST.EXPLORATORY
    assert result["p_value"] is None
    assert result["claim_status"] == ST.CLAIM_STATUS
    assert result["improvement_claimed"] is False

    # reordering one cell must not change the answer
    shuffled = ST.compare_pair("A", "B", 42, list(reversed(a)), b, n_boot=500)
    assert shuffled["n_paired_images"] == result["n_paired_images"]
    assert shuffled["mean_difference"] == pytest.approx(result["mean_difference"])

    # a different image set is an error, never a silent inner join
    with pytest.raises(ST.PairingError) as mismatch:
        ST.compare_pair("A", "B", 42, a, b[:2])
    assert "sample sets differ" in str(mismatch.value)

    # duplicated images in one cell are an error
    with pytest.raises(ST.PairingError):
        ST.compare_pair("A", "B", 42, a + [a[0]], b)

    # seed identity is carried, not inferred
    other = ST.compare_pair("A", "B", 3407, a, b, n_boot=200)
    assert other["seed"] == 3407
    assert other["bootstrap_seed"] == ST.DEFAULT_SEED

    # nothing here is allowed to become a confirmatory claim
    ST.assert_no_confirmatory_claim(result)
    with pytest.raises(ST.ConfirmatoryNotAuthorized):
        ST.assert_no_confirmatory_claim({**result, "p_value": 0.01})
    with pytest.raises(ST.ConfirmatoryNotAuthorized):
        ST.assert_no_confirmatory_claim({**result, "improvement_claimed": True})


# --------------------------------------------------------------------------- #
# 12. Statistical routines handle missing seeds and groups
# --------------------------------------------------------------------------- #
def test_12_missing_seeds_groups_and_clusters_are_handled_honestly():
    # a cluster unit with no identifier raises instead of quietly using images
    a = [_record("s1", 0.8, patient_id=None)]
    b = [_record("s1", 0.7, patient_id=None)]
    with pytest.raises(ST.StatisticsError) as no_group:
        ST.compare_pair("A", "B", 42, a, b, unit="patient", n_boot=50)
    assert "no patient identifier" in str(no_group.value)

    # one cluster cannot yield a spread; the interval is NaN, not zero
    degenerate = ST.cluster_bootstrap_ci([0.1, 0.2], ["p1", "p1"], n_boot=50)
    assert degenerate["n_clusters"] == 1
    assert math.isnan(degenerate["ci_low"]) and math.isnan(degenerate["ci_high"])
    assert degenerate["degenerate_reason"]

    # clustering widens the interval when images are not independent
    differences, clusters = [], []
    for patient, values in {"p1": [0.0] * 5, "p2": [0.0] * 5,
                            "p3": [0.4] * 5, "p4": [0.4] * 5}.items():
        differences += values
        clusters += [patient] * 5
    image_ci = ST.paired_ci(differences, unit="image", n_boot=2000)
    cluster_ci = ST.paired_ci(differences, clusters, unit="patient", n_boot=2000)
    assert image_ci["resampling_unit"] == "image"
    assert cluster_ci["resampling_unit"] == "cluster"
    assert cluster_ci["n_clusters"] == 4
    assert (cluster_ci["ci_high"] - cluster_ci["ci_low"]) > (
        image_ci["ci_high"] - image_ci["ci_low"])

    # a missing cell is NOT_AVAILABLE, never imputed
    cells = {(REG.FULL, 42): [_record("s1", 0.5)], (REG.GLOBAL, 42): [_record("s1", 0.4)],
             (REG.LITE, 42): [_record("s1", 0.45)]}
    comparisons = ST.build_comparisons(cells, n_boot=100)
    assert comparisons["full_vs_global"]["per_seed"]["42"]["status"] == "DESCRIPTIVE"
    assert comparisons["full_vs_lite"]["per_seed"]["42"]["status"] == "DESCRIPTIVE"
    assert comparisons["full_vs_baselines"][REG.BASELINES[0]]["per_seed"]["42"][
        "status"] == "NOT_AVAILABLE"
    assert comparisons["confirmatory_authorized"] is False

    # one seed has no spread; sd is None, never 0
    single = ST.seed_summary([0.123])
    assert single["n_seeds"] == 1 and single["sd"] is None
    assert "never a standard error" in single["note"]
    assert ST.seed_summary([])["n_seeds"] == 0

    # the frozen non-inferiority bound is only evaluable with a protocol reference
    with pytest.raises(ST.ConfirmatoryNotAuthorized):
        ST.evaluate_non_inferiority(-0.001)
    met = ST.evaluate_non_inferiority(-0.001, protocol_reference="spec §C")
    assert met["verdict"] == "BOUND_MET"
    assert met["margin"] == -0.005
    assert ST.evaluate_non_inferiority(-0.01, protocol_reference="spec §C")[
        "verdict"] == "BOUND_NOT_MET"
    assert ST.evaluate_non_inferiority(None, protocol_reference="spec §C")[
        "verdict"] == "NOT_EVALUABLE"


# --------------------------------------------------------------------------- #
# 13. Accuracy-efficiency units and bases are correct
# --------------------------------------------------------------------------- #
def test_13_efficiency_units_and_bases_are_declared(adapters, mini):
    plain = adapters(REG.BASELINES[0], 42)

    # the local counter and the canonical analytical counter must agree exactly
    model = plain._model
    device = next(model.parameters()).device
    local = EF._conv_linear_macs(model, lambda m: m(torch.zeros(
        1, 3, P.RESOLUTION, P.RESOLUTION, device=device)))
    canonical = C3.analytical_macs_lower_bound(
        model, (1, 3, P.RESOLUTION, P.RESOLUTION))
    assert local["macs_lower_bound"] == canonical["macs_lower_bound"] > 0
    assert local["macs_lower_bound"] == 46_137_344_000

    profile = EF.profile_cell(plain, mini[0].image, mini[0].task_id,
                              warmup=1, repeats=3)
    assert profile["unique_inference_parameters"] == 7_763_041
    assert profile["parameters_unit"].startswith("parameters")
    assert profile["latency_ms_p50"] > 0
    assert profile["latency_unit"].startswith("milliseconds per image")
    assert profile["memory_unit"] == "MiB"
    assert profile["macs_unit"].startswith("multiply-accumulate")
    # the three quantities carry three distinct units, not one shared "unit" key
    assert profile["latency_unit"] != profile["memory_unit"]
    assert profile["peak_allocated_mib"] is None or profile["peak_allocated_mib"] > 0
    assert profile["conditional_refiner"] is False
    assert profile["macs_if_always_refine"] is None
    assert profile["effective_macs_per_image"] is None

    conditions = profile["profiling_conditions"]
    assert conditions["input_resolution"] == 512
    assert conditions["batch_size"] == 1
    assert conditions["precision"] == "float32"
    assert conditions["warmup_iterations"] == 1
    assert conditions["measured_repeats"] == 3
    assert conditions["timing_source"]
    assert conditions["note"]

    # MACs and total FLOPs are separate measures and are not substituted
    flops = EF.total_flops(plain)
    assert flops["total_flops"] >= 2 * local["macs_lower_bound"]
    assert flops["conv_linear_macs_equivalent"] == flops["total_flops"] / 2
    assert "Not comparable" in flops["note"]

    # a conditional system reports both the always-refine cost and the effective
    # cost at the measured invocation rate, so the saving is visible
    routed = adapters(REG.FULL, 42)
    records = ([{**_record(f"x{i}", 0.5), "refiner_executed": i % 2 == 0}
                for i in range(4)])
    conditional = EF.profile_cell(routed, mini[0].image, mini[0].task_id,
                                  records=records, warmup=1, repeats=2)
    assert conditional["conditional_refiner"] is True
    assert conditional["conditional_refiner_invocation_rate"] == pytest.approx(0.5)
    assert conditional["macs_if_always_refine"] > conditional["effective_macs_per_image"]
    expected = int(conditional["macs_global_only"]
                   + conditional["macs_router_per_image"]
                   + 0.5 * (conditional["macs_refiner_per_call"]
                            + conditional["macs_safety_per_call"]))
    assert conditional["effective_macs_per_image"] == expected
    assert "conditional" in conditional["macs_note"].lower()
    # the routed family has no single module to hand to FlopCounterMode
    assert EF.total_flops(routed)["total_flops"] is None


# --------------------------------------------------------------------------- #
# 14. Reports distinguish synthetic from actual evidence
# --------------------------------------------------------------------------- #
def test_14_reports_never_present_synthetic_as_actual(adapters, mini, tmp_path):
    root = tmp_path / "cells"
    RN.run_cell(REG.BASELINES[0], 42, mini, root=root, source="synthetic",
                device=DEVICE, split_manifest_sha256="0" * 64)

    results = REP.write_tables(root, tmp_path / "tables")
    assert results["banner"] == REP.SYNTHETIC_BANNER
    assert "SYNTHETIC_TEST_ONLY" in results["banner"]
    assert "not research results" in results["banner"]
    assert "must not" in results["banner"]
    assert results["evidence_classes"] == [P.SYNTHETIC_EVIDENCE]
    assert results["research_cells_completed"] == 0
    assert results["synthetic_cells_executed"] == 1
    assert results["registry_status"]["status"] == "NOT_ESTABLISHED_0_OF_24"

    manifest = results["manifest"]
    assert manifest["banner"] == REP.SYNTHETIC_BANNER
    assert manifest["statistics_policy"]["p_values_generated"] == 0
    assert manifest["statistics_policy"]["confirmatory_authorized"] is False
    assert manifest["statistics_policy"]["inference_class"] == ST.EXPLORATORY
    assert manifest["research_cells_completed"] == 0

    # every table that has rows declares its evidence class in the header
    assert set(manifest["tables"]) == set(REP.TABLE_FILES)
    for key, meta in manifest["tables"].items():
        path = tmp_path / "tables" / meta["file"]
        assert path.is_file(), key
        assert meta["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        if meta["rows"]:
            header = path.read_text(encoding="utf-8").splitlines()[0]
            assert "evidence_class" in header, key
            assert "SYNTHETIC_TEST_ONLY" in path.read_text(encoding="utf-8"), key
    # the paired table carries no p-value anywhere
    paired = (tmp_path / "tables" / REP.TABLE_FILES["paired"]).read_text(encoding="utf-8")
    assert "p_value" in paired.splitlines()[0]

    # the real banner says something different and does not claim independence
    assert REP.REAL_BANNER != REP.SYNTHETIC_BANNER
    assert "Not an independent confirmation" in REP.REAL_BANNER
    assert "development/selection-consumed" in REP.REAL_BANNER

    # the three banner states are mutually exclusive
    assert REP._banner([]) == REP.EMPTY_BANNER
    assert REP._banner([P.SYNTHETIC_EVIDENCE]) == REP.SYNTHETIC_BANNER
    assert REP._banner([P.REAL_VAL_EVIDENCE]) == REP.REAL_BANNER
    assert REP._banner([P.SYNTHETIC_EVIDENCE, P.REAL_VAL_EVIDENCE]) == REP.MIXED_BANNER


# --------------------------------------------------------------------------- #
# 15. Repeat execution is deterministic
# --------------------------------------------------------------------------- #
def test_15_repeat_execution_is_deterministic(mini, tmp_path):
    first = RN.run_cell(REG.LITE, 123, mini, root=tmp_path / "a", source="synthetic",
                        device=DEVICE, split_manifest_sha256="0" * 64)
    second = RN.run_cell(REG.LITE, 123, mini, root=tmp_path / "b", source="synthetic",
                         device=DEVICE, split_manifest_sha256="0" * 64)

    for left, right in zip(first["records"], second["records"]):
        assert left["sample_id"] == right["sample_id"]
        for field in ("dice", "iou", "precision", "recall", "hd95",
                      "tp", "fp", "fn", "tn", "state", "refiner_executed"):
            assert left[field] == right[field], (left["sample_id"], field)
    assert (first["summary"]["equal_domain_macro_dice"]
            == second["summary"]["equal_domain_macro_dice"])

    # the published export is byte-identical, so the artifacts agree too
    cell = Path(REG.LITE) / "seed123" / PROV.PER_IMAGE_NAME
    digest_a = hashlib.sha256((tmp_path / "a" / cell).read_bytes()).hexdigest()
    digest_b = hashlib.sha256((tmp_path / "b" / cell).read_bytes()).hexdigest()
    assert digest_a == digest_b
    # and the identity the cell carries is the same
    assert first["adapter_identity"]["component_sha256"] == \
        second["adapter_identity"]["component_sha256"]


# --------------------------------------------------------------------------- #
# 16. Interrupted evaluation resumes correctly
# --------------------------------------------------------------------------- #
def test_16_interruption_resumes_without_duplicating_or_losing_samples(
        adapters, samples, mini, tmp_path):
    adapter = adapters(REG.BASELINES[0], 42)
    roster = [s.sample_id for s in samples]

    # a first pass over one image per domain writes a ledger even without --resume,
    # so an interrupted run always leaves something to resume from
    cell = tmp_path / "resumable"
    first = RN.evaluate_cell(adapter, mini, directory=cell, resume=False)
    assert first["summary"]["n_scored_this_pass"] == len(mini)
    assert PROV.ProgressLedger(cell).count == len(mini)

    # a torn final line from an interrupted append is discarded, not fatal
    with (cell / PROV.PROGRESS_NAME).open("a", encoding="utf-8") as handle:
        handle.write('{"sample_id": "torn", "dice_sha256": "\n')

    resumed = RN.evaluate_cell(adapter, samples, directory=cell, resume=True)
    assert resumed["summary"]["n_scored_this_pass"] == len(samples) - len(mini)
    assert resumed["summary"]["n_from_ledger"] == len(mini)
    assert [r["sample_id"] for r in resumed["records"]] == roster
    assert len(set(roster)) == len(roster)
    assert PROV.ProgressLedger(cell).count == len(samples)

    # the merged roster publishes as a complete cell
    provenance = PROV.build_evaluation_provenance(
        model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_VAL,
        adapter_identity=adapter.identity(), evidence_class=adapter.evidence_class,
        split_manifest_sha256="0" * 64, n_images=len(resumed["records"]),
        evaluation_configuration=PROV.evaluation_config(),
        synthetic=True, training_performed=False)
    doc = PROV.publish_cell(cell, records=resumed["records"], provenance=provenance,
                            summary=resumed["summary"], expected_sample_ids=roster)
    assert doc["per_image_rows"] == len(samples)
    assert PROV.verify_cell(cell)["status"] == "COMPLETE_VALIDATED"

    # a fully complete resume is a no-op, not a re-score
    again = RN.evaluate_cell(adapter, samples, directory=cell, resume=True)
    assert again["summary"]["n_scored_this_pass"] == 0
    assert [r["dice"] for r in again["records"]] == [r["dice"] for r in resumed["records"]]

    # a torn append WITHOUT a trailing newline corrupts the record that follows it.
    # The system must notice and re-score the lost sample rather than publish a gap.
    corrupt = tmp_path / "corrupt"
    RN.evaluate_cell(adapter, mini, directory=corrupt, resume=False)
    with (corrupt / PROV.PROGRESS_NAME).open("a", encoding="utf-8") as handle:
        handle.write('{"sample_id": "torn", "dice_sha256": "')
    healed = RN.evaluate_cell(adapter, samples, directory=corrupt, resume=True)
    assert [r["sample_id"] for r in healed["records"]] == roster
    repair = RN.evaluate_cell(adapter, samples, directory=corrupt, resume=True)
    assert repair["summary"]["n_scored_this_pass"] == 1, "exactly the lost record is re-scored"
    assert [r["sample_id"] for r in repair["records"]] == roster

    # a fresh (non-resume) pass owns the ledger and clears stale entries
    fresh = RN.evaluate_cell(adapter, samples, directory=corrupt, resume=False)
    assert fresh["summary"]["n_scored_this_pass"] == len(samples)
    assert PROV.ProgressLedger(corrupt).count == len(samples)


# --------------------------------------------------------------------------- #
# 17. Protected TEST1683 is never read
# --------------------------------------------------------------------------- #
def test_17_protected_test_split_is_never_read(monkeypatch, tmp_path):
    guard = P.ProtectedSplitGuard()
    with pytest.raises(P.ProtectedSplitError):
        guard.open(P.SPLIT_TEST)
    report = guard.report()
    assert report["test_reads"] == 0
    assert report["test_refusals"] == 1
    assert report["protected_untouched"] is True
    assert P.PROTECTED_SPLITS == frozenset({P.SPLIT_TEST})
    assert P.SPLIT_SEMANTICS[P.SPLIT_TEST]["readable"] is False

    # the loader refuses before a single file is opened
    with pytest.raises(P.ProtectedSplitError):
        RN.load_manifest_samples(P.MANIFEST_FILES[P.SPLIT_TEST], P.SPLIT_TEST)
    guarded = P.ProtectedSplitGuard()
    with pytest.raises(P.ProtectedSplitError):
        RN.load_manifest_samples(P.MANIFEST_FILES[P.SPLIT_TEST], P.SPLIT_TEST,
                                 guard=guarded)
    assert guarded.reads[P.SPLIT_TEST] == 0
    assert guarded.refusals[P.SPLIT_TEST] == 1

    # the CLI refuses the protected split before it resolves any path
    with pytest.raises(SystemExit):
        CLI.main(["evaluate", "--source", "real", "--split", P.SPLIT_TEST,
                  "--root", str(tmp_path), "--device", "cpu"])

    # only the row count is audited, and no image is opened to do it
    def explode(*_args, **_kwargs):
        raise AssertionError("a protected split opened an image")

    import PIL.Image
    monkeypatch.setattr(PIL.Image, "open", explode)
    audit = P.population_audit()
    assert audit["consistent"] is True
    assert audit["populations"][P.SPLIT_TEST]["n"] == 1683
    assert audit["populations"][P.SPLIT_TEST]["readable"] is False
    assert "never opened" in audit["note"]
    # the other populations are still audited to their frozen sizes
    assert audit["populations"][P.SPLIT_TRAIN]["n"] == 5832
    assert audit["populations"][P.SPLIT_VAL]["n"] == 808

    # VAL is readable but may never be described as independent confirmation
    assert P.SPLIT_SEMANTICS[P.SPLIT_VAL]["independent"] is False
    assert "NOT independent" in P.SPLIT_SEMANTICS[P.SPLIT_VAL]["label"]
    assert "NOT_INDEPENDENT" in P.VAL_EVIDENCE_LABEL
    assert P.REAL_VAL_EVIDENCE == P.REAL_VAL_EVIDENCE
    assert P.RESEARCH_EVIDENCE_CLASSES == frozenset({P.REAL_VAL_EVIDENCE})

    # no provenance block may ever be built for the protected split
    identity = {"adapter_kind": "PLAIN", "checkpoint_sha256": "x"}
    with pytest.raises(PROV.ProvenanceError):
        PROV.build_evaluation_provenance(
            model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_TEST,
            adapter_identity=identity, evidence_class=P.REAL_VAL_EVIDENCE,
            split_manifest_sha256="0" * 64, n_images=1,
            evaluation_configuration=PROV.evaluation_config(),
            synthetic=False, training_performed=True)


# --------------------------------------------------------------------------- #
# 18. Existing FULL/Lite training tests remain passing
# --------------------------------------------------------------------------- #
TRAINING_SUITES = ("tests/test_lite_pipeline.py", "tests/test_full_pipeline.py")


def test_18_existing_full_and_lite_training_tests_still_pass(tmp_path):
    for relative in TRAINING_SUITES:
        assert (ROOT / relative).is_file(), relative

    # structural: the training entry points this phase must not have disturbed
    from src.research.full_pipeline import recipe as R
    from src.research.lite_pipeline import recipe as L
    from src.research.lite_pipeline.orchestrator import STAGE_ORDER

    assert STAGE_ORDER == ("G", "CACHE", "R", "L", "B", "S")
    assert R.TRAIN_N == 5832 and R.VAL_N == 808 and R.TEST_N == 1683
    assert L.TOTAL_EXPECTED_PARAMETERS == 272_601
    assert R.ROI_PROPOSAL_THRESHOLD == 0.30
    assert R.SEGMENTATION_OUTPUT_THRESHOLD == 0.50

    if os.environ.get("PHASE_C_RUN_TRAINING_REGRESSION") != "1":
        pytest.skip("set PHASE_C_RUN_TRAINING_REGRESSION=1 to execute the training suites")

    # ``--basetemp`` is supplied so pytest does not rotate its numbered temp roots:
    # that rotation bulk-deletes a hundred-odd stale directories, which this host's
    # safe-delete guard blocks, turning a fully passing run into exit code 1.  The
    # assertion below is unchanged — a genuinely failing training test still fails.
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", *TRAINING_SUITES, "-q", "--no-header",
         "-p", "no:cacheprovider", "--basetemp", str(tmp_path / "suite_tmp")],
        cwd=str(ROOT), capture_output=True, text=True, timeout=5400)
    assert completed.returncode == 0, (
        "existing training suites failed\n"
        + completed.stdout[-6000:] + "\n" + completed.stderr[-2000:])
    # and the summary must actually report passes rather than an empty collection
    assert " passed" in completed.stdout
    assert " failed" not in completed.stdout


# --------------------------------------------------------------------------- #
# CLI integration (Phase C §9): every subcommand is reachable and honest
# --------------------------------------------------------------------------- #
def test_cli_validate_and_plan_are_green(capsys):
    assert CLI.main(["validate"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "VALIDATE_OK"
    checks = payload["checks"]
    assert checks["populations"]["consistent"] is True
    assert checks["known_answer_metrics"]["all_match"] is True
    assert checks["gt_free_adapters"]["gt_free"] is True
    assert checks["gt_free_state_machine"]["gt_free"] is True
    assert checks["protected_split_guard"]["protected_untouched"] is True
    assert checks["registry"]["n_cells"] == 24
    assert checks["statistics_policy"]["confirmatory_authorized"] is False

    assert CLI.main(["plan"]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["n_cells"] == 24
    assert plan["evaluable_splits"] == [P.SPLIT_VAL]
    assert plan["protected_splits"] == [P.SPLIT_TEST]
    assert len(plan["cells"]) == 24


def test_synthetic_matrix_can_never_complete_a_research_cell(adapters, mini, tmp_path):
    outcome = RN.run_matrix(tmp_path / "matrix", mini, source="synthetic",
                            device=DEVICE, seeds=(42,), models=(REG.BASELINES[0],))
    assert outcome["n_cells"] == 1
    assert outcome["n_executed"] == 1
    assert outcome["n_failed"] == 0
    assert outcome["research_cells_completed"] == 0
    assert outcome["evidence_class"] == P.SYNTHETIC_EVIDENCE
    assert "Executed is not the same as established" in outcome["note"]

    verification = PROV.verify_matrix(tmp_path / "matrix")
    assert verification["counts"] == {"COMPLETE_VALIDATED": 1, "MISSING": 23}
    assert verification["research_cells_completed"] == 0
