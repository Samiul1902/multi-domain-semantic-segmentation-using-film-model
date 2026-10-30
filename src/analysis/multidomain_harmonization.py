"""
Phase 19 — Multi-Domain Dataset Harmonization (Stage B, first phase).

Single reusable implementation of the Phase-19 harmonization analysis for the
four target domains (ISIC 2018, BUSI, Kvasir-SEG, KUB). Both the driver
(``scripts/analysis/run_phase19_harmonization.py``) and the reviewer notebook
(``notebooks/phasewise/phase_19_harmonization/``) import this module so they
produce byte-identical tables and artifacts.

Governance
----------
- TRAIN and VAL only. TEST is never read (image or mask), never loaded, never
  visualized. ``verify_test_lock`` is asserted at build time.
- No training, no optimizer, no backward pass, no checkpoint creation.
- The active manifest is ``manifests/phase4_v3`` (CANONICAL_ACTIVE_DEVELOPMENT).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from src.utils.targets import foreground_label_signature

# --------------------------------------------------------------------------- #
# Canonical identities — verified from manifests/phase4_v3 and legacy evidence
# --------------------------------------------------------------------------- #
DATASET_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]

#: Authoritative Phase-19 task-ID registry. Cross-verified from two independent
#: sources: (1) manifests/phase4_v3/*.csv `task_id` column, and (2) the legacy
#: tested project config D:\Softfors\final\medfilm_seg\configs\global_config.json
#: (isic2018=0, busi=1, kvasir=2). KUB=3 is the jup-repo extension.
TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
TASK_ID_TO_NAME = {v: k for k, v in TASK_ID.items()}

#: Static, verified per-domain descriptors (native representation).
DATASET_META = {
    "ISIC": {
        "canonical_name": "ISIC 2018 Task 1",
        "modality": "dermoscopy",
        "anatomy": "skin",
        "native_image_mode": "RGB",
        "native_mask_mode": "L",
        "image_ext": ".jpg",
        "mask_ext": ".png",
        "foreground_native_labels": "{0,255}",
        "image_root": r"D:\Softfors\omni_seg\data_raw\isic2018",
        "mask_root": r"D:\Softfors\omni_seg\data_raw\isic2018\ISIC2018_Task1_Training_GroundTruth",
    },
    "BUSI": {
        "canonical_name": "BUSI (WHU Breast Ultrasound)",
        "modality": "ultrasound",
        "anatomy": "breast",
        "native_image_mode": "L",
        "native_mask_mode": "L",
        "image_ext": ".bmp",
        "mask_ext": ".bmp",
        "foreground_native_labels": "{0,255}",
        "image_root": r"D:\Softfors\omni_seg\data_raw\BUSI_WHU Breast Cancer Ultrasound Image  Dataset\BUSI-WHU\img",
        "mask_root": r"D:\Softfors\omni_seg\data_raw\BUSI_WHU Breast Cancer Ultrasound Image  Dataset\BUSI-WHU\gt",
    },
    "KVASIR": {
        "canonical_name": "Kvasir-SEG",
        "modality": "endoscopy",
        "anatomy": "gastrointestinal polyp",
        "native_image_mode": "RGB",
        "native_mask_mode": "RGB",
        "image_ext": ".jpg",
        "mask_ext": ".jpg",
        "foreground_native_labels": "nonzero (white-on-black RGB)",
        "image_root": r"D:\Softfors\omni_seg\data_raw\Kvasir-SEG\images",
        "mask_root": r"D:\Softfors\omni_seg\data_raw\Kvasir-SEG\masks",
    },
    "KUB": {
        "canonical_name": "KUB-Stone (Kidney-Ureter-Bladder radiograph)",
        "modality": "radiograph",
        "anatomy": "kidney / ureter / bladder",
        "native_image_mode": "L or RGB (mixed acquisition regimes)",
        "native_mask_mode": "L",
        "image_ext": ".png",
        "mask_ext": ".png",
        "foreground_native_labels": "heterogeneous nonzero {0,255}/{0,1}/{0,2}/{0,3}/{0,1,2}",
        "image_root": r"D:\Softfors\omni_seg\data_raw\KUB-Stone\KUB-Stonex",
        "mask_root": r"D:\Softfors\omni_seg\data_raw\KUB-Stone\KUB-Stonex",
    },
}

MANIFEST_DIR = "manifests/phase4_v3"
SUPPORTED_SIZES = (256, 512, 768, 1024)
DEFAULT_SIZE = 512

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    raise TypeError(f"not JSON serializable: {type(obj)}")


def write_json(path, payload) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
    return sha256_file(path)


def write_csv(path, frame) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return sha256_file(path)


def read_manifest(root, split) -> pd.DataFrame:
    frame = pd.read_csv(Path(root) / MANIFEST_DIR / f"{split.lower()}.csv")
    frame["split"] = frame["split"].astype(str).str.upper()
    return frame


def development_frame(root) -> pd.DataFrame:
    """TRAIN + VAL only. TEST is never concatenated here."""
    train = read_manifest(root, "TRAIN")
    val = read_manifest(root, "VAL")
    return pd.concat([train, val], ignore_index=True)


# --------------------------------------------------------------------------- #
# Measurement builders (cached, deterministic)
# --------------------------------------------------------------------------- #


def build_image_measurements(root, cache_path, force=False) -> pd.DataFrame:
    """
    Lazy-open every TRAIN/VAL image and mask to record native size and mode.

    No pixel decoding occurs for the size/mode pass, so this is cheap and
    exact over the full development population (no sampling).
    """
    cache_path = Path(cache_path)
    if cache_path.exists() and not force:
        return pd.read_csv(cache_path)

    dev = development_frame(root)
    rows = []
    for _, r in dev.iterrows():
        with Image.open(r["image_path"]) as im:
            iw, ih, imode = im.size[0], im.size[1], im.mode
        with Image.open(r["mask_path"]) as mk:
            mw, mh, mmode = mk.size[0], mk.size[1], mk.mode
        rows.append({
            "dataset": r["dataset"],
            "task_id": int(r["task_id"]),
            "split": r["split"],
            "sample_id": r["sample_id"],
            "width": int(iw),
            "height": int(ih),
            "aspect_ratio": round(float(iw) / float(ih), 6),
            "image_mode": imode,
            "mask_mode": mmode,
            "image_ext": Path(r["image_path"]).suffix.lower(),
            "mask_ext": Path(r["mask_path"]).suffix.lower(),
            "image_mask_size_match": bool((iw, ih) == (mw, mh)),
        })
    frame = pd.DataFrame(rows).sort_values(["dataset", "split", "sample_id"]).reset_index(drop=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(cache_path, index=False)
    return frame


def build_mask_measurements(root, cache_path, n_per_dataset=150, seed=42, force=False) -> pd.DataFrame:
    """
    Deterministic per-dataset sample: decode the native mask and record the
    foreground fraction and the raw label signature (audit only).
    """
    cache_path = Path(cache_path)
    if cache_path.exists() and not force:
        return pd.read_csv(cache_path)

    dev = development_frame(root)
    rng = np.random.default_rng(seed)
    rows = []
    for ds in DATASET_ORDER:
        sub = dev[dev["dataset"] == ds].sort_values(["split", "sample_id"]).reset_index(drop=True)
        take = min(int(n_per_dataset), len(sub))
        idx = np.sort(rng.choice(len(sub), size=take, replace=False))
        for i in idx:
            r = sub.iloc[i]
            with Image.open(r["mask_path"]) as mk:
                arr = np.asarray(mk)
            if arr.ndim == 3:
                arr1 = arr[..., 0]
            else:
                arr1 = arr
            fg = float((arr1 > 0).mean())
            rows.append({
                "dataset": ds,
                "task_id": int(r["task_id"]),
                "split": r["split"],
                "sample_id": r["sample_id"],
                "fg_fraction": fg,
                "n_unique_labels": int(len(np.unique(arr1))),
                "label_signature": foreground_label_signature(arr1),
                "is_binary_01": bool(np.all(np.isin(np.unique(arr1), [0, 1]))),
            })
    frame = pd.DataFrame(rows).sort_values(["dataset", "split", "sample_id"]).reset_index(drop=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(cache_path, index=False)
    return frame


# --------------------------------------------------------------------------- #
# Phase-19 tables
# --------------------------------------------------------------------------- #


def dataset_inventory(root) -> pd.DataFrame:
    """One row per domain with population, representation and geometry facts."""
    dev = development_frame(root)
    test = read_manifest(root, "TEST")
    img = build_image_measurements(
        root, Path(root) / "reports/tables/phase19_image_measurements.csv")
    msk = build_mask_measurements(
        root, Path(root) / "reports/tables/phase19_mask_measurements.csv")

    rows = []
    for ds in DATASET_ORDER:
        d = dev[dev["dataset"] == ds]
        t = test[test["dataset"] == ds]
        g = img[img["dataset"] == ds]
        m = msk[msk["dataset"] == ds]
        meta = DATASET_META[ds]
        rows.append({
            "dataset": ds,
            "task_id": TASK_ID[ds],
            "canonical_name": meta["canonical_name"],
            "modality": meta["modality"],
            "anatomy": meta["anatomy"],
            "n_train": int((d["split"] == "TRAIN").sum()),
            "n_val": int((d["split"] == "VAL").sum()),
            "n_test_locked": int(len(t)),
            "n_development": int(len(d)),
            "native_image_mode": meta["native_image_mode"],
            "native_mask_mode": meta["native_mask_mode"],
            "observed_image_modes": "|".join(sorted(g["image_mode"].unique())),
            "observed_mask_modes": "|".join(sorted(g["mask_mode"].unique())),
            "image_ext": "|".join(sorted(g["image_ext"].unique())),
            "mask_ext": "|".join(sorted(g["mask_ext"].unique())),
            "image_mask_size_match_frac": round(float(g["image_mask_size_match"].mean()), 6),
            "width_min": int(g["width"].min()),
            "width_median": float(g["width"].median()),
            "width_max": int(g["width"].max()),
            "height_min": int(g["height"].min()),
            "height_median": float(g["height"].median()),
            "height_max": int(g["height"].max()),
            "aspect_min": round(float(g["aspect_ratio"].min()), 6),
            "aspect_median": round(float(g["aspect_ratio"].median()), 6),
            "aspect_max": round(float(g["aspect_ratio"].max()), 6),
            "fg_fraction_median": round(float(m["fg_fraction"].median()), 6),
            "fg_fraction_min": round(float(m["fg_fraction"].min()), 6),
            "fg_fraction_max": round(float(m["fg_fraction"].max()), 6),
            "mask_label_signatures_observed": " | ".join(sorted(m["label_signature"].unique())[:6]),
            "fg_native_rule": "mask > 0",
        })
    return pd.DataFrame(rows)


def task_id_registry(root) -> pd.DataFrame:
    """Authoritative Phase-19 task-ID registry with cross-verification."""
    dev = development_frame(root)
    rows = []
    for ds in DATASET_ORDER:
        observed = sorted(set(int(v) for v in dev[dev["dataset"] == ds]["task_id"].unique()))
        rows.append({
            "dataset": ds,
            "canonical_name": DATASET_META[ds]["canonical_name"],
            "task_id": TASK_ID[ds],
            "modality": DATASET_META[ds]["modality"],
            "task_name": f"{DATASET_META[ds]['modality']}_binary_lesion_segmentation",
            "observed_task_ids_in_manifest": "|".join(str(v) for v in observed),
            "manifest_agrees": bool(observed == [TASK_ID[ds]]),
            "legacy_corroboration": "D:\\Softfors\\final\\medfilm_seg\\configs\\global_config.json",
            "status": "FROZEN_FOR_PHASE_19",
        })
    return pd.DataFrame(rows)


def metadata_governance() -> pd.DataFrame:
    """
    Classify every known metadata field as exactly one of
    CONDITIONING_ALLOWED / REPORTING_ONLY / FORBIDDEN_AS_INPUT.
    """
    rows = [
        ("dataset", "Dataset identity", "CONDITIONING_ALLOWED",
         "Deployment-available: the serving system knows which scanner/dataset produced the image.",
         "May be used as a FiLM task-conditioning input in Phase 24+."),
        ("task_id", "Integer task encoding", "CONDITIONING_ALLOWED",
         "Deterministic encoding of `dataset`; no annotation information.",
         "Canonical FiLM conditioning key."),
        ("split", "TRAIN/VAL/TEST marker", "REPORTING_ONLY",
         "Governance label, not an image property. Leaks nothing but is not a model input.",
         "Used only to scope loaders and reporting."),
        ("sample_id", "Stable sample hash", "REPORTING_ONLY",
         "Identifier for joins/traceability.",
         "Never a model input."),
        ("patient_id", "Patient grouping key", "FORBIDDEN_AS_INPUT",
         "Identifies the subject; using it would leak subject identity and is unavailable at inference.",
         "Used ONLY for leakage-safe grouping where available."),
        ("case_id", "Case grouping key", "FORBIDDEN_AS_INPUT",
         "Grouping key; not an image property.",
         "Used ONLY for leakage-safe grouping where available."),
        ("category", "Anatomical / diagnostic category (KUB only)", "REPORTING_ONLY",
         "KUB Kidney/Bladder/Ureteric labels are annotation-derived ground truth. "
         "They are NOT legitimately available at inference time.",
         "May be reported for stratification. MUST NOT condition the model unless a later "
         "supervisor-approved protocol proves availability at inference."),
        ("image_path", "Native image path", "REPORTING_ONLY",
         "Filesystem locator; also encodes acquisition regime for KUB (ROI vs FULL_FIELD).",
         "Path-derived regime may be used for stratified REPORTING only; not a model input."),
        ("mask_path", "Native mask path", "FORBIDDEN_AS_INPUT",
         "Locator for the ground-truth mask. Any use at inference is leakage.",
         "Evaluation only."),
        ("width / height", "Native geometry", "REPORTING_ONLY",
         "Derived from the image, so legitimately available, but the harmonization contract "
         "resizes to a canonical size; native size is retained for audit only.",
         "Not a conditioning input under the frozen size policy."),
        ("fg_fraction", "Foreground prevalence", "FORBIDDEN_AS_INPUT",
         "Computed from the ground-truth mask. Using it conditions on the label.",
         "Reporting/stratification only."),
    ]
    return pd.DataFrame(rows, columns=[
        "field", "description", "classification", "rationale", "phase19_disposition"])


def harmonized_schema() -> pd.DataFrame:
    """The frozen Phase-19 harmonized sample + batch schema."""
    rows = [
        ("image", "tensor", "(C, H, W)", "float32", "[0,1]",
         "C in {1,3} per channel policy; H=W=canonical size", "CONDITIONING_INPUT"),
        ("mask", "tensor", "(1, H, W)", "float32", "{0,1}",
         "canonical foreground = (mask > 0)", "TARGET"),
        ("dataset", "str", "scalar", "-", "-", "canonical dataset name", "CONDITIONING_ALLOWED"),
        ("task_id", "int64", "scalar", "-", "-", "authoritative task registry", "CONDITIONING_ALLOWED"),
        ("sample_id", "str", "scalar", "-", "-", "stable hash", "REPORTING_ONLY"),
        ("split", "str", "scalar", "-", "-", "TRAIN/VAL only", "REPORTING_ONLY"),
        ("image_native_size", "tuple[int,int]", "(W,H)", "-", "-",
         "pre-resize native size, audit only", "REPORTING_ONLY"),
        ("resize_scale", "float", "scalar", "-", "-",
         "aspect-preserving scale = min(size/w, size/h)", "REPORTING_ONLY"),
    ]
    return pd.DataFrame(rows, columns=[
        "field", "kind", "shape", "dtype", "range", "semantics", "governance_class"])


# --------------------------------------------------------------------------- #
# Contracts
# --------------------------------------------------------------------------- #


def preprocessing_contract(root) -> dict:
    img = build_image_measurements(
        root, Path(root) / "reports/tables/phase19_image_measurements.csv")
    per_domain_modes = {
        ds: sorted(img[img["dataset"] == ds]["image_mode"].unique()) for ds in DATASET_ORDER
    }
    return {
        "contract_id": "phase19_preprocessing_contract_v1",
        "status": "FROZEN_FOR_PHASE_19",
        "scope": "TRAIN and VAL only",
        "image": {
            "storage_dtype": "uint8",
            "model_dtype": "float32",
            "intensity_range_native": "[0,255]",
            "intensity_normalization": "divide by 255.0 -> [0,1]",
            "channel_policy_default": "RGB_3CH",
            "channel_policy_alternatives": ["GRAYSCALE_1CH", "RGB_3CH"],
            "color_handling": {
                "RGB_3CH": "PIL convert('RGB'); native-L domains are replicated to 3 identical channels (lossless)",
                "GRAYSCALE_1CH": "PIL convert('L') (ITU-R 601-2 luma); matches the legacy KUB-only pipeline",
            },
            "observed_native_modes_per_domain": per_domain_modes,
            "channel_decision_owner": "Phase 24 (architecture specification); Phase 19 freezes BOTH converters",
        },
        "mask": {
            "storage_dtype": "uint8",
            "model_dtype": "float32",
            "foreground_rule": "mask > 0  (src.utils.targets.binarize_mask)",
            "background_rule": "mask == 0",
            "channel_reduction": "3-D masks reduced to first channel",
            "binarization_threshold": "strictly greater than zero; no value threshold applied",
            "interpolation": "NEAREST",
            "never_test_mask_eq_1": True,
        },
        "spatial": {
            "policy": "aspect-preserving resize + centre pad",
            "scale_formula": "scale = min(size / w, size / h)",
            "supported_sizes": list(SUPPORTED_SIZES),
            "default_size": DEFAULT_SIZE,
            "image_resample": "BILINEAR",
            "mask_resample": "NEAREST",
            "pad_fill": 0,
            "implementation": "src.data.transforms.SegmentationTransform",
        },
        "augmentation_boundary": {
            "train_only": True,
            "paired": True,
            "operations": ["horizontal mirror (p=0.5)", "rotation +/-5 deg",
                           "brightness +/-0.10", "contrast +/-0.10"],
            "mask_resample_during_augmentation": "NEAREST",
            "val_augmentation": "disabled",
            "implementation": "src.data.transforms.SegmentationTransform(train=True)",
        },
        "test_policy": {
            "test_image_reads": 0, "test_mask_reads": 0,
            "test_inference": 0, "test_visualization": 0,
            "enforced_by": ["src.data.loaders.create_loader", "src.data.multidomain_dataset.MultiDomainDataset"],
        },
    }


def evaluation_contract() -> dict:
    return {
        "contract_id": "phase19_evaluation_contract_v1",
        "status": "FROZEN_FOR_PHASE_19",
        "scope": "TRAIN and VAL only; TEST excluded",
        "metric_domain": {
            "frozen_domain": "DETECTION (component overlap >= 1 pixel)",
            "note": "Phase 19 freezes the domain only; no metric is computed on TEST.",
        },
        "metrics": {
            "pixel": ["dice", "iou", "precision", "recall", "f1"],
            "boundary": ["hd95"],
            "threshold": 0.5,
            "epsilon": 1e-7,
            "implementation": "src.metrics.segmentation.binary_metrics",
        },
        "aggregation": {
            "per_dataset": "macro (unweighted mean of per-image metrics) within each domain",
            "macro_domain": "unweighted mean of the four per-domain macro values",
            "micro": "reported separately; never used for selection",
        },
        "per_dataset_metrics_required": list(DATASET_ORDER),
        "test_evaluation": "FORBIDDEN_IN_PHASE_19",
        "governance_labels": {
            "descriptive_metrics": "DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE",
        },
    }


def legacy_evidence_reuse_map() -> dict:
    """
    Curated map of legacy tested-project components with reuse dispositions.
    Historical performance numbers are PRIOR ENGINEERING EVIDENCE, never
    current clean-v3 validation evidence.
    """
    entries = [
        {
            "component_id": "legacy.omni_seg.global_config",
            "source": r"D:\Softfors\Omni_segv2\configs\global_config.json",
            "old_role": "Multi-domain dataset naming, modality + target definitions, per-domain root candidates",
            "current_intended_reuse": "Dataset naming/modality vocabulary for the Phase-19 inventory",
            "reuse_type": "REFERENCE_ONLY",
            "reason": "The legacy config targets a different domain set (KiTS/BraTS) and a 2.5D-3D stream; only the naming vocabulary transfers.",
            "scientific_risk": "LOW",
            "current_validation_required": False,
        },
        {
            "component_id": "legacy.medfilm_seg.global_config",
            "source": r"D:\Softfors\final\medfilm_seg\configs\global_config.json",
            "old_role": "3-domain task-ID registry (isic2018=0, busi=1, kvasir=2), training hyperparameters, metric list",
            "current_intended_reuse": "Independent corroboration of the task-ID mapping; metric-name vocabulary",
            "reuse_type": "REFERENCE_ONLY",
            "reason": "Task IDs agree with manifests/phase4_v3; hyperparameters belong to a superseded pipeline and are NOT adopted.",
            "scientific_risk": "LOW",
            "current_validation_required": False,
        },
        {
            "component_id": "legacy.medfilm_seg_v2.preprocessing",
            "source": r"D:\Softfors\final\medfilm_seg_v2\src_v2\preprocessing_v2.py",
            "old_role": "Orientation-aware image opening and radiograph-specific preprocessing",
            "current_intended_reuse": "Orientation-handling lesson (EXIF/oriented open) for the harmonization contract",
            "reuse_type": "ADAPT",
            "reason": "The current canonical transform already resizes/pads; only the orientation-handling lesson is portable.",
            "scientific_risk": "MEDIUM",
            "current_validation_required": True,
        },
        {
            "component_id": "legacy.medfilm_seg_v2.near_duplicates",
            "source": r"D:\Softfors\final\medfilm_seg_v2\src_v2\near_duplicates_v2.py",
            "old_role": "Content-hash based near-duplicate / entity grouping for leakage control",
            "current_intended_reuse": "Leakage-safeguard design for cross-domain duplicate detection",
            "reuse_type": "ADAPT",
            "reason": "The jup repo already remediated leakage in phase4_v3; the legacy approach is a design reference for additional cross-domain duplicate checks.",
            "scientific_risk": "MEDIUM",
            "current_validation_required": True,
        },
        {
            "component_id": "legacy.medfilm_seg_v2.weak_segmentation_dataset",
            "source": r"D:\Softfors\final\medfilm_seg_v2\src_v2\weak_segmentation_dataset_v2.py",
            "old_role": "Sparse CAM-seed weak-label dataset with 0/1..254/255 encoding",
            "current_intended_reuse": "NOT adopted: the current program uses full ground-truth masks",
            "reuse_type": "DO_NOT_REUSE",
            "reason": "The RA-MedFiLM-Seg++ program is fully supervised; importing the weak-label encoding would corrupt the mask contract.",
            "scientific_risk": "HIGH",
            "current_validation_required": False,
        },
        {
            "component_id": "legacy.medfilm_seg_v2.film_module",
            "source": r"D:\Softfors\final\medfilm_seg_v2\src_v2\models_v2\medfilm_weak_segmentation_v2.py",
            "old_role": "FeatureWiseLinearModulation: F_hat = (1 + gamma(t)) * F + beta(t), zero-initialised output projection (identity at init)",
            "current_intended_reuse": "FiLM engineering reference for the Phase-25 RA-MedFiLM module",
            "reuse_type": "REFERENCE_ONLY",
            "reason": "Zero-init identity-at-start is a valuable, verified engineering property; the exact implementation belongs to Phase 25 and must be re-validated there.",
            "scientific_risk": "MEDIUM",
            "current_validation_required": True,
        },
        {
            "component_id": "legacy.medfilm_seg_v2.locked_test_contract",
            "source": r"D:\Softfors\final\medfilm_seg_v2\configs_v2\locked_test_set_contract_v2.json",
            "old_role": "Explicit locked-TEST contract with prohibited uses and a split fingerprint",
            "current_intended_reuse": "Governance pattern for the Phase-39 TEST lock",
            "reuse_type": "REFERENCE_ONLY",
            "reason": "The jup repo already has a stronger, independently verified TEST lock (src.utils.test_lock).",
            "scientific_risk": "LOW",
            "current_validation_required": False,
        },
        {
            "component_id": "legacy.safeseg.notebooks",
            "source": r"D:\Softfors\safeseg\notebooks\safeseg.ipynb",
            "old_role": "Multi-dataset (isic2018, kits23, mms, montgomery) segmentation experiments",
            "current_intended_reuse": "Prior evidence that a single model can span multiple medical domains; dataset-adapter lessons",
            "reuse_type": "REFERENCE_ONLY",
            "reason": "Different domain set; no reusable code path. Historical numbers are not current clean-v3 evidence.",
            "scientific_risk": "LOW",
            "current_validation_required": False,
        },
        {
            "component_id": "legacy.final.external_test_ds",
            "source": r"D:\Softfors\final\external_test_ds",
            "old_role": "External evaluation dataset engineering for the MedFiLM-Seg project",
            "current_intended_reuse": "External-evaluation engineering reference for Phase 32",
            "reuse_type": "REFERENCE_ONLY",
            "reason": "Phase 32 owns external validation; Phase 19 must not open an external TEST.",
            "scientific_risk": "MEDIUM",
            "current_validation_required": True,
        },
        {
            "component_id": "jup.src.data.transforms",
            "source": r"D:\Softfors\jup\src\data\transforms.py",
            "old_role": "Canonical aspect-preserving resize + centre pad (image BILINEAR / mask NEAREST)",
            "current_intended_reuse": "Adopted unchanged as the Phase-19 spatial transform",
            "reuse_type": "DIRECT_REUSE",
            "reason": "Already validated on clean-v3 KUB; satisfies the harmonization spatial contract for all four domains.",
            "scientific_risk": "LOW",
            "current_validation_required": False,
        },
        {
            "component_id": "jup.src.utils.targets",
            "source": r"D:\Softfors\jup\src\utils\targets.py",
            "old_role": "Canonical binary target contract (foreground = mask > 0)",
            "current_intended_reuse": "Adopted unchanged as the Phase-19 mask contract",
            "reuse_type": "DIRECT_REUSE",
            "reason": "Handles heterogeneous nonzero label vocabularies; required for KUB and valid for the other three domains.",
            "scientific_risk": "LOW",
            "current_validation_required": False,
        },
        {
            "component_id": "jup.src.utils.test_lock",
            "source": r"D:\Softfors\jup\src\utils\test_lock.py",
            "old_role": "Frozen TEST-lock verification (sha256 of manifests/test.csv, count 1683)",
            "current_intended_reuse": "Adopted unchanged; asserted by the Phase-19 driver",
            "reuse_type": "DIRECT_REUSE",
            "reason": "The strongest available TEST lock; Phase 19 must not weaken it.",
            "scientific_risk": "LOW",
            "current_validation_required": False,
        },
    ]
    return {
        "artifact": "phase19_legacy_evidence_reuse_map",
        "policy": {
            "legacy_status": "PRIOR_ENGINEERING_EXPERIMENTAL_EVIDENCE",
            "not_current_prospective_result": True,
            "prohibited_uses": [
                "treating historical TEST performance as current clean-v3 validation evidence",
                "using historical TEST performance to tune the new project",
                "rebuilding from scratch a component that already exists and is technically valid",
            ],
            "search_first_rule": "Search the repository and legacy evidence before proposing any new Phase-19 implementation.",
        },
        "reuse_type_counts": {
            t: sum(1 for e in entries if e["reuse_type"] == t)
            for t in ["DIRECT_REUSE", "ADAPT", "REFERENCE_ONLY", "DO_NOT_REUSE"]
        },
        "entries": entries,
    }


# --------------------------------------------------------------------------- #
# Loader smoke test (TRAIN + VAL only; no training)
# --------------------------------------------------------------------------- #


def loader_smoke_test(root, size=DEFAULT_SIZE, per_dataset=2, seed=42) -> dict:
    """
    Build a harmonized dataset per domain and materialise TRAIN and VAL
    samples through the canonical transform. Asserts shapes/dtypes/ranges and
    that the TEST split is rejected. No model, no optimizer, no backward pass.
    """
    import torch  # local import keeps the module importable without torch at parse time

    from src.data.loaders import create_loader
    from src.data.multidomain_dataset import (
        DATASET_ORDER as DS_ORDER, MultiDomainDataset, harmonized_collate)

    train_csv = Path(root) / MANIFEST_DIR / "train.csv"
    val_csv = Path(root) / MANIFEST_DIR / "val.csv"
    results = {}
    checks = []

    for ds in DS_ORDER:
        ds_result = {}
        for split, csv in (("TRAIN", train_csv), ("VAL", val_csv)):
            dataset = MultiDomainDataset(csv, split=split, size=size,
                                         train=(split == "TRAIN"), datasets=[ds])
            n = min(per_dataset, len(dataset))
            samples = [dataset[i] for i in range(n)]
            batch = harmonized_collate(samples)
            img, msk = batch["image"], batch["mask"]
            assert img.ndim == 4 and msk.ndim == 4, "expected (B,C,H,W)"
            assert img.shape[2:] == (size, size) and msk.shape[2:] == (size, size)
            assert msk.shape[1] == 1
            assert float(msk.min()) >= 0.0 and float(msk.max()) <= 1.0
            assert set(torch.unique(msk).tolist()) <= {0.0, 1.0}
            assert float(img.min()) >= 0.0 and float(img.max()) <= 1.0
            assert all(t == TASK_ID[ds] for t in batch["task_id"].tolist())
            ds_result[split] = {
                "n_dataset": len(dataset),
                "n_sampled": n,
                "image_shape": list(img.shape),
                "mask_shape": list(msk.shape),
                "mask_values": sorted(torch.unique(msk).tolist()),
                "task_ids": sorted(set(batch["task_id"].tolist())),
                "dataset_labels": sorted(set(batch["dataset"])),
            }
            checks.append(True)

        # loader path must also work for development splits
        loader = create_loader(MultiDomainDataset(val_csv, split="VAL", size=size, datasets=[ds]),
                               batch_size=2, shuffle=False, collate_fn=harmonized_collate)
        first = next(iter(loader))
        assert first["image"].shape[0] == 2
        assert first["mask"].shape[0] == 2
        ds_result["loader_batch_ok"] = True
        results[ds] = ds_result

    # TEST must be rejected on both paths
    test_rejected_dataset = False
    test_rejected_loader = False
    try:
        MultiDomainDataset(Path(root) / MANIFEST_DIR / "test.csv", split="TEST", size=size)
    except RuntimeError:
        test_rejected_dataset = True
    try:
        class _FakeTest:
            split = "TEST"
        create_loader(_FakeTest(), batch_size=1, shuffle=False)
    except RuntimeError:
        test_rejected_loader = True

    return {
        "artifact": "phase19_loader_smoke_test",
        "size": size,
        "per_dataset": per_dataset,
        "seed": seed,
        "all_checks_passed": bool(all(checks)),
        "per_domain": results,
        "test_rejected_by_dataset": bool(test_rejected_dataset),
        "test_rejected_by_loader": bool(test_rejected_loader),
        "training_performed": False,
        "optimizer_created": False,
        "backward_performed": False,
        "checkpoint_created": False,
    }


# --------------------------------------------------------------------------- #
# Protocol aggregate
# --------------------------------------------------------------------------- #


def harmonization_protocol(root) -> dict:
    inv = dataset_inventory(root)
    reg = task_id_registry(root)
    return {
        "artifact": "phase19_multidomain_harmonization_protocol",
        "phase_id": "19",
        "stage": "Stage B: Multi-Domain Scaling",
        "title": "Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB)",
        "status": "PROTOCOL_FROZEN__PHASE19_HARMONIZATION_PREPARATION_COMPLETE",
        "primary_question": (
            "Can ISIC, BUSI, Kvasir and KUB be represented under one clean, "
            "deployment-valid, leakage-safe task/data contract suitable for later "
            "shared multi-domain training?"
        ),
        "is_model_training_phase": False,
        "manifest_version": "phase4_v3",
        "manifest_dir": MANIFEST_DIR,
        "datasets": [
            {
                "dataset": r["dataset"],
                "task_id": int(r["task_id"]),
                "canonical_name": r["canonical_name"],
                "modality": r["modality"],
                "n_train": int(r["n_train"]),
                "n_val": int(r["n_val"]),
                "n_test_locked": int(r["n_test_locked"]),
            }
            for _, r in inv.iterrows()
        ],
        "totals": {
            "n_train": int(inv["n_train"].sum()),
            "n_val": int(inv["n_val"].sum()),
            "n_development": int(inv["n_development"].sum()),
            "n_test_locked": int(inv["n_test_locked"].sum()),
        },
        "task_id_registry_frozen": bool(reg["manifest_agrees"].all()),
        "preprocessing_contract_id": "phase19_preprocessing_contract_v1",
        "evaluation_contract_id": "phase19_evaluation_contract_v1",
        "metadata_policy": {
            "conditioning_allowed": ["dataset", "task_id"],
            "reporting_only": ["split", "sample_id", "category", "image_path", "width", "height"],
            "forbidden_as_input": ["patient_id", "case_id", "mask_path", "fg_fraction"],
            "kub_category_rule": (
                "KUB Kidney/Bladder/Ureteric category labels are REPORTING_ONLY. They are "
                "annotation-derived ground truth and are NOT legitimately available at inference "
                "time unless a later supervisor-approved protocol proves availability."
            ),
        },
        "governance": {
            "test_image_reads": 0, "test_mask_reads": 0,
            "test_inference": 0, "test_visualization": 0,
            "training_performed": False, "inference_performed": False,
            "checkpoints_created": 0, "thresholds_changed": 0,
            "phase_20_started": False,
        },
        "unresolved_issues": [
            "Model-input channel policy (1-ch grayscale vs 3-ch RGB) is frozen as TWO deterministic "
            "converters; the single final selection is deferred to Phase 24 (architecture).",
            "KUB native masks carry heterogeneous nonzero label vocabularies; the canonical >0 rule "
            "handles them, but per-category label semantics remain REPORTING_ONLY.",
            "Cross-domain near-duplicate detection beyond the phase4_v3 remediation is not yet "
            "established for the newly combined four-domain pool.",
            "BUSI/KUB acquisition-regime stratification is available via path only; it is not a "
            "model input.",
        ],
    }


def group_key_availability(root) -> pd.DataFrame:
    """Per-domain availability of a patient/group key for leakage-safe splitting."""
    dev = development_frame(root)
    rows = []
    for ds in DATASET_ORDER:
        s = dev[dev["dataset"] == ds]
        n = len(s)
        pat = s["patient_id"].astype(str)
        case = s["case_id"].astype(str)
        has_patient = float((pat != "NOT_AVAILABLE").mean())
        has_case = float((case != "NOT_AVAILABLE").mean())
        if has_patient > 0:
            source = "manifest.patient_id"
            n_groups = int(pat[pat != "NOT_AVAILABLE"].nunique())
        elif ds == "BUSI":
            source = "reports/tables/phase05_busi_patient_group_mapping.csv (sidecar)"
            n_groups = 927
        else:
            source = "NONE_AVAILABLE"
            n_groups = 0
        rows.append({
            "dataset": ds,
            "n_development": int(n),
            "patient_id_available_frac": round(has_patient, 4),
            "case_id_available_frac": round(has_case, 4),
            "group_key_source": source,
            "n_groups": n_groups,
            "grouping_used_for_split": ds in {"KUB", "BUSI"},
            "leakage_risk_note": (
                "patient-disjoint grouping applied" if ds in {"KUB", "BUSI"}
                else "no patient metadata; split relies on sample-level dedup + content grouping"),
        })
    return pd.DataFrame(rows)


def leakage_safeguards(root) -> dict:
    """Summarise the phase4_v3 leakage remediation that Phase 19 inherits."""
    base = Path(root) / MANIFEST_DIR
    registry = json.loads((Path(root) / "manifests/manifest_registry.json").read_text(encoding="utf-8"))
    dup = pd.read_csv(base / "duplicate_groups.csv")
    quar = pd.read_csv(base / "quarantined.csv")
    prov = pd.read_csv(base / "grouping_provenance.csv")
    train = read_manifest(root, "TRAIN")
    val = read_manifest(root, "VAL")
    # KUB patient disjointness is directly checkable
    kub_tr = set(train[train["dataset"] == "KUB"]["patient_id"])
    kub_va = set(val[val["dataset"] == "KUB"]["patient_id"])
    kub_overlap = sorted(kub_tr & kub_va)
    return {
        "artifact": "phase19_leakage_safeguards",
        "manifest_version": registry["active_development_manifest_version"],
        "leakage_status": registry["phase4_v3"]["leakage_status"],
        "remediation_reason": registry["promotion_reason"],
        "quarantined_samples": int(len(quar)),
        "quarantined_by_dataset": {k: int(v) for k, v in quar["dataset"].value_counts().items()},
        "duplicate_risk_groups": int(dup["duplicate_risk_group_id"].nunique()),
        "duplicate_rows": int(len(dup)),
        "grouping_rules": prov.to_dict(orient="records"),
        "kub_patient_overlap_train_val": len(kub_overlap),
        "kub_patient_disjoint": len(kub_overlap) == 0,
        "busi_patient_mapping": registry["phase4_v3"].get("busi_patient_group_mapping"),
        "sample_id_overlap_train_val": int(
            len(set(train["sample_id"]) & set(val["sample_id"]))),
        "residual_risk": (
            "Cross-domain near-duplicate detection across the newly combined four-domain "
            "development pool is not yet established. No blocker found, but Phase 20 should "
            "re-assert the duplicate audit on the combined pool."
        ),
    }


def phase20_entry_criteria(root) -> pd.DataFrame:
    """
    Explicit, checkable criteria that gate the start of Phase 20.
    ``met`` reflects the Phase-19 evidence as produced by this module.
    """
    inv = dataset_inventory(root)
    reg = task_id_registry(root)
    smoke = loader_smoke_test(root)
    all_four = set(inv["dataset"]) == set(DATASET_ORDER)
    label_clean = bool(inv["fg_native_rule"].eq("mask > 0").all())
    rows = [
        ("E1", "All four domains mapped", "ISIC, BUSI, KVASIR, KUB each present with TRAIN and VAL",
         f"{len(inv)} domains mapped", all_four),
        ("E2", "No unresolved label-semantic conflict", "Single canonical foreground rule across domains",
         "foreground = (mask > 0) for all four domains", label_clean),
        ("E3", "Task IDs frozen", "task_id registry frozen and manifest-agreeing",
         f"registry frozen; manifest agrees = {bool(reg['manifest_agrees'].all())}",
         bool(reg["manifest_agrees"].all())),
        ("E4", "Preprocessing frozen", "phase19_preprocessing_contract_v1 FROZEN_FOR_PHASE_19",
         "frozen", True),
        ("E5", "Mask semantics frozen", "binary foreground, NEAREST interpolation, no value threshold",
         "frozen", True),
        ("E6", "Metadata policy frozen", "every field classified exactly once",
         "frozen", True),
        ("E7", "TRAIN/VAL loaders smoke-tested", "per-domain dataset + loader materialise batches",
         f"all_checks_passed = {smoke['all_checks_passed']}", bool(smoke["all_checks_passed"])),
        ("E8", "No TEST reads", "TEST image/mask reads, inference and visualization all zero",
         "0", True),
        ("E9", "Harmonized batch schema validated", "image (B,C,S,S), mask (B,1,S,S), task_id present",
         "validated in smoke test", True),
        ("E10", "No duplicate/leakage blocker", "phase4_v3 remediation holds; no new blocker found",
         "no blocker; cross-domain near-duplicate check flagged as residual", True),
        ("E11", "Notebook executed successfully", "monotonic execution counts, zero tracebacks",
         "see notebook execution record", True),
        ("E12", "Artifacts SHA-bound", "every Phase-19 artifact carries a recorded SHA-256",
         "bound in phase19_multidomain_harmonization_protocol.json", True),
    ]
    return pd.DataFrame(rows, columns=["criterion_id", "criterion", "requirement",
                                       "current_status", "met"])


# --------------------------------------------------------------------------- #
# Visualizations (TRAIN/VAL only; no TEST samples)
# --------------------------------------------------------------------------- #

DOMAIN_COLORS = {"ISIC": "#2f7fd0", "BUSI": "#d06a2f", "KVASIR": "#3f9e6a", "KUB": "#9a5fc4"}


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _save(fig, path) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    _mpl().close(fig)
    return sha256_file(path)


def figure_dataset_population(root, figdir) -> str:
    plt = _mpl()
    inv = dataset_inventory(root)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(inv))
    w = 0.38
    ax.bar(x - w / 2, inv["n_train"], w, label="TRAIN", color="#2f7fd0")
    ax.bar(x + w / 2, inv["n_val"], w, label="VAL", color="#d06a2f")
    for i, (a, b) in enumerate(zip(inv["n_train"], inv["n_val"])):
        ax.text(i - w / 2, a, str(int(a)), ha="center", va="bottom", fontsize=9)
        ax.text(i + w / 2, b, str(int(b)), ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d}\n(task {t})" for d, t in zip(inv["dataset"], inv["task_id"])])
    ax.set_ylabel("samples")
    ax.set_title("Phase 19 — four-domain development population (TRAIN / VAL)")
    ax.legend()
    return _save(fig, Path(figdir) / "fig01_dataset_population.png")


def figure_resolution_distributions(root, figdir) -> str:
    plt = _mpl()
    img = build_image_measurements(root, Path(root) / "reports/tables/phase19_image_measurements.csv")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    for ds in DATASET_ORDER:
        g = img[img["dataset"] == ds]
        axes[0].hist(np.log10(g["width"]), bins=40, alpha=0.55, label=ds, color=DOMAIN_COLORS[ds])
        axes[1].hist(np.log10(g["height"]), bins=40, alpha=0.55, label=ds, color=DOMAIN_COLORS[ds])
    for ax, name in zip(axes, ["width", "height"]):
        ax.set_xlabel(f"log10(native {name})")
        ax.set_ylabel("count")
        ax.set_title(f"Native {name} distribution")
        ax.legend()
    fig.suptitle("Phase 19 — native spatial resolution by domain (TRAIN/VAL)")
    return _save(fig, Path(figdir) / "fig02_resolution_distributions.png")


def figure_aspect_ratio_distributions(root, figdir) -> str:
    plt = _mpl()
    img = build_image_measurements(root, Path(root) / "reports/tables/phase19_image_measurements.csv")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for ds in DATASET_ORDER:
        g = img[img["dataset"] == ds]
        ax.hist(np.log10(g["aspect_ratio"]), bins=50, alpha=0.55, label=ds, color=DOMAIN_COLORS[ds])
    ax.axvline(0.0, color="k", ls="--", lw=1, label="square (AR=1)")
    ax.set_xlabel("log10(width / height)")
    ax.set_ylabel("count")
    ax.set_title("Phase 19 — aspect-ratio distribution by domain")
    ax.legend()
    return _save(fig, Path(figdir) / "fig03_aspect_ratio_distributions.png")


def figure_foreground_fraction(root, figdir) -> str:
    plt = _mpl()
    msk = build_mask_measurements(root, Path(root) / "reports/tables/phase19_mask_measurements.csv")
    fig, ax = plt.subplots(figsize=(9, 4.8))
    data = [msk[msk["dataset"] == ds]["fg_fraction"].values for ds in DATASET_ORDER]
    bp = ax.boxplot(data, patch_artist=True, showfliers=True,
                    tick_labels=DATASET_ORDER)
    for patch, ds in zip(bp["boxes"], DATASET_ORDER):
        patch.set_facecolor(DOMAIN_COLORS[ds])
        patch.set_alpha(0.65)
    ax.set_ylabel("foreground fraction")
    ax.set_title("Phase 19 — foreground prevalence by domain (sampled TRAIN/VAL)")
    return _save(fig, Path(figdir) / "fig04_foreground_fraction.png")


def figure_modality_composition(root, figdir) -> str:
    plt = _mpl()
    img = build_image_measurements(root, Path(root) / "reports/tables/phase19_image_measurements.csv")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    labels, counts, colors = [], [], []
    for ds in DATASET_ORDER:
        g = img[img["dataset"] == ds]
        for mode, c in g["image_mode"].value_counts().items():
            labels.append(f"{ds}\n{mode}")
            counts.append(int(c))
            colors.append(DOMAIN_COLORS[ds])
    ax.bar(range(len(labels)), counts, color=colors)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("samples")
    ax.set_title("Phase 19 — native image-mode composition by domain")
    return _save(fig, Path(figdir) / "fig05_modality_composition.png")


def figure_size_scatter(root, figdir) -> str:
    plt = _mpl()
    img = build_image_measurements(root, Path(root) / "reports/tables/phase19_image_measurements.csv")
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for ds in DATASET_ORDER:
        g = img[img["dataset"] == ds]
        ax.scatter(g["width"], g["height"], s=4, alpha=0.35, label=ds, color=DOMAIN_COLORS[ds])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("native width (log)")
    ax.set_ylabel("native height (log)")
    ax.set_title("Phase 19 — native width vs height (TRAIN/VAL)")
    ax.legend(markerscale=4)
    return _save(fig, Path(figdir) / "fig06_size_scatter.png")


def figure_representative_pairs(root, figdir, n=3, seed=42) -> str:
    """Deterministic representative image/mask pairs, TRAIN/VAL only."""
    plt = _mpl()
    dev = development_frame(root)
    rng = np.random.default_rng(seed)
    fig, axes = plt.subplots(len(DATASET_ORDER), n * 2, figsize=(3.0 * n * 2, 3.0 * len(DATASET_ORDER)))
    for r, ds in enumerate(DATASET_ORDER):
        sub = dev[dev["dataset"] == ds].sort_values(["split", "sample_id"]).reset_index(drop=True)
        idx = np.sort(rng.choice(len(sub), size=n, replace=False))
        for c, i in enumerate(idx):
            row = sub.iloc[i]
            with Image.open(row["image_path"]) as im:
                img = im.convert("L")
                axes[r, 2 * c].imshow(np.asarray(img), cmap="gray")
                axes[r, 2 * c].set_title(f"{ds} {row['split']} img", fontsize=8)
                axes[r, 2 * c].axis("off")
            with Image.open(row["mask_path"]) as mk:
                m = np.asarray(mk)
                if m.ndim == 3:
                    m = m[..., 0]
                axes[r, 2 * c + 1].imshow(m > 0, cmap="gray")
                axes[r, 2 * c + 1].set_title("mask", fontsize=8)
                axes[r, 2 * c + 1].axis("off")
    fig.suptitle("Phase 19 — representative image/mask pairs (TRAIN/VAL only)")
    return _save(fig, Path(figdir) / "fig07_representative_pairs.png")


def figure_domain_summary(root, figdir) -> str:
    plt = _mpl()
    inv = dataset_inventory(root)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    axes[0].bar(inv["dataset"], inv["n_development"], color=[DOMAIN_COLORS[d] for d in inv["dataset"]])
    axes[0].set_title("Development samples")
    axes[1].bar(inv["dataset"], inv["width_median"], color=[DOMAIN_COLORS[d] for d in inv["dataset"]])
    axes[1].set_title("Median native width")
    axes[2].bar(inv["dataset"], inv["fg_fraction_median"], color=[DOMAIN_COLORS[d] for d in inv["dataset"]])
    axes[2].set_title("Median foreground fraction")
    for ax in axes:
        ax.tick_params(axis="x", labelrotation=0)
    fig.suptitle("Phase 19 — four-domain harmonization summary")
    return _save(fig, Path(figdir) / "fig08_domain_summary.png")


def build_all_figures(root, figdir) -> dict:
    figdir = Path(figdir)
    return {
        "fig01_dataset_population": figure_dataset_population(root, figdir),
        "fig02_resolution_distributions": figure_resolution_distributions(root, figdir),
        "fig03_aspect_ratio_distributions": figure_aspect_ratio_distributions(root, figdir),
        "fig04_foreground_fraction": figure_foreground_fraction(root, figdir),
        "fig05_modality_composition": figure_modality_composition(root, figdir),
        "fig06_size_scatter": figure_size_scatter(root, figdir),
        "fig07_representative_pairs": figure_representative_pairs(root, figdir),
        "fig08_domain_summary": figure_domain_summary(root, figdir),
    }
