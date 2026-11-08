"""Phase-wise notebook coverage inventory.

Scans every directory under notebooks/phasewise, classifies notebook presence,
validity, implementation completeness and experiment completeness, then writes
PHASEWISE_NOTEBOOK_COVERAGE.csv.

Read-only on all research artifacts.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
PHASEWISE = ROOT / "notebooks" / "phasewise"

STATUSES = [
    "NOTEBOOK_COMPLETE", "NOTEBOOK_PRESENT_BUT_BROKEN", "NOTEBOOK_PRESENT_BUT_OBSOLETE",
    "NOTEBOOK_MISSING_IMPLEMENTATION_EXISTS", "NOTEBOOK_MISSING_RESULTS_EXIST",
    "NOTEBOOK_MISSING_EXPERIMENT_NOT_EXECUTED", "DOCUMENTATION_ONLY_PHASE",
    "SOURCE_ARTIFACT_MISSING", "REQUIRES_HUMAN_AUTHORIZATION",
]

# Phases whose experiment is gated by authorization / consumed access.
GATED = {"39"}
# Phases that are governance / literature / specification rather than experiments.
DOC_ONLY = {"00", "01", "23", "24", "38"}

TRAIN_PAT = re.compile(r"\.fit\(|trainer\.train\(|optimizer\.step\(|loss\.backward\(|torch\.optim\.|run_training")
TEST_PAT = re.compile(r"phase4_v3[/\\]test|TEST1683|test_lock")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def tokens_for(folder: str) -> tuple[str, list[str], str]:
    m = re.match(r"phase_?(\d{1,2})([a-z]?)", folder)
    if not m:
        m2 = re.match(r"post_phase(\d{1,2})", folder)
        if m2:
            n = int(m2.group(1))
            return f"POST{n}", [f"phase{n}", f"phase{n:02d}"], "post"
        return "NA", [], "other"
    n = int(m.group(1))
    letter = m.group(2)
    toks = [f"phase{n:02d}", f"phase{n}"]
    if letter:
        toks = [f"phase{n:02d}{letter}", f"phase{n}{letter}", f"phase{n:02d}", f"phase{n}"]
    pid = f"{n:02d}{letter.upper()}"
    return pid, toks, "main"


def count_matching(dirs: list[Path], toks: list[str]) -> tuple[int, list[str]]:
    if not toks:
        return 0, []
    names: list[str] = []
    for d in dirs:
        if not d.exists():
            continue
        try:
            entries = list(d.iterdir())
        except OSError:
            continue
        for p in entries:
            low = p.name.lower()
            if any(t in low for t in toks):
                names.append(p.name)
    return len(names), names[:6]


def main() -> None:
    folders = sorted([d for d in PHASEWISE.iterdir() if d.is_dir()],
                     key=lambda p: p.name)
    audit_dirs = [ROOT / "reports/audits", ROOT / "reports/tables",
                  ROOT / "reports/figures", ROOT / "experiments",
                  ROOT / "checkpoints", ROOT / "logs", ROOT / "runs"]

    rows = []
    for folder in folders:
        pid, toks, kind = tokens_for(folder.name)
        nbs = sorted(folder.rglob("*.ipynb"))
        nb_rel = ";".join(p.relative_to(ROOT).as_posix() for p in nbs)

        # --- notebook validity ---
        valid, code_cells, train_cells, test_cells, stale = 0, 0, 0, 0, 0
        impl_refs = 0
        for p in nbs:
            try:
                nb = json.loads(p.read_bytes().decode("utf-8"))
                valid += 1
            except Exception:  # noqa: BLE001
                continue
            cells = nb.get("cells", [])
            code_cells += sum(1 for c in cells if c.get("cell_type") == "code")
            src = "\n".join("".join(c.get("source", [])) for c in cells)
            if TRAIN_PAT.search(src):
                train_cells += 1
            if TEST_PAT.search(src):
                test_cells += 1
            if "src." in src or "scripts." in src:
                impl_refs += 1
            # obsolete: absolute paths that no longer resolve
            abs_paths = set(re.findall(r"[A-Za-z]:\\\\[^\s'\"\),\]]+", src))
            missing_paths = [q for q in abs_paths if not Path(q).exists()]
            if abs_paths and len(missing_paths) / len(abs_paths) > 0.5:
                stale += 1

        # --- evidence on disk ---
        n_audit, audit_names = count_matching([ROOT / "reports/audits"], toks)
        n_table, table_names = count_matching([ROOT / "reports/tables"], toks)
        n_exp, exp_names = count_matching([ROOT / "experiments"], toks)
        n_ckpt, ckpt_names = count_matching([ROOT / "checkpoints"], toks)
        n_log, log_names = count_matching([ROOT / "logs"], toks)
        n_pred, pred_names = count_matching([ROOT / "reports/predictions"], toks)

        # --- implementation on disk ---
        impl_files = 0
        for sub in ("scripts/training", "scripts/analysis", "src/models", "src/research"):
            base = ROOT / sub
            if not base.exists():
                continue
            for p in base.rglob("*.py"):
                low = p.name.lower()
                if any(t in low for t in toks):
                    impl_files += 1

        has_results = (n_audit + n_table) > 0
        has_impl = impl_files > 0 or impl_refs > 0
        has_experiment_artifacts = (n_exp + n_ckpt) > 0

        # --- status ---
        num = pid.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ") if pid not in ("NA",) else "NA"
        if not nbs:
            if pid in GATED:
                status = "REQUIRES_HUMAN_AUTHORIZATION"
            elif pid in DOC_ONLY and not has_results:
                status = "DOCUMENTATION_ONLY_PHASE"
            elif has_results:
                status = "NOTEBOOK_MISSING_RESULTS_EXIST"
            elif has_impl:
                status = "NOTEBOOK_MISSING_EXPERIMENT_NOT_EXECUTED"
            elif has_experiment_artifacts:
                status = "NOTEBOOK_MISSING_RESULTS_EXIST"
            else:
                status = "DOCUMENTATION_ONLY_PHASE"
        else:
            if valid < len(nbs):
                status = "NOTEBOOK_PRESENT_BUT_BROKEN"
            elif stale:
                status = "NOTEBOOK_PRESENT_BUT_OBSOLETE"
            else:
                status = "NOTEBOOK_COMPLETE"

        # --- implementation / experiment status ---
        if impl_files > 0:
            impl_status = "IMPLEMENTATION_PRESENT"
        elif impl_refs > 0:
            impl_status = "REFERENCED_IN_NOTEBOOK_ONLY"
        else:
            impl_status = "NO_DEDICATED_IMPLEMENTATION"

        if pid in GATED:
            exp_status = "GATED_CONSUMED_ONE_SHOT"
        elif has_experiment_artifacts and has_results:
            exp_status = "EXECUTED_WITH_RESULTS"
        elif has_results:
            exp_status = "RESULTS_PRESENT_NO_RUN_ARTIFACTS"
        elif pid in DOC_ONLY:
            exp_status = "NOT_AN_EXPERIMENT"
        elif has_impl:
            exp_status = "NOT_EXECUTED"
        else:
            exp_status = "NOT_APPLICABLE"

        rows.append({
            "phase_id": pid,
            "phase_folder": folder.relative_to(ROOT).as_posix(),
            "original_notebook": nb_rel or "NONE",
            "notebook_status": status,
            "implementation_status": impl_status,
            "experiment_status": exp_status,
            "saved_results": f"audits={n_audit};tables={n_table}",
            "checkpoints": n_ckpt,
            "training_logs": n_log,
            "prediction_artifacts": n_pred,
            "missing_dependency": "",
            "required_fix": "",
            "generated_notebook": "",
            "verification_status": "PENDING",
            "_tokens": toks,
            "_n_notebooks": len(nbs),
            "_code_cells": code_cells,
            "_train_cells": train_cells,
            "_test_cells": test_cells,
            "_audit_names": audit_names[:3],
            "_exp_names": exp_names[:3],
        })

    fields = ["phase_id", "phase_folder", "original_notebook", "notebook_status",
              "implementation_status", "experiment_status", "saved_results",
              "checkpoints", "training_logs", "prediction_artifacts",
              "missing_dependency", "required_fix", "generated_notebook",
              "verification_status"]
    with (OUT / "PHASEWISE_NOTEBOOK_COVERAGE.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})

    from collections import Counter
    print(f"PHASE_DIRECTORIES {len(rows)}")
    print("STATUS:", dict(Counter(r["notebook_status"] for r in rows)))
    print("EXPERIMENT:", dict(Counter(r["experiment_status"] for r in rows)))
    print()
    for r in rows:
        if r["notebook_status"].startswith("NOTEBOOK_MISSING"):
            print(f"  MISSING {r['phase_id']:5s} {r['phase_folder'][20:]:44s} "
                  f"{r['notebook_status']:38s} exp={r['experiment_status']}")


if __name__ == "__main__":
    main()
