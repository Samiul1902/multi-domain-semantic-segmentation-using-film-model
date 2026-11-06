"""One-off task-owned updater for the final four-phase coding verification.

Preserves the exact CRLF / indent=2 / ensure_ascii=False serialization of the
original file. No original historical status or title entry is modified.
"""
import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
PATH = ROOT / "reports" / "audits" / "code_completion_matrix.json"

data = json.loads(PATH.read_text(encoding="utf-8"))
rows = {r["phase"]: r for r in data["rows"]}

BASELINE = "48ea5ba179d4038a4ddd3ebb272ef8aaeaccb2a4"
FOCUSED = ("PYTHONPATH='D:\\Softfors\\jup\\.venv\\Lib\\site-packages' "
           "/c/WINDOWS/py.exe -3.11-64 -S -m pytest "
           "tests/test_phase22_scale_regional_synthetic.py "
           "tests/test_phase39_single_pass_synthetic.py "
           "tests/test_phase41_packaging_synthetic.py "
           "tests/test_phase42_parity_synthetic.py "
           "tests/test_single_pass_transaction.py "
           "tests/test_deployment_artifacts.py "
           "tests/test_late_phase_synthetic.py -q")

# --------------------------------------------------------------------------- #
# Phase 22 — Task 1
# --------------------------------------------------------------------------- #
r = rows["22"]
r["relevant_tests"] = ["tests/test_phase22_scale_regional_synthetic.py"]
r["coding_status"] = "CODE_COMPLETE_SYNTHETIC_VERIFIED"
r["remaining_verification"] = (
    "No genuine real-data scale/regional/resource experiment executed; only "
    "deterministic synthetic coding verification of the frozen primitives")
r["software_implemented"] = "IMPLEMENTED"
r["synthetic_verification_passed"] = True
r["synthetic_verification_evidence"] = (
    "14 deterministic synthetic tests: aspect-preserving resize/pad inversion, "
    "boundary threshold rule, ROI geometry clipping/square-padding edge cases, "
    "MAC scaling, Gini, safe correlation, paired domain-stratified bootstrap, "
    "macro-domain Dice, TEST-path guard. Frozen source SHA-256 of "
    "phase22_common.py and phase22_scale.py matches the historical "
    "phase22_no_new_training_audit.json pins byte-for-byte. No new real-data finding.")
r["original_phase_gate_passed"] = False
r["original_phase_gate_status"] = "PHASE22_REAL_DATA_DIAGNOSTIC_NOT_EXECUTED__NOT_STARTED_HISTORICAL"
r["real_research_experiment_status"] = "PENDING"
r["external_authorization_status"] = "NOT_REQUIRED_FOR_SYNTHETIC_CODING_VERIFICATION"
r["defects_repaired"] = []
r["known_non_blocking_limitations"] = [
    "paired_domain_stratified_bootstrap(n_boot=0) raises an unhelpful IndexError; "
    "n_boot=0 is not a valid input and the source is SHA-pinned by a frozen audit, "
    "so the file was deliberately NOT modified (no functional impact for valid inputs)",
]

# --------------------------------------------------------------------------- #
# Phase 39 — Task 2
# --------------------------------------------------------------------------- #
r = rows["39"]
r["relevant_tests"] = [
    "tests/test_late_phase_synthetic.py",
    "tests/test_single_pass_transaction.py",
    "tests/test_phase39_single_pass_synthetic.py",
]
r["coding_status"] = "CODE_COMPLETE_SYNTHETIC_VERIFIED"
r["remaining_verification"] = (
    "New single_pass.run_once is synthetic-verified; not bound into a new "
    "authorized Phase39 release. The protected one-shot TEST evaluation is NOT executed.")
r["software_implemented"] = "IMPLEMENTED"
r["synthetic_verification_passed"] = True
r["synthetic_verification_evidence"] = (
    "21 deterministic synthetic tests: exactly-once evaluation, frozen population "
    "identity, checkpoint-family SHA binding with no silent fallback, "
    "authorization refusal before output/reader, no test-time tuning surface, "
    "atomic publication with per_sample_sha256 binding, interrupted-attempt "
    "consumption, duplicate refusal, audit-record integrity and fail-closed "
    "malformed-input handling. Protected v1.2 preflight exercised only with a "
    "redirected synthetic ROOT. TEST1683 never accessed.")
r["original_phase_gate_passed"] = False
r["original_phase_gate_status"] = "PHASE39_ONE_SHOT_PROTECTED_TEST_NOT_AUTHORIZED_NOT_EXECUTED"
r["real_test_evaluation_status"] = "REAL_TEST_EVALUATION_NOT_EXECUTED"
r["real_research_experiment_status"] = "PENDING"
r["external_authorization_status"] = "EXTERNAL_AUTHORIZATION_REQUIRED"
r["defects_repaired"] = []

