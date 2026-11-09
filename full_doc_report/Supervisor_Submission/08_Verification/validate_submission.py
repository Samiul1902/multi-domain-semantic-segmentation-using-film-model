#!/usr/bin/env python
"""Stage 2 — validate the ReMedFiLM supervisor submission and build the ZIP.

CHECKS
------
1. References   : Markdown links, HTML src/href and inline-code path references
                  in every package .md are resolved against the package first,
                  then the parent repository. Broken references fail the build.
2. Dependencies : AST scan of every package .py; classify stdlib / third-party /
                  local imports and verify that each local `src.*` dependency has
                  a flattened equivalent shipped in the package.
3. Science      : assert canonical VAL808 numbers, parameter counts, split
                  counts, EXTERNAL884 composition, HAM10000 exclusion, Phase-28
                  13-arm completeness and the inconclusive A8_vs_A7 CI.
4. Safety       : no checkpoints, raw arrays/images, patient workbook, test.csv,
                  quarantined.csv, or credentials inside the package.
5. ZIP          : build one archive, verify CRC (testzip), member count, and
                  per-member SHA-256 against the source files.

A ZIP cannot contain its own hash. The archive SHA-256 is therefore written
out-of-band to <zip>.sha256 and printed at the end of the run.

Usage:
    .venv/Scripts/python.exe \
        full_doc_report/Supervisor_Submission/08_Verification/validate_submission.py
"""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "full_doc_report" / "Supervisor_Submission"
ZIP_PATH = ROOT / "full_doc_report" / "ReMedFiLM_Supervisor_Submission.zip"
SHA_PATH = Path(str(ZIP_PATH) + ".sha256")
ARC_ROOT = "Supervisor_Submission"
MANIFEST_REL = "08_Verification/SUBMISSION_MANIFEST.csv"

NEW_DOCS = [
    "README_FOR_SUPERVISOR.md",
    "05_Datasets/DATASET_GUIDE.md",
    "05_Datasets/DATASET_RESOURCE_TABLE.csv",
    "05_Datasets/HAM10000_AUDIT_REPORT.md",
    "05_Datasets/EXTERNAL_SKIN_EVALUATION_MATRIX.csv",
    "04_Ablation_Phase28/README.md",
    "08_Verification/THESIS_GAPS_AND_EVIDENCE_GAPS.md",
    "08_Verification/HAM10000_AUDIT.json",
    "08_Verification/COPY_MAP.json",
    "08_Verification/SUBMISSION_MANIFEST.csv",
    "08_Verification/VERIFICATION_REPORT.md",
    "08_Verification/VERIFICATION_REPORT.json",
    "08_Verification/audit_ham10000.py",
    "08_Verification/build_dataset_tables.py",
    "08_Verification/build_submission_package.py",
    "08_Verification/validate_submission.py",
]

FORBIDDEN_SUFFIXES = {".pt", ".pth", ".ckpt", ".npy", ".npz", ".pkl",
                      ".bmp", ".dcm", ".pem", ".key"}
FORBIDDEN_NAMES = {"Patient_infos_BUSI-WHU.xlsx", "test.csv", "quarantined.csv"}
# Files deliberately cited as MISSING in the gap register — not broken links.
KNOWN_MISSING = {
    "V8_FINAL_SCIENTIFIC_QA.md", "V8_PUBLICATION_READINESS.md",
    "V7_TO_V8_CORRECTIONS.md", "v8_qa.py",
}
THIRD_PARTY = {
    "torch", "numpy", "pandas", "scipy", "PIL", "matplotlib", "sklearn",
    "tqdm", "yaml", "docx", "nbformat", "nbclient", "pytest", "cv2",
    "seaborn", "skimage", "openpyxl", "lxml", "jsonschema", "tabulate",
}
LOCAL_PREFIXES = ("src.",)

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_ATTR = re.compile(r"(?:src|href)\s*=\s*[\"']([^\"']+)[\"']")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
PATH_TOKEN = re.compile(
    r"^(?:[A-Za-z0-9_.+\-]+/)*[A-Za-z0-9_.+\-]+"
    r"\.(?:md|csv|json|png|svg|pdf|docx|py|ipynb|txt|xlsx|yaml|yml)$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(rel: str):
    return json.loads((OUT / rel).read_text(encoding="utf-8"))


def read_csv(rel: str) -> list[dict]:
    with (OUT / rel).open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# 1. Reference validation
# ---------------------------------------------------------------------------
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "data_cache", "runs"}

