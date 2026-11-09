"""Build the single V9 source-linked registry and the wide analysis CSVs."""
from __future__ import annotations
import csv, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
FDR = ROOT / "full_doc_report"
BUILD = FDR / "v9_build"
sys.path.insert(0, str(ROOT))

from src.models.barr.ra_medfilm_barr import (  # noqa: E402
    ROI_EXPANSION, ROI_PROPOSAL_THRESHOLD, SEGMENTATION_OUTPUT_THRESHOLD,
    SOMEGA_ACCEPT_THRESHOLD, TAU_C8_FINAL_FLOAT, STATES,
)

A = json.loads((BUILD / "v9_analysis.json").read_text(encoding="utf-8"))
COMP = json.loads((FDR / "REMEDFILM_FULL_COMPONENT_REGISTRY.json").read_text(encoding="utf-8"))
CKPT = {c["symbol"]: c["checkpoint_sha256"] for c in COMP["components"]}


def sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


SRC = {
    "internal": FDR / "tables" / "REMEDFILM_INTERNAL_PER_SAMPLE.csv",
    "paired": FDR / "tables" / "REMEDFILM_PAIRED_DELTA.json",
    "external": ROOT / "reports" / "tables" / "c1_external_stress_per_case.csv",
    "ablation_defs": ROOT / "reports" / "tables" / "phase28_table_01_arm_definitions.csv",
    "ablation_metrics": ROOT / "reports" / "tables" / "phase28_table_02_arm_primary_metrics.csv",
    "contrasts": ROOT / "reports" / "tables" / "phase28_table_08_bootstrap_statistics.csv",
    "efficiency": ROOT / "reports" / "audits" / "phase34_efficiency_result_v1_4.json",
    "robustness": ROOT / "reports" / "tables" / "phase36_robustness_v1_23" / "phase36_image_robustness_by_domain_condition.csv",
    "components": FDR / "REMEDFILM_FULL_COMPONENT_REGISTRY.json",
    "holdout": ROOT / "reports" / "audits" / "phase30_primary_noninferiority_result.json",
    "test": ROOT / "reports" / "audits" / "phase39_final_test_v1_2_scientific_result.json",
    "manifest": ROOT / "manifests" / "manifest_metadata.json",
}
SHA = {k: (sha(v) if v.exists() else "SOURCE_MISSING") for k, v in SRC.items()}

DICE = "per-image Dice = 2|A∩B|/(|A|+|B|) on 512x512 binary masks at threshold 0.50"
MACRO = "equal-weight mean of the four per-domain per-image means"
POOLED = "equal-weight mean over all images (pooled; descriptive only)"
FULL = "ReMedFiLM FULL"
FULLC = "G + R_psi + B_phi + S_omega"
G = "GlobalMedFiLM"
CONFIG = ("seed=42; tau_C8=-0.024358327623641256; ROI>=0.30; ROI_expansion=1.5; "
          "S_omega_accept>=0.50; mask>=0.50; frozen staged modules; no joint optimisation")

metrics = []


def add(mid, metric, value, *, model=FULL, components=FULLC, population="VAL808",
        split="VAL", domain="MACRO_DOMAIN_EQUAL_WEIGHT", n=808, unit="ratio",
        definition=DICE, aggregation=MACRO, source="internal", evidence="DERIVED_FROM_SAVED_PREDICTIONS",
        verification="RECOMPUTED_FROM_FROZEN_SAVED_MASKS", ckpt=None, run_id="phase27_preservation_seed42"):
    metrics.append({
        "metric_id": mid, "metric": metric, "value": value, "unit": unit,
        "model_identity": model, "active_components": components,
        "population": population, "split": split, "domain": domain, "n": n,
        "run_id": run_id, "seed": 42, "checkpoint_sha256": ckpt or ";".join(f"{k}={v[:12]}" for k, v in CKPT.items()),
        "config": CONFIG, "metric_definition": definition, "aggregation": aggregation,
        "source_path": rel(SRC[source]), "source_sha256": SHA[source],
        "evidence_class": evidence, "verification": verification,
    })


