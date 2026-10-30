"""Synchronize current project state without changing scientific artifacts or hard rules."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT/'reports/audits'
DOCS = [f'docs/{n}.md' for n in ['ARCHITECTURE','DESIGN','MEMORY','PRD','RULES','TASKS']] + ['notebooks/phasewise/PHASE_INDEX.md']
OLD = '29518fc13f3de60113e1110a12a3f38bac5f54c246751503fe29e595f6dbe997'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(name, data):
    (AUD/(name+'.json')).write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


def main():
    nb = ROOT/'notebooks/phasewise/phase_25d_benefit_router/phase25d_benefit_router.ipynb'
    new = sha(nb)
    freeze = json.loads((AUD/'phase25d_final_freeze.json').read_text())
    det = json.loads((AUD/'phase25d_notebook_compliance_repair_determinism.json').read_text())
    assert new == det['new_canonical_notebook_sha']
    archive = AUD/'phase25d_compliance_pre_repair_control_docs'
    archive.mkdir(exist_ok=True)
    originals = {}
    for rel in DOCS:
        backup = archive/Path(rel).name
        if not backup.exists():
            backup.write_bytes((ROOT/rel).read_bytes())
        originals[rel] = backup.read_text(encoding='utf-8')
    texts = dict(originals)
    verified = '**Last verified:** 2026-10-01 — Phase25D canonical reviewer-notebook compliance repair complete'
    for rel in DOCS:
        if rel != 'docs/RULES.md':
            texts[rel] = re.sub(r'^\*\*Last verified:\*\*[^\n]*', verified, texts[rel], flags=re.M)

    def replace(rel, old, replacement):
        assert old in texts[rel], (rel, old)
        texts[rel] = texts[rel].replace(old, replacement)

    p = 'docs/ARCHITECTURE.md'
    replace(p, '> The benefit router is **specified and frozen in contract only — NOT trained**, and\n> **Phase25B (GT-free pre-refinement feature extraction) is `REENTRY_ELIGIBLE_NOT_STARTED`**.\n> Nothing in this section may be used to claim a trained router or a routing result.',
        '> The benefit router is **TRAINED / FROZEN in Phase25D (COMPLETE_CANONICAL)**, including its learned task embedding.\n> **Phase25B and Phase25C are COMPLETE canonical**. Phase25E is **ELIGIBLE_NOT_STARTED**.\n> Resource-gate calibration and routing results remain future work.')
    replace(p, 'SPECIFIED, NOT TRAINED', 'TRAINED / FROZEN in Phase25D')
    p = 'docs/DESIGN.md'
    replace(p, '> **Status update 2026-09-30.**', '> **Status update 2026-10-01.**')
    replace(p, '> (§16). The router itself is **specified but NOT trained**; Phase25B is\n> `REENTRY_ELIGIBLE_NOT_STARTED`. The bullets below are retained as the original design\n> intent.',
        '> (§16). The router is **TRAINED / FROZEN in Phase25D (COMPLETE_CANONICAL)**; Phase25B and Phase25C are COMPLETE canonical.\n> Phase25E is **ELIGIBLE_NOT_STARTED**. The bullets below retain the original design intent.')
    replace(p, 'SPECIFIED, NOT TRAINED', 'TRAINED / FROZEN in Phase25D')
    p = 'docs/PRD.md'
    replace(p, '(Phase-21 / Phase-25A); the benefit router is **specified, NOT trained**.',
        '(Phase-21 / Phase-25A); the benefit router is **TRAINED / FROZEN in Phase25D (COMPLETE_CANONICAL)**.\nPhase25B and Phase25C are COMPLETE canonical; Phase25E is **ELIGIBLE_NOT_STARTED**.')
    replace(p, 'This is the **official future direction**, but it is **NOT IMPLEMENTED, NOT TRAINED, NOT\nVALIDATED, NOT FROZEN**.',
        'The original design described the future direction. The global model, regional refiner and\nbenefit router have since been trained and frozen through Phase25D. The resource-aware gate\nand complete integrated routing system remain unvalidated; Phase25E is ELIGIBLE_NOT_STARTED.')
    p = 'docs/RULES.md'
    replace(p, '> **Updated 2026-09-30** (Phase-25C governance cleanup complete; Phase 25D eligible/not started).',
        '> **Updated 2026-10-01** (Phase25D canonical reviewer-notebook compliance repair complete).')
    replace(p, '  **Phase 25D is `ELIGIBLE_NOT_STARTED`**. Phase 25E–25G `NOT_STARTED`.',
        '  at Phase25C completion, Phase25D was eligible/not started; it has since completed canonically.\n'
        '- **Phase25D first blocked attempt = BLOCKED_ATTEMPT_PROVENANCE**.\n'
        '- **Phase25D router training spec v1.2.1 = COMPLETE / FROZEN**.\n'
        '- **Phase25D benefit router = COMPLETE_CANONICAL / TRAINED / FROZEN**.\n'
        '- **Phase25E = ELIGIBLE_NOT_STARTED**.\n- **Phase25F = NOT_STARTED**.\n- **Phase25G = NOT_STARTED**.')
    replace(p, '- The benefit router is **specified, NOT trained**. The historical Phase-21/22 baselines are',
        '- The benefit router is **TRAINED / FROZEN**. The historical Phase-21/22 baselines are')
    # All rules outside the explicitly authorized current-state section are identical.
    for part in [0, 1]:
        if part == 0:
            assert texts[p].split('## 14.')[0] == originals[p].split('## 14.')[0]
        else:
            assert texts[p].split('## 15.')[1] == originals[p].split('## 15.')[1]
    p = 'docs/TASKS.md'
    replace(p, '· Phase 25D ELIGIBLE_NOT_STARTED', '· Phase25D COMPLETE · Phase25E ELIGIBLE_NOT_STARTED')
    replace(p, '| 25E | Resource-aware pre-execution gate | **NOT_STARTED** |', '| 25E | Resource-aware pre-execution gate | **ELIGIBLE_NOT_STARTED** |')
    replace(p, '| Phase 25E | **NOT_STARTED** | — |', '| Phase 25E | **ELIGIBLE_NOT_STARTED** | Phase25D canonical completion; no gate execution |')
    evidence = (f"`phase25d_final_freeze.json` + `phase25d_final_freeze_notebook_compliance_addendum.json`; "
                f"notebook `{new}`; final checkpoint `{freeze['final_checkpoint_sha256']}`; "
                f"OOF `{freeze['oof_sha256']}`; `{freeze['terminal']}`")
    replace(p, '| Phase 25D | **ELIGIBLE_NOT_STARTED** — benefit-router training (owns the 16-D task embedding) | `phase25c_phase25d_handoff_schema.json` |',
        '| Phase 25D | **COMPLETE_CANONICAL / TRAINED / FROZEN** — includes learned 16-D task embedding | '+evidence+' |')
    replace(p, 'No router has been trained,', 'At Phase25B completion, no router had yet been trained;')
    replace(p, 'Labels are **gain supervision only**: no\n> router was trained,', 'Labels are **gain supervision only**: Phase25C itself did not train the\n> router,')
    marker = '### Historical (retained as provenance — Phase-13 era)'
    assert texts[p].split(marker)[1] == originals[p].split(marker)[1]
    p = 'docs/MEMORY.md'
    replace(p, 'Latest governance terminal:', 'Historical Phase25C governance terminal (superseded):')
    replace(p, 'Phase 25D spec-repair terminal:', 'Historical Phase25D spec-repair terminal (before accepted training):')
    replace(p, 'R2 0.089.', 'R2 = 0.087657630443573 (≈0.088 to 3 decimals).')
    replace(p, '## DOWNSTREAM STAGE OWNERSHIP (repaired 2026-09-30; Phase 25C completed 2026-09-30)',
        '## DOWNSTREAM STAGE OWNERSHIP (verified 2026-10-01; Phase25D COMPLETE canonical)')
    replace(p, '`sample_id` and trains `BARRBenefitRouterV1` including its learned `Embedding(4,16)`',
        '`sample_id` and trained `BARRBenefitRouterV1` including its learned `Embedding(4,16)`')
    replace(p, '**Phase 25D = benefit-router training.** Joins', '**Phase 25D = benefit-router training.** Joined')
    replace(p, 'to Phase 25D only.** Phase 25D is **ELIGIBLE_NOT_STARTED**.',
        'to Phase 25D only.** Phase25D is **COMPLETE canonical**. It trained BARRBenefitRouterV1 and its learned Embedding(4,16).')
    replace(p, '(params linear core 36,353 = bookkeeping only; **NOT TRAINED**).',
        'params (linear core 36,353 = bookkeeping only); **TRAINED / FROZEN in Phase25D**.')
    bindings = (f'- Phase25D canonical notebook: `{new}`\n'
        f'- Phase25D final checkpoint: `{freeze["final_checkpoint_sha256"]}`\n'
        f'- Phase25D OOF predictions: `{freeze["oof_sha256"]}`\n'
        f'- Phase25D final history: `{freeze["final_history_sha256"]}`\n'
        f'- PRE_NOTEBOOK_COMPLIANCE_REPAIR_PROVENANCE = `{OLD}`\n')
    replace(p, '## CANONICAL SHAs\n', '## CANONICAL SHAs\n\n'+bindings)
    p = 'notebooks/phasewise/PHASE_INDEX.md'
    replace(p, '*(see audit)*', '`'+new+'`')
    replace(p, '> only** — no router training, no 16-D task embedding, `test_reads = 0`. Phase 25D\n> (benefit-router training) is **eligible but not started**; no 25D notebook was created.',
        '> only** — no router training, no 16-D task embedding, `test_reads = 0`.\n'
        '> At Phase25C completion, Phase25D was eligible/not-started and no Phase25D notebook yet existed.\n'
        '> Phase25D has since completed canonically. Phase25E is **ELIGIBLE_NOT_STARTED**.\n\n'
        f'PRE_NOTEBOOK_COMPLIANCE_REPAIR_PROVENANCE = `{OLD}`\n\n'
        'The original notebook is preserved at `reports/audits/phase25d_notebook_compliance_pre_repair.ipynb`.\n'
        'The original scientific freeze is unchanged; the notebook migration is bound by\n'
        '`reports/audits/phase25d_final_freeze_notebook_compliance_addendum.json`.')
    replace(p, '# After spec repair v1.2.1: REENTRY_ELIGIBLE_NOT_STARTED',
        '# Historical after spec repair v1.2.1, before training: REENTRY_ELIGIBLE_NOT_STARTED\n  # Current: COMPLETE_CANONICAL / TRAINED / FROZEN')
    replace(p, 'phase25e_resource_aware_pre_gate.ipynb                        # NOT YET CREATED',
        'phase25e_resource_aware_pre_gate.ipynb                        # ELIGIBLE_NOT_STARTED; NOT YET CREATED')
    replace(p, '- **Phase-25D canonical notebook** (`phase25d_benefit_router.ipynb`)',
        '- **Phase-25D canonical notebook** (`phase25d_benefit_router.ipynb`) — SHA-256 `'+new+'`')
    # Label terminal strings as phase-completion provenance, never present eligibility.
    for p in ['notebooks/phasewise/PHASE_INDEX.md', 'docs/TASKS.md']:
        if p.endswith('PHASE_INDEX.md'):
            texts[p] = texts[p].replace('## 1. Canonical / frozen notebooks\n',
                '## 1. Canonical / frozen notebooks\n\nTerminal strings record each phase\'s historical completion boundary; current state is in the Status column and current-focus text.\n')
    records = []
    for rel, content in texts.items():
        (ROOT/rel).write_text(content, encoding='utf-8', newline='')
        records.append({'path':rel, 'before_sha256':sha(archive/Path(rel).name), 'after_sha256':sha(ROOT/rel)})
    write('phase25d_oof_r2_reporting_reconciliation', {
        'classification':'REPORTING_ROUNDING_CORRECTION_ONLY','science_changed':False,
        'source':'reports/audits/phase25d_final_freeze.json', 'r2_exact':0.087657630443573,
        'rounded_3_decimals':'0.088','rounded_4_decimals':'0.0877','rounded_6_decimals':'0.087658',
        'corrections':[{'path':'docs/MEMORY.md','old':'R2 0.089','new':'R2 = 0.087657630443573 (≈0.088 to 3 decimals)'}],
        'scanned_files':DOCS, 'remaining_r2_0_089':sum(len(re.findall(r'R2\s+0\.089', t)) for t in texts.values())})
    # Review all relevant matches, distinguishing historical terminal/provenance lines.
    reviewed = []
    stale = []
    for rel, content in texts.items():
        for n,line in enumerate(content.splitlines(),1):
            if re.search(r'25[- ]?D|25[- ]?E|router.*not trained|no.*25D.*notebook',line,re.I):
                historical = bool(re.search(r'PHASE25C_.*__PHASE25D|PHASE25D_ROUTER_TRAINING_SPEC.*__PHASE25D_REENTRY|historical|at Phase25C completion|before training',line,re.I))
                bad = bool(re.search(r'Phase\s*25D\s+(?:is\s+)?[*` ]*(?:ELIGIBLE_NOT_STARTED|REENTRY_ELIGIBLE_NOT_STARTED)|router.*NOT trained|Phase\s*25E\s*\|\s*\*\*NOT_STARTED',line,re.I)) and not historical
                reviewed.append({'path':rel,'line':n,'text':line,'historical_provenance':historical,'current_stale':bad})
                if bad:
                    stale.append(reviewed[-1])
    assert not stale, stale
    assert all('0.089' not in t for t in texts.values())
    write('phase25d_project_control_docs_sync', {
        'classification':'NOTEBOOK_AND_GOVERNANCE_COMPLIANCE_REPAIR_ONLY','science_changed':False,
        'documents':records,'reviewed_state_references':reviewed,
        'current_stale_phase25d_state_count':len(stale), 'historical_provenance_preserved':True,
        'original_docs_archive':str(archive.relative_to(ROOT)), 'rules_outside_section14_unchanged':True,
        'phase13_tasks_chronology_unchanged':True, 'router_status':'TRAINED_FROZEN',
        'phase25e_status':'ELIGIBLE_NOT_STARTED', 'all_pass':True})
    print('Seven project control docs synchronized; historical chronology and hard rules preserved.')


if __name__ == '__main__':
    main()