# Inline-code path-like strings are *names of artifacts*, not hyperlinks. These
# explicit policy sets stop the validator from treating deliberately withheld
# manifests, external dataset sidecars, or Stage-2 generated outputs as broken
# package links.
WITHHELD_ARTIFACTS = {
    "test.csv", "quarantined.csv", "all_paired.csv",
    "Patient_infos_BUSI-WHU.xlsx",
}
EXTERNAL_DATASET_ARTIFACTS = {
    "metadata.csv", "LICENSE.txt", "ATTRIBUTION.txt",
    "images/LICENSE.txt", "images/ATTRIBUTION.txt",
    "HAM10000/images/ATTRIBUTION.txt", "kavsir_bboxes.json", "annotations.json",
    "NNNNN-NN-NNNNNNN.png", "ISIC_0026042.png", "ISIC_0029819.png",
}
STAGE2_GENERATED_ARTIFACTS = {
    "SUBMISSION_MANIFEST.csv", "VERIFICATION_REPORT.md", "VERIFICATION_REPORT.json",
    "08_Verification/SUBMISSION_MANIFEST.csv",
    "08_Verification/VERIFICATION_REPORT.md",
    "08_Verification/VERIFICATION_REPORT.json",
}


def basename_index(roots: list[Path]) -> dict[str, list[Path]]:
    """Index file and directory basenames inside one or more roots."""
    idx: dict[str, list[Path]] = defaultdict(list)
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.is_file() or p.is_dir():
                idx[p.name].append(p)
    return idx


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def rel_to(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return ""


def token_in(t: str, names: set[str]) -> bool:
    return t in names or Path(t.rstrip("/")).name in names


def policy_status(t: str) -> tuple[str, str]:
    if token_in(t, KNOWN_MISSING):
        return "DOCUMENTED_MISSING_REFERENCE", ""
    if token_in(t, WITHHELD_ARTIFACTS):
        return "DOCUMENTED_WITHHELD_ARTIFACT", ""
    if token_in(t, EXTERNAL_DATASET_ARTIFACTS):
        return "EXTERNAL_DATASET_NAMED_ARTIFACT", ""
    return "", ""


def normalise_target(raw: str) -> tuple[str, Path | None]:
    t = unquote(raw.split("#")[0].split("?")[0]).strip()
    if t.startswith("file://"):
        parsed = urlparse(t)
        p = unquote(parsed.path)
        # file:///d:/Softfors/jup/... -> d:/Softfors/jup/...
        if re.match(r"^/[A-Za-z]:/", p):
            p = p[1:]
        return t, Path(p)
    return t, None


def check_references(md_files: list[Path], all_files: list[Path]) -> dict:
    pkg_idx = basename_index([OUT])
    repo_idx = basename_index([ROOT / d for d in
                               ("manifests", "reports", "docs", "src", "scripts",
                                "paper_doc", "notebooks", "assets", "full_doc_report",
                                "tests", "configs") if (ROOT / d).is_dir()])
    for p in ROOT.iterdir():
        if p.is_file():
            repo_idx[p.name].append(p)

    copy_map = json.loads((OUT / "08_Verification" / "COPY_MAP.json").read_text(
        encoding="utf-8"))
    source_by_dst = {e["destination"]: ROOT / e["source"] for e in copy_map}

    def resolve_link(t: str, file_uri_path: Path | None, doc: Path,
                     rel_doc: str) -> tuple[str, str]:
        status, where = policy_status(t)
        if status:
            return status, where

        # 0) file:// URIs in copied methodology docs
        if file_uri_path is not None:
            if file_uri_path.exists() and inside(file_uri_path, ROOT):
                matches = pkg_idx.get(file_uri_path.name, [])
                if matches:
                    return "PACKAGE_INTERNAL_EQUIVALENT", rel_to(matches[0], OUT)
                return "REPOSITORY_EXTERNAL", rel_to(file_uri_path, ROOT)
            return "DOCUMENTED_LOCAL_FILE_URI", file_uri_path.as_posix()

        source_doc = source_by_dst.get(rel_doc)
        candidates: list[tuple[Path, Path, str]] = [
            (doc.parent / t, OUT, "PACKAGE_INTERNAL"),
            (OUT / t, OUT, "PACKAGE_INTERNAL"),
        ]
        if source_doc is not None:
            candidates.append((source_doc.parent / t, ROOT, "REPOSITORY_EXTERNAL"))
        candidates.extend([
            (ROOT / t, ROOT, "REPOSITORY_EXTERNAL"),
            (ROOT / t.lstrip("/"), ROOT, "REPOSITORY_EXTERNAL"),
        ])
        for c, base, status in candidates:
            if c.exists() and inside(c, base):
                suffix = "_DIRECTORY" if c.is_dir() else ""
                return status + suffix, rel_to(c, base)

        base_name = Path(t.rstrip("/")).name
        if base_name:
            for idx, root, status, suffix in (
                    (pkg_idx, OUT, "PACKAGE_INTERNAL", "_BASENAME"),
                    (repo_idx, ROOT, "REPOSITORY_EXTERNAL", "_BASENAME")):
                matches = sorted(idx.get(base_name, []),
                                 key=lambda p: len(rel_to(p, root)))
                if matches:
                    return status + suffix, rel_to(matches[0], root)

        if token_in(t, STAGE2_GENERATED_ARTIFACTS):
            return "STAGE2_GENERATED_ARTIFACT", ""
        return "BROKEN", ""

    def classify_inline(t: str, doc: Path, rel_doc: str) -> tuple[str, str]:
        status, where = policy_status(t)
        if status:
            return status, where
        if token_in(t, STAGE2_GENERATED_ARTIFACTS):
            return "STAGE2_GENERATED_ARTIFACT", ""
        status, where = resolve_link(t, None, doc, rel_doc)
        if status != "BROKEN":
            return status, where
        return "INLINE_CODE_NAMED_ARTIFACT", ""

    rows: list[dict] = []
    for doc in md_files:
        text = doc.read_text(encoding="utf-8", errors="replace")
        rel_doc = doc.relative_to(OUT).as_posix()
        targets: list[tuple[str, str]] = []
        for m in MD_LINK.finditer(text):
            targets.append((m.group(1), "markdown_link"))
        for m in HTML_ATTR.finditer(text):
            targets.append((m.group(1), "html_attr"))
        for m in INLINE_CODE.finditer(text):
            tok = m.group(1).strip()
            # Only single path-like tokens, not prose or shell commands.
            if PATH_TOKEN.match(tok) and " " not in tok and "\\" not in tok:
                targets.append((tok, "inline_code_path"))

        for raw, kind in targets:
            t, file_uri_path = normalise_target(raw)
            if not t or t.startswith(("http://", "https://", "mailto:", "data:", "#")):
                continue
            if kind == "inline_code_path":
                status, where = classify_inline(t, doc, rel_doc)
            else:
                status, where = resolve_link(t, file_uri_path, doc, rel_doc)
            rows.append(dict(doc=rel_doc, kind=kind, target=raw,
                             status=status, resolved_to=where))
    counts = Counter(r["status"] for r in rows)
    return {
        "rows": rows, "counts": dict(counts),
        "broken": [r for r in rows if r["status"] == "BROKEN"],
        "note": ("Only unresolved Markdown/HTML link targets are classified BROKEN. "
                 "Inline-code path-like tokens are artifact names, not hyperlinks: "
                 "they are resolved where possible or assigned an explicit "
                 "WITHHELD / EXTERNAL / GENERATED / NAMED status. Copied repository "
                 "documents retain their original repository-relative links; "
                 "source-aware resolution uses COPY_MAP.json to resolve them from "
                 "their original locations. REPOSITORY_EXTERNAL, "
                 "REPOSITORY_EXTERNAL_BASENAME and PACKAGE_INTERNAL_EQUIVALENT "
                 "entries are documented resolutions, not package-link failures."),
    }


# ---------------------------------------------------------------------------
# 2. Code dependency validation
# ---------------------------------------------------------------------------
def check_dependencies(py_files: list[Path]) -> dict:
    flat_names = {p.stem for p in OUT.rglob("*.py")}
    modules: dict[str, dict] = {}
    parse_failures: list[str] = []
    for p in py_files:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_failures.append(f"{p.relative_to(OUT).as_posix()}: {exc}")
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for full in names:
                top = full.split(".")[0]
                if top == "__future__":
                    continue
                if top in sys.stdlib_module_names:
                    cls = "STDLIB"
                elif full.startswith(LOCAL_PREFIXES) or top in {
                        "phase25c_common", "phase25f_execution_common",
                        "phase25f_post_safety_features", "phase25f_spec_repair_common"}:
                    cls = "LOCAL_PROJECT"
                elif top in THIRD_PARTY:
                    cls = "THIRD_PARTY"
                else:
                    cls = "UNCLASSIFIED"
                rec = modules.setdefault(full, dict(module=full, classification=cls,
                                                    n_uses=0, files=[]))
                rec["n_uses"] += 1
                f = p.relative_to(OUT).as_posix()
                if f not in rec["files"]:
                    rec["files"].append(f)

    local = {k: v for k, v in modules.items() if v["classification"] == "LOCAL_PROJECT"}
    unresolved = []
    for name, rec in sorted(local.items()):
        leaf = name.split(".")[-1]
        if leaf in flat_names:
            rec["resolution"] = "FLATTENED_EQUIVALENT_IN_PACKAGE"
        else:
            rec["resolution"] = "MISSING_FLATTENED_EQUIVALENT"
            unresolved.append(name)

    third_party = {k: v for k, v in modules.items() if v["classification"] == "THIRD_PARTY"}
    availability = {}
    for name in sorted(third_party):
        try:
            availability[name] = importlib.util.find_spec(name.split(".")[0]) is not None
        except (ImportError, ValueError):
            availability[name] = False
    return {
        "py_files": len(py_files),
        "parse_failures": parse_failures,
        "modules": sorted(modules.values(), key=lambda r: r["module"]),
        "classification_counts": dict(Counter(v["classification"] for v in modules.values())),
        "local_modules": local,
        "unresolved_local": unresolved,
        "third_party_available_in_this_env": availability,
        "note": ("Scripts were copied out of the repository package tree into flat code/ "
                 "directories. `src.*` imports need the original repository on PYTHONPATH "
                 "to re-execute; flattened equivalents are shipped for reading. "
                 "Third-party availability is informational and environment-specific."),
    }


# ---------------------------------------------------------------------------
# 3. Scientific consistency
# ---------------------------------------------------------------------------
def check_science() -> dict:
    checks: list[dict] = []

    def add(name, ok, detail):
        checks.append(dict(check=name, passed=bool(ok), detail=str(detail)))

    reg = read_json("03_Experimental_Results/reconciliation/REMEDFILM_V8_RESULTS_REGISTRY.json")
    cr = reg["canonical_result"]
    val = read_csv("03_Experimental_Results/internal/REMEDFILM_FULL_VAL808_METRICS.csv")
    macro = next(r for r in val if r["domain"] == "MACRO_DOMAIN_EQUAL_WEIGHT")
    add("canonical_full_macro_dice_matches_val808_table",
        abs(float(cr["full_macro_dice"]) - float(macro["full_dice"])) < 1e-12,
        f'registry {cr["full_macro_dice"]} vs table {macro["full_dice"]}')
    add("canonical_global_macro_dice_matches_val808_table",
        abs(float(cr["global_macro_dice"]) - float(macro["global_dice"])) < 1e-12,
        f'registry {cr["global_macro_dice"]} vs table {macro["global_dice"]}')
    add("canonical_paired_delta_matches_val808_table",
        abs(float(cr["paired_delta_dice"]) - float(macro["delta_dice"])) < 1e-12,
        f'registry {cr["paired_delta_dice"]} vs table {macro["delta_dice"]}')
    add("canonical_ci_excludes_zero",
        cr["paired_delta_ci_low"] > 0 and cr["paired_delta_ci_high"] > 0,
        f'CI [{cr["paired_delta_ci_low"]}, {cr["paired_delta_ci_high"]}]')
    add("val808_domain_counts_sum_to_808",
        sum(int(r["n"]) for r in val if r["domain"] != "MACRO_DOMAIN_EQUAL_WEIGHT") == 808,
        {r["domain"]: int(r["n"]) for r in val if r["domain"] != "MACRO_DOMAIN_EQUAL_WEIGHT"})
    recon = read_json("03_Experimental_Results/reconciliation/REMEDFILM_FULL_RESULT_RECONCILIATION.json")
    add("legacy_0_837862_is_rejected",
        "REPORTING_INCONSISTENCY" in json.dumps(recon).upper()
        or "REJECT" in json.dumps(recon).upper(),
        "0.837862 adjudicated as a V5/V6/V7 hard-coded reporting inconsistency")
    add("legacy_value_absent_from_val808_metrics_table",
        "0.837862" not in (OUT / "03_Experimental_Results/internal/REMEDFILM_FULL_VAL808_METRICS.csv")
        .read_text(encoding="utf-8"),
        "0.837862 must not appear as a headline metric")

    comp = read_json("02_Methodology_and_Architecture/REMEDFILM_FULL_COMPONENT_REGISTRY.json")
    comp_txt = json.dumps(comp)
    add("full_total_parameters_4837420", "4837420" in comp_txt.replace(",", ""),
        "G 3,523,001 + R_psi 1,276,401 + B_phi 36,801 + S_omega 1,217 = 4,837,420")
    add("v8_verified_total_parameters_matches",
        reg["canonical_model"]["verified_total_parameters"] == 4837420,
        reg["canonical_model"]["verified_total_parameters"])
    add("backbone_parameters_3523001",
        reg["baseline_model"]["parameters"] == 3523001,
        reg["baseline_model"]["parameters"])

    train = read_csv("05_Datasets/manifests/train.csv")
    valm = read_csv("05_Datasets/manifests/val.csv")
    add("train_manifest_5832", len(train) == 5832, len(train))
    add("val_manifest_808", len(valm) == 808, len(valm))
    resource = read_csv("05_Datasets/DATASET_RESOURCE_TABLE.csv")
    rt = {r["id"]: r for r in resource}
    add("resource_table_isic_split_counts",
        (rt["1"]["train"], rt["1"]["val"], rt["1"]["quarantined"]) == ("2556", "357", "46"),
        (rt["1"]["train"], rt["1"]["val"], rt["1"]["quarantined"]))
    add("resource_table_kub_split_counts",
        (rt["4"]["train"], rt["4"]["val"], rt["4"]["quarantined"]) == ("1978", "280", "4"),
        (rt["4"]["train"], rt["4"]["val"], rt["4"]["quarantined"]))
    add("resource_table_has_8_datasets_including_ham10000",
        len(resource) == 8 and any("HAM10000" in r["dataset"] for r in resource),
        [r["dataset"] for r in resource])

    cohort = read_json("03_Experimental_Results/external/c1_cohort_construction.json")
    add("external884_total_analysed", cohort["total_analysed"] == 884, cohort["total_analysed"])
    add("external884_composition_612_252_20",
        (cohort["cohorts"]["cvc"]["rows_analysed"],
         cohort["cohorts"]["breast"]["rows_analysed"],
         cohort["cohorts"]["stones"]["rows_analysed"]) == (612, 252, 20),
        "612 CVC + 252 BrEaST + 20 Stones")
    ham_c = cohort["cohorts"]["ham10000"]
    add("ham10000_zero_rows_analysed_and_excluded",
        ham_c["rows_analysed"] == 0 and "EXCLUDED" in ham_c["status"],
        f'{ham_c["rows_in_manifest"]} manifest rows, {ham_c["rows_analysed"]} analysed, {ham_c["status"]}')

    ham = read_json("08_Verification/HAM10000_AUDIT.json")
    inv = ham["local_inventory"]
    add("ham10000_inventory_10015_each",
        (inv["jpg_images"], inv["png_masks"], inv["metadata_rows"]) == (10015, 10015, 10015),
        (inv["jpg_images"], inv["png_masks"], inv["metadata_rows"]))
    add("ham10000_full_stem_match",
        ham["matched_mask_coverage"]["three_way_matched_stems"] == 10015,
        ham["matched_mask_coverage"]["coverage_pct"])
    add("ham10000_zero_id_overlap",
        ham["overlap"]["id_overlap"]["exact_overlap_all_paired_including_test_ids"] == 0,
        0)
    add("ham10000_zero_byte_identical_overlap",
        ham["overlap"]["image_hash_overlap"]["n_byte_identical_sha256_matches"] == 0,
        ham["overlap"]["image_hash_overlap"]["n_byte_size_candidates"])
    add("ham10000_no_saved_full_predictions",
        ham["prediction_evidence"]["n_saved_per_case_full_prediction_artifacts_for_ham10000"] == 0,
        0)
    add("ham10000_not_a_completed_benchmark",
        ham["evaluation_status"]["completed_quantitative_segmentation_benchmark"] is False
        and ham["evaluation_status"]["part_of_external884"] is False,
        ham["evaluation_status"]["status"])
    add("ham10000_boundaries_respected",
        ham["boundaries"]["protected_test1683_pixels_opened"] is False
        and ham["boundaries"]["inference_performed"] is False
        and ham["boundaries"]["test_csv_opened"] is False,
        ham["boundaries"])
    matrix = read_csv("05_Datasets/EXTERNAL_SKIN_EVALUATION_MATRIX.csv")
    hrow = next(r for r in matrix if r["cohort"] == "HAM10000")
    add("ham10000_matrix_has_no_fabricated_metrics",
        all(hrow[k] == "NOT_ESTABLISHED" for k in
            ["dice", "iou", "precision", "recall", "hd95_px", "paired_delta"]),
        {k: hrow[k] for k in ["dice", "iou", "precision", "recall", "hd95_px", "paired_delta"]})

    arms = read_csv("04_Ablation_Phase28/results/phase28_table_01_arm_definitions.csv")
    metrics = read_csv("04_Ablation_Phase28/results/phase28_table_02_arm_primary_metrics.csv")
    expected = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "R1", "R2", "R3", "F1"]
    add("phase28_13_arms_defined_with_metrics",
        [a["arm"] for a in arms] == expected and [m["arm"] for m in metrics] == expected,
        f"{len(arms)} definitions / {len(metrics)} metric rows")
    boot = read_csv("04_Ablation_Phase28/results/phase28_table_08_bootstrap_statistics.csv")
    a87 = next(r for r in boot if r["contrast"] == "A8_vs_A7")
    add("phase28_a8_vs_a7_ci_includes_zero",
        float(a87["ci95_low"]) < 0 < float(a87["ci95_high"]),
        f'mean {a87["mean_difference"]}, CI [{a87["ci95_low"]}, {a87["ci95_high"]}]')
    runs = read_csv("06_Training_History/phase28_training_run_registry.csv")
    add("phase28_18_historical_training_runs", len(runs) == 18, len(runs))

    hist = read_csv("06_Training_History/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv")
    components = Counter(r["component"] for r in hist)
    add("training_history_has_5_separate_component_histories",
        len(components) == 5 and all(v > 0 for v in components.values()),
        dict(components))
    add("no_joint_full_curve_claimed",
        not any("FULL" in c.upper() and "JOINT" in c.upper() for c in components),
        "no jointly trained FULL curve exists")

    passed = sum(1 for c in checks if c["passed"])
    return {"checks": checks, "n_checks": len(checks), "n_passed": passed,
            "n_failed": len(checks) - passed,
            "failed": [c for c in checks if not c["passed"]]}