INT = A["internal_val808"]
add("INT_MACRO_G_DICE", "macro_dice", INT["macro_global"], model=G, components="G",
    ckpt=f"G={CKPT['G'][:12]}", evidence="FROZEN_BACKBONE_REFERENCE")
add("INT_MACRO_FULL_DICE", "macro_dice", INT["macro_full"], evidence="PAIRED_PRESERVATION_EVIDENCE")
add("INT_MACRO_DELTA_DICE", "paired_macro_delta_dice", INT["macro_delta"], model="FULL minus G",
    definition="paired per-image Dice difference, FULL - G; domain-stratified macro",
    evidence="PAIRED_PRESERVATION_EVIDENCE")
add("INT_MACRO_DELTA_CI_LOW", "paired_macro_delta_ci_low", INT["macro_delta_ci"][0],
    model="FULL minus G", definition="2.5th percentile, 10,000-replicate domain-stratified bootstrap",
    evidence="DERIVED_BOOTSTRAP", verification="REPRODUCIBLE_FROM_PER_SAMPLE_CSV")
add("INT_MACRO_DELTA_CI_HIGH", "paired_macro_delta_ci_high", INT["macro_delta_ci"][1],
    model="FULL minus G", definition="97.5th percentile, 10,000-replicate domain-stratified bootstrap",
    evidence="DERIVED_BOOTSTRAP", verification="REPRODUCIBLE_FROM_PER_SAMPLE_CSV")
add("INT_POOLED_G_DICE", "pooled_image_mean_dice", INT["pooled_global"], model=G, components="G",
    aggregation=POOLED, evidence="FROZEN_BACKBONE_REFERENCE")
add("INT_POOLED_FULL_DICE", "pooled_image_mean_dice", INT["pooled_full"], aggregation=POOLED,
    evidence="PAIRED_PRESERVATION_EVIDENCE")
add("INT_POOLED_DELTA_DICE", "pooled_image_mean_delta_dice", INT["pooled_delta"], model="FULL minus G",
    aggregation=POOLED, definition="mean paired per-image Dice difference", evidence="PAIRED_PRESERVATION_EVIDENCE")
for mid, metric, val in (("INT_HARMFUL", "case_count", INT["n_harmful"]),
                         ("INT_BENEFICIAL", "case_count", INT["n_beneficial"]),
                         ("INT_UNCHANGED", "case_count", INT["n_unchanged"])):
    add(mid, metric, val, unit="count", aggregation="count", definition=mid.split("_")[-1].lower() + " paired Dice change",
        evidence="PAIRED_PRESERVATION_EVIDENCE")
for dom in ("ISIC", "BUSI", "KVASIR", "KUB"):
    d = INT["domains"][dom]
    for key, metric, unit in (("global_dice", "Dice", "ratio"), ("full_dice", "Dice", "ratio"),
                              ("delta", "paired_delta_dice", "ratio"), ("global_iou", "IoU", "ratio"),
                              ("full_iou", "IoU", "ratio"), ("global_precision", "Precision", "ratio"),
                              ("full_precision", "Precision", "ratio"), ("global_recall", "Recall", "ratio"),
                              ("full_recall", "Recall", "ratio"), ("global_hd95", "HD95_px", "pixel"),
                              ("full_hd95", "HD95_px", "pixel")):
        model = G if key.startswith("global") else ("FULL minus G" if key == "delta" else FULL)
        comp = "G" if key.startswith("global") else FULLC
        add(f"INT_{dom}_{key.upper()}", metric, d[key], model=model, components=comp, domain=dom, n=d["n"],
            unit=unit, aggregation="mean over images within one domain",
            definition=("95th-percentile symmetric surface distance in pixels" if metric == "HD95_px" else DICE),
            evidence=("FROZEN_BACKBONE_REFERENCE" if key.startswith("global") else "PAIRED_PRESERVATION_EVIDENCE"))
    add(f"INT_{dom}_HARMFUL", "case_count", d["harmful"], unit="count", domain=dom, n=d["n"], aggregation="count",
        definition="harmful paired Dice change", evidence="PAIRED_PRESERVATION_EVIDENCE")
