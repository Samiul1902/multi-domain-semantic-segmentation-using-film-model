import json
from pathlib import Path

OUT = Path(r"D:\Softfors\jup\full_doc_report")
p = OUT / "SCIENTIFIC_CORRECTIONS.json"
d = json.loads(p.read_text(encoding="utf-8"))

d["corrections"] = [
    {
        "id": "CORR-01",
        "field": "ReMedFiLM FULL VAL808 macro Dice (seed 42)",
        "previously_published": 0.837862,
        "corrected_value": 0.837290,
        "reported_as_percent_in_V7": "83.79%",
        "authoritative_sources": [
            "reports/audits/phase27_preservation_result.json (macro_point delta +0.0022101453)",
            "reports/audits/phase29_phase_d_val808_per_seed_continuity.json "
            "(macro_final_dice 0.8372891053775793)",
            "independent re-scoring of reports/figures/phase27_preservation/masks/*_final.png",
        ],
        "verification": "Re-scoring reproduces the frozen Phase 27 delta to 1.8e-07.",
        "resolution": ("0.837862 / 83.79% appears in no frozen artifact. It was carried "
                       "forward by an earlier consolidation CSV and by the V7 report."),
        "impact": "Net gain over the backbone is +0.221 pp, not +0.28 pp.",
    },
    {
        "id": "CORR-02",
        "field": "ReMedFiLM FULL net gain over backbone (VAL808)",
        "previously_published": "+0.28 pp",
        "corrected_value": "+0.2210 pp",
        "authoritative_sources": [
            "full_doc_report/tables/REMEDFILM_INTERNAL_METRICS.csv",
            "reports/audits/phase27_preservation_result.json",
        ],
        "resolution": "Direct consequence of CORR-01; the delta is recomputed, not re-quoted.",
        "impact": "The improvement is smaller than reported but remains positive and its 95% CI excludes zero.",
    },
    {
        "id": "CORR-03",
        "field": "ReMedFiLM FULL analytical compute",
        "previously_published": "34.72 GMACs",
        "corrected_value": "32.4379 GMACs (expected conditional)",
        "authoritative_sources": [
            "reports/tables/c2_barr/c2_barr_aggregate.json -> "
            "compute.analytical_gmacs_lower_bound.FINAL_A8_C9_EXPECTED_CONDITIONAL",
        ],
        "resolution": ("34.72 is the always-refine (gated execute-all) cost. The deployable "
                       "system routes only 24.3% of cases, so its expected conditional cost "
                       "is 31.5517 + 0.2431 x 3.646 = 32.4379 GMACs."),
        "impact": ("Reporting 34.72 overstates the compute of the proposed system by 7.0% "
                   "and understates its efficiency advantage."),
    },
    {
        "id": "CORR-04",
        "field": "Seed-42 VAL808 macro Dice, two safety variants",
        "previously_published": "0.8373512 (phase29_val808_seedwise_metrics.json)",
        "corrected_value": 0.8372891,
        "authoritative_sources": [
            "reports/audits/phase29_phase_d_val808_per_seed_continuity.json",
            "reports/audits/phase27_preservation_result.json",
        ],
        "resolution": ("Two safety-acceptance states exist (n_accepted 268 vs 266). The "
                       "continuity artifact and Phase 27 agree on 266 and are canonical; "
                       "re-scoring the saved masks reproduces that state."),
        "impact": "Descriptive only; does not change any conclusion.",
    },
]

d["report_status"] = {
    "V7_docx_pdf": "CONTAINS CORR-01..CORR-03 — must not be republished unchanged",
    "V4_V5_V6": "superseded, retained for provenance only",
    "corrected_figures": "full_doc_report/figures/efficiency/EFF01_accuracy_vs_compute.png",
    "corrected_tables": [
        "full_doc_report/tables/REMEDFILM_INTERNAL_METRICS.csv",
        "full_doc_report/tables/REMEDFILM_EFFICIENCY.csv",
        "full_doc_report/tables/REMEDFILM_PROGRESSION_RESULTS.csv",
    ],
    "action_taken": ("Older report files are preserved untouched. No new DOCX/PDF was "
                     "generated, because rebuilding the report is a separate authorised "
                     "task and republishing with stale charts is prohibited."),
}

p.write_text(json.dumps(d, indent=2), encoding="utf-8")
print("corrections:", len(d["corrections"]))
for c in d["corrections"]:
    print(f"  {c['id']}: {c['field'][:52]:54s} {c['previously_published']} -> {c['corrected_value']}")