# --------------------------------------------------------------------------- #
# Phase 41 — Task 3
# --------------------------------------------------------------------------- #
r = rows["41"]
r["relevant_tests"] = [
    "tests/test_deployment_artifacts.py",
    "tests/test_full_pipeline.py",
    "tests/test_phase41_packaging_synthetic.py",
]
r["coding_status"] = "CODE_COMPLETE_SYNTHETIC_VERIFIED"
r["remaining_verification"] = (
    "No genuine deployment artifact published: a valid trained checkpoint is "
    "required and none exists. Historical Phase26 single-channel design vs RGB "
    "source reconciliation is not authorized.")
r["software_implemented"] = "IMPLEMENTED"
r["synthetic_verification_passed"] = True
r["synthetic_verification_evidence"] = (
    "31 deterministic synthetic tests over byte-only G/R/B/S families: "
    "write-once byte-preserving packaging, model identity, frozen config/dependency "
    "record binding, preprocessing identity, five corruption modes, package "
    "loading, registry/rollback/monitor lifecycle, architecture compatibility and "
    "incompatible family/schema/authority rejection. Every emitted manifest has "
    "deployment_authorized=false and evidence_class=SYNTHETIC_TEST_ONLY.")
r["original_phase_gate_passed"] = False
r["original_phase_gate_status"] = (
    "GENUINE_DEPLOYMENT_ARTIFACT_REQUIRES_VALID_TRAINED_CHECKPOINT__NOT_PRODUCED")
r["real_research_experiment_status"] = "PENDING"
r["external_authorization_status"] = "EXTERNAL_AUTHORIZATION_REQUIRED"
r["defects_repaired"] = []
r["design_note"] = (
    "Trust in the expected manifest digest is explicitly delegated to the caller "
    "and held write-once in the release registry; dependencies are bound by the "
    "manifest SHA-256 (name==version strings), not by per-file dependency hashes.")

# --------------------------------------------------------------------------- #
# Phase 42 — Task 4
# --------------------------------------------------------------------------- #
r = rows["42"]
r["relevant_tests"] = [
    "tests/test_deployment_artifacts.py",
    "tests/test_full_pipeline.py",
    "tests/test_phase42_parity_synthetic.py",
]
r["coding_status"] = "CODE_COMPLETE_SYNTHETIC_VERIFIED"
r["remaining_verification"] = (
    "Real packaged deployment validation against real data is NOT executed; no "
    "real segmentation accuracy is claimed.")
r["software_implemented"] = "IMPLEMENTED"
r["synthetic_verification_passed"] = True
r["synthetic_verification_evidence"] = (
    "8 deterministic synthetic tests comparing direct vs package-loaded inference "
    "across output shapes, probability maps, binary masks, task conditioning "
    "(tasks 0..3), routing decisions and safety decisions: BIT_EXACT on all "
    "controls. Incompatible synthetic family is rejected. No real accuracy "
    "metric is produced.")
r["original_phase_gate_passed"] = False
r["original_phase_gate_status"] = "REAL_PACKAGED_DEPLOYMENT_VALIDATION_NOT_EXECUTED"
r["real_research_experiment_status"] = "PENDING"
r["external_authorization_status"] = "EXTERNAL_AUTHORIZATION_REQUIRED"
r["defects_repaired"] = []
r["exact_equality_finding"] = (
    "NOT GUARANTEED IN GENERAL. assert_exact uses torch.equal / np.array_equal "
    "with ZERO numerical tolerance (no allclose/isclose/atol/rtol). Exact equality "
    "is REQUIRED, and holds for this synthetic batch only because both arms share "
    "identical weights, dtype, device and deterministic execution. "
    "FullPackageRuntime reuses canonical FamilyBundle.load + build_gtfree rather "
    "than reimplementing inference. Any precision divergence (CPU vs CUDA, "
    "TF32/AMP, float16 serialisation, differing reduction order) is REJECTED "
    "with ArtifactError rather than quantified; a 1e-6 perturbation and a "
    "float16 round-trip are both demonstrated to be rejected. "
    "validate_control_batch labels success BIT_EXACT unconditionally: this is an "
    "observation on the observed control batch, not a guarantee.")

# --------------------------------------------------------------------------- #
# Phase 35 / 36 — Task 5: read-only frozen gate review, no classification change
# --------------------------------------------------------------------------- #
rows["35"]["frozen_gate_review"] = {
    "reviewed_without_reopening": True,
    "generic_synthetic_unit_tests_are_not_the_frozen_smoke": True,
    "frozen_smoke_status": (
        "EXECUTED: phase35_synthetic_smoke_terminal_v1_0h.json records "
        "terminal_state=COMPLETE, smoke_success=true, all_pass=true; "
        "v1_0h3 terminal records 1 canonical captured smoke invocation plus "
        "2 disclosed additional diagnostic invocations, failed_invocations=0."),
    "scientific_execution_status": (
        "NOT STARTED: phase35_v1_0h3_terminal.json records "
        "phase35_scientific_execution_started=false, invocations=0, "
        "phase35_execute_env_set=false; eligibility adjudication requires "
        "explicit supervisor authorization and does NOT self-grant it."),
    "pending_execution": "PHASE35_SCIENTIFIC_INTERPRETABILITY_EXECUTION",
    "coding_classification_note": (
        "CODE_COMPLETE_VERIFIED is a coding/software classification only. It does "
        "NOT assert that the original phase-specific scientific gate has passed."),
}