for k, v in INT["decisions"].items():
    add(f"ROUTE_DECISION_{k}", "case_count", v, unit="count", aggregation="count",
        definition=f"VAL808 cases with router decision {k}", evidence="FROZEN_STATE_MACHINE_LOG",
        verification="READ_FROM_FROZEN_PER_SAMPLE_TABLE")
for k, v in INT["branches"].items():
    add(f"ROUTE_BRANCH_{k}", "case_count", v, unit="count", aggregation="count",
        definition=f"VAL808 cases with state-machine branch {k}", evidence="FROZEN_STATE_MACHINE_LOG",
        verification="READ_FROM_FROZEN_PER_SAMPLE_TABLE")

# efficiency
E = A["efficiency"]
add("EFF_FULL_PARAMETERS", "parameters", COMP["verified_total_parameters"], model=FULL,
    unit="count", population="STATIC", split="NOT_APPLICABLE", domain="ALL", n=0,
    definition="sum of verified trainable parameters", aggregation="count",
    source="components", evidence="VERIFIED_CHECKPOINT_COUNT", verification="STRICT_LOAD_AND_COUNT")
for key, mid, defn in (("always_refine_literal", "EFF_ALWAYS_REFINE_GMAC", "always-refine literal MAC = G + R_psi"),
                       ("gated_execute_all", "EFF_GATED_EXECUTE_ALL_GMAC", "execute-all gated MAC = G + B_phi + R_psi + S_omega"),
                       ("val808_conditional_gmac", "EFF_A8_VAL808_CONDITIONAL_GMAC", "G + B_phi + (279/808)*(R_psi + S_omega); VAL808 realized activation"),
                       ("holdout_conditional_gmac", "EFF_A8_HOLDOUT_CONDITIONAL_GMAC", "G + B_phi + (240/875)*(R_psi + S_omega); ROUTER_HOLDOUT realized activation")):
    add(mid, "gmac", E[key], model=FULL, unit="GMAC", population=("VAL808" if "VAL808" in mid else "ROUTER_HOLDOUT_875" if "HOLDOUT" in mid else "STATIC"),
        split="NOT_APPLICABLE", domain="ALL", n=0, definition=defn, aggregation="analytical sum",
        source="efficiency", evidence="ANALYTICAL_MAC_LOWER_BOUND", verification="RECOMPUTED_FROM_FROZEN_CONSTANTS")
for key, mid in (("skip_mean", "EFF_LATENCY_SKIP_MEAN_MS"), ("skip_p50", "EFF_LATENCY_SKIP_P50_MS"),
                 ("execute_mean", "EFF_LATENCY_EXECUTE_MEAN_MS"), ("execute_p50", "EFF_LATENCY_EXECUTE_P50_MS"),
                 ("holdout_weighted_mean", "EFF_LATENCY_HOLDOUT_WEIGHTED_MEAN_MS"),
                 ("val808_weighted_mean", "EFF_LATENCY_VAL808_WEIGHTED_MEAN_MS")):
    add(mid, "latency_ms", E["latency_ms"][key], model=FULL, unit="ms",
        population=("ROUTER_HOLDOUT_875" if "HOLDOUT" in mid else "VAL808" if "VAL808" in mid else "CONTROLLED_COMPONENT_PATH"),
        split="NOT_APPLICABLE", domain="ALL", n=1000,
        definition="batch-1 forward-only model compute path, RTX 3060 Ti; NOT end-to-end pipeline latency",
        aggregation="median or arithmetic mean of 1,000 measured repeats", source="efficiency",
        evidence="MEASURED_HARDWARE_SPECIFIC_RUNTIME", verification="READ_FROM_FROZEN_PROFILE")

