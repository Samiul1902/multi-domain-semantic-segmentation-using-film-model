"""H3 (A_TARGET_SUPPORT_REDESIGN) — AUTHORITATIVE size-adaptive sigma calibration.

PRE-EXECUTION RECONCILIATION (replaces the prior h3_calibrate_size_adaptive_sigma.py).

Key corrections vs the superseded calibration:
  * Population is bound to manifests/phase4_v3/train.csv (clean-v3 TRAIN). Orphan
    samples not present in any clean-v3 manifest split are QUARANTINED.
  * Component identity is preserved by (sample_id, component_id). We do NOT
    relabel a combined downsampled mask (that merges neighbours / drops tinies /
    changes cardinality). For every original GT component we map its centroid
    through the EXACT H3 runtime transform (cx*scale+left)/4, (cy*scale+top)/4
    and read the 128-space foreground area at that point -- which is precisely
    what src/data/kub_localizer_dataset.py does at training time.
  * A_ref = p75 of those per-component 128-space areas (authoritative ONLY path).

No VAL/TEST data is read. No model, no CUDA. TRAIN-only geometry audit.

Outputs
-------
  reports/tables/h3_v2_component_area_audit.csv   (per (sample_id,component_id))
  reports/tables/h3_v2_area_distribution.json     (percentiles, A_ref, digests, ND)
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.inference.heatmap_targets import heatmap_space_component_areas

T = ROOT / "reports/tables"
MAN = ROOT / "manifests" / "phase4_v3"
SIGMA_MIN, SIGMA_MAX = 0.35, 0.75


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def digest(seq):
    h = hashlib.sha256()
    for x in sorted(seq):
        h.update(str(x).encode())
        h.update(b"\n")
    return h.hexdigest()


def sigma_of(a, a_ref):
    a = np.maximum(a, 0.0)
    return np.clip(SIGMA_MIN + (SIGMA_MAX - SIGMA_MIN) * np.sqrt(a / a_ref), SIGMA_MIN, SIGMA_MAX)


# ---------------------------------------------------------------------------
# Canonical clean-v3 TRAIN FULL_FIELD population (bound to train.csv)
# ---------------------------------------------------------------------------
train_manifest = pd.read_csv(MAN / "train.csv")
train_ids = set(train_manifest["sample_id"].astype(str))

samples = pd.read_csv(T / "kub_train_samples_sized.csv")
comp = pd.read_csv(T / "kub_train_components_sized.csv")

ff = samples[(samples["view_type"] == "FULL_FIELD") &
             (samples["sample_id"].astype(str).isin(train_ids))].reset_index(drop=True)
canon_train_ids = set(ff["sample_id"].astype(str))
orphan_train = set(samples[(samples["view_type"] == "FULL_FIELD")]["sample_id"].astype(str)) - train_ids

stratum_lookup = {
    (r.sample_id, int(r.component_id)): r.size_stratum
    for r in comp.itertuples()
}

# ---------------------------------------------------------------------------
# Per-GT-component area mapping (exact runtime transform, no augmentation)
# ---------------------------------------------------------------------------
rows = []
for s in ff.itertuples():
    mask = Image.open(s.mask_path).convert("L")
    w, h = mask.size
    scale = min(512 / w, 512 / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    m_small = mask.resize((rw, rh), Image.Resampling.NEAREST)
    m_arr = np.asarray(m_small) > 0
    padded = np.zeros((512, 512), dtype=bool)
    left = (512 - rw) // 2
    top = (512 - rh) // 2
    padded[top:top + rh, left:left + rw] = m_arr

    label128, areas128 = heatmap_space_component_areas(padded, 512, 128)
    label512, areas512 = heatmap_space_component_areas(padded, 512, 512)  # factor 1 -> exact 512 map

    orig = np.asarray(mask) > 0
    labeled_o, n_o = label(orig, np.ones((3, 3), int))
    for cid in range(1, n_o + 1):
        ys, xs = np.where(labeled_o == cid)
        cy_o, cx_o = ys.mean(), xs.mean()
        original_area = int((labeled_o == cid).sum())
        # 512-space area for this component
        cy_512 = int(round(cy_o * scale + top))
        cx_512 = int(round(cx_o * scale + left))
        cy_512 = max(0, min(511, cy_512))
        cx_512 = max(0, min(511, cx_512))
        lbl512 = int(label512[cy_512, cx_512])
        area_512 = int(areas512[lbl512]) if lbl512 > 0 else 0
        # 128-space area (exact runtime mapping: /factor, factor=4)
        cy_128 = (cy_o * scale + top) / 4.0
        cx_128 = (cx_o * scale + left) / 4.0
        icy = max(0, min(127, int(round(cy_128))))
        icx = max(0, min(127, int(round(cx_128))))
        lbl128 = int(label128[icy, icx])
        area_128 = int(areas128[lbl128]) if lbl128 > 0 else 0
        stratum = stratum_lookup.get((s.sample_id, cid))
        rows.append({
            "sample_id": s.sample_id,
            "component_id": cid,
            "original_area": original_area,
            "area_512": area_512,
            "area_128": area_128,
            "centroid_x": float(cx_o),
            "centroid_y": float(cy_o),
            "survives_rasterization": bool(area_128 > 0),
            "size_stratum": stratum if stratum is not None else "UNMATCHED",
        })

audit = pd.DataFrame(rows)
audit.to_csv(T / "h3_v2_component_area_audit.csv", index=False)

area128 = audit["area_128"].to_numpy(dtype=float)
A_REF = float(np.percentile(area128, 75))
audit["sigma"] = sigma_of(area128, A_REF)

# ---------------------------------------------------------------------------
# Non-degeneracy verification
# ---------------------------------------------------------------------------
sigma = audit["sigma"].to_numpy()
n_distinct = int(np.unique(np.round(sigma, 6)).size)
frac_ceil = float((sigma >= SIGMA_MAX - 1e-9).mean())
frac_floor = float((sigma <= SIGMA_MIN + 1e-9).mean())
tiny_mask = (audit["size_stratum"] == "TINY").to_numpy()
nontiny_mask = audit["size_stratum"].isin(["SMALL", "MEDIUM", "LARGE"]).to_numpy()
tiny_sigma = float(np.median(sigma[tiny_mask])) if tiny_mask.any() else None
nontiny_sigma = float(np.median(sigma[nontiny_mask])) if nontiny_mask.any() else None

pcts = {}
for p in [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]:
    pcts[f"p{p}"] = float(np.percentile(area128, p))

canon_comp_ids = list(zip(audit["sample_id"].astype(str), audit["component_id"].astype(int)))

out = {
    "status": "AUTHORITATIVE_TRAIN_ONLY_CALIBRATION__CANONICAL_CLEAN_V3",
    "axis": "A_PROPOSAL_SUPPLY_RECALL_LIMITATION",
    "intervention": "A_TARGET_SUPPORT_REDESIGN",
    "population": {
        "source_manifest": "manifests/phase4_v3/train.csv",
        "manifest_sha256": sha256_file(MAN / "train.csv"),
        "filter": "view_type == FULL_FIELD AND sample_id IN clean-v3 TRAIN manifest",
        "n_images": int(len(canon_train_ids)),
        "n_components": int(len(audit)),
        "train_sample_id_digest_sha256": digest(canon_train_ids),
        "train_component_id_digest_sha256": digest(canon_comp_ids),
        "orphan_samples_quarantined": sorted(orphan_train),
        "orphan_count": int(len(orphan_train)),
    },
    "mapping": {
        "method": "per-GT-component: original centroid -> (cx*scale+left)/4,(cy*scale+top)/4 -> 128-space label area (EXACT H3 runtime path; NO relabeling of combined downsampled mask)",
        "scale": "min(512/w,512/h); aspect-preserving NEAREST resize + centre pad to 512",
        "note": "Component identity preserved by (sample_id, component_id). 128-space area is the label area at the component's mapped centroid, matching kub_localizer_dataset.py.",
    },
    "A_ref_definition": "p75 of per-component 128-space areas over canonical clean-v3 TRAIN FULL_FIELD",
    "A_ref": A_REF,
    "sigma_formula": "sigma_i = clip(0.35 + 0.40 * sqrt(A128_i / A_ref), 0.35, 0.75)",
    "area128_percentiles": pcts,
    "zero_area_count": int((area128 == 0).sum()),
    "zero_area_handling": "Deterministic frozen rule: area_128 == 0 -> sigma = sigma_min (0.35). The Gaussian is still drawn at the centroid; a zero-area component is treated as the smallest possible object (sharpest peak). No VAL/TEST influence.",
    "non_degeneracy": {
        "n_distinct_sigma_levels": n_distinct,
        "frac_at_ceil_0.75": frac_ceil,
        "frac_at_floor_0.35": frac_floor,
        "median_sigma": float(np.median(sigma)),
        "tiny_median_sigma": tiny_sigma,
        "nontiny_median_sigma": nontiny_sigma,
        "tiny_lt_nontiny": bool(tiny_sigma is not None and nontiny_sigma is not None and tiny_sigma < nontiny_sigma),
        "all_in_bounds": bool(((sigma >= SIGMA_MIN - 1e-9) & (sigma <= SIGMA_MAX + 1e-9)).all()),
        "passed": bool(
            n_distinct > 1 and frac_ceil < 1.0 and frac_floor < 1.0
            and tiny_sigma is not None and nontiny_sigma is not None and tiny_sigma < nontiny_sigma
        ),
    },
    "superseded_calibrations": {
        "h3_aref_code_exact.json": {"p75": 14.0, "method": "relabeled 128-space components (n=1149) -- MERGES components, cardinality wrong -> superseded"},
        "h3_code_exact_sigma_distribution.json": {"p75": 12.0, "method": "relabeled direct 128-space (n=1078) -- relabeling, cardinality wrong -> superseded"},
        "reason_for_difference": "Both prior values relabeled the combined downsampled mask, which merges neighbouring components and drops tinies, changing component cardinality and inflating/deflating areas. The authoritative path preserves (sample_id,component_id) and reads the 128-area at each centroid, matching the runtime.",
    },
}

(T / "h3_v2_area_distribution.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