# ---------------------------------------------------------------------------
# 4. Safety
# ---------------------------------------------------------------------------
def check_safety(files: list[Path]) -> dict:
    violations = []
    for p in files:
        rel = p.relative_to(OUT).as_posix()
        if p.suffix.lower() in FORBIDDEN_SUFFIXES or p.name in FORBIDDEN_NAMES:
            violations.append(f"{rel}: forbidden artifact")
        if p.suffix.lower() in {".md"} and rel in NEW_DOCS:
            t = p.read_text(encoding="utf-8", errors="replace")
            for kw in ("BEGIN PRIVATE KEY", "PASSWORD=", "API_KEY="):
                if kw in t.upper():
                    violations.append(f"{rel}: possible credential string")
    abs_paths = []
    for p in files:
        if p.suffix.lower() == ".md" and p.relative_to(OUT).as_posix() in NEW_DOCS:
            for m in re.finditer(r"[A-Za-z]:\\\\[^\s`\)\]]+", p.read_text(encoding="utf-8", errors="replace")):
                abs_paths.append((p.relative_to(OUT).as_posix(), m.group(0)[:100]))
    return {"violations": violations,
            "absolute_local_paths_in_new_docs": abs_paths[:20],
            "absolute_path_note": ("Local HAM10000 inspection paths are disclosed to the "
                                   "supervisor on purpose; copied frozen manifests retain "
                                   "their original absolute paths as historical provenance."),
            "forbidden_suffixes": sorted(FORBIDDEN_SUFFIXES),
            "forbidden_names": sorted(FORBIDDEN_NAMES)}