# ablation
AB = A["ablation_router_development"]
for arm, d in AB["arms"].items():
    for key, metric, unit in (("n_routed", "routed_cases", "count"),
                              ("all_eligible_mean_delta", "all_eligible_mean_delta_dice", "ratio"),
                              ("conditional_mean_delta", "conditional_mean_delta_dice_routed", "ratio"),
                              ("harmful_routed", "harmful_routed_cases", "count"),
                              ("harmful_all_eligible", "harmful_fraction_all_eligible", "ratio"),
                              ("harmful_conditional", "harmful_fraction_conditional", "ratio"),
                              ("benefit_capture", "benefit_capture", "ratio"),
                              ("gmac", "gmac", "GMAC")):
        if d[key] is None:
            continue
        add(f"ABL_{arm}_{key.upper()}", metric, d[key], model=f"ablation arm {arm}", components=d["definition"],
            population="ROUTER_DEVELOPMENT_4957", split="ROUTER_DEVELOPMENT", domain="ALL_FOUR_DOMAINS",
            n=AB["n"], unit=unit, definition=f"Phase28 arm {arm}: {d['definition']}",
            aggregation=("count" if unit == "count" else "per-arm aggregate over 4,957"),
            source="ablation_metrics", evidence=d["role"], verification="READ_FROM_FROZEN_CSV")
for c, d in AB["contrasts"].items():
    for key, metric in (("mean_difference", "paired_mean_difference"), ("ci_low", "ci_low"), ("ci_high", "ci_high")):
        add(f"ABL_CONTRAST_{c}_{key.upper()}", metric, d[key], model=c, components="paired contrast",
            population="ROUTER_DEVELOPMENT_4957", split="ROUTER_DEVELOPMENT", domain="ALL_FOUR_DOMAINS",
            n=d["n"], definition="matched paired contrast on the common 4,957 cases",
            aggregation="paired mean difference", source="contrasts", evidence="DERIVED_BOOTSTRAP",
            verification="READ_FROM_FROZEN_CSV")

# external
EXT = A["external884"]
for ck, d in EXT["cohorts"].items():
    for key, metric, unit in (("global_dice", "Dice", "ratio"), ("full_dice", "Dice", "ratio"),
                              ("delta", "paired_delta_dice", "ratio"), ("global_iou", "IoU", "ratio"),
                              ("full_iou", "IoU", "ratio"), ("global_precision", "Precision", "ratio"),
                              ("full_precision", "Precision", "ratio"), ("global_recall", "Recall", "ratio"),
                              ("full_recall", "Recall", "ratio"), ("global_hd95", "HD95_px", "pixel"),
                              ("full_hd95", "HD95_px", "pixel"), ("global_assd", "ASSD_px", "pixel"),
                              ("full_assd", "ASSD_px", "pixel")):
        n = d.get("hd95_n" if metric in ("HD95_px", "ASSD_px") else "recall_n" if metric == "Recall" else "n", d["n"])
        model = G if key.startswith("global") else ("FULL minus G" if key == "delta" else FULL)
        add(f"EXT_{ck.upper()}_{key.upper()}", metric, d[key], model=model, components=("G" if key.startswith("global") else FULLC),
            population=f"EXTERNAL_{ck.upper()}", split="EXTERNAL_RETROSPECTIVE", domain=ck, n=n, unit=unit,
            definition=("surface distance in pixels; no physical spacing available" if unit == "pixel" else DICE),
            aggregation="macro over cases (equal case weight)", source="external",
            evidence="EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS", verification="READ_FROM_FROZEN_PER_CASE_TABLE")
    for key, metric, unit in (("improved", "improved_cases", "count"), ("worsened", "worsened_cases", "count"),
                              ("unchanged", "unchanged_cases", "count"), ("n_selected", "executed_cases", "count"),
                              ("fp_only", "false_positive_only_cases", "count")):
        add(f"EXT_{ck.upper()}_{key.upper()}", metric, d[key], unit=unit, population=f"EXTERNAL_{ck.upper()}",
            split="EXTERNAL_RETROSPECTIVE", domain=ck, n=d["n"], aggregation="count", source="external",
            evidence="EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS", verification="READ_FROM_FROZEN_PER_CASE_TABLE")
    for i, lab in enumerate(("ci_low", "ci_high")):
        add(f"EXT_{ck.upper()}_DELTA_CI_{lab.upper()}", "paired_delta_ci", d["delta_ci"][i], model="FULL minus G",
            population=f"EXTERNAL_{ck.upper()}", split="EXTERNAL_RETROSPECTIVE", domain=ck, n=d["n"],
            definition="paired percentile bootstrap over cases", aggregation="macro over cases",
            source="external", evidence="DERIVED_BOOTSTRAP", verification="REPRODUCIBLE_FROM_PER_CASE_TABLE")
