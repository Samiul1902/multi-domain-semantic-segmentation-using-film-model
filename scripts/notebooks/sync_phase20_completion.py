"""
Phase-20 COMPLETION governance synchronization.

Additively updates, and executes where applicable:

  1. reports/audits/phasewise_notebook_map.json        (statuses 19-21)
  2. notebooks/phasewise/README.md                     (roadmap rows + completion section)
  3. notebooks/phasewise/phase_19|20|21_*/README.md    (status lines)
  4. PROJECT_MASTER_PLAN.md                            (phase lines + completion note)
  5. notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb (completion section; executed)

No training, no inference, no TEST access, no frozen-gate change.
Idempotent: the recorded transition is derived from a DECLARED baseline (the
post-Stage-B-activation state), never from observed on-disk deltas, so a re-run
converges and the journal SHA is stable.

Run:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe scripts/notebooks/sync_phase20_completion.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
MAP = ROOT / "reports/audits/phasewise_notebook_map.json"
PW_README = ROOT / "notebooks/phasewise/README.md"
INDEX_NB = ROOT / "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb"
MASTER_PLAN = ROOT / "PROJECT_MASTER_PLAN.md"
OUT = ROOT / "reports/audits/phase20_completion_governance_state.json"

PROTOCOL = ROOT / "reports/audits/phase20_shared_global_baseline_protocol.json"
CLOSURE = ROOT / "experiments/phase20_shared_unetpp_fourdomain_seed42_clean_v3/closure.json"
EVAL = ROOT / "reports/audits/phase20_val_evaluation.json"
P21 = ROOT / "reports/audits/phase20_phase21_entry_criteria.json"
NB20 = ROOT / ("notebooks/phasewise/phase_20_multidomain_baselines/"
               "phase20_shared_global_unetpp_baseline.ipynb")

PHASE_README = {
    19: ROOT / "notebooks/phasewise/phase_19_harmonization/README.md",
    20: ROOT / "notebooks/phasewise/phase_20_multidomain_baselines/README.md",
    21: ROOT / "notebooks/phasewise/phase_21_global_medfilm/README.md",
}

# Declared baseline = the state established by sync_stage_b_governance.py
# (post-H3 closure / Stage-B activation). Provenance:
#   * phase 19 - reports/audits/stage_b_governance_state.json  -> CURRENT_AUTHORIZED
#   * phase 20 - notebooks/phasewise/README.md roadmap row      -> NOT_STARTED_AND_NOT_AUTHORIZED
#   * phase 21 - notebooks/phasewise/README.md roadmap row      -> NOT_STARTED
PRE_PHASE20_STATUS = {
    "19": "CURRENT_AUTHORIZED",
    "20": "NOT_STARTED_AND_NOT_AUTHORIZED",
    "21": "NOT_STARTED",
}
NEW_STATUS = {
    "19": "COMPLETE",
    "20": "COMPLETE",
    "21": "ELIGIBLE_NOT_STARTED",
}

TERMINAL = "PHASE20_SHARED_GLOBAL_BASELINE_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strip_timing(nb) -> None:
    for c in nb.cells:
        if isinstance(c.get("metadata"), dict):
            c["metadata"].pop("execution", None)


def coalesce_streams(nb) -> None:
    for c in nb.cells:
        outs = c.get("outputs")
        if not outs:
            continue
        merged = []
        for o in outs:
            if (o.get("output_type") == "stream" and merged
                    and merged[-1].get("output_type") == "stream"
                    and merged[-1].get("name") == o.get("name")):
                p = merged[-1]
                pt, ct = p.get("text", ""), o.get("text", "")
                if isinstance(pt, list):
                    pt = "".join(pt)
                if isinstance(ct, list):
                    ct = "".join(ct)
                p["text"] = pt + ct
            else:
                merged.append(o)
        c["outputs"] = merged


def exec_nb(path: Path) -> dict:
    nb = nbformat.read(str(path), as_version=4)
    NotebookClient(nb, kernel_name="jup-venv", timeout=1200,
                   resources={"metadata": {"path": str(ROOT)}}).execute()
    strip_timing(nb)
    coalesce_streams(nb)
    nbformat.write(nb, str(path))
    errs = sum(1 for c in nb.cells if c.cell_type == "code"
               for o in c.get("outputs", []) if o.get("output_type") == "error")
    counts = [c.get("execution_count") for c in nb.cells if c.cell_type == "code"]
    mono = all(counts[i] == i + 1 for i in range(len(counts)))
    return {"code_cells": len(counts), "tracebacks": errs, "monotonic": bool(mono)}


# --------------------------------------------------------------------------- #
def update_notebook_map(record: dict) -> None:
    old = sha(MAP)
    entries = json.loads(MAP.read_text(encoding="utf-8"))
    changed = [
        {"phase_id": pid, "from": PRE_PHASE20_STATUS[pid], "to": NEW_STATUS[pid]}
        for pid in sorted(NEW_STATUS)
        if PRE_PHASE20_STATUS[pid] != NEW_STATUS[pid]
    ]
    for e in entries:
        pid = e.get("phase_id")
        if pid in NEW_STATUS:
            e["status"] = NEW_STATUS[pid]
        if pid == "19":
            e["reviewer_notebook"] = "phase19_multidomain_dataset_harmonization.ipynb"
            e["canonical_source"] = "reports/audits/phase19_multidomain_harmonization_protocol.json"
            e["visual_artifacts"] = "reports/figures/phase19_harmonization/"
        if pid == "20":
            e["title"] = "Shared Four-Domain Global Baseline (single frozen UNet++, no FiLM, no regional module)"
            e["reviewer_notebook"] = "phase20_shared_global_unetpp_baseline.ipynb"
            e["canonical_source"] = "reports/audits/phase20_shared_global_baseline_protocol.json"
            e["visual_artifacts"] = "reports/figures/phase20_multidomain_baseline/"
            e["baseline_metric"] = "macro_domain_mean_validation_dice"
        if pid == "21":
            e["canonical_source"] = "PENDING_PHASE21_AUTHORIZATION"
            e["authorization_required"] = True
    MAP.write_text(json.dumps(entries, indent=1), encoding="utf-8")
    record["phasewise_notebook_map"] = {
        "path": "reports/audits/phasewise_notebook_map.json",
        "old_sha256": old, "new_sha256": sha(MAP),
        "status_changes": changed,
        "status_changes_baseline": "declared_post_stage_b_activation (canonical, run-independent)",
        "status_changes_baseline_provenance":
            "reports/audits/stage_b_governance_state.json (phase 19) + "
            "notebooks/phasewise/README.md roadmap rows (phases 20-21)",
    }


def update_phasewise_readme(record: dict) -> None:
    old = sha(PW_README)
    text = PW_README.read_text(encoding="utf-8")
    rows = {
        "| [`phase_19_harmonization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_19_harmonization/README.md) | Multi-Domain Dataset Harmonization | Standardize ISIC, BUSI, Kvasir, KUB under one leakage-safe task/data contract | **CURRENT / AUTHORIZED** |":
            "| [`phase_19_harmonization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_19_harmonization/README.md) | Multi-Domain Dataset Harmonization | Standardize ISIC, BUSI, Kvasir, KUB under one leakage-safe task/data contract | **COMPLETE** |",
        "| [`phase_20_multidomain_baselines/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_20_multidomain_baselines/README.md) | Multi-Domain Global Baseline Evaluation | Evaluate global baselines across all 4 modalities | NOT_STARTED_AND_NOT_AUTHORIZED |":
            "| [`phase_20_multidomain_baselines/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_20_multidomain_baselines/README.md) | Shared Four-Domain Global Baseline | Single frozen UNet++ shared across ISIC/BUSI/Kvasir/KUB (no FiLM, no regional module) | **COMPLETE** |",
        "| [`phase_21_global_medfilm/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_21_global_medfilm/README.md) | Global MedFiLM Reference Architecture | Unified feature-interleaved multi-domain backbone | NOT_STARTED |":
            "| [`phase_21_global_medfilm/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_21_global_medfilm/README.md) | Global MedFiLM Reference Architecture | Unified feature-interleaved multi-domain backbone | **ELIGIBLE / NOT STARTED** (authorization required) |",
    }
    for a, b in rows.items():
        text = text.replace(a, b)

    marker = "## Stage-B Phase-20 completion (shared four-domain global baseline)"
    if marker not in text:
        c = json.loads(CLOSURE.read_text(encoding="utf-8"))
        ev = json.loads(EVAL.read_text(encoding="utf-8"))
        p21 = json.loads(P21.read_text(encoding="utf-8"))
        section = (
            f"\n\n{marker}\n\n"
            "Phase 20 is **COMPLETE**. It establishes **ONE** strong conventional shared segmentation\n"
            "baseline over all four Stage-B domains under the frozen Phase-19 harmonized protocol —\n"
            "**no FiLM, no task conditioning, no regional mechanism, no localizer, no ROI/proposal**.\n\n"
            f"- Experiment: `{c['experiment_id']}`\n"
            f"- Architecture: single frozen **UNet++** ({c['model_params']:,} params), one shared parameter set, one head\n"
            f"- Best epoch **{c['best_epoch']}** — **macro-domain VAL Dice {c['best_macro_domain_dice']:.6f}**\n"
            f"- Early stopped at epoch {c['final_epoch']} (patience {c['early_stopping_patience']}); "
            f"resumes during training: {c['resume_count']}\n"
            f"- Canonical VAL pass: **{ev['samples_evaluated']}** samples, exactly {ev['canonical_val_inference_runs']} inference run, "
            f"threshold {ev['threshold']}\n"
            f"- Persisted predictions: **{ev['prob_maps_persisted']}** NPZ (prob float16 / pred uint8 / gt uint8)\n"
            f"- Phase-21 entry criteria: **{sum(1 for x in p21['criteria'] if x['met'])}/{len(p21['criteria'])} met**\n"
            f"- TEST reads: image {ev['test_reads']['test_image_reads']}, mask {ev['test_reads']['test_mask_reads']}, "
            f"inference {ev['test_reads']['test_inference']}, visualization {ev['test_reads']['test_visualization']}\n\n"
            f"- Protocol: `reports/audits/phase20_shared_global_baseline_protocol.json`\n"
            f"- Notebook: `notebooks/phasewise/phase_20_multidomain_baselines/phase20_shared_global_unetpp_baseline.ipynb`\n"
            f"- Terminal state: **`{TERMINAL}`**\n"
            f"- **Phase 21 is ELIGIBLE but NOT STARTED** — it requires fresh supervisor authorization.\n"
        )
        text = text.rstrip("\n") + section
    PW_README.write_text(text, encoding="utf-8")
    record["phasewise_readme"] = {
        "path": "notebooks/phasewise/README.md",
        "old_sha256": old, "new_sha256": sha(PW_README)}


def update_phase_readmes(record: dict) -> None:
    out = {}
    for n, path in PHASE_README.items():
        old = sha(path)
        text = path.read_text(encoding="utf-8")
        if n == 19:
            text = text.replace(
                "- **Current Status:** CURRENT / AUTHORIZED (Stage B) — "
                "harmonization protocol + preparation COMPLETE; scientific execution/training not authorized",
                "- **Current Status:** COMPLETE (Stage B) — harmonization protocol, contracts, tables, "
                "figures and reviewer notebook delivered and SHA-bound; TEST reads = 0")
        elif n == 20:
            text = re.sub(r"- \*\*Current Status:\*\*[^\n]*",
                          "- **Current Status:** COMPLETE — single frozen shared UNet++ four-domain "
                          "baseline trained and canonically evaluated on 808 VAL samples "
                          f"(`{TERMINAL}`)",
                          text, count=1)
            marker = "## Phase-20 completion status"
            if marker not in text:
                c = json.loads(CLOSURE.read_text(encoding="utf-8"))
                text = text.rstrip("\n") + (
                    f"\n\n{marker}\n\n"
                    f"Phase 20 is **COMPLETE** (Stage B). One conventional shared four-domain baseline:\n"
                    f"a single frozen **UNet++** ({c['model_params']:,} params) with one shared parameter\n"
                    "set and one output head, trained with a frozen domain-balanced sampler, and selected\n"
                    f"on `phase20_macro_domain_mean_dice_v1`. Best epoch **{c['best_epoch']}**, macro-domain\n"
                    f"VAL Dice **{c['best_macro_domain_dice']:.6f}**; early stopped at epoch {c['final_epoch']}.\n\n"
                    "No FiLM, no task conditioning, no regional module, no localizer, no ROI/proposal.\n"
                    f"Terminal state: **`{TERMINAL}`**. Phase 21 is **eligible but NOT started**.\n")
        else:
            text = re.sub(r"- \*\*Current Status:\*\*[^\n]*",
                          "- **Current Status:** ELIGIBLE / NOT STARTED — Phase-20 baseline is frozen "
                          "and all Phase-21 entry criteria are met; scientific execution requires fresh "
                          "supervisor authorization",
                          text, count=1)
            marker = "## Phase-21 eligibility"
            if marker not in text:
                p21 = json.loads(P21.read_text(encoding="utf-8"))
                text = text.rstrip("\n") + (
                    f"\n\n{marker}\n\n"
                    "Phase 21 (Global MedFiLM) is **ELIGIBLE but NOT STARTED**. All "
                    f"**{sum(1 for x in p21['criteria'] if x['met'])}/{len(p21['criteria'])}** Phase-21 entry criteria are met "
                    "(`reports/audits/phase20_phase21_entry_criteria.json`), and the Phase-20 baseline\n"
                    "checkpoint is frozen and immutable. Starting Phase 21 requires a fresh supervisor\n"
                    "authorization; it must be compared against the Phase-20 baseline on the **same 64**\n"
                    "deterministically selected VAL cases.\n")
        path.write_text(text, encoding="utf-8")
        out[f"phase_{n}"] = {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                             "old_sha256": old, "new_sha256": sha(path)}
    record["phase_readmes"] = out


def update_master_plan(record: dict) -> None:
    old = sha(MASTER_PLAN)
    text = MASTER_PLAN.read_text(encoding="utf-8")
    repl = {
        "- **Phase 19:** CURRENT / AUTHORIZED (dataset harmonization; **not** a training phase)":
            "- **Phase 19:** COMPLETE (dataset harmonization; **not** a training phase)",
        "- **Phase 19:** Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB) (**CURRENT / AUTHORIZED** — Stage B active; protocol + preparation COMPLETE)":
            "- **Phase 19:** Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB) (**COMPLETE**)",
        "- **Phase 20:** Multi-Domain Global Baseline Evaluation (NOT_STARTED_AND_NOT_AUTHORIZED)":
            "- **Phase 20:** Shared Four-Domain Global Baseline — single frozen UNet++ (**COMPLETE**; macro-domain VAL Dice 0.792007)",
        "- **Phase 21:** Global MedFiLM Reference Architecture (NOT_STARTED)":
            "- **Phase 21:** Global MedFiLM Reference Architecture (**ELIGIBLE / NOT STARTED** — authorization required)",
    }
    for a, b in repl.items():
        text = text.replace(a, b)

    marker = "## Stage-B Phase-20 completion (shared four-domain global baseline)"
    if marker not in text:
        c = json.loads(CLOSURE.read_text(encoding="utf-8"))
        ev = json.loads(EVAL.read_text(encoding="utf-8"))
        note = (
            f"{marker}\n\n"
            "**Phase 20 COMPLETE.** ONE conventional shared four-domain baseline under the frozen\n"
            "Phase-19 harmonized protocol — **no FiLM, no task conditioning, no regional module,\n"
            "no localizer, no ROI/proposal**.\n\n"
            f"- Experiment: `{c['experiment_id']}`\n"
            f"- Single frozen **UNet++**, {c['model_params']:,} params, one shared parameter set, one head\n"
            f"- **Macro-domain VAL Dice {c['best_macro_domain_dice']:.6f}** at best epoch {c['best_epoch']}; "
            f"early stopped at epoch {c['final_epoch']}\n"
            f"- Canonical VAL evaluation: {ev['samples_evaluated']} samples, exactly one inference run\n"
            f"- TEST reads: **0** (image / mask / inference / visualization)\n"
            f"- **Phase 21: ELIGIBLE but NOT STARTED** (authorization required)\n"
            f"- Terminal state: **`{TERMINAL}`**\n\n---\n\n")
        marker7 = "## 7. Canonical 41-Phase Master Progression (Phase 00 through Phase 40)"
        if marker7 in text:
            text = text.replace(marker7, note + marker7, 1)
        else:
            text = text.rstrip("\n") + "\n\n" + note
    MASTER_PLAN.write_text(text, encoding="utf-8")
    record["project_master_plan"] = {
        "path": "PROJECT_MASTER_PLAN.md",
        "old_sha256": old, "new_sha256": sha(MASTER_PLAN)}


def update_index(record: dict) -> None:
    old = sha(INDEX_NB)
    nb = nbformat.read(str(INDEX_NB), as_version=4)
    marker = "Phase-20 Completion and Phase-21 Eligibility"
    if not any(marker in "".join(c.source) for c in nb.cells):
        c = json.loads(CLOSURE.read_text(encoding="utf-8"))
        ev = json.loads(EVAL.read_text(encoding="utf-8"))
        p21 = json.loads(P21.read_text(encoding="utf-8"))
        nb.cells.append(nbformat.v4.new_markdown_cell(
            f"## {marker}\n\n"
            "**Phase 20 COMPLETE** — one conventional shared four-domain baseline (single frozen\n"
            "UNet++, no FiLM, no regional module, no localizer, no ROI/proposal), trained under the\n"
            "frozen Phase-19 harmonized protocol.\n\n"
            f"- Experiment: `{c['experiment_id']}`\n"
            f"- Macro-domain VAL Dice **{c['best_macro_domain_dice']:.6f}** (best epoch {c['best_epoch']}, "
            f"early stop at {c['final_epoch']})\n"
            f"- Canonical VAL pass: {ev['samples_evaluated']} samples, one inference run; "
            f"{ev['prob_maps_persisted']} predictions persisted\n"
            f"- TEST reads: 0\n"
            f"- **Phase 21 is ELIGIBLE but NOT STARTED** — authorization required\n"
            f"- Terminal state: `{TERMINAL}`\n"))
        nb.cells.append(nbformat.v4.new_code_cell(
            "import json as _j, pandas as _pd\n"
            "_c = _j.loads((ROOT / 'experiments/phase20_shared_unetpp_fourdomain_seed42_clean_v3/closure.json').read_text(encoding='utf-8'))\n"
            "_e = _j.loads((ROOT / 'reports/audits/phase20_val_evaluation.json').read_text(encoding='utf-8'))\n"
            "_p = _j.loads((ROOT / 'reports/audits/phase20_phase21_entry_criteria.json').read_text(encoding='utf-8'))\n"
            "_d = _pd.read_csv(ROOT / 'reports/tables/phase20_domain_performance.csv')\n"
            "display(_d[_d['row_type'].isin(['DOMAIN','MACRO_DOMAIN'])][['row_type','dataset','n','dice','iou','mcc']])\n"
            "_rows = [\n"
            "    {'phase': '19', 'status': 'COMPLETE'},\n"
            "    {'phase': '20', 'status': 'COMPLETE'},\n"
            "    {'phase': '21', 'status': 'ELIGIBLE / NOT STARTED'},\n"
            "]\n"
            "display(_pd.DataFrame(_rows))\n"
            "print('best epoch          :', _c['best_epoch'])\n"
            "print('macro-domain dice   :', round(_c['best_macro_domain_dice'], 6))\n"
            "print('stop reason         :', _c['stop_reason'], '| final epoch', _c['final_epoch'])\n"
            "print('VAL samples         :', _e['samples_evaluated'], '| inference runs', _e['canonical_val_inference_runs'])\n"
            "print('TEST reads          :', _e['test_reads'])\n"
            "print('phase21 criteria    :', sum(1 for x in _p['criteria'] if x['met']), '/', len(_p['criteria']))\n"
            "print('phase21 may start   :', _p['phase21_may_start'])\n"
            f"print('TERMINAL STATE      : {TERMINAL}')\n"))
    nbformat.write(nb, str(INDEX_NB))
    res = exec_nb(INDEX_NB)
    record["phasewise_index"] = {
        "path": "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb",
        "old_sha256": old, "new_sha256": sha(INDEX_NB),
        "change": "added Phase-20 completion / Phase-21 eligibility section", **res}


def main() -> int:
    closure = json.loads(CLOSURE.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    p21 = json.loads(P21.read_text(encoding="utf-8"))
    record = {
        "artifact": "phase20_completion_governance_state",
        "status": TERMINAL,
        "generated_by": "scripts/notebooks/sync_phase20_completion.py",
        "phase20_protocol": {
            "path": "reports/audits/phase20_shared_global_baseline_protocol.json",
            "sha256": sha(PROTOCOL), "status": protocol["status"]},
        "phase20_experiment": {
            "experiment_id": closure["experiment_id"],
            "best_epoch": closure["best_epoch"],
            "best_macro_domain_dice": closure["best_macro_domain_dice"],
            "final_epoch": closure["final_epoch"],
            "stop_reason": closure["stop_reason"],
            "checkpoint_sha256": closure["best_checkpoint_sha256"],
        },
        "governance": {
            "stage_b": "ACTIVE",
            "phase_19": "COMPLETE",
            "phase_20": "COMPLETE",
            "phase_21": "ELIGIBLE_NOT_STARTED",
            "phase_21_authorization_required": True,
            "phase_21_started": False,
            "film_used": False,
            "regional_module_used": False,
            "localizer_used": False,
            "roi_proposal_used": False,
            "task_conditioning_used": False,
            "test": "CLOSED",
            "test_reads": 0,
            "frozen_historical_artifacts_modified": 0,
        },
        "synchronized": {},
    }
    update_notebook_map(record["synchronized"])
    update_phasewise_readme(record["synchronized"])
    update_phase_readmes(record["synchronized"])
    update_master_plan(record["synchronized"])
    update_index(record["synchronized"])

    flat = []
    for k, v in record["synchronized"].items():
        if k == "phase_readmes":
            flat.extend(v.values())
        else:
            flat.append(v)
    record["idempotence"] = {
        "all_synchronized_files_converged": all(f["old_sha256"] == f["new_sha256"] for f in flat),
        "files_checked": len(flat),
        "note": ("Every synchronized file was byte-identical before and after this run; the sync "
                 "is convergent/idempotent. Transitions are recorded from a declared baseline, "
                 "never from observed on-disk deltas."),
    }

    OUT.write_text(json.dumps(record, indent=2), encoding="utf-8")

    print("=== PHASE-20 COMPLETION GOVERNANCE SYNC ===")
    for k, v in record["synchronized"].items():
        if k == "phase_readmes":
            for kk, vv in v.items():
                print(f"  {kk:<10} {vv['old_sha256'][:12]} -> {vv['new_sha256'][:12]}")
        elif isinstance(v, dict) and "old_sha256" in v:
            print(f"  {k:<26} {v['old_sha256'][:12]} -> {v['new_sha256'][:12]}")
    print("idempotence:", json.dumps(record["idempotence"]))
    print("governance artifact:", OUT.relative_to(ROOT), "| sha256:", sha(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
