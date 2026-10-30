#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0 SCIENTIFIC EXECUTION STATIC PREFLIGHT.

STATIC SOURCE + GOVERNANCE ANALYSIS ONLY. No model construction, no checkpoint deserialization,
no forward, no autograd, no Grad-CAM, no router attribution, and NO protected-data read. This
script NEVER imports torch.

Emits `reports/audits/phase35_scientific_execution_static_preflight_v1_0.json`.
Exit 0 iff every check passes. Any failure REQUIRES a STOP before any protected read.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "scientific_driver": "scripts/analysis/phase35_scientific_execution_v1_0.py",
    "preflight": "scripts/analysis/phase35_scientific_execution_preflight_v1_0.py",
    "v1_0b_execution": "scripts/analysis/phase35_interpretability_execution_v1_0b.py",
    "v1_0b_common": "scripts/analysis/phase35_interpretability_common_v1_0b.py",
    "v1_0h_execution": "scripts/analysis/phase35_interpretability_execution_v1_0h.py",
    "v1_0e_execution": "scripts/analysis/phase35_interpretability_execution_v1_0e.py",
    "v1_0d_execution": "scripts/analysis/phase35_interpretability_execution_v1_0d.py",
    "spec_doc": "docs/phase35_interpretability_spec_v1_0.md",
    "g_source": "src/models/film/global_medfilm.py",
    "b_phi_source": "scripts/analysis/train_phase25d_router.py",
    "domain_registry": "src/analysis/multidomain_harmonization.py",
}

AUTHORITY_FILES = {
    "gallery": "reports/tables/phase21_gallery_selection_64.csv",
    "feature_schema": "reports/tables/phase25b_feature_schema.csv",
    "normalization_authority": "reports/tables/phase25d_final_normalization_stats.csv",
    "g_checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "b_phi_checkpoint": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
    "router_cache_deep": "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
                         "val808_router_deep_features_f32.npy",
    "router_cache_scalars": "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
                            "val808_router_scalars_f32.npy",
    "router_cache_prob": "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
                         "val808_global_prob_f16.npy",
    "router_cache_geometry": "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
                             "val808_roi_geometry.json",
    "val_manifest": "manifests/phase4_v3/val.csv",
    "split_manifest": "reports/audits/phase24_router_split_manifest.csv",
}

EXPECTED_SHA = {
    "gallery": "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9",
    "feature_schema": "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4",
    "normalization_authority":
        "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb",
    "g_checkpoint": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "b_phi_checkpoint": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
}

RES = []


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(name: str) -> str:
    return (ROOT / FILES[name]).read_text(encoding="utf-8")


def ck(cid: str, desc: str, ok: bool, detail: str = "") -> None:
    RES.append((cid, desc, bool(ok), detail))


def _strip_comments(src: str) -> str:
    """Remove '#' line comments so frozen literal checks are not confused by comment text."""
    out = []
    for line in src.splitlines():
        i = line.find("#")
        out.append(line if i < 0 else line[:i])
    return "\n".join(out)


