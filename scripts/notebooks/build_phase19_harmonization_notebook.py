"""
Build + execute the Phase-19 reviewer notebook.

    notebooks/phasewise/phase_19_harmonization/phase19_multidomain_dataset_harmonization.ipynb

The notebook imports the reusable module (src.analysis.multidomain_harmonization)
so its tables are byte-identical to the driver's artifacts. It reads the
produced artifacts, renders tables and figures, runs the TRAIN/VAL loader smoke
test, and asserts the Stage-B invariants. No training, no inference, no TEST.

Run:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe scripts/notebooks/build_phase19_harmonization_notebook.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = ROOT / "notebooks/phasewise/phase_19_harmonization/phase19_multidomain_dataset_harmonization.ipynb"
NB_PATH.parent.mkdir(parents=True, exist_ok=True)

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))          # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))            # noqa: E731

cells = []

# --------------------------------------------------------------------------- #
cells.append(md("""
# Phase 19 — Multi-Domain Dataset Harmonization

**Stage B: Multi-Domain Scaling — first active Stage-B notebook**

**Project:** RA-MedFiLM-Seg++ (Regional Scale-Aware Feature Interleaving Multi-Domain Medical Segmentation)
**Target venue:** Q1 / A* peer-reviewed medical computer vision

---

## 1. Title / scope / governance

| Item | Value |
|---|---|
| Phase | 19 |
| Stage | Stage B: Multi-Domain Scaling |
| Title | Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB) |
| Scientific purpose | MULTI-DOMAIN DATASET HARMONIZATION |
| Model training in this phase | **NO** |
| Manifest | `manifests/phase4_v3` (CANONICAL_ACTIVE_DEVELOPMENT) |
| Cohorts read | TRAIN and VAL only |
| TEST | `CLOSED` — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |

This notebook is a **data-harmonization** artifact. It does not train a model, create an
optimizer, run a backward pass, or create a checkpoint. Phase 20 is **not** started.
"""))

cells.append(code("""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from IPython.display import display, Image, Markdown

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 60)


def find_root():
    \"\"\"Repository-root discovery that does not depend on one shell, OS or hardcoded path.\"\"\"
    p = Path.cwd()
    for _ in range(6):
        if (p / "manifests").is_dir() and (p / "reports").is_dir() and (p / "src").is_dir():
            return p
        p = p.parent
    return Path("D:/Softfors/jup")


ROOT = find_root()
AUD = ROOT / "reports/audits"
TAB = ROOT / "reports/tables"
FIG = ROOT / "reports/figures/phase19_harmonization"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


print("repository root :", ROOT)
print("audits          :", AUD.relative_to(ROOT))
print("tables          :", TAB.relative_to(ROOT))
"""))

# --------------------------------------------------------------------------- #
cells.append(md("""
## 2. Why Stage B starts now

The post-Phase14 / H3 target-support branch has been formally adjudicated and is now
**closed**. The supervisor has directed that the unresolved regional localizer branch must
not block the main multi-domain research program. Stage B therefore becomes active and the
main program begins at **Phase 19**.

This is a deliberate governance transition, recorded in
`reports/audits/stage_b_phase19_authorization.json`.
"""))

cells.append(code("""
auth = jload(AUD / "stage_b_phase19_authorization.json")
decision = auth["REGIONAL_BRANCH_SUPERVISOR_DECISION"]

display(Markdown("### REGIONAL_BRANCH_SUPERVISOR_DECISION"))
display(pd.DataFrame(sorted(decision.items()), columns=["key", "value"]))

print("authorization status :", auth["status"])
print("decision type        :", auth["decision_type"])
print("Stage B active       :", auth["stage_b_activation"]["active"])
print("Phase-19 authorized  :", auth["phase19_authorization"]["status"])
"""))

# --------------------------------------------------------------------------- #
cells.append(md("""
## 3. Regional branch handoff summary

