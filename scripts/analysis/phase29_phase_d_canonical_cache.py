"""Phase29 PHASE D - CANONICAL SHARED FIXED-G VAL808 CACHE BUILDER (v1.1 canonical).

Work order: PHASE 29 - PHASE D: CANONICAL VAL808 EXECUTION + THREE-SEED
REPRODUCIBILITY FREEZE

Sections implemented here:
    §0  bind/verify authoritative artifacts (BLOCK on drift)
    §2  canonical root = data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/
        (must be absent/clean before construction; v1_0 preserved as evidence)
    §3  ONE logical shared fixed-G extraction (808 samples, 102 batch forwards)
    §4  EXACT Phase27 G numerics: CUDA, eval(), fp32 input/model,
        torch.no_grad() + torch.amp.autocast(fp16, ENABLED),
        torch.inference_mode = FALSE, batch 8, contiguous within-domain
    §5  canonical cache outputs (global_prob_f16, router_deep_features_f32,
        router_scalars_f32, roi_geometry.json) - NO GT, NO task ground truth

This script performs GLOBAL G inference ONLY.  It does NOT run R_psi / B_phi /
S_omega.  The router deep features + scalars are the GT-free tap outputs of the
SAME global G forward (deterministic, seed-independent) - extracted once and
shared by all seeds.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase29_phase_d_canonical_cache.py
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase29_phase_d_common as D  # noqa: E402
import phase27_exec_common as E  # noqa: E402
import phase27_spec_common as S  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from src.data.barr_roi import (  # noqa: E402
    REGIONAL_CANVAS_RESOLUTION,
    roi_geometry,
)
from src.features.barr_pre_refinement_features import (  # noqa: E402
    DEEP_DIM as PRE_DEEP_DIM,
    SCALAR_DIM as PRE_SCALAR_DIM,
    build_feature_vector,
)
from src.models.film.global_medfilm import GlobalMedFiLM  # noqa: E402

say = print

TAPS = ("bridge", "decoder2", "decoder1")
TAP_MODULES = {"bridge": "bridge", "decoder2": "decoder2", "decoder1": "decoder1"}

CANON_ROOT = D.ROOT / "data_cache" / "phase29_val808_shared_fixed_g_v1_1_canonical"
NONCANON_ROOT = D.CACHE29D  # v1_0 - preserved as evidence only

# ---------------------------------------------------------------- §6 target ---
PHASE27_GLOBAL_PROB_ABS = D.ROOT / D.PHASE27_GLOBAL_PROB
PHASE27_GLOBAL_PROB_SHA = D.PHASE27_GLOBAL_PROB_SHA


class TapRecorder:
    """Inference-only forward hooks on the three G taps (read outputs)."""

    def __init__(self, model: torch.nn.Module):
        self.store = {}
        self.handles = []
        for tap in TAPS:
            module = getattr(model, TAP_MODULES[tap])
            self.handles.append(module.register_forward_hook(self._make(tap)))

    def _make(self, tap):
        def hook(_m, _i, out):
            self.store[tap] = out
        return hook

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles.clear()


def image_only_transform(image, size: int = REGIONAL_CANVAS_RESOLUTION) -> torch.Tensor:
    """EXACT replica of run_phase27_exec_phaseA.image_only_transform.

    Image-only path (aspect-preserving bilinear resize + centre pad +
    permute(2,0,1) / 255.0).  The mask is NEVER opened -> ZERO GT reads.
    """
    image = image.convert("RGB")
    width, height = image.size
    scale = min(size / width, size / height)
    rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (size - rw) // 2, (size - rh) // 2
    right, bottom = size - rw - left, size - rh - top
    image = ImageOps.expand(image, (left, top, right, bottom))
    arr = np.asarray(image, dtype=np.float32).copy()
    return torch.from_numpy(arr).permute(2, 0, 1) / 255.0


def load_global_only(device):
    cfg = E.jload(E.ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json")
    g = GlobalMedFiLM(
        task_count=cfg["model"]["task_count"],
        in_channels=cfg["model"]["in_channels"],
        out_channels=cfg["model"]["out_channels"],
        channels=tuple(cfg["model"]["channels"]),
        task_embedding_dim=cfg["model"]["task_embedding_dim"],
        film_hidden_dim=cfg["model"]["film_hidden_dim"],
    )
    g.load_state_dict(torch.load(E.ROOT / E.COMPONENT_PATHS["global_medfilm"],
                                map_location="cpu", weights_only=False)["model_state"])
    g.eval()
    g.requires_grad_(False)
    g.to(device)
    counts = sum(p.numel() for p in g.parameters())
    assert counts == 3523001, counts
    return g, counts


# --------------------------------------------------------------------------- #
def verify_predecessors() -> dict:
    """§0: bind/verify the six authoritative artifacts + additions + components."""
    checks = []
    for rel, exp in [
        ("reports/audits/phase29_phase_d_causal_order_defect.json",
         "4dc020838461df2fadb5d3a6c4cef41e03714a18f73cccc4693ea52916150b1f"),
        ("reports/audits/phase29_phase_d_post_safety_causal_dependency_proof.json",
         "61fa2d196e763091155d22497182841024a3262f9c95d096e2a0feac7fa0d228"),
        ("reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json",
         "dc721c1143bdd03b542da95e1cfb22c638362535aea6bbcefaf28a99323c7526"),
        ("reports/audits/phase29_val808_shared_global_cache_contract_v1_2.json",
         "85e63779b08ae4d529577e249d55639eb94285f7ae1ed5c8758c13cbff468875"),
        ("reports/audits/phase29_phase_d_global_reproduction_gate_v1_1.json",
         "24423bd2cce0f0579de006b0d91b15f55b6893886b0e914bfcc267366e1a2c8c"),
        ("reports/audits/phase29_phase_c_reconciliation_terminal.json",
         "4a421d6f858e1b28af16269d05d55f7a6b95961ce5ee454ddfdf265097683b9e"),
        ("reports/audits/phase29_phase_c_final_check_reconciled.json",
         "b15b63f45fc29f88301332e7699f59e5f788de95ef81df8c7c9b08b89d49d636"),
    ]:
        b = E.bind(rel, exp)
        checks.append({"path": rel, "expected": exp, "observed": b["sha256"],
                       "match": b["match"]})
    for k, p in E.COMPONENT_PATHS.items():
        b = E.bind(p, E.COMPONENT_SHAS[k])
        checks.append({"path": p, "expected": E.COMPONENT_SHAS[k],
                       "observed": b["sha256"], "match": b["match"]})
    b = E.bind(E.VAL808_MANIFEST, E.VAL808_MANIFEST_SHA)
    checks.append({"path": E.VAL808_MANIFEST, "expected": E.VAL808_MANIFEST_SHA,
                   "observed": b["sha256"], "match": b["match"]})
    # seed123 / seed3407 calibration
    for s, name in [(123, "phase29_seed123_final_router_calibration.json"),
                    (3407, "phase29_seed3407_final_router_calibration.json")]:
        rel = f"reports/audits/{name}"
        b = E.bind(rel, None)
        checks.append({"path": rel, "expected": None, "observed": b["sha256"],
                       "match": b["exists"]})
    all_ok = all(c["match"] for c in checks)
    return {"checks": checks, "all_match": all_ok,
            "n_checks": len(checks), "n_failed": sum(1 for c in checks if not c["match"])}


# --------------------------------------------------------------------------- #
def main() -> int:
    t0 = time.time()
    D.AUD.mkdir(parents=True, exist_ok=True)

    # ---- §0 predecessor verification --------------------------------------- #
    prov = verify_predecessors()
    D.write_json({"artifact": "phase29_phase_d_canonical_cache_predecessor_binding",
                  "phase": "29", "phase_label": "PHASE_D",
                  "section": "§0",
                  "checks": prov["checks"], "all_match": prov["all_match"],
                  "n_checks": prov["n_checks"], "n_failed": prov["n_failed"],
                  "block_on_drift": True},
                 D.AUD / "phase29_phase_d_canonical_cache_predecessor_binding.json")
    if not prov["all_match"]:
        say("PREDECESSOR DRIFT DETECTED -> BLOCKED")
        for c in prov["checks"]:
            if not c["match"]:
                say(f"  DRIFT {c['path']}: {c['observed']} != {c['expected']}")
        D.write_json({"artifact": "phase29_phase_d_canonical_cache_terminal",
                      "terminal": D.BLOCKED["FROZEN_ARTIFACT_DRIFT"],
                      "all_pass": False},
                     D.AUD / "phase29_phase_d_canonical_cache_terminal.json")
        return 1
    say(f"§0 predecessor binding OK ({prov['n_checks']} checks, 0 drift)")

    # ---- §2 canonical root cleanliness gate -------------------------------- #
    if CANON_ROOT.exists():
        entries = [p.name for p in CANON_ROOT.iterdir()]
        if entries:
            say(f"CANONICAL ROOT NOT CLEAN: {entries} -> BLOCKED")
            D.write_json({"artifact": "phase29_phase_d_canonical_cache_terminal",
                          "terminal": D.BLOCKED["VAL808_CACHE_INTEGRITY_FAILURE"],
                          "reason": "canonical_root_not_clean",
                          "entries": entries, "all_pass": False},
                         D.AUD / "phase29_phase_d_canonical_cache_terminal.json")
            return 1
    CANON_ROOT.mkdir(parents=True, exist_ok=True)
    say(f"§2 canonical root clean: {CANON_ROOT.relative_to(D.ROOT)}")

    # ---- device + component ------------------------------------------------- #
    device = torch.device("cuda")
    assert torch.cuda.is_available()
    say(f"device={device} torch={torch.__version__} cuda={torch.version.cuda} "
        f"gpu={torch.cuda.get_device_name(0)}")

    g, g_params = load_global_only(device)
    say(f"§0 G loaded (params={g_params})")

    # ---- §3/§4 population + canonical order -------------------------------- #
    rows = D.val808_rows()
    df = pd.DataFrame(rows).sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    assert len(df) == D.VAL808_N, len(df)
    for dom, n in D.VAL808_DOMAIN_N.items():
        assert int((df["dataset"] == dom).sum()) == n, (dom, int((df["dataset"] == dom).sum()))
    sample_ids = df["sample_id"].astype(str).tolist()
    pos = {sid: i for i, sid in enumerate(sample_ids)}
    say(f"§3 population n={len(sample_ids)} domains={sorted(df['dataset'].unique().tolist())}")

    # ---- outputs (§5) ------------------------------------------------------- #
    global_prob_f16 = np.lib.format.open_memmap(
        CANON_ROOT / "val808_global_prob_f16.npy", mode="w+", dtype=np.float16,
        shape=(len(df), REGIONAL_CANVAS_RESOLUTION, REGIONAL_CANVAS_RESOLUTION))
    # router deep features: concatenated 3 taps (64+64+64 = 192) - frozen Phase25B layout
    # scalars: 10-D (x1,y1,x2,y2,width,height,area_fraction,crop_side,pad_top,pad_left)
    # both are deterministic, GT-free functions of the SAME G forward.
    deep = np.zeros((len(df), 192), dtype=np.float32)
    scal = np.zeros((len(df), 10), dtype=np.float32)

    geom_rows = []
    batch_forwards = 0
    n_dom_batches = {}

    domains = sorted(df["dataset"].unique().tolist())
    for dom in domains:
        sub = df[df["dataset"] == dom].reset_index(drop=True)
        n = len(sub)
        nb = 0
        for start in range(0, n, E.BATCH_SIZE):
            chunk = sub.iloc[start:start + E.BATCH_SIZE]
            imgs, tasks = [], []
            for _, row in chunk.iterrows():
                with Image.open(row["image_path"]) as image:
                    it = image_only_transform(image, REGIONAL_CANVAS_RESOLUTION)
                imgs.append(it)
                tasks.append(int(row["task_id"]))
            batch_img = torch.stack(imgs).to(device)
            batch_task = torch.tensor(tasks, dtype=torch.long, device=device)

            rec = TapRecorder(g)
            try:
                # §4 EXACT Phase27 semantics
                with torch.no_grad(), torch.amp.autocast(device_type=device.type, enabled=True):
                    logits = g(batch_img, batch_task)
                prob = torch.sigmoid(logits.float()).cpu().numpy()[:, 0]
                cmaps_batch = {t: rec.store[t].float().cpu().numpy() for t in TAPS}
            finally:
                rec.close()
            batch_forwards += 1
            nb += 1

            for i in range(batch_img.shape[0]):
                row = chunk.iloc[i]
                sid = str(row["sample_id"])
                gi = pos[sid]
                p_global = prob[i].astype(np.float32)
                global_prob_f16[gi] = p_global.astype(np.float16)

                # ---- ROI geometry (frozen 0.30) ------------------------------- #
                geom = roi_geometry(p_global, E.ROI_PROPOSAL_THRESHOLD)
                if geom is None:
                    geom_rows.append({"sample_id": sid, "dataset": dom,
                                      "roi_available": False})
                else:
                    rec = {"sample_id": sid, "dataset": dom, "roi_available": True}
                    for k in ("y1", "y2", "x1", "x2", "clip_y1", "clip_y2",
                              "clip_x1", "clip_x2", "pad_top", "pad_bottom",
                              "pad_left", "pad_right", "crop_side_pixels",
                              "effective_magnification", "margin"):
                        rec[k] = geom[k]
                    geom_rows.append(rec)

                # ---- deep features + scalars (canonical Phase25B 202-D) -------- #
                # Use the frozen build_feature_vector verbatim, then split into the
                # 192-D deep block and the 10-D scalar block.  This reproduces the
                # EXACT canonical Phase25B ordering (6 x 32 deep + 10 scalars).
                if geom is None:
                    # no ROI -> frozen FAIL-CLOSED semantics; store zeros so the
                    # shared cache is well-formed (rows are marked roi_available=False).
                    deep[gi] = np.zeros(PRE_DEEP_DIM, dtype=np.float32)
                    scal[gi] = np.zeros(PRE_SCALAR_DIM, dtype=np.float32)
                else:
                    cmaps = {t: cmaps_batch[t][i] for t in TAPS}
                    vec202 = build_feature_vector(cmaps, p_global, geom)
                    assert vec202.shape == (PRE_DEEP_DIM + PRE_SCALAR_DIM,), vec202.shape
                    deep[gi] = vec202[:PRE_DEEP_DIM].astype(np.float32)
                    scal[gi] = vec202[PRE_DEEP_DIM:].astype(np.float32)
        n_dom_batches[dom] = nb
        say(f"  [{dom}] n={n} batches={nb} forwards={batch_forwards} "
            f"elapsed={time.time()-t0:.0f}s")

    global_prob_f16.flush()
    np.save(CANON_ROOT / "val808_router_deep_features_f32.npy", deep)
    np.save(CANON_ROOT / "val808_router_scalars_f32.npy", scal)
    geo_by_id = {r["sample_id"]: {k: v for k, v in r.items()
                                  if k not in ("sample_id", "dataset", "task_id",
                                               "roi_available")}
                 for r in geom_rows if r["roi_available"]}
    D.write_json({"artifact": "phase29_phase_d_canonical_roi_geometry",
                  "phase": 29, "stage": "PHASE_D_CANONICAL_SHARED_G_CACHE",
                  "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
                  "population": "VAL808", "population_n": len(sample_ids),
                  "sample_id_order": sample_ids,
                  "roi_proposal_threshold": E.ROI_PROPOSAL_THRESHOLD,
                  "roi_expansion": E.ROI_EXPANSION,
                  "geometry_source": "CANONICAL_GLOBAL_PROB_AT_0.30__GT_FREE",
                  "gt_derived_information_persisted": False,
                  "n_no_roi": sum(1 for r in geom_rows if not r["roi_available"]),
                  "geometry": geo_by_id,
                  "regenerable_from": "val808_global_prob_f16.npy @ 0.30"},
                 CANON_ROOT / "val808_roi_geometry.json")

    exp_batches, exp_total = E.expected_batch_counts()
    assert batch_forwards == exp_total == 102, (batch_forwards, exp_total)
    assert n_dom_batches == {"BUSI": 11, "ISIC": 45, "KUB": 35, "KVASIR": 11}, n_dom_batches
    say(f"§3 batch forwards OK: {batch_forwards} == 102 "
        f"({n_dom_batches})")

    # ---- hashes ------------------------------------------------------------- #
    shas = {f: D.sha256_file(CANON_ROOT / f) for f in
            ["val808_global_prob_f16.npy", "val808_router_deep_features_f32.npy",
             "val808_router_scalars_f32.npy", "val808_roi_geometry.json"]}
    gen_summary = {
        "artifact": "phase29_val808_shared_cache_build_summary",
        "phase": "29", "phase_label": "PHASE_D", "cache_version": "v1_1_canonical",
        "canonical_root": str(CANON_ROOT.relative_to(D.ROOT)).replace("\\", "/"),
        "noncanonical_root_preserved": str(NONCANON_ROOT.relative_to(D.ROOT)).replace("\\", "/"),
        "logical_g_passes": 1,
        "g_samples": len(sample_ids),
        "batch_forwards": batch_forwards,
        "batch_forwards_by_domain": n_dom_batches,
        "expected_batch_forwards": exp_total,
        "batch_size": E.BATCH_SIZE,
        "device": str(device),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
        "autocast_enabled": True,
        "autocast_dtype": "float16",
        "inference_mode": False,
        "grad_context": "torch.no_grad()",
        "input_dtype": "float32",
        "model_dtype": "float32",
        "prob_casting": "sigmoid(logits.float()) -> float32 -> float16 storage",
        "g_params": g_params,
        "g_checkpoint_sha256": E.COMPONENT_SHAS["global_medfilm"],
        "val808_images_read": len(sample_ids),
        "val808_gt_reads": 0,
        "deep_feature_dim": 192,
        "scalar_dim": 10,
        "domain_order": domains,
        "cache_file_shas": shas,
        "generated_utc": D.now_utc(),
        "elapsed_seconds": round(time.time() - t0, 1),
        "all_pass": True,
    }
    D.write_json(gen_summary, D.AUD / "phase29_val808_shared_cache_build_summary_v1_1_canonical.json")

    # ---- §6 GLOBAL REPRODUCTION GATE --------------------------------------- #
    new_global_sha = shas["val808_global_prob_f16.npy"]
    target_sha = PHASE27_GLOBAL_PROB_SHA
    bit_identical = (new_global_sha == target_sha)
    say("")
    say("=" * 74)
    say("§6 GLOBAL REPRODUCTION GATE")
    say(f"  new global prob sha256 : {new_global_sha}")
    say(f"  Phase27 target sha256  : {target_sha}")
    say(f"  bit_identical          : {bit_identical}")
    if not bit_identical:
        a = np.load(CANON_ROOT / "val808_global_prob_f16.npy")
        b = np.load(PHASE27_GLOBAL_PROB_ABS)
        diff = np.abs(a.astype(np.float32) - b.astype(np.float32))
        rows_diff = int((diff.max(axis=(1, 2)) > 0).sum())
        D.write_json({
            "artifact": "phase29_phase_d_global_reproduction_gate_result",
            "phase": "29", "phase_label": "PHASE_D", "section": "§6",
            "target": D.PHASE27_GLOBAL_PROB, "target_sha256": target_sha,
            "observed_sha256": new_global_sha, "bit_identical": False,
            "max_abs_diff": float(diff.max()),
            "rows_with_any_diff": rows_diff, "n_rows": int(a.shape[0]),
            "all_pass": False,
        }, D.AUD / "phase29_phase_d_global_reproduction_gate_result.json")
        D.write_json({"artifact": "phase29_phase_d_canonical_cache_terminal",
                      "terminal": D.BLOCKED["VAL808_CACHE_INTEGRITY_FAILURE"],
                      "reason": "global_reproduction_gate_not_bit_identical",
                      "all_pass": False},
                     D.AUD / "phase29_phase_d_canonical_cache_terminal.json")
        say("GLOBAL REPRODUCTION GATE FAILED -> STOP (BLOCKED terminal)")
        return 1

    D.write_json({
        "artifact": "phase29_phase_d_global_reproduction_gate_result",
        "phase": "29", "phase_label": "PHASE_D", "section": "§6",
        "target": D.PHASE27_GLOBAL_PROB, "target_sha256": target_sha,
        "observed_sha256": new_global_sha, "bit_identical": True,
        "gate": "load-bearing", "n_rows": len(sample_ids),
        "all_pass": True,
    }, D.AUD / "phase29_phase_d_global_reproduction_gate_result.json")
    say("GLOBAL REPRODUCTION GATE PASSED (bit-identical)")

    # ---- §2 v1_0 preserved as evidence -------------------------------------- #
    D.write_json({
        "artifact": "phase29_phase_d_noncanonical_cache_isolation_v1_1",
        "phase": "29", "phase_label": "PHASE_D", "section": "§2",
        "canonical_root": str(CANON_ROOT.relative_to(D.ROOT)).replace("\\", "/"),
        "noncanonical_root": str(NONCANON_ROOT.relative_to(D.ROOT)).replace("\\", "/"),
        "noncanonical_status": "PRESERVED_AS_EVIDENCE_ONLY__NOT_USED_FOR_INFERENCE",
        "noncanonical_files": {p.name: D.sha256_file(p)
                               for p in sorted(NONCANON_ROOT.iterdir())},
        "all_pass": True,
    }, D.AUD / "phase29_phase_d_noncanonical_cache_isolation_v1_1.json")

    D.write_json({"artifact": "phase29_phase_d_canonical_cache_terminal",
                  "phase": "29", "phase_label": "PHASE_D",
                  "terminal": "PHASE29_PHASE_D_CANONICAL_SHARED_G_CACHE_BUILT__"
                              "GLOBAL_REPRODUCTION_GATE_BIT_IDENTICAL__ELIGIBLE_FOR_SEED_INFERENCE",
                  "all_pass": True},
                 D.AUD / "phase29_phase_d_canonical_cache_terminal.json")

    say("")
    say("=" * 74)
    say(f"CANONICAL CACHE COMPLETE n={len(sample_ids)} forwards={batch_forwards}")
    say(f"global_prob sha256 : {new_global_sha}")
    say(f"deep_features sha  : {shas['val808_router_deep_features_f32.npy']}")
    say(f"scalars sha        : {shas['val808_router_scalars_f32.npy']}")
    say(f"roi_geometry sha   : {shas['val808_roi_geometry.json']}")
    say(f"elapsed={time.time()-t0:.0f}s")
    say("=" * 74)
    say("PHASE29_PHASE_D_CANONICAL_SHARED_G_CACHE_BUILT__GLOBAL_REPRODUCTION_GATE_BIT_IDENTICAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