for sub in ("six_positive", "fourteen_absent"):
    d = EXT["cohorts"]["stones"][sub]
    for key in ("global_dice", "full_dice", "delta"):
        add(f"EXT_STONES_{sub.upper()}_{key.upper()}", "Dice" if key != "delta" else "paired_delta_dice",
            d[key], model=("FULL minus G" if key == "delta" else G if key.startswith("global") else FULL),
            components=("G" if key.startswith("global") else FULLC), population=f"EXTERNAL_STONES_{sub.upper()}",
            split="EXTERNAL_RETROSPECTIVE", domain="KUB_NEGATIVE_CONTROL" if sub == "fourteen_absent" else "KUB_POSITIVE",
            n=d["n"], aggregation="macro over cases", source="external",
            evidence="MATERIAL_FAILURE_NEGATIVE_CONTROL" if sub == "fourteen_absent" else "EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS",
            verification="READ_FROM_FROZEN_PER_CASE_TABLE")

# robustness summary
for dom, d in A["robustness_phase36"]["domains"].items():
    add(f"ROB_{dom}_WORST_CONDITION_DELTA", "mean_paired_delta_dice", d["worst_delta"], model=FULL,
        population="VAL808_SYNTHETIC_PERTURBATION", split="VAL", domain=dom, n=808,
        definition=f"worst synthetic image condition ({d['worst_condition']})",
        aggregation="macro over samples within domain and condition", source="robustness",
        evidence="DEVELOPMENT_SET_SYNTHETIC_PERTURBATION_ROBUSTNESS_EVIDENCE", verification="READ_FROM_FROZEN_CSV")

# holdout canonical
H = json.loads(SRC["holdout"].read_text(encoding="utf-8"))
add("HOLDOUT_G_MACRO_DICE", "macro_dice", H["global_macro_dice"], model=G, components="G",
    population="ROUTER_HOLDOUT_875", split="ROUTER_HOLDOUT", n=875, source="holdout",
    evidence="ONE_SHOT_HOLDOUT_WITH_DISCLOSED_DEVIATION", verification="READ_FROM_FROZEN_JSON")
add("HOLDOUT_A8_MACRO_DICE", "macro_dice", H["a8_macro_dice"], population="ROUTER_HOLDOUT_875",
    split="ROUTER_HOLDOUT", n=875, source="holdout", evidence="ONE_SHOT_HOLDOUT_WITH_DISCLOSED_DEVIATION")
add("HOLDOUT_MACRO_DELTA", "paired_macro_delta_dice", H["macro_delta_dice"], model="FULL minus G",
    population="ROUTER_HOLDOUT_875", split="ROUTER_HOLDOUT", n=875, source="holdout",
    evidence="ONE_SHOT_HOLDOUT_WITH_DISCLOSED_DEVIATION")