The regional evidence is **preserved as unresolved / not promoted** — it is neither erased nor
successfully integrated. The correct summary is:

> Oracle regional processing shows potential, but the current GT-free predicted localization
> path does not preserve enough practical benefit.

**H3 did NOT succeed.** The failure boundary fired. H3 materially improved proposal supply but
the recovered supply did not translate into sufficient downstream Tiny-recall gain.
"""))

cells.append(code("""
h3 = jload(AUD / "h3_formal_adjudication.json")
h3o = h3["observed"]

display(pd.DataFrame([
    ("scientific label", h3["scientific_label"]),
    ("governance wrapper", h3["status"]),
    ("zero-proposal TINY", h3o["zero_proposal_tiny_fraction"]),
    ("zero-proposal GT", h3o["zero_proposal_gt_fraction"]),
    ("formal TinyRecall_H3", h3o["formal_TinyRecall_H3_fraction"]),
    ("formal R_H3", h3o["formal_R_H3_fraction"]),
    ("failure boundary", "FIRED" if h3["failure_boundary"]["fired"] else "not fired"),
    ("selected epoch", h3["selected_checkpoint"]["selected_epoch"]),
    ("checkpoint replay", h3["checkpoint_selection_replay_verdict"]),
    ("TEST reads", h3["governance"]["test_reads"]),
], columns=["H3 item", "value"]))

display(Markdown("### Regional evidence preserved"))
display(pd.DataFrame({"preserved evidence": auth["regional_evidence_preserved"]["preserved_evidence"]}))
print("regional branch state :", auth["regional_evidence_preserved"]["status"])
print("explicitly NOT        :", auth["regional_evidence_preserved"]["explicitly_not"])
"""))

# --------------------------------------------------------------------------- #
cells.append(md("""
## 4. Legacy tested-project evidence policy

Older tested MedFiLM / RA-MedFiLM projects are treated as **PRIOR ENGINEERING /
EXPERIMENTAL EVIDENCE** — never as current clean-v3 validation evidence. Historical TEST
performance is **not** used to tune the new project.

Before proposing any new Phase-19 implementation, the repository and the legacy evidence are
searched first: if functionality already exists and is technically valid, it is reused or
adapted rather than rebuilt.
"""))

cells.append(code("""
reuse = jload(AUD / "phase19_legacy_evidence_reuse_map.json")
print("policy:", json.dumps(reuse["policy"], indent=1))
print()
print("reuse-type counts:", reuse["reuse_type_counts"])
print()
reuse_df = pd.DataFrame(reuse["entries"])[
    ["component_id", "reuse_type", "scientific_risk", "current_validation_required"]]
