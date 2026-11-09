"""V8 Task B — one source-linked results registry + four provenance CSVs.

Run:  .venv/Scripts/python.exe full_doc_report/v8_build/v8_registry.py

Reads only frozen / previously verified artifacts.  No training, no inference,
no protected TEST1683 access, no fabricated measurements.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v8_common import (  # noqa: E402
    FDR, ROOT, SRC, read_csv, rel, sha256, write_csv, write_json,
)

# --------------------------------------------------------------------------- #
# canonical identity / configuration (read from disk, never hardcoded results)
# --------------------------------------------------------------------------- #
COMP = json.loads(SRC["components"].read_text(encoding="utf-8"))
COMPONENTS = COMP["components"]
CKPT = {c["symbol"]: c["checkpoint_sha256"] for c in COMPONENTS}
CKPT_ALL = ";".join(f"{k}={v[:12]}" for k, v in CKPT.items())
CKPT_G = f"G={CKPT['G'][:12]}"

sys.path.insert(0, str(ROOT))
from src.models.barr.ra_medfilm_barr import (  # noqa: E402
    ROI_EXPANSION, ROI_PROPOSAL_THRESHOLD, SEGMENTATION_OUTPUT_THRESHOLD,
    SOMEGA_ACCEPT_THRESHOLD, STATES, TAU_C8_FINAL_FLOAT,
)

CONFIG_FULL = (
    f"seed=42; tau_C8={TAU_C8_FINAL_FLOAT!r}; ROI>={ROI_PROPOSAL_THRESHOLD}; "
    f"ROI_expansion={ROI_EXPANSION}; S_omega_accept>={SOMEGA_ACCEPT_THRESHOLD}; "
    f"mask>={SEGMENTATION_OUTPUT_THRESHOLD}; frozen staged modules; no joint optimisation"
)
CONFIG_G = "seed=42; single shared task-conditioned backbone; mask>=0.50; no BARR modules"

DICE_DEF = "per-image Dice = 2|A∩B|/(|A|+|B|) on 512x512 binary masks at threshold 0.50"
IOU_DEF = "per-image intersection over union on binary masks at threshold 0.50"
HD95_DEF = "95th-percentile symmetric surface distance in pixels (undefined when either surface is empty)"
MACRO_AGG = "equal-weight mean of the four per-domain means (domain-stratified, not pooled)"

REGISTRY_FIELDS = [
    "metric_id", "metric", "value", "unit", "model_identity", "active_components",
    "population", "split", "domain", "n", "run_id", "seed", "checkpoint_sha256",
    "config", "metric_definition", "aggregation", "source_path", "source_sha256",
    "evidence_class", "verification",
]

METRICS: list[dict] = []
_sha_cache: dict[str, str] = {}


def source_sha(key: str) -> str:
    p = SRC[key]
    s = str(p)
    if s not in _sha_cache:
        _sha_cache[s] = sha256(p) if p.exists() else "SOURCE_MISSING"
    return _sha_cache[s]


def mk(mid, metric, value, *, model="ReMedFiLM FULL", components="G + R_psi + B_phi + S_omega",
       population="VAL808", split="VAL", domain="MACRO_DOMAIN_EQUAL_WEIGHT", n=808,
       run_id="phase27_preservation_seed42", seed=42, ckpt=CKPT_ALL, config=CONFIG_FULL,
       definition=DICE_DEF, aggregation=MACRO_AGG, source="val808",
       evidence="DERIVED_FROM_SAVED_PREDICTIONS", verification="RECOMPUTED_FROM_MASKS"):
    sp = rel(SRC[source])
    METRICS.append({
        "metric_id": mid, "metric": metric, "value": value,
        "unit": {"Dice": "ratio", "IoU": "ratio", "Precision": "ratio", "Recall": "ratio",
                 "HD95_px": "pixel", "ASSD_px": "pixel"}.get(metric, "count/ratio"),
        "model_identity": model, "active_components": components,
        "population": population, "split": split, "domain": domain, "n": n,
        "run_id": run_id, "seed": seed, "checkpoint_sha256": ckpt, "config": config,
        "metric_definition": definition, "aggregation": aggregation,
        "source_path": sp, "source_sha256": source_sha(source),
        "evidence_class": evidence, "verification": verification,
    })


# --------------------------------------------------------------------------- #
# 1. INTERNAL VAL808 — canonical re-scored masks
# --------------------------------------------------------------------------- #
VAL = read_csv(SRC["val808"])
DOMAIN_N = {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280}

for row in VAL:
    dom = row["domain"]
    n = int(row["n"])
    D = dom if dom in DOMAIN_N else "MACRO_DOMAIN_EQUAL_WEIGHT"
    agg = "mean over images within one domain" if dom in DOMAIN_N else MACRO_AGG
    p = "INT_" + dom
    mk(f"{p}_G_DICE", "Dice", row["global_dice"], model="GlobalMedFiLM",
       components="G", domain=D, n=n, ckpt=CKPT_G, config=CONFIG_G,
       aggregation=agg, evidence="FROZEN_BACKBONE_REFERENCE",
       verification="RECOMPUTED_FROM_MASKS")
    mk(f"{p}_FULL_DICE", "Dice", row["full_dice"], domain=D, n=n,
       aggregation=agg, evidence="PAIRED_PRESERVATION_EVIDENCE",
       verification="RECOMPUTED_FROM_MASKS")
    mk(f"{p}_PAIRED_DELTA_DICE", "Dice", row["delta_dice"],
       model="ReMedFiLM FULL minus GlobalMedFiLM", domain=D, n=n,
       definition="paired per-image Dice difference, FULL - G", aggregation=agg,
       evidence="PAIRED_PRESERVATION_EVIDENCE", verification="RECOMPUTED_FROM_MASKS")
    for col, metric, definition in (
        ("full_iou", "IoU", IOU_DEF),
        ("full_precision", "Precision", "per-image TP/(TP+FP) at threshold 0.50"),
        ("full_recall", "Recall", "per-image TP/(TP+FN) at threshold 0.50"),
        ("full_hd95_px", "HD95_px", HD95_DEF),
    ):
        mk(f"{p}_FULL_{metric.upper()}", metric, row[col], domain=D, n=n,
           definition=definition, aggregation=agg, evidence="PAIRED_PRESERVATION_EVIDENCE",
           verification="RECOMPUTED_FROM_MASKS")
    for col, label in (("n_harmful", "HARMFUL"), ("n_beneficial", "BENEFICIAL"),
                       ("n_unchanged", "UNCHANGED")):
        mk(f"{p}_{label}", "case_count", row[col], domain=D, n=n,
           model="ReMedFiLM FULL vs GlobalMedFiLM", definition=f"cases with {label.lower()} paired Dice change",
           aggregation="count", evidence="PAIRED_PRESERVATION_EVIDENCE",
           verification="RECOMPUTED_FROM_MASKS")

PAIRED = json.loads(SRC["paired_delta"].read_text(encoding="utf-8"))
for mid, metric, value in (
    ("INT_MACRO_DELTA_POINT", "paired_delta_dice", PAIRED["point"]),
    ("INT_MACRO_DELTA_CI_LOW", "paired_delta_dice_ci_low", PAIRED["ci_low"]),
    ("INT_MACRO_DELTA_CI_HIGH", "paired_delta_dice_ci_high", PAIRED["ci_high"]),
):
    mk(mid, metric, value, model="ReMedFiLM FULL minus GlobalMedFiLM",
       run_id="domain_stratified_bootstrap_seed20261027", seed=20261027,
       definition="paired macro Dice delta, 10,000-replicate domain-stratified percentile bootstrap",
       aggregation="percentile bootstrap CI over images", source="paired_delta",
       evidence="DERIVED_BOOTSTRAP", verification="REPRODUCIBLE_FROM_PER_SAMPLE_CSV")

# six-model baseline comparison (frozen Phase 21; FULL comes from canonical table only)
for row in read_csv(SRC["six_model"]):
    key = row["model_key"]
    mk(f"BASE_{key.upper()}_MACRO_DICE", "Dice", row["macro_domain_dice"],
       model=row["display_name"], components=("G" if key == "global_medfilm" else "baseline network"),
       run_id=f"phase{row['phase']}_{key}", seed=42,
       ckpt=(CKPT_G if key == "global_medfilm" else "NOT_APPLICABLE_BASELINE"),
       config=(CONFIG_G if key == "global_medfilm" else "frozen Phase 20/21 baseline, mask>=0.50"),
       aggregation=MACRO_AGG, source="six_model",
       evidence="FROZEN_HISTORICAL_BENCHMARK", verification="READ_FROM_FROZEN_CSV")

# frozen routing counts
ROUTING = read_csv(SRC["routing"])
branch = Counter(r["state_machine_branch"] for r in ROUTING)
decision = Counter(r["router_decision"] for r in ROUTING)
ROUTING_COUNTS = {"n": len(ROUTING), "branches": dict(branch), "decisions": dict(decision)}
for k, v in sorted({**{f"BRANCH_{a}": b for a, b in branch.items()},
                    **{f"DECISION_{a}": b for a, b in decision.items()}}.items()):
    mk(f"ROUTE_{k}", "case_count", v, definition=f"number of VAL808 cases with {k}",
       aggregation="count", source="routing", evidence="FROZEN_STATE_MACHINE_LOG",
       verification="READ_FROM_FROZEN_CSV")

# efficiency
for row in read_csv(SRC["efficiency"]):
    if row["model"] not in ("GlobalMedFiLM (G)", "ReMedFiLM (FULL)"):
        continue
    is_full = "FULL" in row["model"]
    for metric, col in (("parameters", "params"), ("gmacs", "gmacs")):
        if not row[col]:
            continue
        mk(f"EFF_{'FULL' if is_full else 'G'}_{metric.upper()}", metric, row[col],
           model=row["model"], components=("G + R_psi + B_phi + S_omega" if is_full else "G"),
           definition=("count of trainable parameters" if metric == "parameters"
                       else f"analytical compute, {row['gmacs_semantics']}"),
           aggregation="analytical sum", source="efficiency",
           evidence=row["gmacs_semantics"] if metric == "gmacs" else "VERIFIED_CHECKPOINT_COUNT",
           verification="READ_FROM_FROZEN_CSV")
    if row["latency_p50_ms"]:
        mk(f"EFF_{'FULL' if is_full else 'G'}_LATENCY_P50_MS", "latency_p50_ms",
           row["latency_p50_ms"], model=row["model"],
           definition="measured batch-1 forward-only p50 latency on RTX 3060 Ti",
           aggregation="median of measured repeats", source="efficiency",
           evidence=row["latency_p50_semantics"], verification="READ_FROM_FROZEN_CSV")

# --------------------------------------------------------------------------- #
# 2. EXTERNAL retrospective evaluation
# --------------------------------------------------------------------------- #
EXT = read_csv(SRC["external"])
for row in EXT:
    full = row["model"] == "ReMedFiLM FULL"
    mid = f"EXT_{row['cohort_key'].upper()}_{'FULL' if full else 'G'}_{row['metric'].upper()}"
    mk(mid, row["metric"], row["mean"],
       model=row["model"], components=("G + R_psi + B_phi + S_omega" if full else "G"),
       population=f"EXTERNAL_{row['cohort_key'].upper()}", split="EXTERNAL_RETROSPECTIVE",
       domain=row["domain_analogue"], n=int(row["n_defined"]),
       run_id="c1_external_stress_retrospective", seed="NOT_APPLICABLE_SAVED_PREDICTIONS",
       ckpt="NOT_RECORDED_FOR_EXTERNAL_RUN", config="retrospective saved predictions; no retraining",
       definition={"Dice": DICE_DEF, "IoU": IOU_DEF, "HD95_px": HD95_DEF,
                   "ASSD_px": "average symmetric surface distance in pixels"}.get(
                       row["metric"], f"per-case {row['metric']} at threshold 0.50"),
       aggregation=("macro over cases (equal case weight); n_defined excludes undefined cases"),
       source="external", evidence="EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS",
       verification="READ_FROM_FROZEN_CSV")
    # explicit denominators as separate registry rows
    METRICS[-1]["n_total"] = row["n_total"]
    METRICS[-1]["ci_low"] = row["ci_low"]
    METRICS[-1]["ci_high"] = row["ci_high"]

for row in read_csv(SRC["stones_sub"]):
    if row["metric"] not in ("Dice", "empty_prediction_rate"):
        continue
    arm = "FULL" if row["arm"] == "barr" else "G"
    mk(f"EXT_STONES_{row['subgroup'].upper()}_{arm}_{row['metric'].upper()}",
       row["metric"], (row["mean"] or "NOT_RECORDED"),
       model=("ReMedFiLM FULL" if arm == "FULL" else "GlobalMedFiLM"),
       population="EXTERNAL_STONES_SUBGROUP", split="EXTERNAL_RETROSPECTIVE",
       domain="KUB_NEGATIVE_CONTROL", n=int(row["n_defined"]),
       run_id="c1_external_stress_stones_subgroups", seed="NOT_APPLICABLE_SAVED_PREDICTIONS",
       definition=("false-positive foreground on a study with no reference lesion"
                   if row["metric"] == "empty_prediction_rate" else DICE_DEF),
       aggregation="macro over cases (equal case weight)", source="stones_sub",
       evidence=("MATERIAL_FAILURE_NEGATIVE_CONTROL" if row["subgroup"] == "fourteen_absent"
                 else "EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS"),
       verification="READ_FROM_FROZEN_CSV")

# --------------------------------------------------------------------------- #
# 3. ABLATION / PROGRESSION
# --------------------------------------------------------------------------- #
ABL = read_csv(SRC["ablation"])
for row in ABL:
    if row["record_type"] == "Audit gate":
        continue
    tag = row["arm_or_stage"].replace(" ", "_").upper()
    pop = row["population"] or "MULTI_POPULATION_AUDIT"
    for col, metric in (("n_routed", "routed_cases"), ("routed_fraction", "routed_fraction"),
                        ("accepted_fraction", "accepted_fraction"),
                        ("mean_delta_dice", "mean_delta_dice"),
                        ("harmful_share", "harmful_share"),
                        ("benefit_capture", "benefit_capture"),
                        ("gmacs", "gmacs"), ("ci_low", "ci_low"), ("ci_high", "ci_high"),
                        ("ci_excludes_zero", "ci_excludes_zero")):
        v = row.get(col, "")
        if v == "":
            continue
        mk(f"ABL_{tag}_{metric.upper()}", metric, v,
           model=row["name"] or f"ablation arm {row['arm_or_stage']}",
           components=row["active_components"] or "NOT_RECORDED",
           population=pop, split=("VAL" if pop == "VAL808" else "ROUTER_DEV"),
           domain="ALL_FOUR_DOMAINS", n=int(row["n"] or 0),
           run_id=("phase28_ablation_matrix" if row["record_type"] == "ABLATION"
                   else "phase25_to_phase27_progression"),
           seed=42, ckpt=("NOT_RECORDED_PER_ARM" if row["record_type"] == "ABLATION" else CKPT_ALL),
           config="frozen Phase 28 arm definitions on ROUTER_DEVELOPMENT_4957",
           definition=f"Phase 28 / progression field `{col}`",
           aggregation="per-arm aggregate over ROUTER_DEVELOPMENT_4957",
           source="ablation", evidence=row["evidence_class"],
           verification="READ_FROM_FROZEN_CSV")

# --------------------------------------------------------------------------- #
# 4. TRAINING HISTORY
# --------------------------------------------------------------------------- #
HIST = read_csv(SRC["history"])
HIST_ROWS = []
for r in HIST:
    component = r["component"]
    identity = {
        "GlobalMedFiLM (G)": "GlobalMedFiLM",
        "R_psi (Regional Refiner)": "R_psi",
        "B_phi (Benefit Router)": "B_phi",
        "S_omega (Post-Safety Gate)": "S_omega",
        "F1 (Ablation Variant)": "F1 ablation variant",
    }.get(component, component)
    src_path = r["source_path"]
    abs_src = ROOT / src_path
    HIST_ROWS.append({
        "run_id": r["experiment_id"], "model_identity": identity, "component": component,
        "seed": r["seed"], "epoch": r["epoch"], "metric": r["metric_name"],
        "value": r["metric_value"], "best_epoch": r["best_epoch"],
        "population": ("VAL808 + TRAIN5832" if identity == "GlobalMedFiLM"
                       else "ROUTER_DEVELOPMENT_4957"),
        "split": "TRAIN/VAL_HISTORY_LOG", "n": "NOT_APPLICABLE_EPOCH_LOG",
        "aggregation": "logged value at one epoch (not a cross-run aggregate)",
        "metric_definition": r["metric_name"],
        "source_path": src_path,
        "source_exists": abs_src.exists(),
        "evidence_class": r["evidence_status"],
        "checkpoint_sha256": "NOT_RECORDED_FOR_EVERY_EPOCH",
        "verification": "GENUINE_HISTORICAL_LOG",
    })
    if component in ("GlobalMedFiLM (G)",) and r["metric_name"] == "val_macro_dice":
        mk(f"TRAIN_G_EPOCH{r['epoch']}_VAL_MACRO_DICE", "val_macro_dice", r["metric_value"],
           model="GlobalMedFiLM", components="G", population="VAL808", split="VAL",
           domain="MACRO_DOMAIN_EQUAL_WEIGHT", n=808, run_id=r["experiment_id"], seed=42,
           ckpt=CKPT_G, config=CONFIG_G, definition="logged validation macro-domain Dice at one epoch",
           aggregation="single epoch value", source="history",
           evidence="GENUINE_HISTORICAL_TRAINING", verification="READ_FROM_HISTORY_LOG")

# --------------------------------------------------------------------------- #
# 5. Emit
# --------------------------------------------------------------------------- #
# normalise optional columns to a stable superset for CSVs
for m in METRICS:
    for extra in ("n_total", "ci_low", "ci_high"):
        m.setdefault(extra, "")

source_manifest = []
for key, p in sorted(SRC.items()):
    source_manifest.append({
        "key": key, "path": rel(p), "exists": p.exists(),
        "bytes": p.stat().st_size if p.exists() else 0,
        "sha256": sha256(p) if p.exists() else "SOURCE_MISSING",
    })

REGISTRY = {
    "artifact": "REMEDFILM_V8_RESULTS_REGISTRY",
    "version": "V8",
    "purpose": "single source-linked registry consumed by every V8 figure, table and prose number",
    "canonical_model": {
        "name": "ReMedFiLM FULL (RA-MedFiLM-BARR)",
        "components": ["G = GlobalMedFiLM", "R_psi = BARRRegionalRefinerV1",
                       "B_phi = BARRBenefitRouterV1", "S_omega = BARRPostSafetyV1"],
        "verified_total_parameters": COMP["verified_total_parameters"],
        "all_components_verified": COMP["all_components_verified"],
        "assembly": COMP["assembly"],
        "checkpoint_sha256": CKPT,
    },
    "baseline_model": {"name": "GlobalMedFiLM", "role": "backbone and legitimate ablation baseline",
                       "parameters": next(c["measured_parameters"] for c in COMPONENTS if c["symbol"] == "G")},
    "canonical_result": {
        "population": "VAL808", "n": 808, "seed": 42,
        "full_macro_dice": next(r["full_dice"] for r in VAL
                                if r["domain"] == "MACRO_DOMAIN_EQUAL_WEIGHT"),
        "global_macro_dice": next(r["global_dice"] for r in VAL
                                  if r["domain"] == "MACRO_DOMAIN_EQUAL_WEIGHT"),
        "paired_delta_dice": PAIRED["point"],
        "paired_delta_ci_low": PAIRED["ci_low"],
        "paired_delta_ci_high": PAIRED["ci_high"],
        "evidence_class": "PAIRED_PRESERVATION_EVIDENCE__RESCORED_FROM_SAVED_MASKS",
    },
    "runtime_constants": {
        "tau_C8_final": TAU_C8_FINAL_FLOAT, "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
        "roi_expansion": ROI_EXPANSION, "s_omega_accept_threshold": SOMEGA_ACCEPT_THRESHOLD,
        "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
        "states": list(STATES),
    },
    "routing_val808": ROUTING_COUNTS,
    "domain_counts": DOMAIN_N,
    "populations": {
        "TRAIN": 5832, "VAL808": 808, "TEST1683": "PROTECTED__NOT_OPENED",
        "ROUTER_DEVELOPMENT_4957": 4957, "ROUTER_HOLDOUT_875": 875,
        "EXTERNAL884": {"CVC-ClinicDB": 612, "BrEaST-Lesions-USG": 252,
                        "Stones_where_are_you": 20},
    },
    "source_manifest": source_manifest,
    "metric_count": len(METRICS),
    "metrics": METRICS,
    "excluded_sources": [
        {"path": "full_doc_report/tables/REMEDFILM_MODEL_COMPARISON.csv",
         "reason": "ReMedFiLM FULL per-domain Dice cells are single-sample values, not domain means; "
                   "contradict the canonical re-scored mask table. V8 uses phase21_six_model_comparison.csv "
                   "for baselines and REMEDFILM_FULL_VAL808_METRICS.csv for FULL."},
        {"path": "full_doc_report/tables/subgroup_performance_summary.csv",
         "reason": "legacy V3-era table with macro 0.8379 / +0.28 pp, superseded by canonical re-score."},
        {"path": "full_doc_report/PROGRESSION_AND_PROPAGATION_EVIDENCE.csv",
         "reason": "Stage 4 records 0.837862 with routed 0.2265 / accepted 0.2042 / +0.2783 pp / harm 0.1878; "
                   "all conflict with the frozen VAL808 state machine (0.3453 / 0.3292 / +0.2210 pp / 0.1200)."},
        {"path": "full_doc_report/tables/ReMedFiLM_External_Routing_Safety_V7.csv",
         "reason": "V7-era external routing counts conflict with the frozen c1_external_stress_* artifacts."},
        {"path": "scripts/analysis/build_v5_pdf_report.py, build_v6_pdf_report.py, build_v7_pdf_report.py",
         "reason": "hardcode 0.837862 / 0.837910 / 0.837815 and impossible 183/165/31 routing counts; "
                   "no frozen artifact supports them."},
    ],
    "declaration": ("No model was retrained, no new inference was run, no checkpoint was modified, "
                    "and the protected TEST1683 inputs were not opened while building this registry."),
}

out_registry = write_json(FDR / "REMEDFILM_V8_RESULTS_REGISTRY.json", REGISTRY)

# CSV 1 — internal
internal_cols = REGISTRY_FIELDS + ["n_total", "ci_low", "ci_high"]
internal = [m for m in METRICS if m["metric_id"].startswith(("INT_", "BASE_", "ROUTE_", "EFF_", "TRAIN_"))]
out_internal = write_csv(FDR / "REMEDFILM_V8_INTERNAL_EVALUATION.csv", internal, internal_cols)

# CSV 2 — external
external = [m for m in METRICS if m["metric_id"].startswith("EXT_")]
out_external = write_csv(FDR / "REMEDFILM_V8_EXTERNAL_EVALUATION.csv", external, internal_cols)

# CSV 3 — training history (full epoch-level provenance)
hist_cols = ["run_id", "model_identity", "component", "seed", "epoch", "metric", "value",
             "best_epoch", "population", "split", "n", "aggregation", "metric_definition",
             "source_path", "source_exists", "evidence_class", "checkpoint_sha256", "verification"]
out_hist = write_csv(FDR / "REMEDFILM_V8_TRAINING_HISTORY.csv", HIST_ROWS, hist_cols)

# CSV 4 — ablation / progression
ablation = [m for m in METRICS if m["metric_id"].startswith("ABL_")]
out_abl = write_csv(FDR / "REMEDFILM_V8_ABLATION_RESULTS.csv", ablation, internal_cols)

print("registry metrics:", len(METRICS))
print("  internal rows :", len(internal))
print("  external rows :", len(external))
print("  history rows  :", len(HIST_ROWS))
print("  ablation rows :", len(ablation))
print("routing VAL808  :", ROUTING_COUNTS)
for p in (out_registry, out_internal, out_external, out_hist, out_abl):
    print("  wrote", rel(p), p.stat().st_size, "bytes")