add("HOLDOUT_DELTA_CI_LOW", "paired_macro_delta_ci_low", H["macro_ci"][0], model="FULL minus G",
    population="ROUTER_HOLDOUT_875", split="ROUTER_HOLDOUT", n=875, source="holdout",
    evidence="ONE_SHOT_HOLDOUT_WITH_DISCLOSED_DEVIATION")
add("HOLDOUT_DELTA_CI_HIGH", "paired_macro_delta_ci_high", H["macro_ci"][1], model="FULL minus G",
    population="ROUTER_HOLDOUT_875", split="ROUTER_HOLDOUT", n=875, source="holdout",
    evidence="ONE_SHOT_HOLDOUT_WITH_DISCLOSED_DEVIATION")

registry = {
    "artifact": "REMEDFILM_V9_RESULTS_REGISTRY",
    "version": "V9",
    "created_utc": "2026-11-09",
    "purpose": "single source-linked numeric authority for every V9 table, figure and prose number",
    "canonical_model": {
        "name": "ReMedFiLM FULL (RA-MedFiLM-BARR)",
        "definition": "G + R_psi + B_phi + S_omega",
        "components": {"G": "GlobalMedFiLM", "R_psi": "BARRRegionalRefinerV1",
                       "B_phi": "BARRBenefitRouterV1", "S_omega": "BARRPostSafetyV1"},
        "verified_total_parameters": COMP["verified_total_parameters"],
        "all_components_verified": COMP["all_components_verified"],
        "checkpoint_sha256": CKPT,
        "global_medfilm_is_not_full": True,
    },
    "runtime_constants": {
        "tau_C8_final": TAU_C8_FINAL_FLOAT, "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
        "roi_expansion": ROI_EXPANSION, "s_omega_accept_threshold": SOMEGA_ACCEPT_THRESHOLD,
        "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD, "states": list(STATES),
    },
    "inference_implementation_class": {
        "class": "B_HISTORICAL_OFFLINE_CACHED_CANDIDATE_REPLAY",
        "evidence": ("src/models/barr/ra_medfilm_barr.py::forward_inference requires external "
                     "router_features_202, oof_refined_crop_prob and safety_post_features_16; "
                     "the refiner module is never invoked (only a counter is incremented)."),
        "deployable_end_to_end_inference": False,
        "interpretation": "saved-candidate decision/fusion replay; not a deployable online pipeline",
    },
    "canonical_result": {
        "population": "VAL808", "n": 808, "seed": 42,
        "full_macro_dice": INT["macro_full"], "global_macro_dice": INT["macro_global"],
        "paired_macro_delta": INT["macro_delta"], "paired_macro_delta_ci": INT["macro_delta_ci"],
        "pooled_full_dice": INT["pooled_full"], "pooled_global_dice": INT["pooled_global"],
        "pooled_delta": INT["pooled_delta"],
        "harmful": INT["n_harmful"], "beneficial": INT["n_beneficial"], "unchanged": INT["n_unchanged"],
        "status": "INTERNAL_DEVELOPMENT_VALIDATION_ONLY_NOT_PRISTINE_TEST",
    },
    "populations": {
        "TRAIN_MANIFEST": 5913, "TRAIN_USED": 5832, "VAL_MANIFEST": 845, "VAL808": 808,
        "TEST1683": "PROTECTED__HISTORICAL_PHASE39_ACCESS_DISCLOSED__NO_V9_ACCESS",
        "ROUTER_DEVELOPMENT_4957": 4957, "ROUTER_HOLDOUT_875": 875,
        "EXTERNAL884": {"CVC-ClinicDB": 612, "BrEaST-Lesions-USG": 252, "Stones_where_are_you": 20},
        "HAM10000": 10015,
    },
    "ham10000": {
        "status": "EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED",
        "images": 10015, "masks": 10015, "metadata_rows": 10015,
        "classes": {"NV": 6705, "MEL": 1113, "BKL": 1099, "BCC": 514, "AKIEC": 327, "VASC": 142, "DF": 115},
        "mask_dimensions": [600, 450], "mask_modes": {"L": 9613, "P": 402},
        "binary_values": [0, 255], "all_foreground_masks": ["ISIC_0026042", "ISIC_0029819"],
        "image_exact_duplicate_pairs": [["ISIC_0024366", "ISIC_0029861"], ["ISIC_0024777", "ISIC_0029938"]],
        "id_overlap_with_internal_isic2018_task1": 0,
        "licence": "CC BY-NC 4.0 (non-commercial)",
        "reason_not_established": ("Images are the ISIC-2018 Task-3 / HAM10000 classification release. "
                                   "The 10,015 binary masks have no provenance, licence or official annotation "
                                   "record in the local copy; two masks are degenerate all-foreground. "
                                   "They are not used as ground truth."),
    },
    "ablation_population": "ROUTER_DEVELOPMENT_4957",
    "val808_vs_ablation": ("The 13-arm ablation was run on ROUTER_DEVELOPMENT (n=4,957, drawn from TRAIN). "
                           "VAL808 is a separate paired preservation experiment (n=808). They are never pooled."),
    "test1683_disclosure": {
        "historical_access": True,
        "phase": 39,
        "v9_access": False,
        "v8_access": False,
        "relabel_as_untouched_prohibited": True,
        "descriptive_result_n": 1683,
        "descriptive_macro_dice": 0.8314368385956257,
        "qualifier": "POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES",
        "confirmatory_comparison_available": False,
        "v9_use": "disclosed only; not used as evidence of preservation, superiority or harm",
    },
    "source_manifest": [{"key": k, "path": rel(v), "exists": v.exists(),
                         "sha256": SHA[k]} for k, v in SRC.items()],
    "metric_count": len(metrics),
    "metrics": metrics,
    "declaration": ("No training, no new neural inference, no checkpoint mutation, no protected TEST1683 "
                    "image/mask/manifest access, and no GitHub publication occurred during the V9 build."),
}
out = FDR / "REMEDFILM_V9_RESULTS_REGISTRY.json"
out.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")

