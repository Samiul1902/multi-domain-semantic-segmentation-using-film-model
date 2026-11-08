"""Phase D/E — Training history recovery.

Builds two machine-readable artifacts from the genuine per-epoch logs stored in
`experiments/*/history.csv` and the frozen closure/registry metadata:

  tables/TRAINING_RUN_REGISTRY.csv   one row per training run
  tables/REMEDFILM_EPOCH_HISTORY.csv long-form epoch records

Nothing is synthesised. Metrics absent from a run's log are simply not emitted,
and the registry records the absence explicitly.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
TABLES = OUT / "tables"
TABLES.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Model identity: derived from the experiment directory, never invented.
# --------------------------------------------------------------------------
MODEL_RULES = [
    ("phase21_global_medfilm", "GlobalMedFiLM (G)", "G_BACKBONE"),
    ("phase20b_shared_unet_fourdomain", "U-Net", "BASELINE"),
    ("phase20b_shared_attention_unet", "Attention U-Net", "BASELINE"),
    ("phase20b_shared_deeplabv3plus", "DeepLabV3+", "BASELINE"),
    ("phase20b_shared_transformer_mit_unet", "Transformer/MiT-style U-Net", "BASELINE"),
    ("phase20_shared_unetpp", "U-Net++", "BASELINE"),
    ("phase25a_barr_regional_refiner", "R_psi (Regional Refiner)", "COMPONENT"),
    ("phase25d_barr_benefit_router", "B_phi (Benefit Router)", "COMPONENT"),
    ("phase25f_barr_post_safety", "S_omega (Post-Safety Gate)", "COMPONENT"),
    ("phase28_refiner_f1_no_pglobal", "F1 (Ablation Variant)", "ABLATION"),
    ("phase29_seed", "ReMedFiLM component (seed replication)", "COMPONENT"),
    ("phase14_kub_refiner", "Regional refiner (precursor)", "PRECURSOR"),
    ("phase13b_kub_localizer", "KUB localizer (ROI proposal)", "PRECURSOR"),
    ("h3_kub_localizer", "KUB localizer (H3)", "PRECURSOR"),
    ("post_phase13_h2", "KUB localizer (H2 diagnostics)", "PRECURSOR"),
    ("phase10_kub_", "KUB baseline", "BASELINE"),
    ("phase9_kub_unet", "U-Net", "BASELINE"),
]

COMPONENT_RULES = [
    ("/bphi/", "B_phi (Benefit Router)"),
    ("/somega/", "S_omega (Post-Safety Gate)"),
    ("/final_refit/", "R_psi (Regional Refiner)"),
    ("/fold", "R_psi (Regional Refiner)"),
]

# Canonical long-form metric names. `None` target => metric is not part of the
# canonical set and is not emitted.
METRIC_MAP = {
    "train_loss": "train_loss",
    "val_loss": "val_loss",
    "macro_domain_dice": "val_macro_dice",
    "val_macro_dice": "val_macro_dice",
    "val_dice": "val_dice",
    "val_iou": "val_iou",
    "val_macro_iou": "val_macro_iou",
    "val_precision": "val_precision",
    "val_recall": "val_recall",
    "val_macro_precision": "val_macro_precision",
    "val_macro_recall": "val_macro_recall",
    "learning_rate": "learning_rate",
    "lr": "learning_rate",
    "epoch_seconds": "epoch_seconds",
    "elapsed_seconds": "epoch_seconds",
    "peak_gpu_allocated": "peak_gpu_allocated",
    "peak_gpu_reserved": "peak_gpu_reserved",
    "early_stop_dice": "val_refiner_dice",
    "early_stop_loss": "val_refiner_loss",
    "train_BCE": "train_bce",
    "train_Dice_loss": "train_dice_loss",
    "train_huber": "train_huber",
    "early_stop_huber": "val_router_huber",
    "train_bce": "train_bce",
    "early_stop_bce": "val_safety_bce",
    "val_crop_dice": "val_crop_dice",
    "tiny_recall90": "val_localizer_tiny_recall90",
    "overall_recall90": "val_localizer_overall_recall90",
    "val_tiny_recall90": "val_localizer_tiny_recall90",
    "val_overall_recall90": "val_localizer_overall_recall90",
    "best_so_far": "best_metric_so_far",
    "best_epoch_so_far": "best_epoch_so_far",
}
for _d in ("ISIC", "BUSI", "KVASIR", "KUB"):
    METRIC_MAP[f"val_dice_{_d}"] = f"val_dice_{_d}"
    METRIC_MAP[f"val_iou_{_d}"] = f"val_iou_{_d}"
    METRIC_MAP[f"val_precision_{_d}"] = f"val_precision_{_d}"
    METRIC_MAP[f"val_recall_{_d}"] = f"val_recall_{_d}"

DOMAIN_DATASET = {
    "phase21_global_medfilm": "MULTI_DOMAIN(ISIC,BUSI,KVASIR,KUB)",
    "phase20_shared_unetpp": "MULTI_DOMAIN(ISIC,BUSI,KVASIR,KUB)",
    "phase20b_shared_unet_fourdomain": "MULTI_DOMAIN(ISIC,BUSI,KVASIR,KUB)",
    "phase20b_shared_attention_unet": "MULTI_DOMAIN(ISIC,BUSI,KVASIR,KUB)",
    "phase20b_shared_deeplabv3plus": "MULTI_DOMAIN(ISIC,BUSI,KVASIR,KUB)",
    "phase20b_shared_transformer_mit_unet": "MULTI_DOMAIN(ISIC,BUSI,KVASIR,KUB)",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def identify(rel: str) -> tuple[str, str, str]:
    """Return (model_identity, model_role, dataset)."""
    low = rel.lower().replace("\\", "/")
    model, role = "UNIDENTIFIED", "UNIDENTIFIED"
    for token, name, r in MODEL_RULES:
        if token in low:
            model, role = name, r
            break
    if "phase29_seed" in low:
        comp = "ReMedFiLM component (seed replication)"
        for tok, nm in COMPONENT_RULES:
            if tok in low:
                comp = nm
                break
        model = comp
    if "phase25" in low:
        for tok, nm in COMPONENT_RULES:
            if tok in low:
                model = nm
                break
    dataset = "KUB" if ("kub" in low or "phase13" in low or "phase14" in low
                        or "h3_kub" in low) else ""
    for token, ds in DOMAIN_DATASET.items():
        if token in low:
            dataset = ds
            break
    if "phase25" in low or "phase28" in low or "phase29" in low:
        dataset = "ROUTER_DEVELOPMENT_4957(fit) / VAL808(select)"
    return model, role, dataset


def seed_of(rel: str, config: dict | None) -> str:
    low = rel.lower()
    if "seed3407" in low:
        return "3407"
    if "seed123" in low:
        return "123"
    if "seed42" in low:
        return "42"
    if config:
        s = (config.get("configuration", {}) or {}).get("training", {}).get("seed")
        if s is not None:
            return str(s)
        s = config.get("training", {}).get("seed")
        if s is not None:
            return str(s)
        # run.json stores the seed at the top level
        s = config.get("seed")
        if s is not None:
            return str(s)
    return "NOT_RECORDED"


def find_closure(hist: Path) -> dict | None:
    for cand in ("closure.json", "phase21_training_closure.json",
                 "run.json", "config.json"):
        p = hist.parent / cand
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
    return None


def main() -> None:
    registry_rows = []
    epoch_rows = []
    provenance = []

    hist_files = sorted(ROOT.glob("experiments/**/history.csv"))
    for hist in hist_files:
        rel = hist.relative_to(ROOT).as_posix()
        run_id = rel.replace("experiments/", "").replace("/history.csv", "").replace("/", "__")
        model, role, dataset = identify(rel)

        with hist.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            cols = reader.fieldnames or []
            records = list(reader)

        closure = find_closure(hist)
        seed = seed_of(rel, closure)
        n_epochs = len(records)
        epochs = [int(float(r["epoch"])) for r in records if r.get("epoch") not in (None, "")]

        # ---- best epoch / selection ----
        best_epoch, selection_metric, selection_rule = None, "", "NOT_RECORDED"
        if closure and closure.get("best_epoch") not in (None, -1):
            best_epoch = int(closure["best_epoch"])
            selection_metric = closure.get("selection_rule_id", "") or closure.get("checkpoint_metric", "")
            selection_rule = "RECORDED_CLOSURE"
        elif closure and closure.get("best_epoch") == -1 and closure.get("stop_reason") in (
                "max_epochs_reached", "MAX_EPOCHS_REACHED"):
            selection_rule = "NOT_APPLICABLE_FIXED_EPOCH_REFIT"
        else:
            # 1) explicit per-epoch selection flags written by the trainer
            for flag in ("is_new_best", "is_best", "is_best_epoch"):
                if flag in cols:
                    hits = [int(float(r["epoch"])) for r in records
                            if str(r.get(flag)).strip().lower() in ("true", "1")]
                    if hits:
                        best_epoch = hits[-1]
                        selection_metric = f"{flag} flag"
                        selection_rule = "RECORDED_FLAG"
                        break
            # 2) checkpoint event column
            if best_epoch is None and "checkpoint_event" in cols:
                hits = [int(float(r["epoch"])) for r in records
                        if "best" in str(r.get("checkpoint_event", "")).lower()]
                if hits:
                    best_epoch = hits[-1]
                    selection_metric = "checkpoint_event=BEST"
                    selection_rule = "RECORDED_EVENT"
            # 3) trailing best-epoch column
            if best_epoch is None and "best_epoch_so_far" in cols:
                vals = [int(float(r["best_epoch_so_far"])) for r in records
                        if str(r.get("best_epoch_so_far")).strip() not in ("", "-1", "None")]
                if vals:
                    best_epoch = max(vals)
                    selection_metric = "best_epoch_so_far"
                    selection_rule = "RECORDED_TRAILING_COLUMN"
            # 4) min early-stopping loss recorded per epoch
            if best_epoch is None:
                for col in ("best_early_stop_loss_so_far", "early_stop_huber", "early_stop_bce"):
                    if col not in cols:
                        continue
                    vals = [(float(r[col]), int(float(r["epoch"]))) for r in records
                            if str(r.get(col)).strip() not in ("", "None", "nan")]
                    if vals:
                        best_epoch = min(vals)[1]
                        selection_metric = f"{col} (min)"
                        selection_rule = "DERIVED_MIN_METRIC"
                        break
            # 5) last resort: argmax of the run's primary metric
            if best_epoch is None:
                for col in ("macro_domain_dice", "val_macro_dice", "val_dice",
                            "tiny_recall90", "val_crop_dice", "early_stop_dice"):
                    if col not in cols:
                        continue
                    vals = [(float(r[col]), int(float(r["epoch"]))) for r in records
                            if str(r.get(col)).strip() not in ("", "None", "nan")]
                    if vals:
                        best_epoch = max(vals)[1]
                        selection_metric = f"argmax {col}"
                        selection_rule = "DERIVED_ARGMAX"
                        break

        # ---- canonical best epoch for the phase13b clean_v3 localizer ----
        if best_epoch is None and "phase13b" in rel and "clean_v3" in rel:
            audit = ROOT / "reports/audits/phase13_clean_v3_localizer_best_epoch_verification.json"
            if audit.exists():
                try:
                    a = json.loads(audit.read_text(encoding="utf-8"))
                    if a.get("replayed_best_epoch") is not None:
                        best_epoch = int(a["replayed_best_epoch"])
                        selection_metric = "canonical_selection_tuple (replayed)"
                        selection_rule = "RECORDED_REPLAY_AUDIT"
                except Exception:  # noqa: BLE001
                    pass

        # ---- checkpoint identity ----
        ckpt_path, ckpt_hash = "", ""
        if closure:
            for key in ("best_checkpoint_sha256", "checkpoint_sha256"):
                if closure.get(key):
                    ckpt_hash = closure[key]
                    break
        for cand in ("best.pt", "final.pt", "refiner_best.pt", "router_best.pt"):
            p = hist.parent / cand
            if p.exists():
                ckpt_path = p.relative_to(ROOT).as_posix()
                if not ckpt_hash:
                    ckpt_hash = sha256(p)
                break
        if not ckpt_path:
            for p in sorted(hist.parent.glob("*.pt")):
                ckpt_path = p.relative_to(ROOT).as_posix()
                if not ckpt_hash:
                    ckpt_hash = sha256(p)
                break

        # ---- evidence status ----
        if n_epochs == 0:
            evidence = "LOG_PRESENT_ZERO_EPOCHS"
        elif closure and closure.get("training_performed") is False:
            evidence = "SYNTHETIC_FIXTURE"
        elif "synthetic" in rel.lower():
            evidence = "SYNTHETIC_FIXTURE"
        elif best_epoch is None and selection_rule == "NOT_APPLICABLE_FIXED_EPOCH_REFIT":
            evidence = "GENUINE_HISTORICAL_TRAINING"
        elif best_epoch is None:
            evidence = "GENUINE_HISTORY_BEST_EPOCH_UNRESOLVED"
        else:
            evidence = "GENUINE_HISTORICAL_TRAINING"

        planned = ""
        if closure:
            planned = (closure.get("configuration", {}) or {}).get("training", {}).get("max_epochs", "")
        registry_rows.append({
            "run_id": run_id,
            "phase": (rel.split("/")[1].split("_")[1] if rel.split("/")[1].startswith("phase")
                      else ("13" if "phase13" in rel else "post13")),
            "model": model,
            "model_role": role,
            "dataset": dataset,
            "seed": seed,
            "epochs_planned": planned,
            "epochs_completed": n_epochs,
            "best_epoch": (best_epoch if best_epoch is not None
                            else ("NOT_APPLICABLE" if selection_rule == "NOT_APPLICABLE_FIXED_EPOCH_REFIT"
                                  else "NOT_RECORDED")),
            "best_epoch_source": selection_rule,
            "selection_metric": selection_metric,
            "best_checkpoint": ckpt_path or "NOT_FOUND",
            "checkpoint_hash": ckpt_hash or "NOT_RECORDED",
            "history_source": rel,
            "history_sha256": sha256(hist),
            "evidence_status": evidence,
        })

        # ---- long-form epoch records ----
        for r in records:
            try:
                ep = int(float(r["epoch"]))
            except (KeyError, TypeError, ValueError):
                continue
            for col, canon in METRIC_MAP.items():
                if col not in cols:
                    continue
                raw = r.get(col)
                if raw in (None, "", "N/A", "nan", "NaN"):
                    continue
                try:
                    val = float(raw)
                except (TypeError, ValueError):
                    continue
                if val != val:  # NaN
                    continue
                epoch_rows.append({
                    "run_id": run_id,
                    "model_identity": model,
                    "model_role": role,
                    "seed": seed,
                    "epoch": ep,
                    "metric": canon,
                    "value": repr(val),
                    "source_metric_column": col,
                    "source_path": rel,
                })

        provenance.append({
            "run_id": run_id,
            "history_source": rel,
            "history_sha256": sha256(hist),
            "n_epoch_records": n_epochs,
            "epoch_min": min(epochs) if epochs else None,
            "epoch_max": max(epochs) if epochs else None,
            "epoch_contiguous": bool(epochs) and epochs == list(range(min(epochs), min(epochs) + len(epochs))),
            "metrics_available": sorted({METRIC_MAP[c] for c in cols if c in METRIC_MAP}),
            "closure_metadata_present": closure is not None,
            "evidence_status": evidence,
        })

    # ---------------- write registry ----------------
    reg_fields = ["run_id", "phase", "model", "model_role", "dataset", "seed",
                  "epochs_planned", "epochs_completed", "best_epoch",
                  "best_epoch_source", "selection_metric", "best_checkpoint",
                  "checkpoint_hash", "history_source", "history_sha256",
                  "evidence_status"]
    with (TABLES / "TRAINING_RUN_REGISTRY.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=reg_fields)
        w.writeheader()
        for r in registry_rows:
            w.writerow({k: r[k] for k in reg_fields})

    # ---------------- write epoch history ----------------
    ep_fields = ["run_id", "model_identity", "model_role", "seed", "epoch",
                 "metric", "value", "source_metric_column", "source_path"]
    with (TABLES / "REMEDFILM_EPOCH_HISTORY.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ep_fields)
        w.writeheader()
        w.writerows(epoch_rows)

    # ---------------- provenance ----------------
    (OUT / "TRAINING_HISTORY_PROVENANCE.json").write_text(json.dumps({
        "artifact": "training_history_provenance",
        "policy": ("Every epoch record is read from a persisted history.csv. "
                   "No value is interpolated, smoothed or synthesised. Metrics a run "
                   "did not log are absent rather than zero."),
        "n_history_files": len(hist_files),
        "n_epoch_records": len(epoch_rows),
        "n_runs": len(registry_rows),
        "runs": provenance,
    }, indent=2), encoding="utf-8")

    print(f"HISTORY_FILES {len(hist_files)}")
    print(f"RUNS {len(registry_rows)}")
    print(f"EPOCH_RECORDS {len(epoch_rows)}")
    from collections import Counter
    print("EVIDENCE:", dict(Counter(r["evidence_status"] for r in registry_rows)))
    print("MODELS:", dict(Counter(r["model"] for r in registry_rows)))


if __name__ == "__main__":
    main()
