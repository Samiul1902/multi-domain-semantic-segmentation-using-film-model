import pathlib

# ---------------- QA doc ----------------
q = pathlib.Path(r"D:\Softfors\jup\full_doc_report\FINAL_NOTEBOOK_QA.md")
s = q.read_text(encoding="utf-8")

old = """| Field | Previous | Corrected | Basis |
|---|---|---|---|
| ReMedFiLM FULL VAL808 macro Dice (seed 42) | `0.837862` | **`0.837290`** | Phase 27 delta `+0.0022101`; Phase 29 continuity `0.8372891053`; independent re-scoring of the saved masks (agreement `1.8×10⁻⁷`) |

`0.837862` appears in no frozen artifact. The net gain over the backbone is
**+0.221 pp**, not +0.278 pp. The old accuracy–compute figure omitted ReMedFiLM
entirely; `EFF01_accuracy_vs_compute.png` now plots it as its own marked point at
32.44 expected conditional GMACs.

Second, smaller discrepancy recorded: `phase29_val808_seedwise_metrics.json`
gives seed-42 `0.8373512` (n_accepted = 268) while the continuity artifact gives
`0.8372891` (n_accepted = 266). The continuity value is canonical and is the one
reproduced by re-scoring."""

new = """Four corrections are registered in `SCIENTIFIC_CORRECTIONS.json`. Three of them
are present in the current **V7** report, which therefore **must not be
republished unchanged**.

| ID | Field | V7 / prior value | Corrected | Basis |
|---|---|---|---|---|
| CORR-01 | ReMedFiLM FULL VAL808 macro Dice (seed 42) | `83.79%` (`0.837862`) | **`83.729%`** (`0.837290`) | Phase 27 Δ `+0.0022101`; Phase 29 continuity `0.8372891053`; independent re-scoring (agreement `1.8×10⁻⁷`) |
| CORR-02 | Net gain over backbone | `+0.28 pp` | **`+0.2210 pp`** | recomputed from CORR-01 |
| CORR-03 | ReMedFiLM analytical compute | `34.72 GMACs` | **`32.4379 GMACs`** (expected conditional) | `c2_barr_aggregate.json` |
| CORR-04 | Seed-42 Dice, second safety variant | `0.8373512` (n_accepted 268) | `0.8372891` (n_accepted 266, canonical) | Phase 27 + Phase 29 continuity |

**CORR-03 matters most for the efficiency claim.** `34.72` is the always-refine
cost. The deployed system routes only 24.3 % of cases, so its expected cost is
`31.5517 + 0.2431 × 3.646 = 32.4379` GMACs. Quoting 34.72 overstates the proposed
system's compute by 7.0 % and understates its efficiency advantage.

The old accuracy–compute figure omitted ReMedFiLM entirely;
`figures/efficiency/EFF01_accuracy_vs_compute.png` now plots it as its own marked
star at 32.44 expected conditional GMACs.

**No new DOCX/PDF was generated.** Rebuilding the report is a separate authorised
task; republishing with the stale charts is prohibited, and the older report
files are preserved untouched."""

assert old in s
s = s.replace(old, new)
q.write_text(s, encoding="utf-8")

# ---------------- index ----------------
i = pathlib.Path(r"D:\Softfors\jup\full_doc_report\ReMedFiLM_Research_Notebook_Index.md")
t = i.read_text(encoding="utf-8")

old2 = """1. **ReMedFiLM FULL VAL808 macro Dice.** An earlier consolidation CSV carried
   `0.837862`. Re-scoring the saved Phase 27 masks gives `0.837290`, matching the
   frozen Phase 27 delta (`+0.0022101`) and the Phase 29 continuity record
   (`0.8372891053`). `0.837862` appears in no frozen artifact. Corrected value is
   used; the net gain is **+0.221 pp**, not +0.278 pp.
2. **Two seed-42 safety variants.** `phase29_val808_seedwise_metrics.json`
   reports `0.8373512` (n_accepted = 268); the continuity artifact reports
   `0.8372891` (n_accepted = 266). The continuity value is canonical and is the
   one reproduced by re-scoring.
3. **KUB unit of analysis.** 2,258 KUB manifest rows are 873 full-field images
   plus 1,385 ROI instance patches — not 2,258 independent images.
4. **14 runs without a recorded selection epoch** are KUB ROI-localiser
   diagnostics and fixed-epoch component refits. They are marked
   `NOT_RECORDED` / `NOT_APPLICABLE`, never imputed."""

new2 = """Full register: `SCIENTIFIC_CORRECTIONS.json` (4 entries).

1. **CORR-01 — ReMedFiLM FULL VAL808 macro Dice.** V7 reports `83.79%`
   (`0.837862`). Re-scoring the saved Phase 27 masks gives `0.837290`, matching
   the frozen Phase 27 delta (`+0.0022101`) and the Phase 29 continuity record
   (`0.8372891053`). `0.837862` appears in no frozen artifact.
2. **CORR-02 — net gain.** `+0.28 pp` becomes **`+0.2210 pp`**.
3. **CORR-03 — analytical compute.** V7 quotes `34.72 GMACs`, the always-refine
   cost. The deployed system routes 24.3 % of cases, so its expected conditional
   cost is **`32.4379 GMACs`**. The 34.72 figure overstates compute by 7.0 %.
4. **CORR-04 — two seed-42 safety variants.** `phase29_val808_seedwise_metrics.json`
   gives `0.8373512` (n_accepted 268); the continuity artifact gives `0.8372891`
   (n_accepted 266), which is canonical and reproduced by re-scoring.
5. **KUB unit of analysis.** 2,258 KUB manifest rows are 873 full-field images
   plus 1,385 ROI instance patches — not 2,258 independent images.
6. **14 runs without a recorded selection epoch** are KUB ROI-localiser
   diagnostics and fixed-epoch component refits. Marked `NOT_RECORDED` /
   `NOT_APPLICABLE`, never imputed.

**V7 must not be republished unchanged.** Its DOCX/PDF are preserved as-is; the
corrected values live in the tables and figures listed above."""

assert old2 in t
t = t.replace(old2, new2)
i.write_text(t, encoding="utf-8")
print("PATCHED both documents")
