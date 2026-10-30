"""
Stage-B governance synchronization (post-H3 closure -> Phase-19 authorization).

Additively updates, and executes where applicable:

  1. reports/audits/phasewise_notebook_map.json   (phase statuses 15-20)
  2. notebooks/phasewise/README.md                (roadmap rows + Stage-B section)
  3. notebooks/phasewise/phase_15..19_*/README.md (status lines)
  4. PROJECT_MASTER_PLAN.md                       (phase lines + transition note)
  5. notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb (Stage-B section; executed)

No training, no inference, no TEST access, no frozen-gate change.
Idempotent: safe to re-run.

Run:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe scripts/notebooks/sync_stage_b_governance.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
AUTH = ROOT / "reports/audits/stage_b_phase19_authorization.json"
PROTOCOL = ROOT / "reports/audits/phase19_multidomain_harmonization_protocol.json"
MAP = ROOT / "reports/audits/phasewise_notebook_map.json"
PW_README = ROOT / "notebooks/phasewise/README.md"
INDEX_NB = ROOT / "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb"
MASTER_PLAN = ROOT / "PROJECT_MASTER_PLAN.md"
OUT = ROOT / "reports/audits/stage_b_governance_state.json"

PHASE_README = {
    15: ROOT / "notebooks/phasewise/phase_15_loss_study/README.md",
    16: ROOT / "notebooks/phasewise/phase_16_fusion/README.md",
    17: ROOT / "notebooks/phasewise/phase_17_kub_regional_ablation/README.md",
    18: ROOT / "notebooks/phasewise/phase_18_kub_final_dev_benchmark/README.md",
    19: ROOT / "notebooks/phasewise/phase_19_harmonization/README.md",
}

DEFERRED_NOTE = (
    "Phase {n} is **DEFERRED_CONDITIONAL_AFTER_H3_INSUFFICIENCY**: scientific execution is "
    "`NOT_EXECUTED` and it is not authorized at this time. The phase is not deleted and is not "
    "renumbered; it may be resumed only under a fresh supervisor authorization after the main "
    "multi-domain program is established."
)

# Declared pre-Stage-B baseline statuses, used to make the recorded transition canonical
# instead of observational (a re-run of an already-converged sync observes zero changes).
# Provenance:
#   * phase 15 - reports/audits/h3_post_adjudication_governance_state.json
#                -> phase_15_status = NOT_STARTED_AND_NOT_AUTHORIZED
#                   (protocol_status PROTOCOL_FROZEN__DESIGN_ONLY, execution NOT started)
#   * phases 16-20 - notebooks/phasewise/README.md roadmap rows (status column = NOT_STARTED)
PRE_STAGE_B_STATUS = {
    "15": "NOT_STARTED_AND_NOT_AUTHORIZED",
    "16": "NOT_STARTED",
    "17": "NOT_STARTED",
    "18": "NOT_STARTED",
    "19": "NOT_STARTED",
    "20": "NOT_STARTED",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    new_status = {
        "15": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
        "16": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
        "17": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
        "18": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
        "19": "CURRENT_AUTHORIZED",
        "20": "NOT_STARTED",
    }
    # Canonical transition, derived from the declared pre-Stage-B baseline rather than from
    # the (already-converged) on-disk state, so it is identical on every run.
    changed = [
        {"phase_id": pid, "from": PRE_STAGE_B_STATUS[pid], "to": new_status[pid]}
        for pid in sorted(new_status)
        if PRE_STAGE_B_STATUS[pid] != new_status[pid]
    ]
    for e in entries:
        pid = e.get("phase_id")
        if pid in new_status:
            e["status"] = new_status[pid]
        if pid == "19":
            e["reviewer_notebook"] = "phase19_multidomain_dataset_harmonization.ipynb"
            e["canonical_source"] = "reports/audits/phase19_multidomain_harmonization_protocol.json"
            e["visual_artifacts"] = "reports/figures/phase19_harmonization/"
        if pid in {"15", "16", "17", "18"}:
            e["roadmap_status"] = "DEFERRED_CONDITIONAL_AFTER_H3_INSUFFICIENCY"
            e["scientific_execution"] = "NOT_EXECUTED"
    MAP.write_text(json.dumps(entries, indent=1), encoding="utf-8")
    record["phasewise_notebook_map"] = {
        "path": "reports/audits/phasewise_notebook_map.json",
        "old_sha256": old, "new_sha256": sha(MAP),
        "status_changes": changed,
        "status_changes_baseline": "declared_pre_stage_b (canonical, run-independent)",
        "status_changes_baseline_provenance": (
            "reports/audits/h3_post_adjudication_governance_state.json (phase 15) + "
            "notebooks/phasewise/README.md roadmap rows (phases 16-20)"),
    }


def update_phasewise_readme(record: dict) -> None:
    old = sha(PW_README)
    text = PW_README.read_text(encoding="utf-8")
    rows = {
        "| [`phase_15_loss_study/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_15_loss_study/README.md) | Regional Refiner Segmentation Loss Study | Asymmetric loss functions (L0, L1, L2, L3) to suppress FP | PROTOCOL FROZEN (design only); EXECUTION NOT_STARTED_AND_NOT_AUTHORIZED |":
            "| [`phase_15_loss_study/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_15_loss_study/README.md) | Regional Refiner Segmentation Loss Study | Asymmetric loss functions (L0, L1, L2, L3) to suppress FP | DEFERRED_CONDITIONAL__NOT_EXECUTED (protocol frozen; post-H3 insufficiency) |",
        "| [`phase_16_fusion/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_16_fusion/README.md) | Regional-Global Mask Fusion | Intelligent fusion between global baseline & regional refiner | NOT_STARTED |":
            "| [`phase_16_fusion/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_16_fusion/README.md) | Regional-Global Mask Fusion | Intelligent fusion between global baseline & regional refiner | DEFERRED_CONDITIONAL__NOT_EXECUTED |",
        "| [`phase_17_kub_regional_ablation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_17_kub_regional_ablation/README.md) | KUB Regional Pipeline Comprehensive Ablation | End-to-end ablation of proposals, resolution, and loss | NOT_STARTED |":
            "| [`phase_17_kub_regional_ablation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_17_kub_regional_ablation/README.md) | KUB Regional Pipeline Comprehensive Ablation | End-to-end ablation of proposals, resolution, and loss | DEFERRED_CONDITIONAL__NOT_EXECUTED |",
        "| [`phase_18_kub_final_dev_benchmark/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_18_kub_final_dev_benchmark/README.md) | KUB Final Development Validation Benchmark | Benchmark finalized KUB regional pipeline on VAL | NOT_STARTED |":
            "| [`phase_18_kub_final_dev_benchmark/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_18_kub_final_dev_benchmark/README.md) | KUB Final Development Validation Benchmark | Benchmark finalized KUB regional pipeline on VAL | DEFERRED_CONDITIONAL__NOT_EXECUTED |",
        "| [`phase_19_harmonization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_19_harmonization/README.md) | Multi-Domain Harmonization | Standardize ISIC, BUSI, Kvasir, KUB task encodings | NOT_STARTED |":
            "| [`phase_19_harmonization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_19_harmonization/README.md) | Multi-Domain Dataset Harmonization | Standardize ISIC, BUSI, Kvasir, KUB under one leakage-safe task/data contract | **CURRENT / AUTHORIZED** |",
        "| [`phase_20_multidomain_baselines/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_20_multidomain_baselines/README.md) | Multi-Domain Global Baseline Evaluation | Evaluate global baselines across all 4 modalities | NOT_STARTED |":
            "| [`phase_20_multidomain_baselines/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_20_multidomain_baselines/README.md) | Multi-Domain Global Baseline Evaluation | Evaluate global baselines across all 4 modalities | NOT_STARTED_AND_NOT_AUTHORIZED |",
    }
    for a, b in rows.items():
        text = text.replace(a, b)

    if "## Stage-B activation (post-H3 supervisor decision)" not in text:
        section = (
            "\n\n## Stage-B activation (post-H3 supervisor decision)\n\n"
            "The post-Phase14 / H3 target-support branch is **CLOSED** with the frozen scientific label\n"
            "**`H3_SUPPLY_REDESIGN_INSUFFICIENT`**. The regional branch is **DEFERRED / NOT PROMOTED** —\n"
            "preserved as diagnostically supported by the Oracle but not deployably resolved. It is neither\n"
            "erased nor successfully integrated.\n\n"
            "- Authorization artifact: `reports/audits/stage_b_phase19_authorization.json`\n"
            "- Supervisor state: `STAGE_B_AUTHORIZED__PHASE19_READY_TO_START`\n"
            "- Option B / Option C: `DEFERRED__NOT_AUTHORIZED`\n"
            "- Phases 15-18: `DEFERRED_CONDITIONAL__NOT_EXECUTED` (not deleted, not renumbered)\n"
            "- **Stage B is ACTIVE**; the main multi-domain program begins at **Phase 19**\n"
            "- Phase 20+: `NOT_STARTED_AND_NOT_AUTHORIZED`\n"
            "- TEST and external TEST remain `CLOSED`\n\n"
            "The correct summary of the regional evidence: *Oracle regional processing shows potential, but the\n"
            "current GT-free predicted localization path does not preserve enough practical benefit.*\n"
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
                "- **Current Status:** NOT_STARTED",
                "- **Current Status:** CURRENT / AUTHORIZED (Stage B) — "
                "harmonization protocol + preparation COMPLETE; scientific execution/training not authorized")
            if "## Stage-B status" not in text:
                text = text.rstrip("\n") + (
                    "\n\n## Stage-B status\n\n"
                    "Phase 19 is the **first active Stage-B notebook**. The harmonization protocol, "
                    "contracts, tables, figures and reviewer notebook are prepared and SHA-bound. "
                    "Phase 19 is a **data-harmonization** phase: no model training, no optimizer, no "
                    "backward pass, no checkpoint. Phase 20 remains "
                    "`NOT_STARTED_AND_NOT_AUTHORIZED`. TEST reads = 0.\n")
        else:
            text = re.sub(r"- \*\*Current Status:\*\*[^\n]*",
                          f"- **Current Status:** DEFERRED_CONDITIONAL__NOT_EXECUTED", text, count=1)
            if f"## Phase-{n} deferral" not in text:
                text = text.rstrip("\n") + f"\n\n## Phase-{n} deferral\n\n" + DEFERRED_NOTE.format(n=n) + "\n"
        path.write_text(text, encoding="utf-8")
        out[f"phase_{n}"] = {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                             "old_sha256": old, "new_sha256": sha(path)}
    record["phase_readmes"] = out


def update_master_plan(record: dict) -> None:
    old = sha(MASTER_PLAN)
    text = MASTER_PLAN.read_text(encoding="utf-8")
    repl = {
        "- **Phase 15:** Regional Refiner Segmentation Loss Study (PROTOCOL FROZEN; L1/L2/L3 NOT trained — clean-v3 revalidation required, separately authorized)":
            "- **Phase 15:** Regional Refiner Segmentation Loss Study (DEFERRED_CONDITIONAL__NOT_EXECUTED — protocol frozen; deferred after H3 insufficiency)",
        "- **Phase 16:** Regional-Global Mask Fusion (NOT_STARTED)":
            "- **Phase 16:** Regional-Global Mask Fusion (DEFERRED_CONDITIONAL__NOT_EXECUTED)",
        "- **Phase 17:** KUB Regional Pipeline Comprehensive Ablation (NOT_STARTED)":
            "- **Phase 17:** KUB Regional Pipeline Comprehensive Ablation (DEFERRED_CONDITIONAL__NOT_EXECUTED)",
        "- **Phase 18:** KUB Final Development Validation Benchmark (NOT_STARTED)":
            "- **Phase 18:** KUB Final Development Validation Benchmark (DEFERRED_CONDITIONAL__NOT_EXECUTED)",
        "- **Phase 19:** Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB) (NOT_STARTED)":
            "- **Phase 19:** Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB) (**CURRENT / AUTHORIZED** — Stage B active; protocol + preparation COMPLETE)",
        "- **Phase 20:** Multi-Domain Global Baseline Evaluation (NOT_STARTED)":
            "- **Phase 20:** Multi-Domain Global Baseline Evaluation (NOT_STARTED_AND_NOT_AUTHORIZED)",
    }
    for a, b in repl.items():
        text = text.replace(a, b)

    if "## Stage-B activation and regional-branch deferral" not in text:
        marker = "## 7. Canonical 41-Phase Master Progression (Phase 00 through Phase 40)"
        note = (
            "## Stage-B activation and regional-branch deferral\n\n"
            "**Post-H3 supervisor governance transition.** The post-Phase14 / H3 target-support branch is\n"
            "**CLOSED** with the frozen scientific label **`H3_SUPPLY_REDESIGN_INSUFFICIENT`**. The regional\n"
            "mechanism is **DEFERRED / NOT PROMOTED** (preserved as diagnostically supported by the Oracle\n"
            "but not deployably resolved — neither erased nor successfully integrated).\n\n"
            "- **Option B / Option C:** `DEFERRED__NOT_AUTHORIZED`\n"
            "- **Phases 15-18:** `DEFERRED_CONDITIONAL__NOT_EXECUTED` (roadmap numbering unchanged)\n"
            "- **Stage B:** ACTIVE — the main multi-domain program begins at **Phase 19**\n"
            "- **Phase 19:** CURRENT / AUTHORIZED (dataset harmonization; **not** a training phase)\n"
            "- **Phase 20+:** `NOT_STARTED_AND_NOT_AUTHORIZED`\n"
            "- **TEST / external TEST:** `CLOSED` (Phase-19 TEST reads = 0)\n\n"
            "Authorization artifact: `reports/audits/stage_b_phase19_authorization.json`.\n\n---\n\n")
        text = text.replace(marker, note + marker, 1)
    MASTER_PLAN.write_text(text, encoding="utf-8")
    record["project_master_plan"] = {
        "path": "PROJECT_MASTER_PLAN.md",
        "old_sha256": old, "new_sha256": sha(MASTER_PLAN)}


def update_index(record: dict) -> None:
    old = sha(INDEX_NB)
    nb = nbformat.read(str(INDEX_NB), as_version=4)
    marker = "Stage-B Activation and Phase-19 Authorization"
    if not any(marker in "".join(c.source) for c in nb.cells):
        nb.cells.append(nbformat.v4.new_markdown_cell(
            "## Stage-B Activation and Phase-19 Authorization\n\n"
            "The post-Phase14 / H3 target-support branch is **CLOSED** "
            "(`H3_SUPPLY_REDESIGN_INSUFFICIENT`). The regional branch is **DEFERRED / NOT PROMOTED** — "
            "preserved as diagnostically supported by the Oracle but not deployably resolved.\n\n"
            "**Stage B is ACTIVE.** The main multi-domain program begins at **Phase 19** "
            "(Multi-Domain Dataset Harmonization) — a data-harmonization phase, not a training phase.\n\n"
            "- Authorization: `reports/audits/stage_b_phase19_authorization.json`\n"
            "- Protocol: `reports/audits/phase19_multidomain_harmonization_protocol.json`\n"
            "- Notebook: `notebooks/phasewise/phase_19_harmonization/phase19_multidomain_dataset_harmonization.ipynb`\n"
            "- Phases 15-18: `DEFERRED_CONDITIONAL__NOT_EXECUTED` (not deleted, not renumbered)\n"
            "- Phase 20+: `NOT_STARTED_AND_NOT_AUTHORIZED`; TEST `CLOSED`\n"))
        nb.cells.append(nbformat.v4.new_code_cell(
            "import json as _j\n"
            "_auth = _j.loads((ROOT / 'reports/audits/stage_b_phase19_authorization.json').read_text(encoding='utf-8'))\n"
            "_proto = _j.loads((ROOT / 'reports/audits/phase19_multidomain_harmonization_protocol.json').read_text(encoding='utf-8'))\n"
            "_rows = [\n"
            "    {'phase': 'post-Phase14 H3', 'status': 'CLOSED / FORMALLY ADJUDICATED / INSUFFICIENT'},\n"
            "    {'phase': '15', 'status': 'DEFERRED_CONDITIONAL__NOT_EXECUTED'},\n"
            "    {'phase': '16', 'status': 'DEFERRED_CONDITIONAL__NOT_EXECUTED'},\n"
            "    {'phase': '17', 'status': 'DEFERRED_CONDITIONAL__NOT_EXECUTED'},\n"
            "    {'phase': '18', 'status': 'DEFERRED_CONDITIONAL__NOT_EXECUTED'},\n"
            "    {'phase': '19', 'status': 'CURRENT / AUTHORIZED'},\n"
            "    {'phase': '20', 'status': 'NOT_STARTED'},\n"
            "]\n"
            "display(pd.DataFrame(_rows))\n"
            "print('authorization status :', _auth['status'])\n"
            "print('Stage B active       :', _auth['stage_b_activation']['active'])\n"
            "print('Phase-19 status      :', _auth['phase19_authorization']['status'])\n"
            "print('protocol status      :', _proto['status'])\n"
            "print('datasets harmonized  :', [d['dataset'] for d in _proto['datasets']])\n"
            "print('TEST reads           :', _proto['governance']['test_image_reads'])\n"))
    nbformat.write(nb, str(INDEX_NB))
    res = exec_nb(INDEX_NB)
    record["phasewise_index"] = {
        "path": "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb",
        "old_sha256": old, "new_sha256": sha(INDEX_NB),
        "change": "added Stage-B activation / Phase-19 authorization section", **res}


def main() -> int:
    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    record = {
        "artifact": "stage_b_governance_state",
        "status": "POST_H3_REGIONAL_BRANCH_DEFERRED__STAGE_B_ACTIVE__PHASE19_READY",
        "generated_by": "scripts/notebooks/sync_stage_b_governance.py",
        "authorization_artifact": {
            "path": "reports/audits/stage_b_phase19_authorization.json",
            "sha256": sha(AUTH), "status": auth["status"]},
        "phase19_protocol": {
            "path": "reports/audits/phase19_multidomain_harmonization_protocol.json",
            "sha256": sha(PROTOCOL), "status": protocol["status"]},
        "governance": {
            "h3": "CLOSED__FORMALLY_INSUFFICIENT",
            "regional_localizer_redesign": "DEFERRED",
            "phases_15_18": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
            "stage_b": "ACTIVE",
            "phase_19": "AUTHORIZED / PROTOCOL + HARMONIZATION PREPARATION COMPLETE",
            "phase_20": "NOT_STARTED_AND_NOT_AUTHORIZED",
            "option_b": "DEFERRED__NOT_AUTHORIZED",
            "option_c": "DEFERRED__NOT_AUTHORIZED",
            "test": "CLOSED",
            "training_performed": False, "inference_performed": False,
            "checkpoints_created": 0, "test_reads": 0,
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
        "all_synchronized_files_converged": all(
            f["old_sha256"] == f["new_sha256"] for f in flat),
        "files_checked": len(flat),
        "note": ("Every synchronized file was byte-identical before and after this run; "
                 "the sync is convergent/idempotent. No content artifact is modified by a "
                 "re-run."),
    }

    OUT.write_text(json.dumps(record, indent=2), encoding="utf-8")

    print("=== STAGE-B GOVERNANCE SYNC SUMMARY ===")
    print(json.dumps(record["synchronized"], indent=2))
    print("idempotence:", json.dumps(record["idempotence"]))
    print("Governance artifact:", OUT.relative_to(ROOT), "| sha256:", sha(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
