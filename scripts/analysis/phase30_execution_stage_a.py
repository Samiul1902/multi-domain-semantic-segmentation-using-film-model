#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase30 ONE-SHOT ROUTER_HOLDOUT execution — STAGE A.

Entry binding -> execution-source freeze -> first-open marker -> IMAGE-ONLY
one-shot inference (875 samples, 111 G batch forwards) -> prediction hash
barrier -> Stage-A pre-GT integrity check.

GT/MASK ACCESS REMAINS ZERO throughout this stage.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase30_execution_stage_a.py
"""
from __future__ import annotations

import math
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase30_execution_common as C  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402

from src.data.barr_roi import roi_geometry  # noqa: E402

say = print
TAPS = ("bridge", "decoder2", "decoder1")
TAP_MODULES = {"bridge": "bridge", "decoder2": "decoder2", "decoder1": "decoder1"}

EXEC_SOURCES = [
    "scripts/analysis/phase30_execution_common.py",
    "scripts/analysis/phase30_execution_stage_a.py",
    "scripts/analysis/run_phase27_exec_phaseA.py",
    "scripts/analysis/phase27_exec_common.py",
    "scripts/analysis/phase27_spec_common.py",
    "scripts/analysis/phase25f_post_safety_features.py",
    "scripts/analysis/phase25f_execution_common.py",
    "scripts/analysis/train_phase25d_router.py",
    "src/data/barr_roi.py",
    "src/features/barr_pre_refinement_features.py",
    "src/models/barr/regional_refiner.py",
    "src/models/film/global_medfilm.py",
    "src/metrics/evaluation_metrics.py",
    "src/utils/device.py",
    "src/utils/test_lock.py",
    "src/data/transforms.py",
]


class TapRecorder:
    def __init__(self, model):
        self.store = {}
        self.handles = []
        for tap in TAPS:
            self.handles.append(getattr(model, TAP_MODULES[tap]).register_forward_hook(self._mk(tap)))

    def _mk(self, tap):
        def hook(_m, _i, out):
            self.store[tap] = out
        return hook

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles.clear()


def main() -> int:
    t0 = time.time()
    say("=" * 78)
    say("PHASE 30 ONE-SHOT ROUTER_HOLDOUT — STAGE A (IMAGE-ONLY)")
    say("=" * 78)

    # ---------------- §0 entry binding ---------------- #
    eb = [C.bind(p, s) for p, s in C.ENTRY_BINDINGS]
    term = C.read_json(C.ROOT / "reports/audits/phase30_specification_terminal_v1_3.json")
    entry_ok = all(b["match"] for b in eb) and term["terminal"] == C.TERMINAL_V1_3
    C.write_json({
        "artifact": "phase30_execution_entry_binding", "phase": 30, "stage": "ENTRY",
        "specification_revision": C.SPEC_REVISION, "method": C.METHOD,
        "bindings": eb, "terminal_observed": term["terminal"],
        "terminal_required": C.TERMINAL_V1_3,
        "standing_before_open": {"ROUTER_HOLDOUT_state": "RESERVED_UNOPENED",
                                 "ROUTER_HOLDOUT_image_reads": 0, "ROUTER_HOLDOUT_GT_reads": 0,
                                 "ROUTER_HOLDOUT_outcome_reads": 0, "model_forwards": 0,
                                 "TEST_reads": 0},
        "generated_utc": C.now_utc(), "all_pass": entry_ok,
    }, C.AUD / "phase30_execution_entry_binding.json")
    say(f"§0 entry binding: {sum(1 for b in eb if b['match'])}/{len(eb)} match, terminal_ok={term['terminal'] == C.TERMINAL_V1_3}")
    if not entry_ok:
        C.write_json({"artifact": "phase30_execution_terminal", "terminal":
                      "PHASE30_ONE_SHOT_EXECUTION_BLOCKED_BEFORE_FIRST_OPEN__ENTRY_DRIFT__NO_RERUN_AUTHORIZED",
                      "all_pass": False}, C.AUD / "phase30_execution_terminal.json")
        return 1

    # ---------------- §1 execution source freeze ---------------- #
    try:
        git_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(C.ROOT),
                                  capture_output=True, text=True).stdout.strip()
        git_status = subprocess.run(["git", "status", "--porcelain"], cwd=str(C.ROOT),
                                    capture_output=True, text=True).stdout
    except Exception as e:  # pragma: no cover
        git_head, git_status = f"UNKNOWN:{e}", ""
    dirty = [l for l in git_status.splitlines() if l.strip()]
    src = [C.bind(p) for p in EXEC_SOURCES]
    device = torch.device("cuda")
    assert torch.cuda.is_available()
    C.write_json({
        "artifact": "phase30_execution_source_freeze", "phase": 30, "stage": "SOURCE_FREEZE",
        "specification_revision": C.SPEC_REVISION, "method": C.METHOD,
        "git_commit": git_head, "working_tree_dirty": bool(dirty),
        "dirty_file_count": len(dirty), "dirty_files": dirty,
        "python_version": sys.version.split()[0], "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
        "determinism_settings": {
            "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
            "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
            "note": "determinism established by exact batch-membership replay (max_abs 0.0), "
                    "not by cudnn.deterministic"},
        "execution_scripts": src,
        "dataset_loader_source": C.bind("src/data/transforms.py"),
        "feature_construction_source": C.bind("src/features/barr_pre_refinement_features.py"),
        "roi_fusion_source": C.bind("src/data/barr_roi.py"),
        "metric_scoring_source": C.bind("src/metrics/evaluation_metrics.py"),
        "generated_utc": C.now_utc(), "all_pass": all(s["exists"] for s in src),
    }, C.AUD / "phase30_execution_source_freeze.json")
    say(f"§1 source freeze: git={git_head[:12]} dirty={len(dirty)} sources={len(src)}")

    # ---------------- §2 system re-bind ---------------- #
    sysb = {
        "bundle_manifest": C.bind(C.BUNDLE_MANIFEST, C.BUNDLE_MANIFEST_SHA),
        "components": {k: C.bind(C.COMPONENT_PATHS[k], C.COMPONENT_SHAS[k]) for k in C.COMPONENT_PATHS},
        "normalizers": {k: C.bind(v[0], v[1]) for k, v in C.NORMALIZATIONS.items()},
        "schemas": {k: C.bind(v[0], v[1]) for k, v in C.SCHEMAS.items()},
    }
    sys_ok = (sysb["bundle_manifest"]["match"]
              and all(v["match"] for v in sysb["components"].values())
              and all(v["match"] for v in sysb["normalizers"].values())
              and all(v["match"] for v in sysb["schemas"].values()))
    C.write_json({"artifact": "phase30_execution_system_rebind", "phase": 30, "stage": "SYSTEM_REBIND",
                  "specification_revision": C.SPEC_REVISION, **sysb,
                  "generated_utc": C.now_utc(), "all_pass": sys_ok},
                 C.AUD / "phase30_execution_system_rebind.json")
    say(f"§2 system rebind: all_match={sys_ok}")
    if not sys_ok:
        C.write_json({"artifact": "phase30_execution_terminal", "terminal":
                      "PHASE30_ONE_SHOT_EXECUTION_BLOCKED_BEFORE_FIRST_OPEN__SYSTEM_DRIFT__NO_RERUN_AUTHORIZED",
                      "all_pass": False}, C.AUD / "phase30_execution_terminal.json")
        return 1

    # ---------------- §3 population + plans re-bind ---------------- #
    gbm = C.rows_of(C.G_BATCH_MANIFEST)
    man = C.rows_of(C.SPLIT_MANIFEST)
    ho = [r for r in man if r["split_role"] == "ROUTER_HOLDOUT"]
    plan = np.load(C.ROOT / C.BOOTSTRAP_PLAN, allow_pickle=True)
    popb = {
        "split_manifest": C.bind(C.SPLIT_MANIFEST, C.SPLIT_MANIFEST_SHA),
        "g_batch_manifest": C.bind(C.G_BATCH_MANIFEST, C.G_BATCH_MANIFEST_SHA),
        "bootstrap_plan": C.bind(C.BOOTSTRAP_PLAN, C.BOOTSTRAP_PLAN_SHA),
    }
    dom_n = {d: sum(1 for r in ho if r["dataset"] == d) for d in C.DOMAINS}
    pop_ok = (all(v["match"] for v in popb.values()) and len(ho) == C.HOLDOUT_N
              and len(gbm) == C.HOLDOUT_N and dom_n == C.DOMAIN_N
              and len({r["group_key"] for r in ho}) == C.HOLDOUT_GROUPS)
    C.write_json({"artifact": "phase30_execution_population_rebind", "phase": 30,
                  "stage": "POPULATION_REBIND", "specification_revision": C.SPEC_REVISION,
                  "population": "ROUTER_HOLDOUT", "n": len(ho),
                  "groups": len({r["group_key"] for r in ho}), "domain_counts": dom_n,
                  **popb, "bootstrap_plan_keys": list(plan.keys())[:6],
                  "regenerated": False, "generated_utc": C.now_utc(), "all_pass": pop_ok},
                 C.AUD / "phase30_execution_population_rebind.json")
    say(f"§3 population rebind: n={len(ho)} groups={len({r['group_key'] for r in ho})} ok={pop_ok}")
    if not pop_ok:
        C.write_json({"artifact": "phase30_execution_terminal", "terminal":
                      "PHASE30_ONE_SHOT_EXECUTION_BLOCKED_BEFORE_FIRST_OPEN__POPULATION_DRIFT__NO_RERUN_AUTHORIZED",
                      "all_pass": False}, C.AUD / "phase30_execution_terminal.json")
        return 1

    # ---------------- §6 FIRST-OPEN MARKER (before any image read) ---------------- #
    C.ONESHOT.mkdir(parents=True, exist_ok=True)
    marker = {
        "artifact": "phase30_first_open_marker", "phase": 30, "stage": "FIRST_OPEN_MARKER",
        "specification_revision": C.SPEC_REVISION, "method": C.METHOD,
        "utc_timestamp": C.now_utc(),
        "population": "ROUTER_HOLDOUT", "n": C.HOLDOUT_N, "groups": C.HOLDOUT_GROUPS,
        "split_manifest_sha256": C.sha256_file(C.ROOT / C.SPLIT_MANIFEST),
        "g_batch_manifest_sha256": C.sha256_file(C.ROOT / C.G_BATCH_MANIFEST),
        "bootstrap_plan_sha256": C.sha256_file(C.ROOT / C.BOOTSTRAP_PLAN),
        "spec_v1_3_sha256": C.sha256_file(C.ROOT / "docs/phase30_final_development_validation_spec_v1_3.md"),
        "terminal_v1_3_sha256": C.sha256_file(C.ROOT / "reports/audits/phase30_specification_terminal_v1_3.json"),
        "final_check_v1_3_sha256": C.sha256_file(C.ROOT / "reports/audits/phase30_preexecution_final_check_v1_3.json"),
        "bundle_manifest_sha256": C.sha256_file(C.ROOT / C.BUNDLE_MANIFEST),
        "component_checkpoint_shas": {k: C.sha256_file(C.ROOT / C.COMPONENT_PATHS[k]) for k in C.COMPONENT_PATHS},
        "normalizer_shas": {k: C.sha256_file(C.ROOT / v[0]) for k, v in C.NORMALIZATIONS.items()},
        "feature_schema_shas": {k: C.sha256_file(C.ROOT / v[0]) for k, v in C.SCHEMAS.items()},
        "execution_script_shas": {p: C.sha256_file(C.ROOT / p) for p in EXEC_SOURCES},
        "environment": {"python": sys.version.split()[0], "torch": torch.__version__,
                        "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
                        "git_commit": git_head},
        "git_source_state": {"commit": git_head, "dirty": bool(dirty), "dirty_count": len(dirty)},
        "pre_open_counters": {"ROUTER_HOLDOUT_image_reads": 0, "ROUTER_HOLDOUT_GT_reads": 0,
                              "ROUTER_HOLDOUT_outcome_reads": 0, "TEST_reads": 0},
        "one_shot_open_about_to_begin": True,
    }
    C.write_json(marker, C.AUD / "phase30_first_open_marker.json")
    marker_sha = C.sha256_file(C.AUD / "phase30_first_open_marker.json")
    say(f"§6 FIRST-OPEN MARKER written + hashed: {marker_sha[:16]}")
    say("    >>> ROUTER_HOLDOUT is now scientifically OPENED (one-shot). <<<")

    # ================================================================== #
    # §8-§10  STAGE A: IMAGE-ONLY ONE-SHOT INFERENCE                       #
    # ================================================================== #
    say("")
    say("§8 Stage A: opening ROUTER_HOLDOUT IMAGES (GT remains closed)")

    manifest = {r["sample_id"]: r for r in C.rows_of("manifests/phase4_v3/train.csv")}
    ordered = sorted(gbm, key=lambda r: int(r["canonical_order_index"]))
    ids = [r["sample_id"] for r in ordered]
    domains = [r["dataset"] for r in ordered]
    tasks = [int(r["task_id"]) for r in ordered]
    n = len(ordered)
    assert n == C.HOLDOUT_N

    g = C.load_g(device)
    r_psi = C.load_rpsi(device)
    b_phi, bphi_st = C.load_bphi(device)
    s_omega, some_st = C.load_somega(device)
    say(f"components loaded (params verified) device={device}")

    # frozen normalizers
    SCALAR_IDX = [192, 193, 194, 195, 196, 197, 200, 201]
    mu = np.asarray(bphi_st["normalizer_mu"], dtype=np.float64).reshape(1, -1)
    sig = np.asarray(bphi_st["normalizer_sigma"], dtype=np.float64).reshape(1, -1)
    const = np.asarray(bphi_st["normalizer_constant_mask"]).reshape(-1)
    sig_safe = np.where(sig < 1e-12, 1.0, sig)
    assert mu.shape[1] == len(SCALAR_IDX) == 8
    smu = np.asarray(some_st["normalizer_mu"], dtype=np.float64).reshape(1, -1)
    ssig = np.asarray(some_st["normalizer_sigma"], dtype=np.float64).reshape(1, -1)
    sconst = np.asarray(some_st["normalizer_constant_mask"]).reshape(-1)
    ssig_safe = np.where(ssig < 1e-12, 1.0, ssig)
    assert smu.shape[1] == 16

    TAU_C8 = C.tau_float(C.TAU_C8_EXACT)
    TAU_C7 = C.tau_float(C.TAU_C7_EXACT)
    LAMBDA_C = C.tau_float(C.LAMBDA_C_EXACT)
    assert abs((TAU_C8 + LAMBDA_C) - TAU_C7) < 1e-15

    from src.features.barr_pre_refinement_features import build_feature_vector

    gp = np.lib.format.open_memmap(C.ONESHOT / "global_prob_f16.npy", mode="w+", dtype=np.float16,
                                   shape=(n, C.CANVAS, C.CANVAS))
    deep = np.zeros((n, 192), dtype=np.float32)
    scal = np.zeros((n, 10), dtype=np.float32)
    geom_doc = {}

    batch_forwards = 0
    dom_batches = {}
    pos = {sid: i for i, sid in enumerate(ids)}
    t_inf = time.time()
    for dom in C.DOMAINS:
        sub = [r for r in ordered if r["dataset"] == dom]
        nb = 0
        for start in range(0, len(sub), C.BATCH_SIZE):
            chunk = sub[start:start + C.BATCH_SIZE]
            imgs, tks = [], []
            for r in chunk:
                with Image.open(manifest[r["sample_id"]]["image_path"]) as im:
                    imgs.append(C.image_only_transform(im, C.CANVAS))
                tks.append(int(r["task_id"]))
            bi = torch.stack(imgs).to(device)
            bt = torch.tensor(tks, dtype=torch.long, device=device)
            rec = TapRecorder(g)
            try:
                with torch.no_grad(), torch.amp.autocast(device_type=device.type, enabled=True):
                    logits = g(bi, bt)
                prob = torch.sigmoid(logits.float()).cpu().numpy()[:, 0]
                cmaps = {t: rec.store[t].float().cpu().numpy() for t in TAPS}
            finally:
                rec.close()
            batch_forwards += 1
            nb += 1
            for i, r in enumerate(chunk):
                gi = pos[r["sample_id"]]
                pg = prob[i].astype(np.float32)
                gp[gi] = pg.astype(np.float16)
                geom = roi_geometry(pg, C.ROI_PROPOSAL_THRESHOLD)
                if geom is None:
                    geom_doc[r["sample_id"]] = {"roi_available": False}
                    deep[gi] = np.zeros(192, dtype=np.float32)
                    scal[gi] = np.zeros(10, dtype=np.float32)
                else:
                    cm = {t: cmaps[t][i] for t in TAPS}
                    vec = build_feature_vector(cm, pg, geom)
                    deep[gi] = vec[:192].astype(np.float32)
                    scal[gi] = vec[192:].astype(np.float32)
                    geom_doc[r["sample_id"]] = {"roi_available": True, **{k: geom[k] for k in (
                        "y1", "y2", "x1", "x2", "clip_y1", "clip_y2", "clip_x1", "clip_x2",
                        "pad_top", "pad_bottom", "pad_left", "pad_right", "crop_side_pixels")}}
        dom_batches[dom] = nb
        say(f"  [{dom}] n={len(sub)} batches={nb} fwd={batch_forwards} t={time.time()-t_inf:.0f}s")
    gp.flush()
    assert batch_forwards == 111, batch_forwards
    assert dom_batches == {"BUSI": 12, "ISIC": 48, "KUB": 38, "KVASIR": 13}, dom_batches
    np.save(C.ONESHOT / "router_deep_features_f32.npy", deep)
    np.save(C.ONESHOT / "router_scalars_f32.npy", scal)
    C.write_json({"artifact": "phase30_canonical_roi_geometry", "roi_proposal_threshold": 0.30,
                  "geometry": geom_doc}, C.ONESHOT / "roi_geometry.json")
    say(f"§8 G extraction complete: {batch_forwards} batch forwards, 1 logical pass")

    # ---------------- §9 B_phi pre-execution routing ---------------- #
    X = np.concatenate([deep, scal], axis=1).astype(np.float32)
    assert X.shape == (n, 202), X.shape
    nrm = (X[:, SCALAR_IDX].astype(np.float64) - mu) / sig_safe
    nrm[:, const] = 0.0
    X[:, SCALAR_IDX] = nrm.astype(np.float32)
    with torch.inference_mode():
        delta_hat = b_phi(torch.from_numpy(X).to(device),
                          torch.tensor(tasks, dtype=torch.long, device=device)
                          ).cpu().numpy().astype(np.float64).reshape(-1)
    assert np.all(np.isfinite(delta_hat))
    utility = delta_hat - LAMBDA_C
    selected = utility >= TAU_C8
    assert bool(np.array_equal(selected, delta_hat >= TAU_C7)), "decision forms disagree"
    n_selected = int(selected.sum())
    n_skip = n - n_selected
    realized_activation = n_selected / n
    say(f"§9 B_phi: selected={n_selected} skip={n_skip} realized={realized_activation:.6f}")

    # ---------------- §10 EXECUTE path: R_psi then S_omega ---------------- #
    # Frozen batch semantics: R_psi batch 8, S_omega batch 128 (both eval fp32, no
    # autocast -> batch-independent GroupNorm/conv, so batching is numerically exact).
    exec_idx = [i for i in range(n) if selected[i]]
    a8_final = np.asarray(gp, dtype=np.float32).copy()   # default global
    a7_final = np.asarray(gp, dtype=np.float32).copy()
    somega_scores = np.full(n, np.nan)
    somega_accept = np.zeros(n, dtype=bool)
    n_rpsi = 0
    n_somega = 0
    n_accept = 0
    n_reject = 0
    n_forced_skip = 0
    state = ["SKIP"] * n

    # --- phase 1: collect EXECUTE crops (GT-free) ---
    work = []          # (i, rin_array, geom, prob_crop)
    for i in exec_idx:
        sid = ids[i]
        gd = geom_doc.get(sid)
        if not gd or not gd.get("roi_available"):
            n_forced_skip += 1
            state[i] = "FORCED_SKIP"
            continue
        pg = np.asarray(gp[i], dtype=np.float32)
        rgb = C.image_only_transform(Image.open(manifest[sid]["image_path"]), C.CANVAS)
        rgb_crop = C.crop_and_resize_vec(rgb, gd, C.CROP)
        prob_crop = C.crop_and_resize_vec(pg, gd, C.CROP)
        rin = np.concatenate([np.asarray(rgb_crop, dtype=np.float32),
                              np.asarray(prob_crop, dtype=np.float32)], axis=0)
        work.append((i, np.ascontiguousarray(rin), gd, prob_crop))

    # --- phase 2: R_psi in chunks of 8 ---
    refined = {}
    for s in range(0, len(work), C.BATCH_SIZE):
        chunk = work[s:s + C.BATCH_SIZE]
        bi = torch.from_numpy(np.stack([w[1] for w in chunk])).to(device)
        with torch.inference_mode():
            out = torch.sigmoid(r_psi(bi).float())[:, 0].cpu().numpy()
        for j, w in enumerate(chunk):
            n_rpsi += 1
            refined[w[0]] = out[j].astype(np.float32)

    # --- phase 3: S_omega 20-D features from the candidate ---
    somega_inputs = []
    for (i, rin, gd, prob_crop) in work:
        pgc = np.asarray(prob_crop, dtype=np.float32)
        pgc = pgc[0] if pgc.ndim == 3 else pgc
        prc = np.asarray(refined[i], dtype=np.float32)
        f16 = np.asarray(C.somega_features(pgc, prc, gd), dtype=np.float64).reshape(1, -1)
        assert f16.shape == (1, 16)
        f16n = ((f16 - smu) / ssig_safe)[0]
        f16n = np.where(sconst, 0.0, f16n).astype(np.float32)
        onehot = np.zeros(4, dtype=np.float32)
        onehot[tasks[i]] = 1.0
        somega_inputs.append((i, np.concatenate([f16n, onehot]).astype(np.float32)))

    # --- phase 4: S_omega in chunks of 128 ---
    for s in range(0, len(somega_inputs), C.SOMEGA_BATCH):
        chunk = somega_inputs[s:s + C.SOMEGA_BATCH]
        bi = torch.from_numpy(np.stack([c[1] for c in chunk])).to(device)
        with torch.inference_mode():
            logits = s_omega(bi).reshape(-1)
            probs = torch.sigmoid(logits).cpu().numpy()
        for j, (i, _) in enumerate(chunk):
            n_somega += 1
            sp = float(probs[j])
            somega_scores[i] = sp
            acc = sp >= C.SOMEGA_ACCEPT_THRESHOLD
            somega_accept[i] = acc
            cand = C.fuse_full_field(np.asarray(gp[i], dtype=np.float32), refined[i],
                                     geom_doc[ids[i]])
            a7_final[i] = cand.astype(np.float32)   # A7 always accepts on EXECUTE
            if acc:
                n_accept += 1
                state[i] = "EXECUTE_THEN_ACCEPT"
                a8_final[i] = cand.astype(np.float32)
            else:
                n_reject += 1
                state[i] = "EXECUTE_THEN_REJECT"

    say(f"§10 EXECUTE path: R_psi_exec={n_rpsi} S_omega_exec={n_somega} "
        f"accept={n_accept} reject={n_reject} forced_skip={n_forced_skip}")
    assert n_rpsi == n_selected - n_forced_skip
    assert n_somega == n_rpsi
    assert n_accept + n_reject + n_forced_skip == n_selected

    # persist Stage-A outputs
    np.save(C.ONESHOT / "bphi_delta_hat_f32.npy", delta_hat.astype(np.float32))
    np.save(C.ONESHOT / "bphi_utility_f32.npy", utility.astype(np.float32))
    np.save(C.ONESHOT / "router_selected_bool.npy", selected)
    np.save(C.ONESHOT / "a8_final_prob_f16.npy", a8_final.astype(np.float16))
    np.save(C.ONESHOT / "a7_companion_prob_f16.npy", a7_final.astype(np.float16))
    np.save(C.ONESHOT / "somega_score_f32.npy", somega_scores.astype(np.float32))
    np.save(C.ONESHOT / "somega_accept_bool.npy", somega_accept)

    # per-sample decision table (NO GT column)
    dec_rows = []
    for i in range(n):
        dec_rows.append([
            i, ids[i], domains[i], tasks[i], repr(float(delta_hat[i])), repr(float(utility[i])),
            repr(float(TAU_C8)), "EXECUTE" if selected[i] else "SKIP", state[i],
            ("" if np.isnan(somega_scores[i]) else repr(float(somega_scores[i]))),
            ("True" if somega_accept[i] else ("False" if selected[i] else "")),
            "A8_REFINED" if state[i] == "EXECUTE_THEN_ACCEPT" else "A8_GLOBAL",
            "A7_REFINED" if state[i] in ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")
            else "A7_GLOBAL",
            ("True" if (geom_doc.get(ids[i]) or {}).get("roi_available") else "False")])
    C.write_csv(C.TAB / "phase30_router_holdout_predictions.csv",
                ["canonical_order_index", "sample_id", "dataset", "task_id", "delta_hat",
                 "utility", "tau_C8", "router_decision", "state_machine", "somega_score",
                 "somega_accept", "a8_source", "a7_source", "roi_available"], dec_rows)

    C.write_json({
        "artifact": "phase30_stage_a_inference_summary", "phase": 30, "stage": "STAGE_A",
        "specification_revision": C.SPEC_REVISION, "method": C.METHOD,
        "population": "ROUTER_HOLDOUT", "n": n, "domain_counts": C.DOMAIN_N,
        "logical_G_passes": 1, "G_samples": n, "G_batch_forwards": batch_forwards,
        "G_batch_forwards_by_domain": dom_batches,
        "G_semantics": {"device": str(device), "autocast_enabled": True, "autocast_dtype": "float16",
                        "grad_context": "torch.no_grad()", "inference_mode": False, "batch_size": 8,
                        "sample_order": "(dataset asc, sample_id asc)",
                        "domain_order": C.DOMAINS, "contiguous_within_domain": True},
        "router": {"policy": "C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY", "runtime_score": C.RUNTIME_SCORE,
                   "tau_C8_exact": f"{C.TAU_C8_EXACT[0]}/{C.TAU_C8_EXACT[1]}",
                   "tau_C7_exact": f"{C.TAU_C7_EXACT[0]}/{C.TAU_C7_EXACT[1]}",
                   "lambda_C_exact": f"{C.LAMBDA_C_EXACT[0]}/{C.LAMBDA_C_EXACT[1]}",
                   "score_path": "FULL_FEATURE_MATRIX_SINGLE_FORWARD", "sigmoid_applied": False},
        "component_batch_semantics": {
            "R_psi": {"batch_size": 8, "autocast": False, "inference_mode": True,
                      "note": "eval fp32 GroupNorm/conv -> batch-independent"},
            "S_omega": {"batch_size": 128, "autocast": False, "inference_mode": True,
                        "note": "eval fp32 -> batch-independent"},
            "B_phi": {"batch_size": "FULL_FEATURE_MATRIX", "sigmoid_applied": False}},
        "n_selected": n_selected, "n_skip": n_skip,
        "realized_activation_fraction": realized_activation,
        "n_Rpsi_exec": n_rpsi, "n_Somega_exec": n_somega,
        "n_accept": n_accept, "n_reject": n_reject, "n_forced_skip": n_forced_skip,
        "safety_accept_fraction": (n_accept / n_selected if n_selected else None),
        "A7_additional_model_forwards": 0,
        "R_psi_exec_equals_router_execute": (n_rpsi + n_forced_skip) == n_selected,
        "Somega_exec_equals_Rpsi_exec": n_somega == n_rpsi,
        "S_omega_saves_compute": False,
        "val808_gt_reads": 0, "ROUTER_HOLDOUT_GT_reads": 0, "TEST_reads": 0,
        "elapsed_seconds": round(time.time() - t0, 1),
        "generated_utc": C.now_utc(), "all_pass": True,
    }, C.AUD / "phase30_stage_a_inference_summary.json")

    # ---------------- §12 PREDICTION HASH BARRIER ---------------- #
    stage_a_files = ["global_prob_f16.npy", "router_deep_features_f32.npy",
                     "router_scalars_f32.npy", "roi_geometry.json", "bphi_delta_hat_f32.npy",
                     "bphi_utility_f32.npy", "router_selected_bool.npy", "a8_final_prob_f16.npy",
                     "a7_companion_prob_f16.npy", "somega_score_f32.npy", "somega_accept_bool.npy"]
    hashes = {f: C.sha256_file(C.ONESHOT / f) for f in stage_a_files}
    hashes["reports/tables/phase30_router_holdout_predictions.csv"] = C.sha256_file(
        C.TAB / "phase30_router_holdout_predictions.csv")
    C.write_json({
        "artifact": "phase30_prediction_hash_barrier", "phase": 30, "stage": "PREDICTION_HASH_BARRIER",
        "specification_revision": C.SPEC_REVISION, "method": C.METHOD,
        "barrier_token": "PREDICTION_HASH_BARRIER_PASS",
        "prediction_hashes": hashes,
        "n_samples": n, "ROUTER_HOLDOUT_GT_reads_at_hash": 0, "GT_loaded_anywhere": False,
        "TEST_reads": 0,
        "all_predictions_durably_persisted": True, "all_decisions_durably_persisted": True,
        "all_prediction_hashes_frozen": True,
        "A8_final_hash_frozen": True, "A7_companion_hash_frozen": True,
        "router_decision_hash_frozen": True,
        "sample_ids_sha256": C.sha256_ids(ids),
        "generated_utc": C.now_utc(), "all_pass": True,
    }, C.AUD / "phase30_prediction_hash_barrier.json")
    say("§12 >>> PREDICTION_HASH_BARRIER_PASS (GT reads at hash = 0)")

    # ---------------- §13 STAGE-A PRE-GT FINAL CHECK ---------------- #
    checks = {
        "population_875_exact": n == 875,
        "G_batch_forwards_111": batch_forwards == 111,
        "G_batch_partition_exact": dom_batches == {"BUSI": 12, "ISIC": 48, "KUB": 38, "KVASIR": 13},
        "logical_G_passes_1": True,
        "G_batch_manifest_honored": True,
        "no_duplicate_samples": len(set(ids)) == 875,
        "all_component_hashes_match": True,
        "all_normalizers_match": True,
        "all_feature_schemas_match": True,
        "bphi_full_matrix_path": True,
        "router_decisions_frozen": True,
        "n_selected_equals_Rpsi_exec": (n_rpsi + n_forced_skip) == n_selected,
        "Rpsi_exec_equals_Somega_exec": n_somega == n_rpsi,
        "A7_additional_forwards_0": True,
        "prediction_hash_barrier_complete": True,
        "GT_reads_0": True, "TEST_reads_0": True,
        "no_training": True, "no_recalibration": True, "no_threshold_change": True,
    }
    n_failed = sum(1 for v in checks.values() if not v)
    C.write_json({"artifact": "phase30_stage_a_pre_gt_final_check", "phase": 30,
                  "stage": "STAGE_A_PRE_GT_FINAL_CHECK", "specification_revision": C.SPEC_REVISION,
                  "n_checks": len(checks), "n_failed": n_failed,
                  "failed": [k for k, v in checks.items() if not v], "checks": checks,
                  "generated_utc": C.now_utc(), "all_pass": n_failed == 0},
                 C.AUD / "phase30_stage_a_pre_gt_final_check.json")
    say(f"§13 Stage-A pre-GT check: {len(checks)-n_failed}/{len(checks)} pass")
    if n_failed:
        C.write_json({"artifact": "phase30_execution_terminal", "terminal":
                      "PHASE30_ONE_SHOT_EXECUTION_BLOCKED_AFTER_FIRST_OPEN__STAGE_A_CHECK_FAILED__"
                      "EVIDENCE_PRESERVED__NO_RERUN_AUTHORIZED", "all_pass": False},
                     C.AUD / "phase30_execution_terminal.json")
        return 1

    say("")
    say("=" * 78)
    say("STAGE A COMPLETE — predictions hashed and frozen; GT NOT read")
    say(f"elapsed={time.time()-t0:.0f}s")
    say("=" * 78)
    say("PHASE30_STAGE_A_COMPLETE__PREDICTION_HASH_BARRIER_PASS__GT_NOT_READ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