# wide internal CSV
rows = []
for dom in ("ISIC", "BUSI", "KVASIR", "KUB", "MACRO_DOMAIN_EQUAL_WEIGHT", "POOLED_IMAGE_MEAN"):
    if dom == "MACRO_DOMAIN_EQUAL_WEIGHT":
        d = {"n": 808, "global_dice": INT["macro_global"], "full_dice": INT["macro_full"],
             "delta": INT["macro_delta"], "full_iou": "", "global_iou": "", "full_precision": "",
             "global_precision": "", "full_recall": "", "global_recall": "", "full_hd95": "",
             "global_hd95": "", "harmful": INT["n_harmful"], "beneficial": INT["n_beneficial"],
             "unchanged": INT["n_unchanged"], "executed": INT["decisions"].get("EXECUTE", 0),
             "accepted": INT["branches"].get("EXECUTE_THEN_ACCEPT", 0)}
    elif dom == "POOLED_IMAGE_MEAN":
        d = {"n": 808, "global_dice": INT["pooled_global"], "full_dice": INT["pooled_full"],
             "delta": INT["pooled_delta"], "full_iou": "", "global_iou": "", "full_precision": "",
             "global_precision": "", "full_recall": "", "global_recall": "", "full_hd95": "",
             "global_hd95": "", "harmful": INT["n_harmful"], "beneficial": INT["n_beneficial"],
             "unchanged": INT["n_unchanged"], "executed": INT["decisions"].get("EXECUTE", 0),
             "accepted": INT["branches"].get("EXECUTE_THEN_ACCEPT", 0)}
    else:
        d = INT["domains"][dom]
    rows.append({"population": "VAL808", "domain": dom, "n": d["n"],
                 "global_dice": d["global_dice"], "full_dice": d["full_dice"], "delta_dice": d["delta"],
                 "global_iou": d["global_iou"], "full_iou": d["full_iou"],
                 "global_precision": d["global_precision"], "full_precision": d["full_precision"],
                 "global_recall": d["global_recall"], "full_recall": d["full_recall"],
                 "global_hd95_px": d["global_hd95"], "full_hd95_px": d["full_hd95"],
                 "n_harmful": d["harmful"], "n_beneficial": d["beneficial"], "n_unchanged": d["unchanged"],
                 "n_executed": d["executed"], "n_accepted": d["accepted"],
                 "aggregation": MACRO if dom not in ("POOLED_IMAGE_MEAN",) else POOLED,
                 "source": "full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv"})