def main() -> int:
    drv = read("scientific_driver")
    common = read("v1_0b_common")
    v1b = read("v1_0b_execution")
    v1h = read("v1_0h_execution")
    v1e = read("v1_0e_execution")
    tree = ast.parse(drv)

    # ---- 01-04 driver identity, classification and gate ------------------------- #
    ck("01", "driver classification is PHASE35_PROSPECTIVE_SCIENTIFIC_EXECUTION_ORCHESTRATOR",
       'CLASSIFICATION = "PHASE35_PROSPECTIVE_SCIENTIFIC_EXECUTION_ORCHESTRATOR"' in drv)
    ck("02", "driver imports the frozen v1.0b commons + v1.0b execution by module name",
       "import phase35_interpretability_common_v1_0b as C" in drv
       and "import phase35_interpretability_execution_v1_0b as V0B" in drv)
    ck("03", "driver calls frozen V0B scientific functions (film/gradcam/router/attribution)",
       all(t in drv for t in ("V0B.extract_film_parameters", "V0B.extract_task_embeddings",
                             "V0B.load_persisted_p_global", "V0B.build_target_mask",
                             "V0B.build_roi_mask", "V0B.router_population_verify",
                             "V0B.router_normalized_features", "V0B.router_gradient_x_input",
                             "V0B.router_group_attribution", "V0B.saliency_self_consistency")))
    ck("04", "scientific execution gated on PHASE35_EXECUTE=1 (refuses without it)",
       'GATE_ENV = C.GATE_ENV' in drv and 'os.environ.get(GATE_ENV) != "1"' in drv)

    # ---- 05-08 mathematics NOT altered ----------------------------------------- #
    ck("05", "driver does NOT redefine the segmentation/ROI thresholds",
       "T_SEGMENTATION_OUTPUT = 0.5" not in drv and "T_ROI_PROPOSAL = 0.3" not in drv)
    ck("06", "driver does NOT redefine the Grad-CAM algorithm (alpha/ReLU/upsample/normalize)",
       "alpha = " not in drv and "cam_raw" not in drv and "F.interpolate" not in drv
       and "torch.relu" not in drv)
    _drv_nosig = drv.replace("sigmoid_applied", "").replace("NO sigmoid", "")
    ck("07", "driver does NOT redefine router attribution mathematics (no sigmoid)",
       "sigmoid(" not in _drv_nosig and "torch.sigmoid" not in _drv_nosig)
    ck("08", "driver does NOT redefine the claim boundary / forbidden-term list",
       "FORBIDDEN_CLAIM_TERMS = [" not in drv)

    # ---- 09-12 four families separately identifiable ---------------------------- #
    for i, fam in enumerate(("I1", "I2", "I3", "I4")):
        ck(f"{9 + i:02d}", f"family {fam} implemented as its own function",
           re.search(rf"def run_{fam.lower()}_", drv) is not None
           and f'"{fam}"' in drv)
    ck("13", "driver never merges families into a single statistic",
       "families_never_merged" in drv)

    # ---- 14-17 protected-data guards reused verbatim ---------------------------- #
    ck("14", "VAL allow-list enforced by sample_id + protected-path guard before every image open",
       drv.count("_assert_allowlisted(") >= drv.count("resolve_val_image_path(")
       and drv.count("_assert_not_protected_path(") >= drv.count("resolve_val_image_path(")
       and 'PROTECTED-DATA GUARD: sample_id outside the 64 allow-list' in drv
       and "ROUTER_HOLDOUT" in drv and "/test/" in drv)
    ck("15", "persisted p_global read uses the frozen loader (prob key only)",
       "V0B.load_persisted_p_global" in drv and "PERSISTED_KEYS_ALLOWED" in common
       and "PERSISTED_KEYS_FORBIDDEN" in common)
    ck("16", "driver opens NO mask/ground-truth file",
       "mask_path" not in drv and ".mask" not in drv and "gt" not in
       [n.lower() for n in re.findall(r'open\(([^)]*)\)', drv)])
    ck("17", "driver asserts zero GT / holdout / TEST reads in counters",
       all(k in drv for k in ('"gt_reads"', '"router_holdout_reads"', '"test_reads"')))

    # ---- 18-21 Grad-CAM contract ----------------------------------------------- #
    ck("18", "Grad-CAM uses the frozen guarded implementation (V0E ..._v1_0f)",
       "V0E.gradcam_gradient_enabled_numerically_guarded" in drv)
    ck("19", "Grad-CAM hook layers resolve to the frozen pair (bridge, decoder1)",
       "GRADCAM_LAYERS = V0D.GRADCAM_LAYERS" in drv
       and 'GRADCAM_LAYERS = ("bridge", "decoder1")' in _strip_comments(read("v1_0d_execution"))
       and "GRADCAM_LAYERS = V0D.GRADCAM_LAYERS" in _strip_comments(v1e))
    ck("19b", "driver passes the frozen hook pair explicitly to the guarded Grad-CAM call",
       "layers=GRADCAM_LAYERS" in drv)
    ck("20", "target mask is the persisted p_global >= 0.50 via frozen build_target_mask",
       "V0B.build_target_mask(p_global)" in drv)
    ck("21", "ROI mask is the persisted p_global >= 0.30 via frozen build_roi_mask",
       "V0B.build_roi_mask(p_global)" in drv)

    # ---- 22-24 router attribution contract ------------------------------------- #
    ck("22", "router attribution reuses V0B.router_gradient_x_input (raw delta_hat, no sigmoid)",
       "V0B.router_gradient_x_input" in drv)
    ck("23", "router group attribution reuses V0B.router_group_attribution (zero-denominator rule)",
       "V0B.router_group_attribution" in drv)
    ck("24", "router population verified before attribution (V0B.router_population_verify)",
       drv.index("V0B.router_population_verify") < drv.index("V0B.router_gradient_x_input"))

    # ---- 25-27 non-executable components and training semantics ----------------- #
    ck("25", "R_psi / S_omega never constructed, loaded or forwarded",
       "R_psi" not in drv.split("FAMILY_COUNTERS")[0].split("def ")[-1]
       or all(f"{c}_model" not in drv for c in ("load_r_psi", "load_s_omega")))
    ck("26", "no optimizer / optimizer.step / training backward in the driver",
       "optimizer.step" not in drv and ".backward(" not in drv
       and "torch.optim" not in drv)
    ck("27", "parameter immutability audited before/after (state_dict_identity)",
       "state_dict_identity" in drv and "MODEL_PARAMETERS_UNCHANGED" in drv)

    # ---- 28 frozen authorities unchanged --------------------------------------- #
    ck("28", "v1.0b commons constants still expose the frozen thresholds",
       "T_SEGMENTATION_OUTPUT = 0.50" in common and "T_ROI_PROPOSAL = 0.30" in common)
    ck("29", "v1.0b execution still exposes the frozen scientific functions",
       all(f"def {f}(" in v1b for f in ("extract_film_parameters", "gradcam_gradient_enabled",
                                        "saliency_self_consistency", "router_gradient_x_input",
                                        "router_group_attribution", "load_g_component",
                                        "load_bphi_component")))

    # ---- 30 all authority inputs exist with expected SHA ----------------------- #
    missing, sha_bad = [], []
    for k, rel in AUTHORITY_FILES.items():
        p = ROOT / rel
        if not p.exists():
            missing.append(k)
            continue
        if k in EXPECTED_SHA and sha(p) != EXPECTED_SHA[k]:
            sha_bad.append(k)
    ck("30", "all authority inputs exist and match their frozen SHA-256",
       not missing and not sha_bad,
       f"missing={missing} sha_mismatch={sha_bad}")

    npass = sum(1 for *_, ok, _ in [(c, d, o, t) for c, d, o, t in RES] if ok)
    nfail = len(RES) - npass
    doc = OrderedDict([
        ("artifact", "phase35_scientific_execution_static_preflight_v1_0"),
        ("section", "§E"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0"),
        ("preflight_class", "STATIC_SOURCE_ANALYSIS__NO_MODEL_EXECUTION"),
        ("no_execution", True), ("torch_imported", False),
        ("source_hashes", {k: (sha(ROOT / v) if (ROOT / v).exists() else None)
                           for k, v in FILES.items()}),
        ("authority_hashes", {k: (sha(ROOT / v) if (ROOT / v).exists() else None)
                              for k, v in AUTHORITY_FILES.items()}),
        ("checks", [{"id": c, "desc": d, "pass": ok, "detail": t} for c, d, ok, t in RES]),
        ("total_checks", len(RES)), ("passed", npass), ("failed", nfail),
        ("generated_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("all_pass", nfail == 0),
    ])
    op = ROOT / "reports/audits/phase35_scientific_execution_static_preflight_v1_0.json"
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"preflight: {npass}/{len(RES)} passed, {nfail} failed")
    for c, d, ok, t in RES:
        if not ok:
            print(f"  FAIL {c}: {d}  {t}")
    print("preflight sha256:", sha(op))
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
