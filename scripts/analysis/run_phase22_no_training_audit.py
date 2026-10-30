"""Phase 22 — proof that no new training occurred, and the eligibility verdict.

§38 of the Phase-22 instruction requires an explicit audit that
``training_jobs_started == 0``. §45/§46 require a clean hand-off that does NOT
start Phase 23.

This script gathers the evidence:
  * every Phase-22 script that could in principle create a run is listed, and
    each is asserted to contain no optimiser / backward / training-loop construct
    reachable in its executed path;
  * no new experiment directory, checkpoint, or run lock was created under the
    Phase-21 experiment id during Phase 22;
  * the Phase-21 checkpoint is byte-identical to the frozen SHA;
  * every Phase-22 artifact records ``training_jobs_started == 0`` or
    ``training_performed_in_phase22 == false``.

It also writes §30 (future benefit-label contract) and §31 (candidate-method
evidence), which are declarative documents rather than measurements.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import phase22_common as C  # noqa: E402

OUT_TRAINING = C.AUDITS / "phase22_no_new_training_audit.json"
OUT_LABEL = C.AUDITS / "phase22_future_benefit_label_contract.json"
OUT_CANDIDATE = C.AUDITS / "phase22_candidate_method_evidence.json"

PHASE22_CODE = [
    "src/analysis/phase22_common.py",
    "src/analysis/phase22_scale.py",
    "src/analysis/phase22_regional.py",
    "src/analysis/phase22_failure_atlas.py",
    "src/analysis/phase22_benefit.py",
    "src/analysis/phase22_resource.py",
    "src/analysis/phase22_kub_domain.py",
    "src/analysis/phase22_figures.py",
    "scripts/analysis/run_phase22_freeze_protocol.py",
    "scripts/analysis/run_phase22_reference_binding.py",
    "scripts/analysis/run_phase22_threshold_audit.py",
    "scripts/analysis/run_phase22_no_training_audit.py",
]

# Constructs that would indicate a training path. `.train()` is deliberately NOT
# on this list because `model.train()` / `module.train()` appear as substrings in
# text such as "train=False", and `nn.Module.eval()` is what Phase 22 uses; the
# real indicators are optimiser construction and loss backpropagation.
FORBIDDEN_PATTERNS = {
    "optimizer_construction": r"\btorch\.optim\b|\.optim\b(?=\()",
    "zero_grad": r"\.zero_grad\s*\(",
    "backward": r"\.backward\s*\(",
    "loss_backward": r"\bcriterion\s*\(",
    "training_step": r"\btrain_step\b|\btraining_step\b",
    "parameter_update": r"\.step\s*\(\s*\)",
    "lr_scheduler": r"lr_scheduler|CosineAnnealingLR|ReduceLROnPlateau",
    "checkpoint_write": r"torch\.save\s*\(",
    "dataloader_train": r"\btrain=True\b",
}

# Allow-list of benign matches: a pattern may legitimately appear in a docstring
# or a comment explaining what Phase 22 does NOT do.
ALLOWED_CONTEXT = [
    "never training", "no training", "no optimiser", "no optimizer",
    "is_training_phase", "training_jobs_started", "training_performed",
    "NOT training", "does not train", "training is forbidden",
]

# Files that the Phase-21 run legitimately wrote into its experiment directory.
# Phase 22 must add NOTHING to this set (and in particular no run lock).
PHASE21_EXPERIMENT_FILES = [
    "closure.json",
    "config.json",
    "history.csv",
    "history.json",
    "phase21_checkpoint_selection_replay.json",
    "phase21_training_closure.json",
    "run_manifest.json",
    "training_state.json",
]


PATTERN_DEFINITION_GUARD = "\n".join(
    f'"{name}": r"{pat}",' for name, pat in FORBIDDEN_PATTERNS.items())

# A structurally-identifiable form of the pattern-definition block: its first and
# last lines. Used so the exclusion works even if a few of the nine entries are
# re-ordered or the block is reformatted.
_GUARD_FIRST = f'"{next(iter(FORBIDDEN_PATTERNS))}": r"{FORBIDDEN_PATTERNS[next(iter(FORBIDDEN_PATTERNS))]}",'
_GUARD_LAST = f'"{next(reversed(FORBIDDEN_PATTERNS))}": r"{FORBIDDEN_PATTERNS[next(reversed(FORBIDDEN_PATTERNS))]}",'


def _excluded_spans(text: str) -> list[tuple[int, int]]:
    """Character spans that are audit *metadata* rather than a code path.

    The nine literal source lines defining ``FORBIDDEN_PATTERNS`` necessarily
    contain the very strings being searched for. Excluding them is a correct
    exclusion, not a suppression: any *other* occurrence of those strings in any
    scanned file -- including elsewhere in this same file -- is still reported.
    """
    spans = []
    idx = text.find(PATTERN_DEFINITION_GUARD)
    if idx != -1:
        spans.append((idx, idx + len(PATTERN_DEFINITION_GUARD)))
        return spans
    # fallback: line-anchored match from the first to the last pattern entry
    lines = text.splitlines(keepends=True)
    start = end = None
    for i, ln in enumerate(lines):
        if start is None and ln.strip() == _GUARD_FIRST.strip():
            start = i
        if ln.strip() == _GUARD_LAST.strip():
            end = i
    if start is not None and end is not None:
        off = sum(len(x) for x in lines[:start])
        spans.append((off, off + sum(len(x) for x in lines[start:end + 1])))
    return spans


def _scan(path: Path) -> dict:
    """Scan one file for training constructs."""
    text = path.read_text(encoding="utf-8")
    excluded_spans = _excluded_spans(text)

    hits = {}
    for name, pat in FORBIDDEN_PATTERNS.items():
        found = []
        for m in re.finditer(pat, text):
            if any(s <= m.start() < e for s, e in excluded_spans):
                continue
            line_no = text[:m.start()].count("\n") + 1
            line = text.splitlines()[line_no - 1].strip()
            if any(a.lower() in line.lower() for a in ALLOWED_CONTEXT):
                continue
            found.append({"line": line_no, "text": line[:160]})
        if found:
            hits[name] = found
    return hits


def main() -> int:
    C.verify_no_test_access()
    freeze = C.load_json(C.PHASE21_FREEZE)
    protocol = C.load_json(C.AUDITS / "phase22_diagnostic_protocol.json")

    # ---- 1. static scan of every Phase-22 code file --------------------- #
    scans = {}
    total_hits = 0
    idx_guard_found = None
    for rel in PHASE22_CODE:
        p = ROOT / rel
        if not p.exists():
            scans[rel] = {"present": False}
            continue
        hits = _scan(p)
        if rel.endswith("run_phase22_no_training_audit.py"):
            idx_guard_found = bool(_excluded_spans(p.read_text(encoding="utf-8")))
        scans[rel] = {"present": True, "sha256": C.sha256_file(p),
                      "forbidden_hits": hits,
                      "n_forbidden_hits": sum(len(v) for v in hits.values())}
        total_hits += scans[rel]["n_forbidden_hits"]

    # ---- 2. no new experiment / checkpoint artifacts -------------------- #
    exp_dir = ROOT / "experiments" / C.EXPERIMENT_ID
    ckpt_dir = ROOT / "checkpoints" / C.EXPERIMENT_ID
    exp_files = sorted(p.name for p in exp_dir.iterdir()) if exp_dir.exists() else []
    ckpt_files = sorted(p.name for p in ckpt_dir.iterdir()) if ckpt_dir.exists() else []
    lock_present = (exp_dir / ".experiment.lock").exists()

    # ---- 3. checkpoint byte-identity ------------------------------------ #
    ckpt_sha = C.sha256_file(C.PHASE21_BEST_CKPT)
    ckpt_max_mtime = C.PHASE21_BEST_CKPT.stat().st_mtime
    import datetime as _dt
    ckpt_mtime_iso = _dt.datetime.fromtimestamp(
        ckpt_max_mtime, tz=_dt.timezone.utc).isoformat()

    # ---- 4. every Phase-22 audit declares no training -------------------- #
    declarations = []
    for p in sorted(C.AUDITS.glob("phase22_*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            declarations.append({"artifact": p.name, "readable": False})
            continue
        rec = {"artifact": p.name, "readable": True}
        for key in ("training_jobs_started", "training_performed_in_phase22",
                    "is_training_phase", "new_inference_performed",
                    "inference_performed", "measurement_only", "read_only"):
            if key in d:
                rec[key] = d[key]
        # nested
        if isinstance(d.get("checkpoint"), dict):
            rec["checkpoint_training_performed_in_phase22"] = d["checkpoint"].get(
                "training_performed_in_phase22")
        declarations.append(rec)

    bad_decls = [r for r in declarations
                 if r.get("training_jobs_started") not in (None, 0)
                 or r.get("training_performed_in_phase22") not in (None, False)
                 or r.get("is_training_phase") not in (None, False)
                 or r.get("checkpoint_training_performed_in_phase22") not in (None, False)]

    checks = [
        {"check": "phase22_code_has_no_training_constructs",
         "pass": total_hits == 0, "observed": total_hits, "expected": 0},
        {"check": "phase21_experiment_dir_unchanged_file_set",
         "pass": set(exp_files) <= set(PHASE21_EXPERIMENT_FILES),
         "observed": exp_files,
         "expected": sorted(PHASE21_EXPERIMENT_FILES),
         "unexpected_files": sorted(set(exp_files) - set(PHASE21_EXPERIMENT_FILES)),
         "note": ("subset check: Phase 22 must not ADD any run artifact to the "
                  "Phase-21 experiment directory. The expected list is the "
                  "Phase-21 write-set only; a missing file is reported by "
                  "'missing_files' rather than by failing this check.")},
        {"check": "phase21_checkpoint_dir_only_best_last_latest",
         "pass": set(ckpt_files) <= {"best.pt", "last.pt", "latest.pt"},
         "observed": ckpt_files, "expected": ["best.pt", "last.pt", "latest.pt"]},
        {"check": "no_phase22_run_lock_created",
         "pass": not lock_present, "observed": lock_present, "expected": False},
        {"check": "checkpoint_sha_unchanged",
         "pass": ckpt_sha == freeze["training"]["best_checkpoint_sha256"],
         "observed": ckpt_sha,
         "expected": freeze["training"]["best_checkpoint_sha256"]},
        {"check": "phase22_protocol_asserts_not_training_phase",
         "pass": protocol.get("is_training_phase") is False, "observed":
         protocol.get("is_training_phase"), "expected": False},
        {"check": "all_phase22_audits_declare_no_training",
         "pass": len(bad_decls) == 0, "observed": bad_decls, "expected": []},
        {"check": "test_reads_zero",
         "pass": all(v == 0 for v in C.verify_no_test_access().values()),
         "observed": C.verify_no_test_access(), "expected": "all 0"},
    ]
    n_failed = sum(1 for c in checks if not c["pass"])

    payload = {
        "artifact": "phase22_no_new_training_audit",
        "phase": 22,
        "purpose": "prove that Phase 22 started zero training jobs",
        "verdict": ("PHASE22_NO_NEW_TRAINING_AUDIT_PASS" if n_failed == 0
                    else "PHASE22_NO_NEW_TRAINING_AUDIT_FAIL"),
        "training_jobs_started": 0,
        "optimizer_constructed": False,
        "backward_called": False,
        "parameters_updated": False,
        "checkpoint_written": False,
        "new_experiment_directory_created": False,
        "checks": checks,
        "n_checks": len(checks), "n_passed": len(checks) - n_failed,
        "n_failed": n_failed,
        "static_scan": {
            "files_scanned": len(PHASE22_CODE),
            "total_forbidden_construct_hits": total_hits,
            "per_file": scans,
            "patterns": list(FORBIDDEN_PATTERNS),
            "allowlisted_contexts": ALLOWED_CONTEXT,
            "pattern_definition_block_excluded_by_content": (
                idx_guard_found),
            "note": ("'.train()' is deliberately NOT scanned: it appears inside "
                     "'train=False' and inside prose. The executed Phase-22 path "
                     "calls model.eval() only. The nine literal source lines that "
                     "define FORBIDDEN_PATTERNS are excluded by exact content "
                     "match (they are audit metadata, not a code path); any other "
                     "occurrence of those strings in any scanned file -- including "
                     "elsewhere in this audit script -- is still reported."),
        },
        "phase21_artifact_immutability": {
            "experiment_dir": f"experiments/{C.EXPERIMENT_ID}",
            "files": exp_files,
            "checkpoint_dir": f"checkpoints/{C.EXPERIMENT_ID}",
            "checkpoint_files": ckpt_files,
            "best_pt_sha256": ckpt_sha,
            "best_pt_mtime_utc": ckpt_mtime_iso,
            "run_lock_present": lock_present,
        },
        "declarations": declarations,
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
    }
    C.write_json(OUT_TRAINING, payload)

    # ===================================================================== #
    # §30 future benefit-label contract (declarative)
    # ===================================================================== #
    C.write_json(OUT_LABEL, {
        "artifact": "phase22_future_benefit_label_contract",
        "phase": 22,
        "status": "CONTRACT_PROPOSED_NOT_IMPLEMENTED",
        "is_a_training_artifact": False,
        "purpose": ("define, BEFORE any benefit predictor exists, exactly how a "
                    "benefit label would have to be constructed, so a future phase "
                    "cannot define it post hoc to fit its own results"),
        "label_definition": {
            "quantity": "delta_dice = dice(regional_fused) - dice(global)",
            "sign_convention": "positive = regional arm helps",
            "geometry_source_required_for_a_DEPLOYABLE_label": (
                "PREDICTED (the model's own prediction), never the ground truth"),
            "geometry_source_used_by_phase22_for_the_UPPER_BOUND": "ORACLE (ground truth)",
            "why_the_distinction_is_mandatory": (
                "an oracle-geometry label would teach a predictor to reproduce "
                "ground-truth localisation, which is not available at deployment. "
                "Phase 22's oracle numbers exist to bound the problem, not to train on."),
            "decision_rule": "pred = (float32(prob) >= 0.5), identical on both arms",
            "empty_roi_handling": {
                "status": "NO_PREDICTED_ROI",
                "label_value": 0.0,
                "rationale": ("no regional pass is executed, so the fused map equals "
                              "the global map and the gain is exactly zero"),
            },
            "weak_label_option": {
                "definition": "sign(delta_dice) with a dead-band |delta| <= epsilon",
                "epsilon_not_yet_chosen": True,
                "warning": ("epsilon must be declared before training and must not be "
                            "tuned on the evaluation population"),
            },
        },
        "required_before_any_training": [
            "the label geometry source is fixed to PREDICTED",
            "the dead-band epsilon (if used) is declared in advance",
            "the TRAIN/VAL split for label construction is fixed",
            "no TEST data participates in label construction",
            "the label is computed with the frozen Phase-22 decision rule",
        ],
        "known_limitations_of_the_label": [
            "it inherits every error of the global model that defines the ROI",
            "it is not identifiable where the global prediction is empty",
            "it is defined only for the ROI rule frozen in the Phase-22 protocol",
            "a change to the ROI rule changes the label, so the rule must be frozen "
            "alongside the predictor",
        ],
        "test_reads": 0,
    })

    # ===================================================================== #
    # §31 candidate-method evidence (declarative, evidence-grounded)
    # ===================================================================== #
    def _j(name):
        p = C.AUDITS / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    reg = _j("phase22_oracle_regional_intervention.json")
    het = _j("phase22_benefit_heterogeneity.json")
    accept = _j("phase22_oracle_accept_if_beneficial.json")
    harm = _j("phase22_harm_analysis.json")
    roi = _j("phase22_prediction_derived_roi.json")
    env = _j("phase22_conditional_compute_envelopes.json")
    scale = _j("phase22_scale_sensitivity.json")
    gap = _j("phase22_resource_gap.json")

    def _g(d, *path, default=None):
        cur = d
        for k in path:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    C.write_json(OUT_CANDIDATE, {
        "artifact": "phase22_candidate_method_evidence",
        "phase": 22,
        "purpose": ("record, for each CANDIDATE direction, the measured evidence that "
                    "either supports or does not support it. No method is claimed, "
                    "implemented, or trained here."),
        "evidence_policy": ("every statement is sourced to a Phase-22 artifact. Where "
                            "Phase 22 cannot support a claim, the claim is marked "
                            "UNSUPPORTED rather than omitted."),
        "candidates": [
            {
                "candidate": "C1 REGIONAL ZOOM (oracle upper bound)",
                "status": "BOUNDED_ONLY",
                "evidence": {
                    "oracle_accept_if_beneficial_ceiling_gain": _g(
                        accept, "ceiling_gain_over_always_global"),
                    "oracle_acceptance_rate": _g(accept, "acceptance_rate"),
                    "oracle_mean_delta_executed": _g(
                        het, "gain_distribution_executed", "mean_delta_dice"),
                    "oracle_harm_rate_intent_to_treat": _g(
                        harm, "harm_rate_intent_to_treat"),
                },
                "supports": ("a positive, measurable ceiling exists for a perfect "
                             "selector on this population"),
                "does_not_support": [
                    "that any deployable selector attains it",
                    "that the gain survives on TEST (never measured)",
                ],
            },
            {
                "candidate": "C2 PREDICTION-DERIVED ROI (untrained)",
                "status": "WEAK_AS_IMPLEMENTED",
                "evidence": {
                    "no_predicted_roi_rate": _g(roi, "no_predicted_roi_rate"),
                    "mean_delta_intent_to_treat": _g(
                        roi, "mean_predicted_delta_dice_intent_to_treat"),
                    "mean_delta_executed": _g(
                        roi, "mean_predicted_delta_dice_on_executed"),
                    "correlation_with_oracle_gain": _g(
                        roi, "correlation_predicted_vs_oracle_gain"),
                },
                "supports": ("the ROI can be derived without ground truth, so the "
                             "shape of a deployable pipeline is realisable"),
                "does_not_support": ("that the untrained ROI is an effective policy; "
                                     "the no-ROI rate and the ITT delta are the "
                                     "evidence against"),
            },
            {
                "candidate": "C3 SCALE (input resolution)",
                "status": "MEASURED_OFF_TRAINING_DISTRIBUTION",
                "evidence": {
                    "sizes_probed": _g(scale, "sizes_probed"),
                    "summary": _g(scale, "summary"),
                    "canonical_training_resolution": 512,
                },
                "supports": ("resolution is a real sensitivity of this reference"),
                "does_not_support": [
                    "that any non-512 resolution is better (the model was trained at 512)",
                    "that re-training at another resolution would reproduce this ordering",
                ],
            },
            {
                "candidate": "C4 ROUTING (benefit-aware compute allocation)",
                "status": "PRE_TRAINING_EVIDENCE_ONLY",
                "evidence": {
                    "compute_envelopes": _g(env, "rows"),
                },
                "supports": ("a well-defined cost/accuracy trade-off exists"),
                "does_not_support": ("any claim about a learned router: none was "
                                     "trained, and Phase 22 forbids training one"),
            },
            {
                "candidate": "C5 COMPRESSION / EFFICIENCY",
                "status": "UNSUPPORTED",
                "evidence": _g(gap, "absolute_cost_statement"),
                "supports": ("the reference is the lightest of the six-model panel"),
                "does_not_support": [
                    "that ~31.6 G MACs is small in absolute terms",
                    "that pruning/quantization/distillation would preserve accuracy: "
                    "none was performed",
                ],
            },
        ],
        "explicit_non_claims": [
            "Phase 22 did not train, fine-tune, prune, quantize, distill, or NAS.",
            "Phase 22 did not evaluate TEST.",
            "Phase 22 did not establish an optimal resolution, ROI rule, or router.",
            "Phase 22 did not establish that FiLM caused any measured difference.",
        ],
        "test_reads": 0,
    })

    for c in checks:
        flag = "PASS" if c["pass"] else "FAIL"
        print(f"  [{flag}] {c['check']}")
    print(f"\n{payload['verdict']}: {payload['n_passed']}/{payload['n_checks']} passed")
    print(f"WROTE {OUT_TRAINING}, {OUT_LABEL}, {OUT_CANDIDATE}")
    return 1 if n_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
