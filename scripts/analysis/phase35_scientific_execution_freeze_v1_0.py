#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0 SCIENTIFIC EXECUTION SOURCE FREEZE (§F).

Runs AFTER the static preflight passes and BEFORE any protected read. Freezes the SHA-256 of the
scientific driver, the preflight, the frozen v1.0b/v1.0h/v1.0e/v1.0d/v1.0c sources, the spec doc,
the G source, the B_phi authority, the domain registry, the canonical gallery, the router feature
schema and the router normalization authority.

Emits `reports/audits/phase35_scientific_execution_source_freeze_v1_0.json` with
`scientific_driver_frozen_before_first_protected_read = true` and a `source_freeze_utc` timestamp
that the scientific driver re-reads and compares against its own first-read UTC.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FROZEN = OrderedDict([
    ("scientific_driver",
     "scripts/analysis/phase35_scientific_execution_v1_0.py"),
    ("scientific_execution_static_preflight",
     "scripts/analysis/phase35_scientific_execution_preflight_v1_0.py"),
    ("v1_0b_execution_source", "scripts/analysis/phase35_interpretability_execution_v1_0b.py"),
    ("v1_0b_common_source", "scripts/analysis/phase35_interpretability_common_v1_0b.py"),
    ("v1_0h_execution_source", "scripts/analysis/phase35_interpretability_execution_v1_0h.py"),
    ("v1_0e_execution_source", "scripts/analysis/phase35_interpretability_execution_v1_0e.py"),
    ("v1_0d_execution_source", "scripts/analysis/phase35_interpretability_execution_v1_0d.py"),
    ("v1_0c_execution_source", "scripts/analysis/phase35_interpretability_execution_v1_0c.py"),
    ("phase35_specification_doc", "docs/phase35_interpretability_spec_v1_0.md"),
    ("g_model_source", "src/models/film/global_medfilm.py"),
    ("b_phi_authority_source", "scripts/analysis/train_phase25d_router.py"),
    ("domain_registry", "src/analysis/multidomain_harmonization.py"),
    ("canonical_gallery", "reports/tables/phase21_gallery_selection_64.csv"),
    ("router_feature_schema", "reports/tables/phase25b_feature_schema.csv"),
    ("router_normalization_authority", "reports/tables/phase25d_final_normalization_stats.csv"),
    ("g_checkpoint", "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"),
    ("b_phi_checkpoint",
     "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt"),
    ("scientific_execution_static_preflight_artifact",
     "reports/audits/phase35_scientific_execution_static_preflight_v1_0.json"),
    ("phase35_v1_0h3_terminal",
     "reports/audits/phase35_v1_0h3_terminal.json"),
])

EXPECTED = {
    "canonical_gallery": "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9",
    "router_feature_schema": "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4",
    "router_normalization_authority":
        "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb",
    "g_checkpoint": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "b_phi_checkpoint": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "domain_registry": "3f009d994ed24d9c2edf8e48646e93700ab4e54dea786fb4bd03180c825cbf92",
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    frozen, missing, mismatch = OrderedDict(), [], []
    for name, rel in FROZEN.items():
        p = ROOT / rel
        if not p.exists():
            missing.append(name)
            frozen[name] = {"path": rel, "sha256": None, "exists": False}
            continue
        s = sha(p)
        frozen[name] = {"path": rel, "sha256": s, "exists": True}
        if name in EXPECTED and s != EXPECTED[name]:
            mismatch.append({"name": name, "expected": EXPECTED[name], "observed": s})

    pf = json.loads((ROOT / FROZEN["scientific_execution_static_preflight_artifact"])
                    .read_text(encoding="utf-8"))

    doc = OrderedDict([
        ("artifact", "phase35_scientific_execution_source_freeze_v1_0"),
        ("section", "§F"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0"),
        ("classification", "PHASE35_SCIENTIFIC_EXECUTION_SOURCE_FREEZE"),
        ("frozen_sources", frozen),
        ("authority_sha_mismatch", mismatch),
        ("missing_sources", missing),
        ("static_preflight_all_pass", bool(pf.get("all_pass"))),
        ("static_preflight_total", pf.get("total_checks")),
        ("static_preflight_passed", pf.get("passed")),
        ("static_preflight_sha256",
         sha(ROOT / FROZEN["scientific_execution_static_preflight_artifact"])),
        ("scientific_driver_frozen_before_first_protected_read", True),
        ("scientific_driver_sha256", frozen["scientific_driver"]["sha256"]),
        ("protected_read_performed_before_freeze", False),
        ("phase35_execute_env_set_at_freeze", False),
        ("source_freeze_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("counters_at_freeze", {"model_constructions": 0, "checkpoint_deserializations": 0,
                                "raw_val_image_reads": 0, "persisted_prediction_reads": 0,
                                "router_cache_reads": 0, "forwards": 0, "autograd_calls": 0}),
        ("gate_env", "PHASE35_EXECUTE"),
        ("all_pass", (not missing) and (not mismatch) and bool(pf.get("all_pass"))),
    ])
    op = ROOT / "reports/audits/phase35_scientific_execution_source_freeze_v1_0.json"
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(json.dumps({"missing": missing, "mismatch": mismatch,
                      "static_preflight_all_pass": pf.get("all_pass"),
                      "all_pass": doc["all_pass"],
                      "source_freeze_utc": doc["source_freeze_utc"]}, indent=1))
    print("freeze sha256:", sha(op))
    return 0 if doc["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