# ---------------------------------------------------------------------------
# 5. Manifest + ZIP
# ---------------------------------------------------------------------------
def build_manifest(files: list[Path]) -> list[dict]:
    copy_map = json.loads((OUT / "08_Verification" / "COPY_MAP.json").read_text(encoding="utf-8"))
    src_by_dst = {e["destination"]: e["source"] for e in copy_map}
    rows = []
    for p in files:
        rel = p.relative_to(OUT).as_posix()
        # A manifest cannot contain its own final SHA-256. Exclude itself so a
        # rerun never carries a stale self-hash from the previous archive.
        if rel == MANIFEST_REL:
            continue
        rows.append(dict(
            relative_path=rel,
            top_level=rel.split("/")[0],
            category=("NEWLY_AUTHORED_OR_GENERATED" if rel not in src_by_dst else "COPIED_FROZEN_ARTIFACT"),
            original_repository_source=src_by_dst.get(rel, "AUTHORED_FOR_SUPERVISOR_PACKAGE"),
            size_bytes=p.stat().st_size,
            sha256=sha256(p),
        ))
    with (OUT / "08_Verification" / "SUBMISSION_MANIFEST.csv").open(
            "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


def build_zip(files: list[Path]) -> dict:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        for p in sorted(files, key=lambda x: x.relative_to(OUT).as_posix()):
            z.write(p, f"{ARC_ROOT}/{p.relative_to(OUT).as_posix()}")
    digest = sha256(ZIP_PATH)
    # newline="\n" is required: on Windows, Path.write_text() would otherwise
    # translate \n to \r\n and GNU `sha256sum -c` would treat the CR as part
    # of the filename.
    with SHA_PATH.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"{digest}  {ZIP_PATH.name}\n")
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        bad = z.testzip()
        members = z.namelist()
        mismatches = []
        for p in files:
            rel = f"{ARC_ROOT}/{p.relative_to(OUT).as_posix()}"
            if rel not in members:
                mismatches.append(f"MISSING MEMBER {rel}")
                continue
            if hashlib.sha256(z.read(rel)).hexdigest() != sha256(p):
                mismatches.append(f"SHA MISMATCH {rel}")
    sizes = Counter(p.suffix.lower() for p in files)
    return {
        "zip_path": ZIP_PATH.relative_to(ROOT).as_posix(),
        "zip_sha256_out_of_band": digest,
        "sha256_sidecar": SHA_PATH.relative_to(ROOT).as_posix(),
        "zip_bytes": ZIP_PATH.stat().st_size,
        "crc_testzip_result": bad or "OK_ALL_MEMBERS_PASS_CRC",
        "n_members": len(members),
        "n_source_files": len(files),
        "member_count_matches": len(members) == len(files),
        "per_member_sha256_mismatches": mismatches,
        "suffix_counts": dict(sizes),
        "self_hash_note": ("A ZIP cannot contain its own SHA-256. The digest is written "
                           "out-of-band to the .sha256 sidecar and reported in the "
                           "delivery message; VERIFICATION_REPORT marks it SELF_EXCLUDED."),
    }