rows["36"]["frozen_gate_review"] = {
    "reviewed_without_reopening": True,
    "generic_synthetic_unit_tests_are_not_the_frozen_smoke": True,
    "frozen_smoke_status": (
        "PARTIAL / WAIVED FOR CURRENT REVISION: the original v1.14 frozen "
        "synthetic smoke was EXECUTED (CONSUMED_SUCCESS 53/53 per "
        "PHASE36_CURRENT_FILE_INDEX.md) and its on-disk byte SHA-256 still "
        "matches the v1.23 science-release attestation. NO v1.20-v1.23 frozen "
        "smoke artifact exists; phase36_v1_23_science_release_attestation.json "
        "explicitly sets requires_v1_23_smoke=false and binds the v1.14 smoke as "
        "HISTORICAL_RUNTIME_SMOKE_EVIDENCE_ONLY. The current-revision frozen "
        "smoke is therefore WAIVED BY ATTESTATION, NOT EXECUTED."),
    "scientific_execution_status": (
        "v1.22 science CONSUMED/FAILED (D97 AttributeError in stage-5 summary, "
        "artifact preserved, no retry); v1.23 science EXECUTED AND COMPLETED "
        "(child_exit_code=0, RESULT_present=true, FAILURE_present=false, "
        "evidence_class=DEVELOPMENT_SET_SYNTHETIC_PERTURBATION_ROBUSTNESS_EVIDENCE). "
        "The ELIGIBLE_NOT_STARTED eligibility file is a pre-execution snapshot."),
    "pending_execution": (
        "CURRENT_REVISION_FROZEN_SMOKE_WAIVED_NOT_EXECUTED; Phase37 NOT_STARTED; "
        "TEST remains PHASE39-only"),
    "coding_classification_note": (
        "CODE_COMPLETE_VERIFIED is a coding/software classification only. It does "
        "NOT assert that a current-revision frozen smoke was executed."),
}

# --------------------------------------------------------------------------- #
# New test-module observations (additive)
# --------------------------------------------------------------------------- #
for module in (
    "tests/test_phase22_scale_regional_synthetic.py",
    "tests/test_phase39_single_pass_synthetic.py",
    "tests/test_phase41_packaging_synthetic.py",
    "tests/test_phase42_parity_synthetic.py",
):
    data["test_module_observations"][module] = ["passed"]

# --------------------------------------------------------------------------- #
# Top-level verification record
# --------------------------------------------------------------------------- #
data["final_four_phase_verification"] = {
    "scope": "Phases 22, 39, 41, 42 synthetic coding verification; no phase advancement",
    "baseline_commit": BASELINE,
    "status_separation": [
        "software_implemented",
        "synthetic_verification_passed",
        "original_phase_gate_passed",
        "real_research_experiment_pending",
        "external_authorization_pending",
    ],
    "focused_test_command": FOCUSED,
    "focused_test_result": "120 passed in 13.35s",
    "focused_test_exit_code": 0,
    "new_test_modules": [
        "tests/test_phase22_scale_regional_synthetic.py",
        "tests/test_phase39_single_pass_synthetic.py",
        "tests/test_phase41_packaging_synthetic.py",
        "tests/test_phase42_parity_synthetic.py",
    ],
    "interpreter_disclosure": (
        "The canonical venv interpreter D:\\Softfors\\jup\\.venv\\Scripts\\python.exe "
        "segfaults on ANY code execution in this session (exit 139 / 0xC0000005); "
        "python --version still works, and the base 64-bit 3.11, 3.14 and node.exe "
        "also fail while 32-bit 3.11 works. Verbose init halts after 'winreg'. "
        "Tests were therefore executed through C:\\Windows\\py.exe -3.11-64 with "
        "-S isolation and PYTHONPATH bound to the venv site-packages "
        "(torch 2.6.0+cu124, numpy 2.4.6, pytest 9.1.1). sys.prefix is the BASE "
        "interpreter, NOT the venv; the Phase39 v1.2 interpreter-is-canonical-venv "
        "check consequently fails closed, which was verified. This deviation is "
        "disclosed rather than hidden."),
    "host_clock_caveat": (
        "Host clock is not synchronised (Leap Indicator 3, Local CMOS); no new "
        "absolute timestamp is authored in this record."),
    "no_real_training": True,
    "no_protected_evaluation": True,
    "TEST1683_accessed": False,
    "real_data_findings_produced": False,
    "genuine_deployment_artifact_published": False,
    "defects_repaired": [],
    "coding_closure_declaration": (
        "RA_MEDFILM_BARR_00_43_CODING_CLOSED__SYNTHETIC_VERIFICATION_COMPLETE__"
        "REAL_SCIENTIFIC_EXECUTION_PENDING"),
    "scientific_phases_passed": False,
}

out = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").replace("\n", "\r\n").encode("utf-8")
PATH.write_bytes(out)
print("WROTE", PATH, "bytes", len(out))
print("STATUS_COUNTS", {s: sum(1 for x in data["rows"] if x["coding_status"] == s)
                        for s in sorted({x["coding_status"] for x in data["rows"]})})
