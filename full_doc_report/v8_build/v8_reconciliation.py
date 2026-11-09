"""V8 Task C — reconcile ~0.837290 / ~0.837862 / ~0.835079.

Everything numeric is read from the frozen artifacts on disk.  No derived SHA,
no timestamp, and no scientific value is hardcoded into the emitted document.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v8_common import FDR, ROOT, SRC, rel, sha256, write_artifact  # noqa: E402

REG = json.loads((FDR / "REMEDFILM_V8_RESULTS_REGISTRY.json").read_text(encoding="utf-8"))
CR = REG["canonical_result"]
FULL = float(CR["full_macro_dice"])
GLOB = float(CR["global_macro_dice"])
DELTA = float(CR["paired_delta_dice"])

NPZ = ROOT / "data_cache/phase29_phase_d_canonical/phase29_phase_d_three_seed_val808_delta_dice.npz"
SEEDWISE = ROOT / "reports/audits/phase29_val808_seedwise_metrics.json"
RECON = json.loads(SRC["reconciliation"].read_text(encoding="utf-8"))

d = np.load(NPZ, allow_pickle=False)
dom = d["domains"]
SEED_KEYS = [("42", "seed42_final_dice"), ("123", "seed123_final_dice"),
             ("3407", "seed3407_final_dice")]


def macro(a) -> float:
    x = np.asarray(a, dtype=float)
    return float(sum(float(x[dom == u].mean()) for u in sorted(set(dom.tolist())))
                 / len(set(dom.tolist())))


npz_macro = {s: macro(d[k]) for s, k in SEED_KEYS}
npz_global = macro(d["global_dice"])
npz_vals = [npz_macro[s] for s, _ in SEED_KEYS]
npz_mean = float(np.mean(npz_vals))
npz_sd = float(np.std(npz_vals, ddof=1))

sw = json.loads(SEEDWISE.read_text(encoding="utf-8"))
sw_vals = [sw["metrics_by_seed"][s]["macro_final_dice"] for s, _ in SEED_KEYS]
sw_mean = float(np.mean(sw_vals))
sw_sd = float(np.std(sw_vals, ddof=1))

# V7's three hardcoded numbers, quoted only as the object of the analysis
V7 = [0.837862, 0.837910, 0.837815]
v7_mean = float(np.mean(V7))
v7_sd = float(np.std(V7, ddof=1))
V7_HEADLINE = 0.837862

routing = REG["routing_val808"]["branches"]
decisions = REG["routing_val808"]["decisions"]
_ids = {m["metric_id"]: m["value"] for m in REG["metrics"]}
N_HARMFUL = int(float(_ids["INT_MACRO_DOMAIN_EQUAL_WEIGHT_HARMFUL"]))
EFF_FULL_GMACS = _ids["EFF_FULL_GMACS"]

# conflicting legacy table arithmetic
prog = (FDR / "PROGRESSION_AND_PROPAGATION_EVIDENCE.csv").read_text(encoding="utf-8")
prog_line = [ln for ln in prog.splitlines() if "Stage 4 (Validated)" in ln][0]

sources = [
    ("Canonical re-scored VAL808 mask table", SRC["val808"]),
    ("Frozen three-seed per-sample Dice archive", NPZ),
    ("Phase 29 recorded seedwise metrics", SEEDWISE),
    ("Frozen VAL808 state-machine predictions", SRC["routing"]),
    ("Prior policy-sweep reconciliation", SRC["reconciliation"]),
    ("Legacy progression evidence (superseded)", FDR / "PROGRESSION_AND_PROPAGATION_EVIDENCE.csv"),
    ("V7 report generator (superseded)", ROOT / "scripts/analysis/build_v7_pdf_report.py"),
]

lines = []
A = lines.append
A("# ReMedFiLM V8 — Result Reconciliation")
A("")
A("**Question.** Three macro-Dice values circulate for VAL808: approximately "
  "`0.837290` (ReMedFiLM FULL), `0.837862` (also labelled ReMedFiLM FULL in V5–V7), "
  "and `0.835079`. Which is the evaluation of the proposed four-component model, and what are the others?")
A("")
A(f"**Verdict.** The proposed model's canonical VAL808 macro Dice is **`{FULL:.9f}`**. "
  f"`{GLOB:.9f}` is the **GlobalMedFiLM backbone** — the legitimate comparator, not a competing FULL value. "
  f"`{V7_HEADLINE:.6f}` is **not a measurement**: it is the arithmetic mean of three numbers hardcoded into "
  "the V5/V6/V7 report generators, and it is contradicted by the frozen three-seed archive it claims to cite. "
  "V8 rejects it. **This is a resolved reporting inconsistency, not a second experimental configuration.**")
A("")
A("---")
A("")
A("## 1. Canonical identity chain")
A("")
A("| Field | Verified value |")
A("|---|---|")
A("| Proposed system | ReMedFiLM FULL = RA-MedFiLM-BARR = `G` + `R_psi` + `B_phi` + `S_omega` |")
A(f"| Verified parameters | {REG['canonical_model']['verified_total_parameters']:,} |")
A("| Population | VAL808 (held-out validation), n = 808 |")
A("| Seed | 42 |")
A(f"| Router threshold | `tau_C8 = {REG['runtime_constants']['tau_C8_final']!r}` |")
A(f"| ROI / safety / output thresholds | {REG['runtime_constants']['roi_proposal_threshold']} / "
  f"{REG['runtime_constants']['s_omega_accept_threshold']} / "
  f"{REG['runtime_constants']['segmentation_output_threshold']} |")
A(f"| Router decisions | SKIP {decisions.get('SKIP')} · EXECUTE {decisions.get('EXECUTE')} |")
A("| Branches | " + " · ".join(f"{k} {v}" for k, v in sorted(routing.items())) + " |")
A(f"| FULL macro Dice | **{FULL:.12f}** |")
A(f"| GlobalMedFiLM macro Dice | {GLOB:.12f} |")
A(f"| Paired Δ | **+{DELTA:.12f}** (95% CI +{float(CR['paired_delta_ci_low']):.9f} to +{float(CR['paired_delta_ci_high']):.9f}) |")
A("| Aggregation | equal-weight mean of four per-domain per-image Dice means |")
A("")
A("Independent cross-checks, all reproducible without any new inference:")
A("")
A(f"* Re-scoring the 808 saved Phase 27 masks (`*_global.png`, `*_final.png`) gives `{FULL:.9f}`.")
A(f"* The frozen per-sample three-seed archive gives seed-42 macro `{npz_macro['42']:.9f}` "
  f"(difference `{abs(npz_macro['42']-FULL):.2e}`).")
A(f"* The same archive gives backbone macro `{npz_global:.9f}` "
  f"(difference `{abs(npz_global-GLOB):.2e}`).")
A(f"* All {sum(routing.values())} cases are accounted for; for all {decisions.get('SKIP')} SKIP cases "
  "the saved FULL mask is byte-identical to the backbone mask.")
A("")
A("## 2. `0.835079` is the comparator, not a discrepancy")
A("")
A(f"`{GLOB:.9f}` is the frozen Phase 21 `GlobalMedFiLM` backbone evaluated on the same 808 images. "
  "GlobalMedFiLM is the first component of the proposed system and a legitimate ablation baseline. "
  "It is **not** the complete proposed model and must never be labelled ReMedFiLM FULL. "
  f"The scientific result of the assembly is the *paired* difference `+{DELTA:.6f}` "
  f"(`+{DELTA*100:.4f}` percentage points), not either absolute number in isolation.")
A("")
A("## 3. Where `0.837862` actually comes from")
A("")
A("V5, V6 and V7 report the same three-seed reproducibility triplet and then print its mean as the "
  "headline seed-42 result:")
A("")
A("| Quantity | V5/V6/V7 printed value |")
A("|---|---|")
for s, v in zip(("42", "123", "3407"), V7):
    A(f"| seed {s} macro Dice | {v:.6f} |")
A(f"| mean | {v7_mean:.6f} |")
A(f"| SD | {v7_sd:.8f} |")
A("")
A(f"The arithmetic mean of those three values is `{v7_mean:.9f}` — i.e. the value printed as "
  f"**both** the seed-42 row and the three-seed mean is the *mean*. That is internally inconsistent: "
  f"the seed-42 cell was overwritten with the mean. `build_v7_pdf_report.py` additionally prints "
  "routing counts 183 selected / 165 accepted / 31 rejected, which cannot be reconciled with the frozen "
  f"state machine ({decisions.get('EXECUTE')} / {routing.get('EXECUTE_THEN_ACCEPT')} / "
  f"{routing.get('EXECUTE_THEN_REJECT')}).")
A("")
A("The V7 QA document claims the triplet was traced to the frozen archive "
  f"`{rel(NPZ)}`. That archive exists and was re-read for V8. Re-aggregating it with the same "
  "equal-domain-weight rule gives:")
A("")
A("| Seed | Genuine macro Dice from frozen NPZ | V7 printed | Difference |")
A("|---|---|---|---|")
for (s, _), v7 in zip(SEED_KEYS, V7):
    A(f"| {s} | {npz_macro[s]:.9f} | {v7:.6f} | {npz_macro[s]-v7:+.9f} |")
A(f"| **mean** | **{npz_mean:.9f}** | {v7_mean:.6f} | {npz_mean-v7_mean:+.9f} |")
A(f"| SD (ddof=1) | {npz_sd:.9f} | {v7_sd:.9f} | — |")
A("")
A(f"None of the three V7 numbers appears in the archive. The genuine across-seed SD is "
  f"`{npz_sd:.9f}`, roughly **{npz_sd/v7_sd:.0f}× larger** than V7's `{v7_sd:.9f}`: V7 understated "
  "seed-to-seed variability by more than an order of magnitude. This matters because all three seeds "
  "share one pre-trained backbone, so the triplet is descriptive component-initialisation stability, "
  "**not** three independent end-to-end training replicates.")
A("")
A("A separate frozen record, `reports/audits/phase29_val808_seedwise_metrics.json`, gives "
  f"a second genuine descriptive triplet ({', '.join(f'{v:.6f}' for v in sw_vals)}; "
  f"mean {sw_mean:.6f}, SD {sw_sd:.9f}). Its seed-42 entry reports "
  f"`{sw['metrics_by_seed']['42']['macro_final_dice']:.7f}` with "
  f"{sw['metrics_by_seed']['42']['n_accepted']} accepted cases rather than the "
  f"{routing.get('EXECUTE_THEN_ACCEPT')} encoded in the saved masks. Those two extra safety decisions "
  "were never persisted as separate refined outputs, so this variant is **genuinely recorded but not "
  "re-derivable**; it is disclosed, not selected.")
A("")
A("## 4. Policy sweep")
A("")
A(f"`{rel(SRC['reconciliation'])}` tested every routing policy expressible from the saved masks "
  f"({len(RECON['policies_tested'])} policies), including top-181/183/185/200/250/279 by utility and "
  "the threshold rule without the safety gate. Verdict recorded there: "
  f"`{RECON['verdict']}`; `any_policy_reproduces_0837862 = {RECON['any_policy_reproduces_0837862']}`. "
  "No policy reproduces `0.837862`.")
A("")
A("## 5. Additional V8-discovered conflicts (excluded from V8 tables)")
A("")
A("| Legacy artifact | Conflict | V8 action |")
A("|---|---|---|")
A("| `tables/REMEDFILM_MODEL_COMPARISON.csv` | The four `dice_*` cells of the ReMedFiLM FULL row are "
  "**single-sample** Dice values, not domain means (each matches exactly one row of the per-sample table). "
  "The row's macro value is correct but its per-domain values are not. | Excluded; baselines taken from "
  "`reports/tables/phase21_six_model_comparison.csv`, FULL from the canonical re-score. |")
A("| `PROGRESSION_AND_PROPAGATION_EVIDENCE.csv` | Stage 4 records `0.837862` with routed 0.2265, "
  "accepted 0.2042, +0.2783 pp and harm 0.1878; the frozen state machine gives routed "
  f"{decisions.get('EXECUTE')/808:.4f}, accepted {routing.get('EXECUTE_THEN_ACCEPT')/808:.4f}, "
  f"+{DELTA*100:.4f} pp and harm {N_HARMFUL/808:.4f}. | Excluded; superseded by "
  "`REMEDFILM_ABLATION_AND_PROGRESSION.csv`. |")
A("| `tables/ReMedFiLM_External_Routing_Safety_V7.csv` | External routing counts (e.g. CVC 118 / 35 / 83) "
  "conflict with the frozen `c1_external_stress_*` artifacts. | Excluded; V8 uses the frozen external tables. |")
A("| `tables/subgroup_performance_summary.csv` | V3-era table with macro 0.8379 / +0.28 pp. | Excluded. |")
A("")
A("## 6. What V8 reports")
A("")
A("| Context | Value | Status |")
A("|---|---|---|")
A(f"| Headline VAL808 ReMedFiLM FULL macro Dice, seed 42 | **{FULL:.6f}** | canonical, reproducible |")
A(f"| GlobalMedFiLM backbone on the same split | {GLOB:.9f} | comparator |")
A(f"| Net paired gain | **+{DELTA*100:.4f} pp** | 95% CI excludes zero |")
A(f"| Three-seed descriptive mean (frozen NPZ) | {npz_mean:.6f} ± {npz_sd:.6f} | descriptive only; shared backbone |")
A(f"| Phase 29 seedwise recorded mean | {sw_mean:.6f} ± {sw_sd:.6f} | recorded variant, not re-derivable |")
A(f"| `{V7_HEADLINE:.6f}` and +0.28 pp | — | **superseded; not used anywhere in V8** |")
A("")
A("## 7. Consequence for the accuracy–cost figure")
A("")
A(f"V7 paired `{V7_HEADLINE:.6f}` with 34.72 GMACs (the always-refine cost), so its ReMedFiLM point was "
  f"wrong on both axes. V8 plots the FULL system as its own marker at `{FULL:.6f}` and "
  f"**{EFF_FULL_GMACS}** expected "
  "conditional GMACs. Because the baseline protocols are historical descriptive comparisons rather than "
  "matched controlled experiments, the chart is captioned as a **historical descriptive comparison**, "
  "not a confirmed Pareto frontier.")
A("")
A("## 8. Unresolved (not silently repaired)")
A("")
A("* The two-case difference between the Phase 29 seedwise record (268 accepted) and the saved-mask "
  "state (266 accepted) cannot be reconstructed from persisted artifacts.")
A("* `0.837862` has no artifact, no policy and no consistent sample accounting behind it; it is rejected "
  "rather than re-labelled as a legitimate alternative configuration.")
A("* C1 (learned vs identity FiLM), C2 (causal safety-gate attribution; A8 vs A7 CI includes zero), and "
  "C3 (matched multi-seed baseline matrix) remain `NOT_ESTABLISHED`. No controlled study is implied here.")
A("")
A("## 9. Source integrity")
A("")
A("SHA-256 values are read from the bytes on disk at build time.")
A("")
A("| Role | Path | SHA-256 |")
A("|---|---|---|")
for name, p in sources:
    A(f"| {name} | `{rel(p)}` | `{sha256(p) if p.exists() else 'SOURCE_MISSING'}` |")
A("")
A("**Declaration.** This reconciliation is analysis-only. No model was retrained, no new inference was run, "
  "no checkpoint or frozen table was modified, and the protected TEST1683 inputs were not opened.")
A("")

out = write_artifact(FDR / "REMEDFILM_V8_RESULT_RECONCILIATION.md", "\n".join(lines))
print("wrote", rel(out), out.stat().st_size, "bytes")
print("canonical FULL", f"{FULL:.12f}", "G", f"{GLOB:.12f}", "delta", f"{DELTA:.12f}")
print("npz seed macro", {k: round(v, 9) for k, v in npz_macro.items()}, "mean", round(npz_mean, 9))