with open(FDR / "REMEDFILM_V9_INTERNAL_EVALUATION.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

# wide external CSV
erows = []
for ck, d in EXT["cohorts"].items():
    if ck == "stones":
        for sub in ("six_positive", "fourteen_absent"):
            s = d[sub]
            erows.append({"cohort": ck, "subgroup": sub, "n": s["n"], "n_defined_surface": 0 if sub == "fourteen_absent" else s["n"],
                          "global_dice": s["global_dice"], "full_dice": s["full_dice"], "delta_dice": s["delta"],
                          "global_iou": "", "full_iou": "", "global_precision": "", "full_precision": "",
                          "global_recall": "", "full_recall": "", "global_hd95_px": "", "full_hd95_px": "",
                          "global_assd_px": "", "full_assd_px": "", "improved": s["improved"],
                          "worsened": s["worsened"], "unchanged": s["unchanged"], "n_executed": "",
                          "fp_only_cases": s["fp_only"]})
    erows.append({"cohort": ck, "subgroup": "all", "n": d["n"], "n_defined_surface": d["hd95_n"],
                  "global_dice": d["global_dice"], "full_dice": d["full_dice"], "delta_dice": d["delta"],
                  "global_iou": d["global_iou"], "full_iou": d["full_iou"],
                  "global_precision": d["global_precision"], "full_precision": d["full_precision"],
                  "global_recall": d["global_recall"], "full_recall": d["full_recall"],
                  "global_hd95_px": d["global_hd95"], "full_hd95_px": d["full_hd95"],
                  "global_assd_px": d["global_assd"], "full_assd_px": d["full_assd"],
                  "improved": d["improved"], "worsened": d["worsened"], "unchanged": d["unchanged"],
                  "n_executed": d["n_selected"], "fp_only_cases": d["fp_only"]})
with open(FDR / "REMEDFILM_V9_EXTERNAL_EVALUATION.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(erows[0]))
    w.writeheader(); w.writerows(erows)

# 13-arm CSV
arows = []
for arm, d in AB["arms"].items():
    arows.append({
        "arm": arm, "definition": d["definition"], "role": d["role"],
        "population": "ROUTER_DEVELOPMENT_4957", "n_eligible": 4957,
        "n_routed": d["n_routed"], "routed_fraction": d["budget_fraction"],
        "all_eligible_mean_delta_dice": d["all_eligible_mean_delta"],
        "conditional_mean_delta_dice_routed": "" if d["conditional_mean_delta"] is None else d["conditional_mean_delta"],
        "n_beneficial_routed": d["beneficial_routed"], "n_harmful_routed": d["harmful_routed"],
        "harmful_fraction_of_all_eligible": d["harmful_all_eligible"],
        "harmful_fraction_of_routed": "" if d["harmful_conditional"] is None else d["harmful_conditional"],
        "benefit_capture": d["benefit_capture"], "conditional_gmac": d["gmac"],
        "delta_gmac_vs_A0": d["delta_gmac_vs_a0"],
    })
with open(FDR / "REMEDFILM_V9_ABLATION_13ARM.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(arows[0]))
    w.writeheader(); w.writerows(arows)

print("registry metrics", len(metrics))
print(out)
print(registry["canonical_result"])
print("val808 gmac", E["val808_conditional_gmac"], "holdout", E["holdout_conditional_gmac"])
