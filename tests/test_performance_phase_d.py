"""Phase D — GPU performance, reliability and reproducibility checks.

Every test here is a check on *behaviour*, not a re-statement of a constant.  The
suite is deliberately CPU-capable: the GPU-specific measurements (allocator peaks,
cross-device parity, deterministic CUDA kernels) are skipped when no device is
present, and the reason is recorded rather than the check being quietly dropped.

Nothing in this file trains a model on real data, reads a protected split, or
touches an institutional trust store.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from src.research.evaluation import protocol as P
from src.research.evaluation import provenance as PROV
from src.research.evaluation import registry as REG
from src.research.full_pipeline import recipe as R
from src.research.performance import bench as B
from src.research.performance import conditional as C
from src.research.performance import determinism as D
from src.research.performance import failures as FL
from src.research.performance import film as F
from src.research.performance import isolation as ISO
from src.research.performance import memory as M
from src.research.performance import report as RP
from src.research.performance import stability as S
from src.research.stage6 import end_to_end as E

CUDA = pytest.mark.skipif(not torch.cuda.is_available(), reason="no CUDA device")
FAST = B.Conditions(device="cpu", warmup=1, repeats=2)


# --------------------------------------------------------------------------- #
# 1. Declared conditions and distinct units
# --------------------------------------------------------------------------- #
def test_01_conditions_are_declared_and_units_never_collide():
    conditions = B.Conditions(device="cpu", warmup=3, repeats=7)
    declared = conditions.as_dict()
    for key in ("device_type", "device_name", "input_resolution", "batch_size",
                "precision", "warmup_iterations", "measured_repeats",
                "cuda_synchronized", "timing_source", "determinism"):
        assert key in declared, key
    assert declared["warmup_iterations"] == 3
    assert declared["measured_repeats"] == 7
    # latency, memory and MACs must never share a unit key (a Phase C defect)
    assert B.percentiles([1.0, 2.0])["unit"] == "milliseconds"
    assert B.measure_peak_memory(lambda: None, device="cpu")["memory_unit"] == "MiB"
    assert (B.benchmark_model(REG.BASELINES[0], seed=42, conditions=FAST)
            ["macs"]["unit"] == "multiply-accumulate")


# --------------------------------------------------------------------------- #
# 2. The routed pipeline is batch-1 by contract
# --------------------------------------------------------------------------- #
def test_02_routed_pipelines_refuse_batching():
    for model_key in (REG.FULL, REG.LITE):
        with pytest.raises(ValueError, match="per-image"):
            B.benchmark_routed(model_key, seed=42,
                               conditions=B.Conditions(device="cpu", batch_size=2,
                                                       warmup=1, repeats=1))
        with pytest.raises(ValueError, match="batch-1 by contract"):
            B.benchmark_batch_scaling(model_key, device="cpu", batches=(1, 2),
                                      warmup=1, repeats=1)
    # a single-network model may be batched
    rows = B.benchmark_batch_scaling(REG.BASELINES[0], device="cpu", batches=(1, 2),
                                     warmup=1, repeats=1)["rows"]
    assert [row["batch_size"] for row in rows] == [1, 2]
    assert all(row["per_image_ms"] is not None for row in rows)


# --------------------------------------------------------------------------- #
# 3. Cold and warm are separate measurements
# --------------------------------------------------------------------------- #
def test_03_cold_call_is_never_averaged_into_the_warm_figure():
    timing = B.time_call(lambda: torch.zeros(64, 64).sum(), warmup=2, repeats=5,
                         device="cpu")
    assert timing["cold_first_call"] is not None
    assert timing["n"] == 5
    assert timing["warmup_iterations"] == 2
    assert timing["measured_repeats"] == 5
    assert "median" in timing and "p90" in timing and "p95" in timing
    assert timing["p95"] >= timing["median"] >= timing["min"]


# --------------------------------------------------------------------------- #
# 4. Every model has a working profiling path
# --------------------------------------------------------------------------- #
def test_04_all_eight_models_have_a_profiling_path():
    assert len(REG.DISPLAY_ORDER) == 8
    for model_key in REG.DISPLAY_ORDER:
        record = B.benchmark_model(model_key, seed=42, conditions=FAST)
        assert record["model_key"] == model_key
        assert record["evidence_class"] == "SYNTHETIC_BENCHMARK"
        assert record["model_forward_ms"]["median"] is not None
        assert record["pipeline_ms"]["median"] is not None
        assert record["parameters"] > 0
        assert record["initialization_ms"]["median"] is not None
        assert record["conditions"]["batch_size"] == 1
        if REG.ADAPTER_KINDS[model_key] == "ROUTED":
            assert record["batched_forward"] is False
            assert record["observed_state"] in (
                "FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")
        else:
            assert record["batched_forward"] is True


# --------------------------------------------------------------------------- #
# 5. All four canonical states are reachable and asserted
# --------------------------------------------------------------------------- #
def test_05_all_four_canonical_states_are_reached_and_asserted():
    reached = {}
    for scenario in C.SCENARIOS:
        record = C.run_scenario(REG.LITE, scenario, seed=42, device="cpu",
                                warmup=1, repeats=2)
        assert record["state_matches"] is True, scenario.name
        assert record["observed_state"] == scenario.expected_state
        reached[scenario.name] = record["observed_state"]
    assert set(reached.values()) == {"FORCED_SKIP", "SKIP_GLOBAL",
                                     "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"}

    # the component counters must agree with the state that was reached
    forced = C.run_scenario(REG.LITE, C.SCENARIOS[0], seed=42, device="cpu",
                            warmup=1, repeats=1)
    assert forced["component_invocations"]["router"] == 0
    assert forced["component_invocations"]["refiner"] == 0
    accepted = C.run_scenario(REG.LITE, C.SCENARIOS[2], seed=42, device="cpu",
                              warmup=1, repeats=1)
    assert accepted["component_invocations"]["refiner"] == 1
    assert accepted["component_invocations"]["safety"] == 1


# --------------------------------------------------------------------------- #
# 6. Scripting a decision is not tuning a threshold
# --------------------------------------------------------------------------- #
def test_06_scripting_a_decision_does_not_touch_a_threshold():
    assert P.ROI_PROPOSAL_THRESHOLD == 0.30
    assert P.SEGMENTATION_OUTPUT_THRESHOLD == 0.50
    assert P.SOMEGA_ACCEPT_THRESHOLD == 0.50
    # the utility offset is derived from the frozen recipe, not hard-coded
    assert C.UTILITY_OFFSET == pytest.approx(float(R.LAMBDA * R.C_ACTION), rel=0, abs=0)
    assert C.UTILITY_OFFSET == pytest.approx(0.025598133105969194, abs=1e-15)
    # and inverting it reproduces canonical_utility exactly
    for utility in (-0.5, 0.0, 0.25):
        score = C.score_for_utility(utility)
        assert E.canonical_utility(score) == pytest.approx(utility, abs=1e-12)


# --------------------------------------------------------------------------- #
# 7. ROI geometry edge cases
# --------------------------------------------------------------------------- #
def test_07_roi_geometry_edge_cases_are_explicit():
    cases = {row["case"]: row for row in C.roi_edge_cases()}
    assert cases["empty_map"]["state"] == "FORCED_SKIP"
    assert cases["all_below_threshold"]["state"] == "FORCED_SKIP"
    for name in ("single_pixel", "centred_blob", "border_touching", "full_canvas"):
        assert cases[name]["state"] == "ROI_PROPOSED", name
        roi = cases[name]["roi"]
        assert 0 <= roi["clip_y1"] < roi["clip_y2"] <= 512
        assert 0 <= roi["clip_x1"] < roi["clip_x2"] <= 512
        assert roi["crop_side_pixels"] > 0
        assert roi["effective_magnification"] > 0
    # a full-canvas ROI is expanded past the canvas and clipped back into it
    assert cases["full_canvas"]["roi"]["crop_side_pixels"] == 768


# --------------------------------------------------------------------------- #
# 8. Execution-mode comparison is ordered and honest
# --------------------------------------------------------------------------- #
def test_08_execution_modes_are_compared_without_a_routing_claim():
    comparison = C.compare_execution_modes(REG.LITE, seed=42, device="cpu",
                                           warmup=1, repeats=3)
    global_only = comparison["global_only_ms"]["median"]
    always = comparison["always_refine_ms"]["median"]
    conditional = comparison["conditional_ms"]["median"]
    # refine-always must cost more than the global backbone alone
    assert always > global_only
    assert comparison["macs_if_always_refine"] > comparison["macs_global_only"]
    assert comparison["effective_macs_per_image"] <= comparison["macs_if_always_refine"]
    assert comparison["conditional_state"] in (
        "FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")
    assert conditional > 0
    # the caveat is carried with the numbers, not left to the reader
    assert "not by itself a lower total cost" in comparison["caveat"]


# --------------------------------------------------------------------------- #
# 9. Contract shapes
# --------------------------------------------------------------------------- #
def test_09_memory_stages_use_the_contract_shapes():
    assert M.GLOBAL_SIDE == P.RESOLUTION == 512
    assert M.ROI_SIDE == 256
    assert M.ROUTER_FEATURE_WIDTH == 202
    assert M.SAFETY_INPUT_WIDTH == 20

    (images, task), target = M._g_inputs(2, "cpu")
    assert tuple(images.shape) == (2, 3, 512, 512)
    assert tuple(target.shape) == (2, 1, 512, 512)

    (roi,), roi_target = M._r_inputs(2, "cpu")
    assert tuple(roi.shape) == (2, 4, 256, 256)          # 3-channel crop + probability crop
    assert tuple(roi_target.shape) == (2, 1, 256, 256)

    (features, task), _ = M._b_inputs(2, "cpu")
    assert tuple(features.shape) == (2, 202)

    (safety,), _ = M._s_inputs(2, "cpu")
    assert tuple(safety.shape) == (2, 20)
    assert float(safety[:, 16:].sum()) == 2.0            # exactly one one-hot per row


def test_09b_transfer_measurement_honours_the_requested_batch_count():
    """Regression for a Phase D defect: --transfer-batches was silently ignored.

    The CLI gated the whole transfer block on --workers, so the flag never reached
    the measurement and every run reported the library default of 6 batches. The
    cost of that silence is a startup-dominated figure quoted as throughput.
    """
    import importlib.util
    import pathlib

    spec = importlib.util.spec_from_file_location(
        "phase_d_cli", pathlib.Path(__file__).resolve().parents[1]
        / "scripts" / "analysis" / "phase_d_performance.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    parser = cli.build_parser()
    default = parser.parse_args(["memory"])
    explicit = parser.parse_args(["memory", "--transfer-batches", "24", "--workers", "2"])
    assert default.transfer_batches == 24
    assert explicit.transfer_batches == 24
    assert explicit.workers == 2

    # The library must actually consume `batches`: warmup batches are excluded, so
    # a 3-batch request with 1 warmup measures exactly 2 batches of `batch` images.
    row = M.dataloader_overhead(workers=0, pin_memory=False, batch=4,
                                batches=3, warmup_batches=1, device="cpu")
    assert row["warmup_batches_excluded"] == 1
    assert row["images_measured"] == 8, row
    assert row["batches"] == 3, row


# --------------------------------------------------------------------------- #
# 10. Determinism and resume
# --------------------------------------------------------------------------- #
def test_10_determinism_and_resume_are_demonstrated():
    checks = [
        D.check_seeding(42),
        D.check_rng_replay(42),
        D.check_empty_state_refused(),
        D.check_loader_order(42),
        D.check_resume_equivalence(42),
        D.check_checkpoint_selection(42),
        D.check_dependency_identities(),
        D.check_prediction_export(42),
        D.check_per_image_results(42),
    ]
    failed = [c["check"] for c in checks if not c["passed"]]
    assert not failed, [c for c in checks if not c["passed"]]

    # the Phase B fix must be both necessary and sufficient, not merely present
    resume = next(c for c in checks if c["check"] == "resume_equivalence")
    assert resume["fix_necessary"] is True
    assert resume["fix_sufficient"] is True
    assert resume["weights_sha256_uninterrupted"] == resume["weights_sha256_resumed"]
    assert resume["resumed_with_fix"] == resume["uninterrupted"][1:]
    assert resume["resumed_without_fix"][0] != resume["uninterrupted"][1]


# --------------------------------------------------------------------------- #
# 11. FiLM conditioning
# --------------------------------------------------------------------------- #
def test_11_film_conditioning_is_verified_functionally():
    propagation = F.check_identity_propagation(device="cpu")
    assert propagation["passed"], propagation["detail"]
    assert len(propagation["sites"]) == 5
    assert all(count == 1 for count in propagation["call_counts"].values())
    # identity at initialization is expected, and is explicitly not the evidence
    assert propagation["identity_at_init"]["identity_at_init"] is True

    gradients = F.check_gradients_and_updates(device="cpu", steps=30)
    assert gradients["passed"], gradients["detail"]
    # the zero-initialised output projection blocks the deeper gradients at step 0
    assert gradients["gradients_at_init"]["output_projection"]["nonzero_tensors"] > 0
    assert gradients["gradients_at_init"]["hidden_layer"]["magnitude"] == 0.0
    assert gradients["gradients_at_init"]["task_embedding"]["magnitude"] == 0.0
    assert gradients["gradients_after_one_step"]["hidden_layer"]["nonzero_tensors"] > 0

    learned = F.check_learned_task_dependence(device="cpu", contract_size=None)
    assert learned["passed"], learned["detail"]
    assert learned["loss"]["last"] < F.TASK_BLIND_OPTIMUM
    assert learned["difference_before_init"]["max_abs_difference"] == 0.0
    assert learned["difference_after_optimization"]["same_task_repeat_identical"] is True

    control = F.check_c1_identity_control(device="cpu")
    assert control["passed"], control["detail"]
    assert control["totals_equal"] is True
    assert control["control_task_difference"]["max_abs_difference"] == 0.0
    assert control["control_loss"] > F.CONTROL_LOSS_FLOOR
    assert control["treatment_loss"] < F.TREATMENT_LOSS_CEILING

    # §6 check 6: the experiment must not touch anything outside the treatment
    scope = F.check_unrelated_components_untouched(device="cpu", steps=20)
    assert scope["passed"], scope["detail"]
    assert scope["unrelated_instance_digest"]["before"] == \
        scope["unrelated_instance_digest"]["after"]
    assert scope["film_sites_unchanged"] is True
    assert scope["architecture_id_unchanged"] is True
    assert scope["matched_arms_unchanged"] is True
    # and the check is not vacuous: the treatment itself did move
    assert scope["treatment_digest"]["before"] != scope["treatment_digest"]["after"]


# --------------------------------------------------------------------------- #
# 12. Failure injection
# --------------------------------------------------------------------------- #
def test_12_all_eight_stage_failures_are_detected(tmp_path):
    report = FL.failure_report(workdir=tmp_path / "failures")
    assert report["n_injections"] == 8
    assert report["all_detected"] is True, report["missed"]
    assert set(report["stages"]) == {
        "global_training", "cache_creation", "refiner_training",
        "benefit_label_generation", "router_training", "safety_training",
        "evaluation_export", "result_publication"}
    for row in report["injections"]:
        assert row["detected"], row
        assert row["guard"] != "-"


# --------------------------------------------------------------------------- #
# 13. Evidence isolation
# --------------------------------------------------------------------------- #
def test_13_synthetic_artifacts_can_never_masquerade_as_research(tmp_path):
    report = ISO.run_all_attacks(tmp_path / "attacks")
    assert report["n_attacks"] == 7
    assert report["all_blocked"] is True, [
        row for row in report["attacks"] if not row["blocked"]]

    # the root-wide marker scan is what catches an off-path copy
    by_name = {row["attack"]: row for row in report["attacks"]}
    assert "namespace_consistent == False" in by_name["artifact_copy"]["blocked_by"]
    assert "foreign_problems=1" in by_name["artifact_copy"]["detail"]

    # a namespace is derived from the evidence class and cannot be supplied
    assert PROV.namespace_for(P.SYNTHETIC_EVIDENCE) == PROV.NAMESPACE_SYNTHETIC
    assert PROV.namespace_for(P.REAL_VAL_EVIDENCE) == PROV.NAMESPACE_RESEARCH
    with pytest.raises(PROV.NamespaceError):
        PROV.namespace_for("SOMETHING_ELSE")

    # and the promotion gate refuses a synthetic document even if hand-built
    forged = {"evidence_class": P.REAL_VAL_EVIDENCE,
              "evidence_namespace": PROV.NAMESPACE_RESEARCH, "synthetic": True,
              "provenance": {"training_performed": True, "split": P.SPLIT_VAL,
                             "checkpoint_sha256": ISO.PROBE_DIGEST,
                             "component_sha256": {}}}
    assert PROV.research_evidence_reasons(forged)


# --------------------------------------------------------------------------- #
# 14. Resource stability
# --------------------------------------------------------------------------- #
def test_14_resource_stability_distinguishes_cache_from_leak():
    growth = S.check_memory_growth(device="cpu", cycles=4)
    assert growth["passed"], growth["detail"]
    handles = S.check_handle_leaks(device="cpu", cycles=3, windows=3)
    assert handles["passed"], handles["detail"]
    assert len(handles["window_deltas"]) == 3
    caches = S.check_unbounded_caches(cycles=5)
    assert caches["passed"], caches["detail"]
    assert caches["temporary_files"] == []
    reload_cost = S.check_reload_overhead(device="cpu")
    assert reload_cost["passed"], reload_cost["detail"]
    assert reload_cost["ratio"] is not None


# --------------------------------------------------------------------------- #
# 15. CPU / CUDA parity
# --------------------------------------------------------------------------- #
@CUDA
def test_15_cpu_cuda_parity_uses_the_inherited_tolerances():
    report = S.parity_report(device="cuda", seed=42)
    assert report["tolerances"]["binary_agreement_min"] == S.PARITY_BINARY_AGREEMENT_MIN
    assert (report["tolerances"]["mean_abs_difference_max"]
            == S.PARITY_MEAN_ABS_DIFFERENCE_MAX)
    assert "not" in report["tolerances"]["source"] or "inherited" in \
        report["tolerances"]["source"]
    assert len(report["records"]) == 8
    for row in report["records"]:
        assert row["shape_match"] is True, row["model_key"]
        assert row["both_finite"] is True, row["model_key"]
        assert row["weights_copied"] is True, row["model_key"]
        assert row["mean_abs_difference"] <= S.PARITY_MEAN_ABS_DIFFERENCE_MAX, row
    assert report["all_passed"] is True, report["failed"]


# --------------------------------------------------------------------------- #
# 16. Evidence label everywhere
# --------------------------------------------------------------------------- #
def test_16_every_phase_d_document_is_labelled_synthetic_benchmark():
    for module in (B, C, M, D, F, FL, ISO, S):
        assert module.EVIDENCE_CLASS == "SYNTHETIC_BENCHMARK", module.__name__
    assert RP.EVIDENCE_CLASS == "SYNTHETIC_BENCHMARK"
    # the label is never the research evidence class
    assert RP.EVIDENCE_CLASS not in P.RESEARCH_EVIDENCE_CLASSES


# --------------------------------------------------------------------------- #
# 17. The report never imputes a missing deliverable
# --------------------------------------------------------------------------- #
def test_17_report_marks_absent_documents_instead_of_filling_them_in(tmp_path):
    report = RP.build_report(tmp_path)
    assert report["status"] == "PHASE_D_INCOMPLETE"
    assert report["deliverables"]
    missing = [d for d in report["deliverables"] if not d["present"]]
    # twelve deliverables read from a document; 12 and 14 are computed
    assert len(missing) == 12
    assert any("without a source document" in item for item in report["12_blockers"])
    markdown = RP.render_markdown(report)
    assert "SYNTHETIC_BENCHMARK" in markdown
    assert "PHASE_D_INCOMPLETE" in markdown
    # a missing document is reported as missing, not as a zero measurement
    assert "No regression document was produced" in markdown
    # Regression for a Phase D defect: `not bool(None)` read an absent regression
    # document as "no regressions", so this criterion reported MET before the suite
    # had ever been run. Absence must not be evidence of success.
    criterion = report["14_decision"]["definition_of_done"][
        "new_engineering_regressions_resolved"]
    assert criterion["met"] is False, criterion
    assert "no regression document" in criterion["detail"].lower()


# --------------------------------------------------------------------------- #
# 18. Protected restrictions remain intact
# --------------------------------------------------------------------------- #
def test_18_protected_splits_are_never_used_by_this_phase(tmp_path):
    # the evaluator refuses a protected split at provenance construction
    with pytest.raises(PROV.ProvenanceError):
        PROV.build_evaluation_provenance(
            model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_TEST,
            adapter_identity={"model_key": REG.BASELINES[0], "seed": 42,
                              "adapter_kind": "PLAIN",
                              "checkpoint_sha256": "SYNTHETIC::probe"},
            evidence_class=P.SYNTHETIC_EVIDENCE, split_manifest_sha256="0" * 64,
            n_images=1, evaluation_configuration=PROV.evaluation_config(),
            synthetic=True, training_performed=False)

    # and no Phase D source file references a protected split or a trust store
    package = Path(__file__).resolve().parents[1] / "src" / "research" / "performance"
    forbidden = ("SPLIT_TEST", "ROUTER_HOLDOUT", "InstitutionalC1Trust")
    for path in sorted(package.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} references {token}"