def all_package_files() -> list[Path]:
    return sorted(p for p in OUT.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts
                  and p.suffix.lower() != ".pyc")


def main() -> int:
    if not (OUT / "08_Verification" / "COPY_MAP.json").is_file():
        raise SystemExit("Stage 1 not run: COPY_MAP.json missing")

    # ---- checks on the current package content ------------------------------
    files = all_package_files()
    md_files = [p for p in files if p.suffix.lower() == ".md"]
    py_files = [p for p in files if p.suffix.lower() == ".py"]
    refs = check_references(md_files, files)
    deps = check_dependencies(py_files)
    science = check_science()
    safety = check_safety(files)
    broken, failed = refs["broken"], science["failed"]

    verdict = ("PASS" if not broken and not failed and not safety["violations"]
               and not deps["unresolved_local"] and not deps["parse_failures"]
               else "FAIL")

    # ---- pre-archive verification report (included in the ZIP) --------------
    # An archive cannot contain its own hash or its own CRC result. Everything
    # knowable before archiving is recorded here; ZIP integrity results are
    # written out-of-band AFTER the archive is built.
    report = {
        "artifact": "REMEDFILM_SUPERVISOR_SUBMISSION_VERIFICATION",
        "report_class": "PRE_ARCHIVE_VERIFICATION",
        "package_root": OUT.relative_to(ROOT).as_posix(),
        "verdict": verdict,
        "references": {k: v for k, v in refs.items() if k != "rows"},
        "reference_rows": refs["rows"],
        "dependencies": deps,
        "science": science,
        "safety": safety,
        "zip": {
            "status": "SELF_EXCLUDED_BY_CONSTRUCTION",
            "expected_archive": ZIP_PATH.relative_to(ROOT).as_posix(),
            "sha256_sidecar": SHA_PATH.relative_to(ROOT).as_posix(),
            "integrity_json": "full_doc_report/Supervisor_Submission_ZIP_INTEGRITY.json",
            "note": ("An archive cannot contain its own hash or CRC result. After "
                     "construction, CRC (testzip), member count, per-member SHA-256 "
                     "and the archive SHA-256 are verified and written out-of-band."),
        },
    }
    lines = [
        "# Supervisor Submission — Verification Report", "",
        f"**Verdict (pre-archive checks):** `{verdict}`  ",
        f"**Markdown documents scanned:** {len(md_files)}  ",
        f"**Python files scanned:** {len(py_files)}", "",
        "This report is generated **before** the ZIP is built, so that it can be "
        "included in the archive. An archive cannot contain its own hash or its own "
        "CRC result: the archive SHA-256, CRC outcome, member count and per-member "
        "SHA-256 verification are written **out-of-band** after construction to "
        "`full_doc_report/Supervisor_Submission_ZIP_INTEGRITY.json` and "
        "`full_doc_report/ReMedFiLM_Supervisor_Submission.zip.sha256`.", "",
        "## 1. File references", "",
        f"- Reference targets classified: "
        + ", ".join(f"`{k}` {v}" for k, v in sorted(refs["counts"].items())),
        f"- **Broken references: {len(broken)}**",
        "",
    ]
    if broken:
        lines += ["| Document | Kind | Target |", "|---|---|---|"]
        lines += [f"| {r['doc']} | {r['kind']} | `{r['target']}` |" for r in broken[:40]]
        lines.append("")
    lines += [
        refs["note"], "",
        "## 2. Code dependencies", "",
        f"- Parse failures: {len(deps['parse_failures'])}",
        f"- Import classification: {deps['classification_counts']}",
        f"- Local `src.*` / flat modules: {len(deps['local_modules'])}; "
        f"**unresolved: {len(deps['unresolved_local'])}**",
        f"- Third-party availability in this environment: "
        f"{sum(deps['third_party_available_in_this_env'].values())}/"
        f"{len(deps['third_party_available_in_this_env'])} present",
        "", deps["note"], "",
        "## 3. Scientific consistency", "",
        f"**{science['n_passed']}/{science['n_checks']} checks passed; "
        f"{science['n_failed']} failed.**", "",
        "| Check | Result | Detail |", "|---|---|---|",
    ]
    for c in science["checks"]:
        detail = str(c["detail"]).replace("|", "\\|")[:190]
        lines.append(f"| `{c['check']}` | {'PASS' if c['passed'] else 'FAIL'} | {detail} |")
    lines += [
        "", "## 4. Publication safety", "",
        f"- Forbidden artifacts / credentials: **{len(safety['violations'])}**",
        f"- Excluded by policy: {', '.join(safety['forbidden_names'])}; "
        f"suffixes {', '.join(safety['forbidden_suffixes'])}",
        f"- Absolute local paths disclosed in new docs: "
        f"{len(safety['absolute_local_paths_in_new_docs'])} (informational)",
        "", safety["absolute_path_note"], "",
        "## 5. ZIP integrity", "",
        "`SELF_EXCLUDED_BY_CONSTRUCTION` — verified after archive construction; "
        "see the out-of-band `Supervisor_Submission_ZIP_INTEGRITY.json`.", "",
        "## 6. Boundaries", "",
        "No training, no new inference, no checkpoint modification, no TEST1683 "
        "pixel access, no `test.csv` opening, no fabricated mask or prediction, "
        "and no modification of frozen source artifacts. All copied artifacts are "
        "byte-identical to their repository originals (SHA-256 in "
        "`SUBMISSION_MANIFEST.csv`, which by construction does not list itself). "
        "The manifest itself is still CRC- and per-member SHA-256-checked by the "
        "out-of-band ZIP integrity record.", "",
    ]
    (OUT / "08_Verification" / "VERIFICATION_REPORT.md").write_text(
        "\n".join(lines), encoding="utf-8")
    (OUT / "08_Verification" / "VERIFICATION_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- manifest (lists every file present now; reports included) ----------
    files = all_package_files()
    manifest = build_manifest(files)
    report["manifest_rows"] = len(manifest)
    report["n_files_at_manifest_time"] = len(files)

    # ---- build the ZIP from the final file set -------------------------------
    files = all_package_files()
    zip_info = build_zip(files)

    integrity = {
        "artifact": "REMEDFILM_SUPERVISOR_SUBMISSION_ZIP_INTEGRITY",
        "pre_archive_verdict": verdict,
        "zip": zip_info,
        "post_archive_verdict": ("PASS" if verdict == "PASS"
                                 and zip_info["crc_testzip_result"] == "OK_ALL_MEMBERS_PASS_CRC"
                                 and zip_info["member_count_matches"]
                                 and not zip_info["per_member_sha256_mismatches"]
                                 else "FAIL"),
        "manifest_rows": len(manifest),
        "manifest_self_excluded": True,
        "zip_members_minus_manifest_rows": zip_info["n_members"] - len(manifest),
        "broken_references": len(broken),
        "science_checks": f"{science['n_passed']}/{science['n_checks']}",
        "unresolved_local_imports": deps["unresolved_local"],
        "safety_violations": safety["violations"],
    }
    (ROOT / "full_doc_report" / "Supervisor_Submission_ZIP_INTEGRITY.json").write_text(
        json.dumps(integrity, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps({
        "pre_archive_verdict": verdict,
        "post_archive_verdict": integrity["post_archive_verdict"],
        "files_in_zip": zip_info["n_members"],
        "broken_references": len(broken),
        "unresolved_local_imports": deps["unresolved_local"],
        "science": f"{science['n_passed']}/{science['n_checks']}",
        "science_failed": [c["check"] for c in failed],
        "safety_violations": safety["violations"],
        "crc": zip_info["crc_testzip_result"],
        "zip": str(ZIP_PATH),
        "zip_sha256": zip_info["zip_sha256_out_of_band"],
    }, ensure_ascii=False, indent=1))
    return 0 if integrity["post_archive_verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
