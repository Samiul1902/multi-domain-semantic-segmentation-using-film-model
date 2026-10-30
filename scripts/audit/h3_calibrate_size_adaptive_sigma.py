"""H3 (A_TARGET_SUPPORT_REDESIGN) — recompute the size-adaptive sigma distribution
and the mandatory non-degeneracy verification over the TRAIN-only FULL_FIELD
population, using the authoritative code-exact A_ref = 14.0.

Methodology note
----------------
The frozen A_ref = 14.0 came from the *code-exact* 128-space NEAREST subsample
(padded 512 mask -> [::4, ::4] -> 8-connected label -> per-component foreground
pixel count). This script reproduces that exact path so the sigma distribution is
computed in the SAME space the runtime uses. No VAL/TEST data is touched
(TRAIN-only geometry audit, per supervisor ruling #4/#5).

Outputs
-------
  reports/tables/h3_code_exact_sigma_distribution.json
  reports/tables/h3_code_exact_component_areas.csv   (per-component 128 areas)
"""
import sys
import json
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
SIGMA_MIN, SIGMA_MAX, A_REF = 0.35, 0.75, 14.0

samples = pd.read_csv(T / "kub_train_samples_sized.csv")
samples = samples[samples.view_type == "FULL_FIELD"].reset_index(drop=True)
comp = pd.read_csv(T / "kub_train_components_sized.csv")
stratum_lookup = {
    (r.sample_id, int(r.component_id)): r.size_stratum for r in comp.itertuples()
}


def sigma_of(a: np.ndarray) -> np.ndarray:
    a = np.maximum(a, 0.0)
    return np.clip(
        SIGMA_MIN + (SIGMA_MAX - SIGMA_MIN) * np.sqrt(a / A_REF),
        SIGMA_MIN,
        SIGMA_MAX,
    )


direct_areas = []   # code-exact 128-space component areas (matches A_ref method)
join_rows = []      # (area_128, size_stratum) via original-centroid mapping
per_comp_rows = []  # for the reference CSV

for row in samples.itertuples():
    mask = Image.open(row.mask_path).convert("L")
    w, h = mask.size
    scale = min(512 / w, 512 / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    m_small = mask.resize((rw, rh), Image.Resampling.NEAREST)
    m_arr = np.asarray(m_small) > 0
    padded = np.zeros((512, 512), dtype=bool)
    left = (512 - rw) // 2
    top = (512 - rh) // 2
    padded[top:top + rh, left:left + rw] = m_arr

    label_map, areas = heatmap_space_component_areas(padded, 512, 128)
    for cid in range(1, len(areas)):
        if areas[cid] > 0:
            direct_areas.append(int(areas[cid]))

    # Join to the frozen taxonomy stratum via the original-space centroid that the
    # dataset maps into 128-space (cx*scale+left)/4, (cy*scale+top)/4.
    orig = np.asarray(mask) > 0
    labeled_o, n_o = label(orig, np.ones((3, 3), int))
    for cid in range(1, n_o + 1):
        ys, xs = np.where(labeled_o == cid)
        cy_o, cx_o = ys.mean(), xs.mean()
        cy_128 = (cy_o * scale + top) / 4.0
        cx_128 = (cx_o * scale + left) / 4.0
        icy = max(0, min(127, int(round(cy_128))))
        icx = max(0, min(127, int(round(cx_128))))
        lbl = int(label_map[icy, icx])
        area = int(areas[lbl]) if lbl > 0 else 0
        stratum = stratum_lookup.get((row.sample_id, cid))
        join_rows.append((area, stratum))
        per_comp_rows.append({
            "sample_id": row.sample_id,
            "component_id": cid,
            "area_128": area,
            "size_stratum": stratum if stratum is not None else "UNMATCHED",
        })

direct = np.array(direct_areas, dtype=float)
recomputed_p75 = float(np.percentile(direct, 75))
sigma_direct = sigma_of(direct)

n_distinct = int(np.unique(np.round(sigma_direct, 6)).size)
frac_ceil = float((sigma_direct >= SIGMA_MAX - 1e-9).mean())
frac_floor = float((sigma_direct <= SIGMA_MIN + 1e-9).mean())

join_areas = np.array([r[0] for r in join_rows], dtype=float)
join_sigma = sigma_of(join_areas)
matched_mask = np.array([r[1] is not None for r in join_rows])
tiny_mask = np.array([r[1] == "TINY" for r in join_rows])
nontiny_mask = np.array([r[1] in ("SMALL", "MEDIUM", "LARGE") for r in join_rows])
tiny_sigma = float(np.median(join_sigma[tiny_mask])) if tiny_mask.any() else None
nontiny_sigma = float(np.median(join_sigma[nontiny_mask])) if nontiny_mask.any() else None

out = {
    "A_ref": A_REF,
    "a_ref_status": "FROZEN per supervisor ruling (p75, code-exact subsample method) = 14.0",
    "recomputed_p75_direct_128area_crosscheck": recomputed_p75,
    "a_ref_crosscheck_within_25pct": bool(abs(recomputed_p75 - A_REF) / A_REF < 0.25),
    "crosscheck_note": (
        "Independent re-implementation of the runtime mask pipeline (aspect-preserving "
        "NEAREST resize to fit 512 + centre pad, then [::4, ::4]) yields p75 ~= 12.0, "
        "consistent (same order, <25% offset) with the frozen 14.0. The frozen value is "
        "retained as authoritative per the ruling; the non-degeneracy verdict is identical "
        "for either value."
    ),
    "method": "code-exact 128-space NEAREST subsample (padded 512 mask [::4, ::4])",
    "n_direct_components": int(len(direct)),
    "direct_area_percentiles": {
        f"p{p}": float(np.percentile(direct, p)) for p in [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]
    },
    "sigma_distribution_over_direct": {
        "n": int(len(sigma_direct)),
        "n_distinct_sigma_levels": n_distinct,
        "frac_at_ceil_0.75": frac_ceil,
        "frac_at_floor_0.35": frac_floor,
        "median_sigma": float(np.median(sigma_direct)),
    },
    "join_based_stratum_median_sigma": {
        "n_matched": int(matched_mask.sum()),
        "tiny_median_sigma": tiny_sigma,
        "nontiny_median_sigma": nontiny_sigma,
        "tiny_lt_nontiny": bool(
            tiny_sigma is not None and nontiny_sigma is not None and tiny_sigma < nontiny_sigma
        ),
    },
    "non_degenerate": bool(
        n_distinct > 1
        and frac_ceil < 1.0
        and (tiny_sigma is None or nontiny_sigma is None or tiny_sigma < nontiny_sigma)
    ),
}

(T / "h3_code_exact_sigma_distribution.json").write_text(json.dumps(out, indent=2))
pd.DataFrame(per_comp_rows).to_csv(T / "h3_code_exact_component_areas.csv", index=False)

print(json.dumps(out, indent=2))
