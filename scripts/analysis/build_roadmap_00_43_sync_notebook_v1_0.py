#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build + execute the reviewer notebook for the RA-MedFiLM-BARR Canonical 00-43
Roadmap + Six-Major-File Governance Synchronization.

Read-only display / audit artifact. Never modifies any artifact, never touches
TEST, never runs the Phase35 smoke or Phase36.

Representation: EXECUTED_WITH_PERSISTED_OUTPUTS.
"""

import hashlib
import json
import os
from collections import OrderedDict

import nbformat
from nbclient import NotebookClient

REPO = r"D:\Softfors\jup"
OUT_NB = os.path.join(
    REPO, "notebooks", "phasewise", "phase_35_interpretability",
    "roadmap_00_43_documentation_sync_v1_0_review.ipynb")
AUDIT_DIR = os.path.join(REPO, "reports", "audits")

CANON = OrderedDict([
    ("docs/ARCHITECTURE.md", "8fffa4e2"),
    ("docs/DESIGN.md", "9e9f08dc"),
    ("docs/MEMORY.md", "bc7de701"),
    ("docs/PRD.md", "1489b07e"),
    ("docs/RULES.md", "f0dc805b"),
    ("docs/TASKS.md", "74c1d942"),
    ("PROJECT_MASTER_PLAN.md", "f67b31c7"),
])


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def md(t):
    return nbformat.v4.new_markdown_cell(t)


def code(t):
    return nbformat.v4.new_code_cell(t)


cells = []

cells.append(md(
    "# RA-MedFiLM-BARR — Canonical 00-43 Roadmap + Six-Major-File Governance Synchronization\n"
    "\n"
    "**Revision:** `RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0__00_TO_43`  \n"
    "**Scope:** DOCUMENTATION / GOVERNANCE ONLY (`science_changed = false`).  \n"
    "**Representation:** `EXECUTED_WITH_PERSISTED_OUTPUTS` (read-only review).\n"
    "\n"
    "This notebook reviews the additive synchronization of the six canonical major files "
    "(`docs/ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/MEMORY.md`, `docs/PRD.md`, `docs/RULES.md`, "
    "`docs/TASKS.md`) plus `PROJECT_MASTER_PLAN.md`. It verifies the original 00-40 / 41-phase "
    "scientific roadmap is **preserved verbatim** and that the new content is **appended only**.\n"
    "\n"
    "It performs **no** scientific execution, does **not** run the Phase35 v1.0f smoke, does "
    "**not** start Phase36, and never reads TEST."
))

cells.append(md("## 1. Pre-update → post-update file hashes"))

cells.append(code(
    ("import hashlib, os, json\n"
     "REPO = r'__REPO__'\n"
     "PRE = {\n"
     "  'docs/ARCHITECTURE.md':'49433f24ac45cfee5f13d346264de4d3d717b52ca5a86290df8a6fc3b0ce1a59',\n"
     "  'docs/DESIGN.md':'bb73797cf93e9617b0cd319aaf9b18344145e885f075a6d1fd7c0b8842e6fac3',\n"
     "  'docs/MEMORY.md':'dbd2b04c596041f9e791112c37954d3dc2b5e2bed697392532aa1969304f4f5f',\n"
     "  'docs/PRD.md':'75e01be3c9b94843aa69384484c6bde5393bdd600a0e8b65662558244cba0739',\n"
     "  'docs/RULES.md':'dc8bf28916ae27d805add9e3f3257d45f06628f3041bebea95525c32f176afa0',\n"
     "  'docs/TASKS.md':'82568bdaf8d6e5da5b46fede33ba990009176f8318af7d06b5d1231d1d6ac2db',\n"
     "  'PROJECT_MASTER_PLAN.md':'a3ffe83e39b24172b39663c06f058d74fff04367dea87de965495774db5e3696'}\n"
     "def sha(p):\n"
     "    h=hashlib.sha256()\n"
     "    with open(p,'rb') as f:\n"
     "        for c in iter(lambda: f.read(1<<20), b''): h.update(c)\n"
     "    return h.hexdigest()\n"
     "print('%-26s %-10s %-10s %s' % ('file','pre','post','changed'))\n"
     "for rel in PRE:\n"
     "    p=os.path.join(REPO, rel.replace('/', os.sep))\n"
     "    post=sha(p)\n"
     "    print('%-26s %-10s %-10s %s' % (rel, PRE[rel][:8], post[:8], post!=PRE[rel]))\n")
    .replace("__REPO__", REPO.replace("\\", "\\\\"))
))

cells.append(md(
    "## 2. Additive preservation check\n"
    "\n"
    "Each updated file must **start with** its original pre-update content unchanged; the new "
    "synchronization block is appended at the end under the marker "
    "`<!-- ROADMAP_EXTENSION_V1_0__00_TO_43 -->`."
))

cells.append(code(
    "import shutil\n"
    "marker='<!-- ROADMAP_EXTENSION_V1_0__00_TO_43 -->'\n"
    "ok=True\n"
    "for rel in PRE:\n"
    "    p=os.path.join(REPO, rel.replace('/', os.sep))\n"
    "    t=open(p,encoding='utf-8').read()\n"
    "    has=marker in t\n"
    "    orig_preserved = t.startswith(open(os.path.join(REPO,'reports','audits','roadmap_00_43_pre_update_backup',os.path.basename(rel)),encoding='utf-8').read())\n"
    "    print('%-26s marker=%s original_at_start=%s' % (rel, has, orig_preserved))\n"
    "    ok = ok and has and orig_preserved\n"
    "print('ALL ADDITIVE + PRESERVED:', ok)"
))

cells.append(md("## 3. Canonical 00-43 roadmap content (Stage E 41-43)"))

cells.append(code(
    "titles=['Deployment Engineering & Model Packaging','End-to-End Deployment Validation',\n"
    "        'Research Deployment Release, Monitoring & Maintenance']\n"
    "for rel in PRE:\n"
    "    t=open(os.path.join(REPO, rel.replace('/', os.sep)),encoding='utf-8').read()\n"
    "    present=[tt for tt in titles if tt in t]\n"
    "    print('%-26s stageE_titles_present=%d' % (rel, len(present)))\n"
    "print()\n"
    "print('Full Stage E table in PROJECT_MASTER_PLAN.md:')\n"
    "t=open(os.path.join(REPO,'PROJECT_MASTER_PLAN.md'),encoding='utf-8').read()\n"
    "i=t.find('### Stage E')\n"
    "print(t[i:i+700])"
))

cells.append(md("## 4. Phase30 qualifier + TEST lock invariants"))

cells.append(code(
    "q='COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL'\n"
    "for rel in PRE:\n"
    "    t=open(os.path.join(REPO, rel.replace('/', os.sep)),encoding='utf-8').read()\n"
    "    print('%-26s phase30_qualifier=%s' % (rel, q in t))\n"
    "print()\n"
    "t=open(os.path.join(REPO,'PROJECT_MASTER_PLAN.md'),encoding='utf-8').read()\n"
    "print('TEST locked until Phase39 stated:', ('Phase 39' in t or 'Phase39' in t))\n"
    "print('Stage E NOT_AUTHORIZED_FOR_EXECUTION stated:', 'NOT_AUTHORIZED_FOR_EXECUTION' in t)"
))

cells.append(md("## 5. Phase35 v1.0f bindings (frozen, exact)"))

cells.append(code(
    "B={\n"
    " 'execution_source':'scripts/analysis/phase35_interpretability_execution_v1_0f.py',\n"
    " 'static_preflight':'reports/audits/phase35_execution_source_static_preflight_v1_0f.json',\n"
    " 'final_check':'reports/audits/phase35_empty_mask_actual_logits_repair_final_check_v1_0f.json',\n"
    " 'terminal':'reports/audits/phase35_empty_mask_actual_logits_repair_terminal_v1_0f.json',\n"
    " 'notebook':'notebooks/phasewise/phase_35_interpretability/phase35_empty_mask_actual_logits_repair_v1_0f_review.ipynb'}\n"
    "EXP={'execution_source':'6a6097f4a3c346df38ab5ec452dc97717cdb65d789bf8bde8031442cb236e3e5',\n"
    "     'static_preflight':'db37af29819c3fe124330d7188551f4584db4a475f725e2e6ff4a5b93af2c678',\n"
    "     'final_check':'85f65e0bcdde69f53607f709d50698fb20bbb6709ecaf2bb955e46dc93e70dee',\n"
    "     'terminal':'63a34ca8b5062301edb3c9a30e3b24053783371659891c31cc78b6d692a246b9',\n"
    "     'notebook':'0b28cbf7c5ce16adbecb9ccb85868ef517d34c24b4e3e9a9c4b37f9f315ea281'}\n"
    "allok=True\n"
    "for k,rel in B.items():\n"
    "    obs=sha(os.path.join(REPO, rel.replace('/', os.sep)))\n"
    "    m=(obs==EXP[k]); allok=allok and m\n"
    "    print('%-18s match=%s %s' % (k, m, obs[:16]))\n"
    "print('ALL v1.0f BINDINGS MATCH:', allok)\n"
    "d=json.load(open(os.path.join(REPO,'reports/audits/phase35_execution_source_static_preflight_v1_0f.json'),encoding='utf-8'))\n"
    "print('preflight:', d['total_n_checks'],'/',d['total_n_checks'],'failed',d['total_n_failed'],'predecessors',d['n_predecessors_preserved'])"
))

cells.append(md("## 6. Governance transfer + no-execution assertion"))

cells.append(code(
    "sync=json.load(open(os.path.join(REPO,'reports/audits/roadmap_00_43_documentation_sync_v1_0.json'),encoding='utf-8'))\n"
    "fc=json.load(open(os.path.join(REPO,'reports/audits/roadmap_00_43_documentation_sync_final_check_v1_0.json'),encoding='utf-8'))\n"
    "term=json.load(open(os.path.join(REPO,'reports/audits/roadmap_00_43_documentation_sync_terminal_v1_0.json'),encoding='utf-8'))\n"
    "print('sync scope                :', sync['scope'])\n"
    "print('science_changed           :', sync['science_changed'])\n"
    "print('scientific_execution_started:', sync['scientific_execution_started'])\n"
    "print('final check               :', fc['n_checks']-fc['n_failed'],'/',fc['n_checks'],'all_pass', fc['all_pass'])\n"
    "print('terminal                  :', term['terminal'][:110],'...')\n"
    "print()\n"
    "print('phase35_smoke_started     :', fc['phase35_smoke_started'])\n"
    "print('phase36_started           :', fc['phase36_started'])\n"
    "print('test_reads                :', fc['test_reads'])"
))

cells.append(md(
    "## 7. Conclusion\n"
    "\n"
    "- All seven canonical files were updated **additively**; original content is preserved "
    "verbatim at the start of each file.\n"
    "- The canonical 00-43 (44-phase) roadmap is recorded; Stage E (Phases 41-43) carries the "
    "exact supervisor titles and is `NOT_AUTHORIZED_FOR_EXECUTION`.\n"
    "- The Phase30 qualifier `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL` is "
    "retained verbatim.\n"
    "- Phase35 v1.0f bindings are frozen and match exactly.\n"
    "- **No** scientific execution occurred; the Phase35 v1.0f smoke and Phase36 are NOT_STARTED; "
    "**TEST remains locked until Phase 39**."
))

nb = nbformat.v4.new_notebook(cells=cells)
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}

client = NotebookClient(nb, timeout=600, kernel_name="python3",
                        resources={"metadata": {"path": REPO}})
client.execute()

if os.path.exists(OUT_NB):
    raise SystemExit("REFUSING TO OVERWRITE FROZEN OUTPUT: %s" % OUT_NB)
nbformat.write(nb, OUT_NB)

sha = sha256_of(OUT_NB)
n_code = sum(1 for c in nb.cells if c.cell_type == "code")
n_md = sum(1 for c in nb.cells if c.cell_type == "markdown")
n_err = sum(1 for c in nb.cells if c.cell_type == "code"
            and any(o.get("output_type") == "error" for o in c.get("outputs", [])))
execs = [c.execution_count for c in nb.cells if c.cell_type == "code"]

audit = OrderedDict([
    ("artifact", "roadmap_00_43_documentation_sync_reviewer_notebook_audit_v1_0"),
    ("revision", "RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0__00_TO_43"),
    ("notebook", OUT_NB.replace(REPO + os.sep, "").replace(os.sep, "/")),
    ("notebook_sha256", sha),
    ("notebook_representation", "EXECUTED_WITH_PERSISTED_OUTPUTS"),
    ("cells", len(nb.cells)), ("markdown_cells", n_md), ("code_cells", n_code),
    ("execution_counts", execs), ("errors", n_err),
    ("read_only", True),
    ("touches_TEST", False),
    ("runs_phase35_smoke", False),
    ("starts_phase36", False),
])
ap = os.path.join(AUDIT_DIR, "roadmap_00_43_documentation_sync_reviewer_notebook_audit_v1_0.json")
if os.path.exists(ap):
    raise SystemExit("REFUSING TO OVERWRITE FROZEN OUTPUT: %s" % ap)
with open(ap, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")

print("notebook:", OUT_NB)
print("sha256  :", sha)
print("cells   :", len(nb.cells), "md", n_md, "code", n_code, "errors", n_err)
print("execs   :", execs)
print("audit   :", ap)