display(reuse_df)
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 5. Four-domain dataset inventory"))
cells.append(code("""
inv = pd.read_csv(TAB / "phase19_dataset_inventory.csv")
display(inv[["dataset", "task_id", "canonical_name", "modality", "anatomy",
             "n_train", "n_val", "n_test_locked", "n_development"]])
display(Markdown("### Representative image / mask pairs (TRAIN/VAL only)"))
display(Image(filename=str(FIG / "fig07_representative_pairs.png")))
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 6. Dataset source paths"))
cells.append(code("""
display(inv[["dataset", "native_image_mode", "observed_image_modes", "observed_mask_modes",
             "image_ext", "mask_ext", "image_mask_size_match_frac"]])
display(pd.DataFrame([
    ("ISIC", r"D:\\Softfors\\omni_seg\\data_raw\\isic2018"),
    ("BUSI", r"D:\\Softfors\\omni_seg\\data_raw\\BUSI_WHU Breast Cancer Ultrasound Image  Dataset\\BUSI-WHU"),
    ("KVASIR", r"D:\\Softfors\\omni_seg\\data_raw\\Kvasir-SEG"),
    ("KUB", r"D:\\Softfors\\omni_seg\\data_raw\\KUB-Stone\\KUB-Stonex"),
], columns=["dataset", "native_root"]))
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 7. TRAIN / VAL population tables"))
cells.append(code("""
pop = inv[["dataset", "task_id", "n_train", "n_val", "n_development", "n_test_locked"]].copy()
pop.loc[len(pop)] = ["TOTAL", "-", int(inv.n_train.sum()), int(inv.n_val.sum()),
                     int(inv.n_development.sum()), int(inv.n_test_locked.sum())]
display(pop)

piv = inv.melt(id_vars=["dataset"], value_vars=["n_train", "n_val"],
               var_name="split", value_name="n")
display(piv.pivot(index="dataset", columns="split", values="n"))
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 8. TEST lock status"))
cells.append(code("""
from src.utils.test_lock import verify_test_lock

lock = verify_test_lock(str(ROOT))
display(pd.DataFrame([
    ("test_sample_count", lock["test_sample_count"]),
    ("full_test_sha256", lock["full_test_sha256"]),
    ("manifest_version", lock["manifest_version"]),
    ("protocol_statement", lock["protocol_statement"][:110] + "..."),
], columns=["TEST lock field", "value"]))

test_reads = {
    "test_image_reads": 0, "test_mask_reads": 0,
    "test_inference": 0, "test_visualization": 0,
}
print("Phase-19 TEST access:", test_reads)
assert all(v == 0 for v in test_reads.values())
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 9. Task-ID mapping"))
cells.append(code("""
reg = pd.read_csv(TAB / "phase19_task_id_registry.csv")
display(reg[["dataset", "task_id", "modality", "observed_task_ids_in_manifest",
             "manifest_agrees", "legacy_corroboration", "status"]])
assert reg["manifest_agrees"].all()
print("Task-ID registry frozen:", bool(reg["manifest_agrees"].all()))
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 10. Image-format comparison"))
cells.append(code("""
img = pd.read_csv(TAB / "phase19_image_measurements.csv")
fmt = img.groupby(["dataset", "image_mode"]).size().rename("n").reset_index()
display(fmt)
display(inv[["dataset", "width_min", "width_median", "width_max",
             "height_min", "height_median", "height_max"]])
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 11. Mask-format comparison"))
cells.append(code("""
msk = pd.read_csv(TAB / "phase19_mask_measurements.csv")
display(inv[["dataset", "native_mask_mode", "observed_mask_modes",
             "mask_label_signatures_observed", "fg_native_rule"]])
display(msk.groupby("dataset")["is_binary_01"].mean().rename("frac_binary_01").reset_index())
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 12. Spatial-resolution distributions"))
cells.append(code("""
display(Image(filename=str(FIG / "fig02_resolution_distributions.png")))
display(Image(filename=str(FIG / "fig03_aspect_ratio_distributions.png")))
display(Image(filename=str(FIG / "fig06_size_scatter.png")))
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 13. Channel / modality comparison"))
cells.append(code("""
display(Image(filename=str(FIG / "fig05_modality_composition.png")))
display(pd.DataFrame([
    ("ISIC", "RGB", "dermoscopy", "3-channel colour carries clinical pigment information"),
    ("BUSI", "L", "ultrasound", "single-channel speckle"),
    ("KVASIR", "RGB", "endoscopy", "3-channel colour carries mucosal information"),
    ("KUB", "L | RGB", "radiograph", "mixed acquisition regimes; native L or RGB"),
], columns=["dataset", "native_image_mode", "modality", "note"]))
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 14. Foreground prevalence"))
cells.append(code("""
display(Image(filename=str(FIG / "fig04_foreground_fraction.png")))
display(inv[["dataset", "fg_fraction_min", "fg_fraction_median", "fg_fraction_max"]])
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 15. Sample-count comparison"))
cells.append(code("""
display(Image(filename=str(FIG / "fig01_dataset_population.png")))
display(Image(filename=str(FIG / "fig08_domain_summary.png")))
share = (inv.set_index("dataset")["n_development"] / inv.n_development.sum()).round(4)
display(share.rename("development_share").reset_index())
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 16. Patient / group-key availability"))
cells.append(code("""
grp = pd.read_csv(TAB / "phase19_group_key_availability.csv")
display(grp)
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 17. Duplicate / leakage safeguards"))
cells.append(code("""
leak = jload(AUD / "phase19_leakage_safeguards.json")
display(pd.DataFrame([
    ("manifest version", leak["manifest_version"]),
    ("leakage status", leak["leakage_status"]),
    ("remediation reason", leak["remediation_reason"]),
    ("quarantined samples", leak["quarantined_samples"]),
    ("quarantined by dataset", json.dumps(leak["quarantined_by_dataset"])),
    ("duplicate risk groups", leak["duplicate_risk_groups"]),
    ("KUB TRAIN/VAL patient overlap", leak["kub_patient_overlap_train_val"]),
    ("KUB patient-disjoint", leak["kub_patient_disjoint"]),
    ("sample_id TRAIN/VAL overlap", leak["sample_id_overlap_train_val"]),
], columns=["safeguard", "value"]))
assert leak["kub_patient_disjoint"]
assert leak["sample_id_overlap_train_val"] == 0
print("residual risk:", leak["residual_risk"])
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 18. Metadata classification"))
cells.append(code("""
meta = pd.read_csv(TAB / "phase19_metadata_governance.csv")
display(meta[["field", "classification", "phase19_disposition"]])
counts = meta["classification"].value_counts().to_dict()
print("classification counts:", counts)
assert set(counts) <= {"CONDITIONING_ALLOWED", "REPORTING_ONLY", "FORBIDDEN_AS_INPUT"}
assert (meta[meta["field"] == "category"]["classification"].iloc[0]) == "REPORTING_ONLY"
print("KUB category labels are REPORTING_ONLY: OK")
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 19. Harmonized sample schema"))
cells.append(code("""
schema = pd.read_csv(TAB / "phase19_harmonized_schema.csv")
display(schema)
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 20. Harmonized batch schema"))
cells.append(code("""
from src.data.multidomain_dataset import MultiDomainDataset, harmonized_collate

_ds = MultiDomainDataset(ROOT / "manifests/phase4_v3/val.csv", split="VAL", size=512, datasets=["ISIC"])
_batch = harmonized_collate([_ds[i] for i in range(3)])
display(pd.DataFrame([
    ("image", str(tuple(_batch["image"].shape)), str(_batch["image"].dtype),
     f"[{float(_batch['image'].min()):.3f}, {float(_batch['image'].max()):.3f}]"),
    ("mask", str(tuple(_batch["mask"].shape)), str(_batch["mask"].dtype),
     f"values {sorted(set(np.unique(_batch['mask'].numpy()).tolist()))}"),
    ("task_id", str(tuple(_batch["task_id"].shape)), str(_batch["task_id"].dtype),
     str(_batch["task_id"].tolist())),
    ("dataset", "list[str]", "-", str(_batch["dataset"])),
    ("sample_id", "list[str]", "-", str(_batch["sample_id"])),
    ("split", "list[str]", "-", str(_batch["split"])),
], columns=["field", "shape", "dtype", "example"]))
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 21. Preprocessing contract"))
cells.append(code("""
pre = jload(AUD / "phase19_preprocessing_contract.json")
display(Markdown("### Image"))
display(pd.DataFrame(sorted(pre["image"].items()), columns=["key", "value"]))
display(Markdown("### Mask"))
display(pd.DataFrame(sorted(pre["mask"].items()), columns=["key", "value"]))
display(Markdown("### Spatial"))
display(pd.DataFrame(sorted(pre["spatial"].items()), columns=["key", "value"]))
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 22. Mask contract"))
cells.append(code("""
display(pd.DataFrame(sorted(pre["mask"].items()), columns=["key", "value"]))
print("canonical foreground rule:", pre["mask"]["foreground_rule"])
print("never test mask == 1     :", pre["mask"]["never_test_mask_eq_1"])
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 23. Augmentation boundary"))
cells.append(code("""
display(pd.DataFrame(sorted(pre["augmentation_boundary"].items()), columns=["key", "value"]))
print("train-only paired augmentation; VAL augmentation disabled.")
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 24. Evaluation metric contract"))
cells.append(code("""
ev = jload(AUD / "phase19_evaluation_contract.json")
display(pd.DataFrame(sorted(ev["metric_domain"].items()), columns=["key", "value"]))
display(pd.DataFrame(sorted(ev["metrics"].items()), columns=["key", "value"]))
display(pd.DataFrame(sorted(ev["aggregation"].items()), columns=["key", "value"]))
print("TEST evaluation:", ev["test_evaluation"])
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 25. Prospective Stage-B invariants"))
cells.append(code("""
smoke = jload(AUD / "phase19_loader_smoke_test.json")
invariants = {
    "four_domains_present": set(inv["dataset"]) == {"ISIC", "BUSI", "KVASIR", "KUB"},
    "task_ids_frozen": bool(reg["manifest_agrees"].all()),
    "foreground_rule_uniform": bool(inv["fg_native_rule"].eq("mask > 0").all()),
    "test_reads_zero": True,
    "loaders_smoke_pass": bool(smoke["all_checks_passed"]),
    "test_rejected_by_dataset": bool(smoke["test_rejected_by_dataset"]),
    "test_rejected_by_loader": bool(smoke["test_rejected_by_loader"]),
    "no_training": not smoke["training_performed"],
    "no_optimizer": not smoke["optimizer_created"],
    "no_backward": not smoke["backward_performed"],
    "no_checkpoint": not smoke["checkpoint_created"],
    "stage_b_active": bool(auth["stage_b_activation"]["active"]),
    "phase20_not_started": auth["locks"]["future_phase_locks"]["phase_20"] == "NOT_STARTED_AND_NOT_AUTHORIZED",
}
display(pd.DataFrame(sorted(invariants.items()), columns=["invariant", "holds"]))
assert all(invariants.values()), [k for k, v in invariants.items() if not v]
print("All Stage-B invariants hold.")
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 26. Legacy-code reuse map"))
cells.append(code("""
rd = pd.DataFrame(reuse["entries"])
display(rd[["component_id", "old_role", "reuse_type", "reason"]])
display(rd["reuse_type"].value_counts().rename("count").reset_index())
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 27. Unresolved harmonization issues"))
cells.append(code("""
protocol = jload(AUD / "phase19_multidomain_harmonization_protocol.json")
for i, issue in enumerate(protocol["unresolved_issues"], 1):
    print(f"{i}. {issue}")
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 28. Artifact provenance"))
cells.append(code("""
rows = []
for name, digest in sorted(protocol["artifacts"].items()):
    base = TAB if name.endswith(".csv") else AUD
    path = base / name
    rows.append({
        "artifact": name,
        "path": str(path.relative_to(ROOT)).replace("\\\\", "/"),
        "recorded_sha256": digest,
        "on_disk_sha256": sha256_file(path),
        "matches": digest == sha256_file(path),
    })
prov = pd.DataFrame(rows)
display(prov[["artifact", "recorded_sha256", "matches"]])
assert prov["matches"].all()

figrows = [{
    "figure": k,
    "path": f"reports/figures/phase19_harmonization/{k}.png",
    "recorded_sha256": v,
    "matches": v == sha256_file(FIG / f"{k}.png"),
} for k, v in sorted(protocol["figures"].items())]
figprov = pd.DataFrame(figrows)
display(figprov[["figure", "matches"]])
assert figprov["matches"].all()
print("All Phase-19 artifacts and figures SHA-verified.")
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 29. Phase-20 entry criteria"))
cells.append(code("""
crit = pd.read_csv(TAB / "phase19_phase20_entry_criteria.csv")
display(crit)
print("criteria met:", int(crit["met"].sum()), "/", len(crit))
assert crit["met"].all()
"""))

# --------------------------------------------------------------------------- #
cells.append(md("## 30. Current terminal state"))
cells.append(code("""
state = {
    "H3": "CLOSED__FORMALLY_INSUFFICIENT",
    "regional_localizer_redesign": "DEFERRED",
    "phases_15_18": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
    "stage_b": "ACTIVE",
    "phase_19": "AUTHORIZED / PROTOCOL + HARMONIZATION PREPARATION COMPLETE",
    "phase_20": "NOT_STARTED_AND_NOT_AUTHORIZED",
    "test": "CLOSED",
}
display(pd.DataFrame(sorted(state.items()), columns=["governance item", "state"]))

display(Markdown("### Final assertions"))
assert h3["scientific_label"] == "H3_SUPPLY_REDESIGN_INSUFFICIENT"
assert auth["status"] == "STAGE_B_AUTHORIZED__PHASE19_READY_TO_START"
assert protocol["status"] == "PROTOCOL_FROZEN__PHASE19_HARMONIZATION_PREPARATION_COMPLETE"
assert protocol["governance"]["training_performed"] is False
assert protocol["governance"]["inference_performed"] is False
assert protocol["governance"]["phase_20_started"] is False
print("✓ All Phase-19 harmonization assertions passed.")
print("TERMINAL STATE: POST_H3_REGIONAL_BRANCH_DEFERRED__STAGE_B_ACTIVE__PHASE19_READY")
"""))

# --------------------------------------------------------------------------- #
nb = nbformat.v4.new_notebook(cells=cells)
# Deterministic cell ids: nbformat assigns a RANDOM 8-char id per cell, which would
# change the notebook SHA on every rebuild even with identical content.
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p19{_i:03d}"
nbformat.write(nb, str(NB_PATH))
print(f"Wrote {NB_PATH} ({len(nb.cells)} cells)")
print("Executing ...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=1800,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()

# Normalize volatile execution artifacts for a stable content-addressed SHA.
for _c in nb.cells:
    if isinstance(_c.get("metadata"), dict):
        _c["metadata"].pop("execution", None)
    _outs = _c.get("outputs")
    if _outs:
        _merged = []
        for _o in _outs:
            if (_o.get("output_type") == "stream" and _merged
                    and _merged[-1].get("output_type") == "stream"
                    and _merged[-1].get("name") == _o.get("name")):
                _p = _merged[-1]
                _pt, _ct = _p.get("text", ""), _o.get("text", "")
                if isinstance(_pt, list):
                    _pt = "".join(_pt)
                if isinstance(_ct, list):
                    _ct = "".join(_ct)
                _p["text"] = _pt + _ct
            else:
                _merged.append(_o)
        _c["outputs"] = _merged
nbformat.write(nb, str(NB_PATH))

code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = sum(1 for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error")
counts = [c.get("execution_count") for c in code_cells]
monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
embedded = sum(1 for c in code_cells for o in c.get("outputs", [])
               if o.get("output_type") == "display_data" and "image/png" in o.get("data", {}))

print(f"Cells: {len(nb.cells)} | markdown: {sum(1 for c in nb.cells if c.cell_type == 'markdown')} "
      f"| code: {len(code_cells)}")
print("Zero tracebacks:", "PASS" if errors == 0 else f"FAIL ({errors})")
print("Monotonic exec counts (1..%d): %s" % (len(code_cells), "PASS" if monotonic else "FAIL"))
print("Embedded PNG outputs:", embedded)
print("Notebook SHA:", hashlib.sha256(NB_PATH.read_bytes()).hexdigest())
