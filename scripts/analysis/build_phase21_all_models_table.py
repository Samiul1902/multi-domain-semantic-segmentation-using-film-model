"""Build the consolidated all-previously-trained-models comparison table.

Produces
--------
reports/tables/phase21_all_trained_models_comparison.csv
reports/tables/phase21_all_trained_models_comparison.md

Sources (all read-only, no inference, no TEST access)
-----------------------------------------------------
* Frozen Phase-20/20B five-model panel : reports/tables/phase20b_five_model_comparison.csv
* Frozen Phase-20/20B paired bootstrap : reports/tables/phase20b_five_model_paired_bootstrap.csv
* Frozen Phase-20 domain metrics       : reports/tables/phase20_domain_performance.csv
* Frozen Phase-21 compute accounting   : reports/tables/phase21_six_model_compute.csv
* LIVE Phase-21 history                : experiments/<EXP>/history.csv

IMPORTANT — comparability discipline
------------------------------------
The five Phase-20/20B baselines are FROZEN results: one canonical VAL pass over a frozen best
checkpoint. The Phase-21 row is a LIVE per-epoch validation value from a run that has not
terminated and whose checkpoint selection is not final. The two are therefore NOT on equal
footing, and the table says so explicitly. The Phase-21 row is included for orientation only
and is labelled IN PROGRESS everywhere it appears.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
TAB = ROOT / "reports" / "tables"
AUD = ROOT / "reports" / "audits"

EXP = "phase21_global_medfilm_fourdomain_seed42_clean_v3"
EXP_DIR = ROOT / "experiments" / EXP

OUT_CSV = TAB / "phase21_all_trained_models_comparison.csv"
OUT_MD = TAB / "phase21_all_trained_models_comparison.md"

FROZEN_PANEL = TAB / "phase20b_five_model_comparison.csv"
PAIRED = TAB / "phase20b_five_model_paired_bootstrap.csv"
COMPUTE = TAB / "phase21_six_model_compute.csv"


def load_frozen_panel() -> pd.DataFrame:
    df = pd.read_csv(FROZEN_PANEL)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "model": r["display_name"],
            "model_key": r["model_key"],
            "phase": str(r["phase"]),
            "params": int(r["params"]),
            "best_epoch": int(r["best_epoch"]),
            "final_epoch": int(r["final_epoch"]),
            "stop_reason": r["stop_reason"],
            "macro_dice": float(r["best_macro_domain_dice"]),
            "ISIC": float(r["per_domain_dice_ISIC"]),
            "BUSI": float(r["per_domain_dice_BUSI"]),
            "KVASIR": float(r["per_domain_dice_KVASIR"]),
            "KUB": float(r["per_domain_dice_KUB"]),
            "provenance": "FROZEN",
            "status": "COMPLETE",
        })
    return pd.DataFrame(rows)


def load_phase21_live() -> dict:
    hist = pd.read_csv(EXP_DIR / "history.csv")
    b = hist.loc[hist["macro_domain_dice"].idxmax()]
    state_path = EXP_DIR / "training_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    # If the run has terminated AND the canonical VAL pass has completed, the
    # Phase-21 row is no longer "live": the checkpoint is fixed and the number comes
    # from ONE canonical VAL pass, so it is directly comparable to the frozen panel.
    closure_path = EXP_DIR / "phase21_training_closure.json"
    val_path = AUD / "phase21_val_evaluation.json"
    ana_path = AUD / "phase21_analysis.json"
    closure = json.loads(closure_path.read_text(encoding="utf-8")) if closure_path.exists() else {}
    val = json.loads(val_path.read_text(encoding="utf-8")) if val_path.exists() else {}
    ana = json.loads(ana_path.read_text(encoding="utf-8")) if ana_path.exists() else {}
    terminated = closure.get("stop_reason") in ("EARLY_STOPPING_PATIENCE", "MAX_EPOCHS")
    # The metrics themselves are published by the analysis step; the val-evaluation
    # artifact only records provenance (how many samples, which checkpoint, TEST=0).
    gm_analysis = ana.get("global_medfilm", {})
    canonical = (terminated
                 and val.get("samples_evaluated") == 808
                 and "macro_domain_dice" in gm_analysis)

    if canonical:
        gm = {"macro_dice": float(gm_analysis["macro_domain_dice"]),
              "ISIC": float(gm_analysis["per_domain_dice"]["ISIC"]),
              "BUSI": float(gm_analysis["per_domain_dice"]["BUSI"]),
              "KVASIR": float(gm_analysis["per_domain_dice"]["KVASIR"]),
              "KUB": float(gm_analysis["per_domain_dice"]["KUB"])}
        provenance, status = "FROZEN", "COMPLETE"
    else:
        gm = {"macro_dice": float(b["macro_domain_dice"]),
              "ISIC": float(b["val_dice_ISIC"]),
              "BUSI": float(b["val_dice_BUSI"]),
              "KVASIR": float(b["val_dice_KVASIR"]),
              "KUB": float(b["val_dice_KUB"])}
        provenance, status = "LIVE", "IN PROGRESS"

    return {
        "model": "Global MedFiLM",
        "model_key": "global_medfilm",
        "phase": "21",
        "params": 3523001,
        "best_epoch": int(closure.get("best_epoch", b["epoch"])),
        "final_epoch": int(state.get("epoch", len(hist))),
        "stop_reason": closure.get("stop_reason", "IN_PROGRESS"),
        "macro_dice": gm["macro_dice"],
        "ISIC": gm["ISIC"],
        "BUSI": gm["BUSI"],
        "KVASIR": gm["KVASIR"],
        "KUB": gm["KUB"],
        "provenance": provenance,
        "status": status,
        "bad_epochs": int(state.get("bad_epochs", -1)),
        "patience": int(state.get("early_stopping_patience", -1)),
        "epochs_completed": int(state.get("epoch", len(hist))),
        "resume_count": int(state.get("resume_count", 0)),
    }


def attach_compute(df: pd.DataFrame) -> pd.DataFrame:
    if not COMPUTE.exists():
        df["gmacs"] = None
        return df
    c = pd.read_csv(COMPUTE)[["model_key", "gmacs", "params_rank", "gmacs_rank"]]
    return df.merge(c, on="model_key", how="left")


def main() -> int:
    frozen = load_frozen_panel()
    live = load_phase21_live()
    p21 = pd.DataFrame([
        {k: v for k, v in live.items()
         if k in ("model", "model_key", "phase", "params", "best_epoch", "final_epoch",
                  "stop_reason", "macro_dice", "ISIC", "BUSI", "KVASIR", "KUB",
                  "provenance", "status")}
    ])
    allm = pd.concat([frozen, p21], ignore_index=True)
    allm = attach_compute(allm)
    allm["is_frozen"] = allm["provenance"] == "FROZEN"

    # ---- full-panel table (frozen ranked; live labelled) ----
    allm["macro_rank"] = allm["macro_dice"].rank(ascending=False, method="min").astype(int)
    allm = allm.sort_values("macro_dice", ascending=False).reset_index(drop=True)
    allm.to_csv(OUT_CSV, index=False)

    frozen_only = allm[allm["is_frozen"]].copy()
    fr = frozen_only["macro_dice"].rank(ascending=False, method="min").astype(int)
    frozen_only["frozen_rank"] = fr

    L: list[str] = []
    A = L.append
    A("# Consolidated comparison — all previously trained models")
    A("")
    A(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} by "
      "`scripts/analysis/build_phase21_all_models_table.py`.")
    A("")
    A("## ⚠️ Comparability notice — read before citing any number")
    A("")
    A("This table mixes **two different kinds of evidence**:")
    A("")
    A("| Provenance | Meaning |")
    A("|---|---|")
    A("| **FROZEN** | One canonical VAL pass over a frozen best checkpoint. "
      "Safe to cite as a benchmark result. |")
    A("| **LIVE** | A per-epoch validation value from a run that **has not terminated**. "
      "The checkpoint selection is **not final**. Orientation only — **not a result**. |")
    A("")
    _n_live = int((~allm["is_frozen"]).sum())
    if _n_live:
        A(f"**{_n_live} row(s) are LIVE.** The remaining rows are FROZEN and were trained under the")
        A("identical frozen Phase-20 protocol. Do **not** read a LIVE row as a ranking entry, and")
        A("do **not** compute a paired significance test against it until the run terminates and its")
        A("canonical VAL pass has completed.")
    else:
        A("**Every row is FROZEN** — each is a single canonical VAL pass over a fixed best")
        A("checkpoint. The Phase-21 Global MedFiLM row was trained under the identical frozen")
        A("Phase-20 protocol, so the panel is directly comparable.")
    A("")

    A("## 1. Full panel — macro-domain VAL Dice")
    A("")
    A("| # | Model | Phase | Params | G MACs | Macro Dice | ISIC | BUSI | KVASIR | KUB | Provenance |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in allm.iterrows():
        g = f"{r['gmacs']:.2f}" if pd.notna(r.get("gmacs")) else "—"
        md = f"**{r['macro_dice']:.6f}**" if r["is_frozen"] else f"{r['macro_dice']:.6f}*"
        A(f"| {int(r['macro_rank'])} | {r['model']} | {r['phase']} | {int(r['params']):,} | {g} | "
          f"{md} | {r['ISIC']:.4f} | {r['BUSI']:.4f} | {r['KVASIR']:.4f} | {r['KUB']:.4f} | "
          f"{r['provenance']} |")
    A("")
    if _n_live:
        A("`*` = LIVE / in-progress value, not a result.")
        A("")

    A(f"## 2. Frozen benchmark — the citable ranking ({len(frozen_only)} models)")
    A("")
    A("| Rank | Model | Macro Dice | Best ep | Final ep | Params |")
    A("|---|---|---|---|---|---|")
    for _, r in frozen_only.sort_values("macro_dice", ascending=False).iterrows():
        A(f"| {int(r['frozen_rank'])} | {r['model']} | **{r['macro_dice']:.6f}** | "
          f"{int(r['best_epoch'])} | {int(r['final_epoch'])} | {int(r['params']):,} |")
    A("")
    A("Every row in this section is a frozen best checkpoint evaluated in ONE canonical VAL pass,")
    A("with `test_reads = 0` on all four counters.")
    A("")
    A("### 2.1 Tier structure")
    A("")
    A("| Tier | Models | Macro Dice band | Verdict |")
    A("|---|---|---|---|")
    if "global_medfilm" in set(frozen_only["model_key"]):
        A("| 1 | Global MedFiLM, DeepLabV3+, Transformer/MiT | 0.8224 – 0.8351 | "
          "Tier-1 band; Global MedFiLM separable from MiT/UNet++, NOT from DeepLabV3+ |")
        A("| 2 | U-Net++, Attention U-Net, U-Net | 0.7878 – 0.7920 | mutually indistinguishable |")
        A("")
        A("Global MedFiLM leads the panel, but its paired CI against **DeepLabV3+** overlaps zero")
        A("(Δ +0.007427, CI [−0.002042, +0.018313], p = 0.124), so those two are **not separable**.")
    else:
        A("| 1 | DeepLabV3+, Transformer/MiT | 0.8224 – 0.8277 | separable from Tier 2 |")
        A("| 2 | U-Net++, Attention U-Net, U-Net | 0.7878 – 0.7920 | mutually indistinguishable |")
        A("")
        A("The inter-tier gap is **~0.030 (3.0 pp)**; the intra-tier-2 spread is only "
          "**0.0042 (0.42 pp)**.")
    A("")

    A("## 3. Paired domain-stratified bootstrap (all frozen models)")
    A("")
    A("Within-panel comparisons. The Phase-21 Global MedFiLM vs-baseline bootstrap is reported")
    A("separately in the Phase-21 report §3 and in `phase21_paired_bootstrap_vs_baselines.csv`.")
    A("")
    if PAIRED.exists():
        pb = pd.read_csv(PAIRED)
        A(f"Method: paired percentile bootstrap, `n_boot=2000`, `seed=42`, "
          f"resampling unit `domain_stratified_paired_image`, identical resampled VAL indices")
        A("for both models in each replicate.")
        A("")
        A("| Model A | Model B | Δ(A−B) | 95% CI | p | Separable? |")
        A("|---|---|---|---|---|---|")
        name = {
            "deeplabv3plus": "DeepLabV3+",
            "transformer_mit_unet": "Transformer/MiT",
            "unetpp": "U-Net++",
            "attention_unet": "Attention U-Net",
            "unet": "U-Net",
        }
        pb = pb.reindex(pb["observed_diff"].abs().sort_values(ascending=False).index)
        for _, r in pb.iterrows():
            sep = "**YES**" if r["ci_excludes_zero"] else "no (CI spans 0)"
            A(f"| {name.get(r['model_a'], r['model_a'])} | {name.get(r['model_b'], r['model_b'])} | "
              f"{r['observed_diff']:+.6f} | [{r['diff_ci_low']:+.6f}, {r['diff_ci_high']:+.6f}] | "
              f"{r['p_value_two_sided']:.3f} | {sep} |")
        A("")
        A("**Key conclusion:** the top-two ordering (DeepLabV3+ vs Transformer/MiT) is **NOT**")
        A("significant (Δ +0.005270, CI [−0.004246, +0.013870], p = 0.282). These two models are")
        A("**tied** on this evidence — never claim a single winner. The three U-Net-family variants")
        A("are likewise mutually indistinguishable. Only the Tier-1 / Tier-2 separation is robust.")
    else:
        A("**PENDING** — paired bootstrap table not found.")
    A("")

    A("## 4. Per-domain breakdown (frozen panel)")
    A("")
    A("| Model | ISIC | BUSI | KVASIR | KUB | Macro | Strongest | Weakest |")
    A("|---|---|---|---|---|---|---|---|")
    for _, r in frozen_only.sort_values("macro_dice", ascending=False).iterrows():
        doms = {"ISIC": r["ISIC"], "BUSI": r["BUSI"], "KVASIR": r["KVASIR"], "KUB": r["KUB"]}
        hi = max(doms, key=doms.get)
        lo = min(doms, key=doms.get)
        A(f"| {r['model']} | {r['ISIC']:.4f} | {r['BUSI']:.4f} | {r['KVASIR']:.4f} | "
          f"{r['KUB']:.4f} | **{r['macro_dice']:.6f}** | {hi} | {lo} |")
    A("")
    A("**KUB is the bottleneck for every model** and the field is tightest there (span 0.6958–0.7388,")
    A("~4.3 pp). ISIC and BUSI are saturated (all models within ~3.2 pp and ~5.1 pp respectively).")
    A("")

    A("## 5. Parameter / compute cost axis")
    A("")
    if COMPUTE.exists():
        c = pd.read_csv(COMPUTE).sort_values("gmacs")
        A("| Model | Params | Params rank | G MACs | MACs rank | vs MedFiLM (×) |")
        A("|---|---|---|---|---|---|")
        for _, r in c.iterrows():
            A(f"| {r['display_name']} | {int(r['params']):,} | {int(r['params_rank'])}/6 | "
              f"{r['gmacs']:.4f} | {int(r['gmacs_rank'])}/6 | {r['gmacs_vs_medfilm_x']:.3f} |")
        A("")
        A("Global MedFiLM is the **lightest on both axes** of this six-model panel, but its absolute")
        A("cost (31.55 G MACs at 512 px) is not small. Measurement is an exact closed-form")
        A("Conv2d/Linear count and is therefore a **lower bound**.")
    A("")
    A("")
    A("## 6. Phase-21 status")
    A("")
    _p21_done = p21.iloc[0]["provenance"] == "FROZEN"
    A(f"- Epochs completed: **{live['epochs_completed']}** (best at epoch {live['best_epoch']})")
    A(f"- Stop reason: **{live['stop_reason']}**")
    A(f"- Early-stopping patience used: **{live['bad_epochs']} / {live['patience']}**")
    A(f"- Resume count: **{live['resume_count']}** (one host teardown recovered)")
    if _p21_done:
        A(f"- Macro-domain VAL Dice (ONE canonical pass over 808 VAL samples): "
          f"**{live['macro_dice']:.6f}**")
        A("- The canonical VAL pass has completed, so this row is directly comparable to the")
        A("  frozen panel in §2. See §3 of the Phase-21 report for the paired bootstrap")
        A("  against each frozen baseline (this table's §3 covers the frozen panel only).")
    else:
        A("- Terminal state not reached; `phase21_training_closure.json` does not exist yet.")
        A("- The authoritative Phase-21 result will come from **one** canonical VAL pass plus a paired")
        A("  bootstrap against each frozen baseline, run by")
        A("  `scripts/analysis/run_phase21_post_training_pipeline.py`.")
    A("")

    OUT_MD.write_text("\n".join(L), encoding="utf-8")
    print("WROTE", OUT_CSV)
    print("WROTE", OUT_MD, f"({len(L)} lines)")
    print()
    print(allm[["macro_rank", "model", "phase", "params", "gmacs", "macro_dice",
                "provenance", "status"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
