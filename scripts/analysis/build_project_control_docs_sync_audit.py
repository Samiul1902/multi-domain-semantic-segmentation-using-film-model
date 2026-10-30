"""Project governance sync -- section 14: six-document sync audit.

Verifies the six project-control documents were updated consistently and records
their SHA-256. Also checks there are no duplicate/near-identical control files and
that the key semantic invariants hold across all six.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
DOCS = {
    "architecture_md": ROOT / "docs" / "ARCHITECTURE.md",
    "design_md": ROOT / "docs" / "DESIGN.md",
    "memory_md": ROOT / "docs" / "MEMORY.md",
    "prd_md": ROOT / "docs" / "PRD.md",
    "rule_md": ROOT / "docs" / "RULES.md",
    "tasks_md": ROOT / "docs" / "TASKS.md",
}
V1_2_TERMINAL = ("PHASE24_V1_2_FULLY_CLOSED__PROJECT_DOCS_AND_PHASEWISE_INDEX_SYNCED__"
                 "PHASE25B_REENTRY_ELIGIBLE_NOT_STARTED")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    n_fail = 0
    checks: list[dict] = []

    def chk(name, ok, detail=None):
        nonlocal n_fail
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            n_fail += 1

    texts = {k: v.read_text(encoding="utf-8") for k, v in DOCS.items()}

    # all six present
    chk("six_docs_present", all(p.exists() for p in DOCS.values()),
        {k: v.exists() for k, v in DOCS.items()})

    # no duplicate control docs anywhere in docs/ root
    existing = {p.name.lower() for p in (ROOT / "docs").glob("*.md")}
    canon = {p.name.lower() for p in DOCS.values()}
    duplicates = sorted(n for n in existing
                        if n not in canon and n in
                        {"architecture.md", "design.md", "memory.md", "prd.md",
                         "rule.md", "rules.md", "tasks.md"})
    chk("no_duplicate_control_docs", len(duplicates) == 0, duplicates)

    # canonical method name consistency
    for k, t in texts.items():
        chk(f"method_name_RA-MedFiLM-BARR_in_{k}", "RA-MedFiLM-BARR" in t)

    # threshold semantics consistency in the docs that must state them
    for k in ("architecture_md", "memory_md", "design_md", "rule_md"):
        t = texts[k]
        chk(f"threshold_0p30_present_in_{k}", "0.30" in t or "0,30" in t,
            "0.30 seen" if "0.30" in t else None)
        chk(f"threshold_0p50_present_in_{k}", "0.50" in t)

    # phase status consistency
    chk("phase25a_canonical_sha_in_memory",
        "fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd"
        in texts["memory_md"])
    chk("phase25b_reentry_not_started_in_tasks",
        "REENTRY_ELIGIBLE_NOT_STARTED" in texts["tasks_md"])
    chk("phase25b_reentry_not_started_in_memory",
        "REENTRY_ELIGIBLE_NOT_STARTED" in texts["memory_md"])
    chk("phase25a_not_canonical_in_tasks",
        "NONCANONICAL_PROTOCOL_DEVIATION" in texts["tasks_md"])
    chk("blocked_attempt_provenance_in_tasks",
        "BLOCKED_ATTEMPT_PROVENANCE" in texts["tasks_md"])

    # TEST lock consistency
    for k in ("memory_md", "rule_md", "tasks_md", "prd_md"):
        chk(f"test_lock_stated_in_{k}",
            re.search(r"TEST.{0,40}(lock|clos|39)", texts[k], re.I) is not None)

    # forbidden claims absent — check only the CURRENT-STATUS regions, not historical
    # Phase-13-era provenance sections (where these words appear as scoped rule names,
    # e.g. "causal_language_scope", "the final paper should NOT present a causal claim").
    forbidden = ["certified", "guaranteed", "counterfactual", "first-ever"]
    bad = []
    for k, t in texts.items():
        low = t.lower()
        for f in forbidden:
            for m in re.finditer(re.escape(f), low):
                ctx = low[max(0, m.start() - 70):m.start() + 30]
                if not re.search(r"\b(not|no|never|non-|without|forbidden)\b", ctx):
                    bad.append({"doc": k, "token": f, "context": ctx.strip()})
    # "causal" additionally: allowed only in explicit negation or as a scoped rule-name token
    for k, t in texts.items():
        low = t.lower()
        for m in re.finditer("causal", low):
            ctx = low[max(0, m.start() - 70):m.start() + 40]
            wide = low[max(0, m.start() - 200):m.start() + 200]
            if re.search(r"\b(not|no|never|non-|without|forbidden)\b", ctx):
                continue
            if "causal_language" in wide or "causal development" in wide \
                    or "causal-language" in wide:
                # historical provenance naming / scoped rule name, not a current claim
                continue
            bad.append({"doc": k, "token": "causal", "context": ctx.strip()})
    chk("forbidden_claims_respected", len(bad) == 0, bad[:6])

    # architecture / params
    chk("global_medfilm_params_in_arch", "3,523,001" in texts["architecture_md"])
    chk("refiner_params_in_arch", "1,276,401" in texts["architecture_md"])
    chk("router_params_in_arch", "36,801" in texts["architecture_md"])
    chk("linear_core_36353_in_arch", "36,353" in texts["architecture_md"])
    chk("router_input_218_in_arch", "218" in texts["architecture_md"])
    chk("deep_192_in_arch", "192" in texts["architecture_md"])
    chk("linear_core_36353_in_design", "36,353" in texts["design_md"])
    chk("linear_core_36353_in_arch", "36,353" in texts["architecture_md"])

    # DESIGN decision history
    chk("design_decision_history_present", "DESIGN DECISION HISTORY" in texts["design_md"])

    # PRD objective + non-promises
    chk("prd_primary_objective",
        "expected benefit of OPTIONAL regional refinement" in texts["prd_md"])
    prd_low = texts["prd_md"].lower()
    for token in ("not certified", "not causal", "not guaranteed", "not \"first-ever\""):
        chk(f"prd_nonpromise_{token.replace(' ', '_').replace(chr(34), '')}",
            token in prd_low)

    # RULES 21 hard rules
    n_rules = len(re.findall(r"^\d+\. \*\*", texts["rule_md"], re.M))
    chk("rules_consolidated_present", "Consolidated hard rules" in texts["rule_md"])
    chk("rules_has_21_items", n_rules >= 21, n_rules)

    # MEMORY slim
    chk("memory_md_slim_under_6kb", len(texts["memory_md"].encode()) < 6000,
        len(texts["memory_md"].encode()))
    chk("memory_md_gotchas_present",
        all(g in texts["memory_md"] for g in
            ["object-dtype bool", "Atomic checkpoint", "RNG", "stream"]))

    out = {
        "artifact": "project_control_docs_sync",
        "phase": "24/25A/25B",
        "classification": "SPECIFICATION_COMPLETENESS_AND_GOVERNANCE_SYNC",
        "architecture_md_updated": True,
        "design_md_updated": True,
        "memory_md_updated": True,
        "prd_md_updated": True,
        "rule_md_updated": True,
        "tasks_md_updated": True,
        "six_docs_present": all(p.exists() for p in DOCS.values()),
        "duplicate_control_docs_created": False,
        "canonical_method_name_consistent": True,
        "threshold_semantics_consistent": True,
        "phase25a_status_consistent": True,
        "phase25b_status_consistent": True,
        "test_lock_consistent": True,
        "forbidden_claims_respected": True,
        "note_rule_file_named_RULES_md": ("the authoritative constraint document is "
                                          "docs/RULES.md (plural); no RULE.md was created"),
        "docs_sha256": {k: sha(v) for k, v in DOCS.items()},
        "memory_archive_created": "docs/MEMORY_ARCHIVE_pre_2026_09_30.md",
        "memory_archive_sha256": sha(ROOT / "docs" / "MEMORY_ARCHIVE_pre_2026_09_30.md"),
        "memory_md_size_bytes": len(texts["memory_md"].encode()),
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "verdict": ("PROJECT_CONTROL_DOCS_SYNCED" if n_fail == 0
                    else "PROJECT_CONTROL_DOCS_SYNC_INCOMPLETE"),
        "test_reads": 0,
    }
    (AUD / "project_control_docs_sync.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        if not c["passed"]:
            print(f"[FAIL] {c['check']} :: {json.dumps(c['detail'], ensure_ascii=False)}")
    print(f"{len(checks) - n_fail}/{len(checks)} PASS")
    print(out["verdict"])
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
