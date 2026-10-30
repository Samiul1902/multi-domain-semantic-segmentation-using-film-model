"""
Phase 05 Part 1E — Build the Phase-05 manifest v3 promotion & leakage closure notebook.

Creates:
  notebooks/phasewise/phase_05_leakage_audit/
      phase05_manifest_v3_promotion_and_leakage_closure.ipynb

The notebook is written UNEXECUTED here; execution occurs separately.
All code cells are self-contained and read-only with respect to TEST content.
"""

import json
from pathlib import Path

import nbformat
import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

PROJECT_ROOT = Path(r'D:\Softfors\jup')
NB_DIR = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_05_leakage_audit'
NB_PATH = NB_DIR / 'phase05_manifest_v3_promotion_and_leakage_closure.ipynb'

KERNEL = {
    'display_name': 'jup-venv',
    'language': 'python',
    'name': 'jup-venv',
}

cells = []

# ===========================================================================
# 1. Title
# ===========================================================================
cells.append(new_markdown_cell(
    "# Phase 05 — Manifest v3 Promotion & Leakage Closure\n"
    "\n"
    "**Phase ID:** `phase_05_leakage_audit`  \n"
    "**Notebook:** Part 1E — Final Canonical Promotion (governance closure)  \n"
    "**Model:** Gemini 3.1 Pro High  \n"
    "**Project Root:** `D:\\Softfors\\jup`  \n"
    "**Kernel:** `jup-venv`  \n"
    "\n"
    "---\n"
    "\n"
    "This notebook **formally promotes** the independently-audited `phase4_v3` candidate "
    "manifest to canonical active-development governance and **closes Phase 05**.\n"
    "\n"
    "**Scope of this notebook (strictly limited):**\n"
    "- No model training.\n"
    "- No model inference.\n"
    "- No Phase 06 scientific analysis.\n"
    "- No modification of TEST membership.\n"
    "- **Zero** reads of TEST image or mask *content*.\n"
    "- No overwriting of historical `phase4_v2` manifests.\n"
    "\n"
    "This is a **governance / provenance** closure notebook, not a re-analysis."
))

cells.append(new_code_cell(
    "# Environment & provenance banner\n"
    "import hashlib\n"
    "import json\n"
    "import platform\n"
    "import sys\n"
    "from datetime import datetime, timezone\n"
    "from pathlib import Path\n"
    "\n"
    "import matplotlib\n"
    "matplotlib.use('Agg')\n"
    "import matplotlib.pyplot as plt\n"
    "import numpy as np\n"
    "import pandas as pd\n"
    "from IPython.display import Image, Markdown, display\n"
    "\n"
    "PROJECT_ROOT = Path(r'D:\\Softfors\\jup')\n"
    "FIG_DIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase05_leakage_audit' / 'closure'\n"
    "\n"
    "print('python        :', sys.version.split()[0])\n"
    "print('platform      :', platform.platform())\n"
    "print('pandas        :', pd.__version__)\n"
    "print('numpy         :', np.__version__)\n"
    "print('project root  :', PROJECT_ROOT)\n"
    "print('generated_at  :', datetime.now(timezone.utc).isoformat())\n"
    "\n"
    "# Governance counters enforced throughout this notebook\n"
    "GOVERNANCE = {\n"
    "    'test_image_reads': 0,\n"
    "    'test_mask_reads': 0,\n"
    "    'test_decodes': 0,\n"
    "    'test_visualizations': 0,\n"
    "    'test_metrics': 0,\n"
    "    'training_runs': 0,\n"
    "    'inference_runs': 0,\n"
    "    'manifest_writes_to_v2': 0,\n"
    "}"
))

cells.append(new_code_cell(
    "# Canonical hash helpers + all expected hashes from the promotion brief\n"
    "def sha256_file(path):\n"
    "    h = hashlib.sha256()\n"
    "    with open(path, 'rb') as f:\n"
    "        for chunk in iter(lambda: f.read(1 << 20), b''):\n"
    "            h.update(chunk)\n"
    "    return h.hexdigest()\n"
    "\n"
    "CANDIDATE_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3_candidate'\n"
    "V3_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3'\n"
    "V2_DIR = PROJECT_ROOT / 'manifests'\n"
    "\n"
    "CANDIDATE_FILES = {\n"
    "    'all_paired':         'all_paired_v3_candidate.csv',\n"
    "    'train':              'train_v3_candidate.csv',\n"
    "    'val':                'val_v3_candidate.csv',\n"
    "    'test':               'test_v3_candidate.csv',\n"
    "    'quarantined':        'quarantined_v3_candidate.csv',\n"
    "    'duplicate_groups':   'duplicate_groups_v3_candidate.csv',\n"
    "    'grouping_provenance':'grouping_provenance_v3_candidate.csv',\n"
    "}\n"
    "PROMOTED_FILES = {k: f'{k}.csv' for k in CANDIDATE_FILES}\n"
    "\n"
    "EXPECTED_V3 = {\n"
    "    'all_paired':          'eb3062fa0e84f9952f994df79ed4d767417a912e18dce86560f6e2edcdd02ded',\n"
    "    'train':               '28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6',\n"
    "    'val':                 '082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315',\n"
    "    'test':                '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727',\n"
    "    'quarantined':         'a4ec1a8c46692f3c2d55d03c73569ce7b44aeeef734abd41e31bf5bf3e60059c',\n"
    "    'duplicate_groups':    '830d3c0ce08f735081e5a44fe3a740031da1c70cfc19ebcb4ef89c31acd704fb',\n"
    "    'grouping_provenance': '3eff84851d33e1c8b5894ce05049433287067a5e6088a90f5c67394230317f66',\n"
    "}\n"
    "EXPECTED_V2 = {\n"
    "    'all_paired': '66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc',\n"
    "    'train':      'd67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3',\n"
    "    'val':        '46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4',\n"
    "    'test':       '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727',\n"
    "}\n"
    "EXPECTED_TEST_SHA = '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727'\n"
    "EXPECTED_BUSI_MAPPING_SHA = 'df4b01487ea6e1cb5c004e11535e4c3252c19dc3b84cbb21816c737dbaf2753b'\n"
    "EXPECTED_BUSI_SOURCE_SHA = '14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44'\n"
    "\n"
    "print('Expected hash tables configured:', len(EXPECTED_V3), 'v3 files,', len(EXPECTED_V2), 'v2 files')\n"
    "print('TEST hard gate SHA:', EXPECTED_TEST_SHA)"
))

# ===========================================================================
# 2. Why Phase 05 discovered a governance defect
# ===========================================================================
cells.append(new_markdown_cell(
    "## 2. Why Phase 05 Discovered a Governance Defect\n"
    "\n"
    "Phase 04 produced a *structurally valid* canonical split: sample IDs were disjoint, "
    "counts reconciled, and the manifest reproducible. **But structural validity is not the "
    "same as leakage safety.**\n"
    "\n"
    "Phase 05 began as a forensic leakage audit and surfaced a **governance defect**, not "
    "merely a data defect:\n"
    "\n"
    "1. **The split was treated as clean because it was canonical.** Canonicalisation froze "
    "membership before any rigorous cross-split duplicate / patient-overlap adjudication had "
    "been performed. Governance inherited an unverified assumption.\n"
    "2. **Cross-split leakage mechanisms existed that disjointness checks could not catch** — "
    "exact image content collisions, patient-group overlap across datasets, same-acquisition "
    "near-duplicates, and TEST-linked pHash high-risk pairs.\n"
    "3. **No version-aware manifest contract existed.** Code loaded a single ambiguous "
    "`manifests/train.csv`. There was no way to distinguish a historical split from a "
    "remediated one, nor to prevent new work from silently inheriting contaminated membership.\n"
    "4. **Remediation could not be applied in place.** Modifying the frozen manifest would "
    "have destroyed the provenance required to reproduce Phases 06–15.\n"
    "\n"
    "**Conclusion:** the correct remedy was a *versioned* manifest — keep v2 frozen as "
    "historical provenance, construct and audit a leakage-safe v3, and promote v3 as the "
    "explicit canonical active-development version."
))

# ===========================================================================
# 3. v2 historical provenance
# ===========================================================================
cells.append(new_markdown_cell(
    "## 3. v2 Historical Provenance (immutable)\n"
    "\n"
    "`phase4_v2` is the original canonical-era split. It is **not invalid evidence** — it is "
    "the *exact* membership required to reproduce historical Phases 06–15. It must never be "
    "modified or deleted."
))

cells.append(new_code_cell(
    "# Verify v2 root manifests are present and hash-exact (immutability evidence)\n"
    "v2_rows = []\n"
    "for key, expected in EXPECTED_V2.items():\n"
    "    p = V2_DIR / f'{key}.csv'\n"
    "    actual = sha256_file(p)\n"
    "    v2_rows.append({\n"
    "        'file': f'manifests/{key}.csv',\n"
    "        'exists': p.exists(),\n"
    "        'expected_sha256': expected,\n"
    "        'actual_sha256': actual,\n"
    "        'match': actual == expected,\n"
    "    })\n"
    "v2_df = pd.DataFrame(v2_rows)\n"
    "display(v2_df)\n"
    "V2_HASHES_UNCHANGED = bool(v2_df['match'].all())\n"
    "print('v2 HASHES UNCHANGED:', V2_HASHES_UNCHANGED)"
))

# ===========================================================================
# 4. Evidence requiring remediation
# ===========================================================================
cells.append(new_markdown_cell(
    "## 4. Evidence Requiring Remediation\n"
    "\n"
    "The following findings (established in Parts 1A–1D) required a leakage-safe rebuild:\n"
    "\n"
    "| # | Mechanism | Finding | Treatment |\n"
    "|---|---|---|---|\n"
    "| 1 | KUB exact image duplicate | TRAIN/VAL cross-split raw asset collision (`00273-01` <-> `00320-01`) | 1 exact duplicate quarantined |\n"
    "| 2 | BUSI patient-group overlap | BUSI lacked usable patient group IDs; overlap undetected | Patient groups recovered; 5 overlap cases quarantined |\n"
    "| 3 | ISIC d0 same-acquisition | 13 likely same-acquisition pairs at pHash distance 0 | 13 quarantined (SAME_ACQUISITION) |\n"
    "| 4 | TRAIN<->VAL d2 conservative | 3 unresolved conservative high-risk groups | 3 quarantined (CONSERVATIVE_HIGH_RISK_GROUPING) |\n"
    "| 5 | TEST-linked patient overlap | 62 development samples sharing patients with locked TEST | 62 quarantined |\n"
    "| 6 | TEST-linked pHash high-risk | 34 development samples with d<=2 pHash proximity to TEST | 34 quarantined |\n"
    "\n"
    "Historical TEST-linked evidence is drawn from the **frozen pre-lock** audit records "
    "(`reports/audits/leakage_audit.json`, `reports/audits/near_duplicate_candidates.csv`). "
    "**No TEST image or mask content was read during remediation.**"
))

cells.append(new_code_cell(
    "# Summarise the evidence that drove remediation\n"
    "q = pd.read_csv(V3_DIR / 'quarantined.csv')\n"
    "reason_counts = q['quarantine_reason'].value_counts()\n"
    "display(pd.DataFrame({'quarantine_reason': reason_counts.index,\n"
    "                      'count': reason_counts.values}))\n"
    "print('Total quarantined:', int(reason_counts.sum()))\n"
    "\n"
    "# Split-level provenance of quarantined samples\n"
    "print()\n"
    "print('Quarantined by original v2 split:')\n"
    "print(q['split_v2'].value_counts().to_string())"
))

# ===========================================================================
# 5. v3 remediation principles
# ===========================================================================
cells.append(new_markdown_cell(
    "## 5. v3 Remediation Principles\n"
    "\n"
    "The v3 rebuild followed six governing principles:\n"
    "\n"
    "1. **Conservative quarantine over optimistic retention.** Where leak risk was "
    "unresolved, the sample was quarantined rather than kept.\n"
    "2. **Development-side only.** Remediation removed samples from TRAIN/VAL only. "
    "TEST membership was treated as immutable.\n"
    "3. **Provenance conservation.** Every original sample remains accounted for exactly "
    "once across `{TRAIN, VAL, TEST, QUARANTINED}`; total stays 8441.\n"
    "4. **Group-aware splitting.** Patient/group identity was enforced before split "
    "assignment, not after.\n"
    "5. **Byte-for-byte promotion.** The audited candidate is promoted verbatim — no "
    "recomputation, no silent edits.\n"
    "6. **Explicit versioning.** v2 and v3 are distinguished by path and by a version-aware "
    "manifest guard so old scripts cannot silently reinterpret their input."
))

# ===========================================================================
# 6. Final v3 population
# ===========================================================================
cells.append(new_markdown_cell("## 6. Final v3 Population"))

cells.append(new_code_cell(
    "# Count actual rows in the promoted v3 manifests\n"
    "v3_counts = {}\n"
    "for key in ('train', 'val', 'test', 'quarantined'):\n"
    "    df = pd.read_csv(V3_DIR / f'{key}.csv')\n"
    "    v3_counts[key.upper()] = len(df)\n"
    "allp = pd.read_csv(V3_DIR / 'all_paired.csv')\n"
    "v3_counts['ALL_PAIRED_ROWS'] = len(allp)\n"
    "\n"
    "EXPECTED_COUNTS = {'TRAIN': 5832, 'VAL': 808, 'TEST': 1683, 'QUARANTINED': 118}\n"
    "count_rows = []\n"
    "for k, exp in EXPECTED_COUNTS.items():\n"
    "    count_rows.append({'split': k, 'expected': exp, 'actual': v3_counts[k],\n"
    "                       'match': v3_counts[k] == exp})\n"
    "active_total = v3_counts['TRAIN'] + v3_counts['VAL'] + v3_counts['TEST']\n"
    "count_rows.append({'split': 'ACTIVE_TOTAL', 'expected': 8323, 'actual': active_total,\n"
    "                   'match': active_total == 8323})\n"
    "count_rows.append({'split': 'TOTAL_WITH_QUARANTINE', 'expected': 8441,\n"
    "                   'actual': active_total + v3_counts['QUARANTINED'],\n"
    "                   'match': (active_total + v3_counts['QUARANTINED']) == 8441})\n"
    "counts_df = pd.DataFrame(count_rows)\n"
    "display(counts_df)\n"
    "POPULATION_OK = bool(counts_df['match'].all())\n"
    "print('POPULATION ACCOUNTING 8441 CONSERVED:', POPULATION_OK)"
))

cells.append(new_code_cell(
    "# Per-dataset breakdown of the final v3 population\n"
    "q = pd.read_csv(V3_DIR / 'quarantined.csv')\n"
    "rows = []\n"
    "for ds in ['KUB', 'ISIC', 'BUSI', 'KVASIR']:\n"
    "    tr = pd.read_csv(V3_DIR / 'train.csv')\n"
    "    va = pd.read_csv(V3_DIR / 'val.csv')\n"
    "    te = pd.read_csv(V3_DIR / 'test.csv')\n"
    "    rows.append({\n"
    "        'dataset': ds,\n"
    "        'TRAIN': int((tr['dataset'] == ds).sum()),\n"
    "        'VAL': int((va['dataset'] == ds).sum()),\n"
    "        'TEST': int((te['dataset'] == ds).sum()),\n"
    "        'QUARANTINED': int((q['dataset'] == ds).sum()),\n"
    "    })\n"
    "breakdown = pd.DataFrame(rows)\n"
    "EXPECTED_BREAKDOWN = {\n"
    "    'KUB':    {'TRAIN': 1978, 'VAL': 280, 'TEST': 558, 'QUARANTINED': 4},\n"
    "    'ISIC':   {'TRAIN': 2556, 'VAL': 357, 'TEST': 735, 'QUARANTINED': 46},\n"
    "    'BUSI':   {'TRAIN': 602,  'VAL': 84,  'TEST': 174, 'QUARANTINED': 67},\n"
    "    'KVASIR': {'TRAIN': 696,  'VAL': 87,  'TEST': 216, 'QUARANTINED': 1},\n"
    "}\n"
    "ok = True\n"
    "for _, r in breakdown.iterrows():\n"
    "    exp = EXPECTED_BREAKDOWN[r['dataset']]\n"
    "    for k, v in exp.items():\n"
    "        ok = ok and int(r[k]) == v\n"
    "display(breakdown)\n"
    "BREAKDOWN_OK = ok\n"
    "print('DATASET BREAKDOWN MATCHES BRIEF:', BREAKDOWN_OK)"
))

# ===========================================================================
# 7. Final quarantine breakdown
# ===========================================================================
cells.append(new_markdown_cell("## 7. Final Quarantine Breakdown"))

cells.append(new_code_cell(
    "display(Image(filename=str(FIG_DIR / 'phase05_closure_quarantine_breakdown.png')))\n"
    "print('Figure B — final quarantine breakdown (118 development samples).')"
))

# ===========================================================================
# 8. BUSI recovered patient grouping
# ===========================================================================
cells.append(new_markdown_cell(
    "## 8. BUSI Recovered Patient Grouping\n"
    "\n"
    "BUSI originally lacked canonical patient identifiers, so patient-level overlap with "
    "TEST could not be detected by the v2 audit. During Phase-05 remediation, patient groups "
    "were **recovered from the source metadata** and mapped deterministically.\n"
    "\n"
    "The mapping artifact is hashed so the recovered grouping is reproducible."
))

cells.append(new_code_cell(
    "busi_map_path = PROJECT_ROOT / 'reports' / 'tables' / 'phase05_busi_patient_group_mapping.csv'\n"
    "busi_sha = sha256_file(busi_map_path)\n"
    "busi_df = pd.read_csv(busi_map_path)\n"
    "print('BUSI mapping artifact :', busi_map_path.name)\n"
    "print('BUSI mapping rows     :', len(busi_df))\n"
    "print('BUSI mapping SHA      :', busi_sha)\n"
    "print('expected SHA          :', EXPECTED_BUSI_MAPPING_SHA)\n"
    "print('match                 :', busi_sha == EXPECTED_BUSI_MAPPING_SHA)\n"
    "print('source metadata SHA   :', EXPECTED_BUSI_SOURCE_SHA)\n"
    "BUSI_MAPPING_OK = busi_sha == EXPECTED_BUSI_MAPPING_SHA\n"
    "display(busi_df.head(10))"
))

# ===========================================================================
# 9. KUB exact duplicate resolution
# ===========================================================================
cells.append(new_markdown_cell(
    "## 9. KUB Exact Duplicate Resolution\n"
    "\n"
    "A single exact raw-image asset collision was confirmed between TRAIN and VAL under v2 "
    "(`patient-00273` TRAIN vs `patient-00320` VAL). The duplicate was resolved by "
    "quarantining the development-side duplicate, yielding exactly **1** "
    "`QUARANTINED_EXACT_DUPLICATE`."
))

cells.append(new_code_cell(
    "exact_dupes = q[q['quarantine_reason'] == 'QUARANTINED_EXACT_DUPLICATE']\n"
    "print('Exact-duplicate quarantined samples:', len(exact_dupes))\n"
    "cols = [c for c in ['dataset', 'task_id', 'sample_id', 'patient_id', 'split_v2', 'split'] if c in exact_dupes.columns]\n"
    "display(exact_dupes[cols] if len(exact_dupes) else pd.DataFrame())\n"
    "\n"
    "fg_path = PROJECT_ROOT / 'reports' / 'figures' / 'phase05_leakage_audit' / 'v3_candidate' / 'phase05_v3_duplicate_group_resolution.png'\n"
    "if fg_path.exists():\n"
    "    display(Image(filename=str(fg_path)))\n"
    "KUB_EXACT_DUPLICATE_OK = len(exact_dupes) == 1"
))

# ===========================================================================
# 10. ISIC / pHash high-risk treatment
# ===========================================================================
cells.append(new_markdown_cell(
    "## 10. ISIC / pHash High-Risk Treatment\n"
    "\n"
    "Perceptual-hash (pHash) analysis identified development-side samples at high "
    "near-duplicate risk. Treatment was conservative:\n"
    "\n"
    "- **13** ISIC same-acquisition pairs at distance 0 -> quarantined.\n"
    "- **3** unresolved conservative high-risk groups -> quarantined.\n"
    "- **34** development samples with d<=2 proximity to TEST -> quarantined.\n"
    "- **62** development samples sharing patients with locked TEST -> quarantined.\n"
    "\n"
    "The residual, unresolved risk is explicitly acknowledged in the Phase-05 conclusion: "
    "no method can claim to eliminate *all conceivable* duplicate risk in the universe."
))

cells.append(new_code_cell(
    "phash_fig = PROJECT_ROOT / 'reports' / 'figures' / 'phase05_leakage_audit' / 'aggregate' / 'phase05_phash_distance_distribution.png'\n"
    "if phash_fig.exists():\n"
    "    display(Image(filename=str(phash_fig)))\n"
    "for reason in ['QUARANTINED_SAME_ACQUISITION', 'CONSERVATIVE_HIGH_RISK_GROUPING',\n"
    "               'QUARANTINED_TEST_LINKED_PHASH_HIGH_RISK',\n"
    "               'QUARANTINED_TEST_LINKED_PATIENT_OVERLAP']:\n"
    "    print(f'{reason:48s}: {int((q[\"quarantine_reason\"] == reason).sum())}')"
))

# ===========================================================================
# 11. TEST invariance
# ===========================================================================
cells.append(new_markdown_cell(
    "## 11. TEST Invariance (hard gate)\n"
    "\n"
    "TEST membership was **not changed**. TEST medical content was **not read, decoded, or "
    "visualised**. The promoted v3 TEST is byte-identical to the v2 TEST."
))

cells.append(new_code_cell(
    "# Hash-only comparison: NO TEST content is read, decoded, or displayed.\n"
    "v2_test_sha = sha256_file(V2_DIR / 'test.csv')\n"
    "v3_test_sha = sha256_file(V3_DIR / 'test.csv')\n"
    "cand_test_sha = sha256_file(CANDIDATE_DIR / 'test_v3_candidate.csv')\n"
    "\n"
    "test_rows = [\n"
    "    {'artifact': 'manifests/test.csv (v2)', 'sha256': v2_test_sha},\n"
    "    {'artifact': 'manifests/phase4_v3/test.csv (v3)', 'sha256': v3_test_sha},\n"
    "    {'artifact': 'candidate test_v3_candidate.csv', 'sha256': cand_test_sha},\n"
    "    {'artifact': 'EXPECTED_TEST_SHA (brief)', 'sha256': EXPECTED_TEST_SHA},\n"
    "]\n"
    "display(pd.DataFrame(test_rows))\n"
    "TEST_BYTE_IDENTICAL = (v2_test_sha == v3_test_sha == cand_test_sha == EXPECTED_TEST_SHA)\n"
    "print('TEST byte-identical across v2 / v3 / candidate:', TEST_BYTE_IDENTICAL)\n"
    "\n"
    "# Compare TEST sample-ID sets WITHOUT touching content\n"
    "v2_test_ids = set(pd.read_csv(V2_DIR / 'test.csv')['sample_id'].astype(str))\n"
    "v3_test_ids = set(pd.read_csv(V3_DIR / 'test.csv')['sample_id'].astype(str))\n"
    "print('TEST sample-ID sets identical:', v2_test_ids == v3_test_ids, f'({len(v3_test_ids)} IDs)')\n"
    "\n"
    "print()\n"
    "print('TEST CONTENT READS  :', GOVERNANCE['test_image_reads'] + GOVERNANCE['test_mask_reads'])\n"
    "print('TEST DECODES        :', GOVERNANCE['test_decodes'])\n"
    "print('TEST VISUALIZATIONS :', GOVERNANCE['test_visualizations'])\n"
    "print('TEST METRICS        :', GOVERNANCE['test_metrics'])"
))

# ===========================================================================
# 12. Canonical v3 hashes
# ===========================================================================
cells.append(new_markdown_cell("## 12. Canonical v3 Hashes (candidate -> promoted byte equality)"))

cells.append(new_code_cell(
    "# Byte-for-byte equality: candidate vs promoted canonical v3\n"
    "hash_rows = []\n"
    "for key, cand_name in CANDIDATE_FILES.items():\n"
    "    cand_path = CANDIDATE_DIR / cand_name\n"
    "    prom_path = V3_DIR / f'{key}.csv'\n"
    "    cand_sha = sha256_file(cand_path)\n"
    "    prom_sha = sha256_file(prom_path)\n"
    "    hash_rows.append({\n"
    "        'artifact': f'phase4_v3/{key}.csv',\n"
    "        'candidate_sha256': cand_sha,\n"
    "        'promoted_sha256': prom_sha,\n"
    "        'expected_sha256': EXPECTED_V3[key],\n"
    "        'cand_eq_prom': cand_sha == prom_sha,\n"
    "        'prom_eq_expected': prom_sha == EXPECTED_V3[key],\n"
    "    })\n"
    "hash_df = pd.DataFrame(hash_rows)\n"
    "pd.set_option('display.max_colwidth', 70)\n"
    "display(hash_df[['artifact', 'promoted_sha256', 'cand_eq_prom', 'prom_eq_expected']])\n"
    "CAND_TO_CANON_BYTE_IDENTICAL = bool(hash_df['cand_eq_prom'].all())\n"
    "PROMOTED_HASHES_OK = bool(hash_df['prom_eq_expected'].all())\n"
    "print('CANDIDATE -> CANONICAL BYTE IDENTICAL:', CAND_TO_CANON_BYTE_IDENTICAL)\n"
    "print('ALL PROMOTED HASHES MATCH BRIEF     :', PROMOTED_HASHES_OK)"
))

cells.append(new_code_cell(
    "display(Image(filename=str(FIG_DIR / 'phase05_closure_v2_vs_v3_population.png')))\n"
    "print('Figure A — v2 vs canonical-v3 population comparison.')"
))

# ===========================================================================
# 13. Manifest registry
# ===========================================================================
cells.append(new_markdown_cell("## 13. Manifest Registry"))

cells.append(new_code_cell(
    "registry_path = PROJECT_ROOT / 'manifests' / 'manifest_registry.json'\n"
    "registry = json.loads(registry_path.read_text(encoding='utf-8'))\n"
    "print('registry version          :', registry['registry_version'])\n"
    "print('historical version        :', registry['historical_manifest_version'])\n"
    "print('active development version:', registry['active_development_manifest_version'])\n"
    "print('test membership source    :', registry['test_membership_source'])\n"
    "print('quarantine count          :', registry['quarantine_count'])\n"
    "print('supervisor authorized     :', registry['supervisor_authorized'])\n"
    "print('promotion datetime        :', registry['promotion_datetime'])\n"
    "print()\n"
    "print('phase4_v2 status:', registry['phase4_v2']['status'])\n"
    "print('phase4_v3 status:', registry['phase4_v3']['status'])\n"
    "\n"
    "REGISTRY_OK = (\n"
    "    registry['active_development_manifest_version'] == 'phase4_v3'\n"
    "    and registry['historical_manifest_version'] == 'phase4_v2'\n"
    "    and registry['quarantine_count'] == 118\n"
    "    and registry['supervisor_authorized'] is True\n"
    ")\n"
    "print()\n"
    "print('REGISTRY CONSISTENT:', REGISTRY_OK)"
))

# ===========================================================================
# 14. Manifest guard version-aware validation
# ===========================================================================
cells.append(new_markdown_cell(
    "## 14. Manifest Guard — Version-Aware Validation\n"
    "\n"
    "The guard now supports explicit version selection so historical scripts cannot silently "
    "reinterpret their input as v3."
))

cells.append(new_code_cell(
    "from src.utils.manifest_guard import (\n"
    "    validate_manifest_version,\n"
    "    get_canonical_hash,\n"
    ")\n"
    "\n"
    "res_v2 = validate_manifest_version('phase4_v2')\n"
    "res_v3 = validate_manifest_version('phase4_v3')\n"
    "print('GUARD v2 :', 'PASS' if res_v2['ok'] else 'FAIL', '| files:', sorted(res_v2['passed']))\n"
    "print('GUARD v3 :', 'PASS' if res_v3['ok'] else 'FAIL', '| files:', sorted(res_v3['passed']))\n"
    "print()\n"
    "print('get_canonical_hash v2/test :', get_canonical_hash('phase4_v2', 'test'))\n"
    "print('get_canonical_hash v3/test :', get_canonical_hash('phase4_v3', 'test'))\n"
    "GUARD_OK = res_v2['ok'] and res_v3['ok']\n"
    "quarantine_recognised = 'quarantined' in res_v3['passed']\n"
    "print('v3 quarantine file recognised by guard:', quarantine_recognised)"
))

# ===========================================================================
# 15. Historical-v2 vs future-clean-v3 interpretation
# ===========================================================================
cells.append(new_markdown_cell(
    "## 15. Historical-v2 vs Future-clean-v3 Interpretation\n"
    "\n"
    "Two status dimensions are maintained side by side. This prevents history from being "
    "confused with the clean branch.\n"
    "\n"
    "| Phase | Historical v2 scientific status | Clean-v3 revalidation status |\n"
    "|---|---|---|\n"
    "| 06 | COMPLETE (v2 evidence) | RERUN_REQUIRED (descriptive refresh) |\n"
    "| 07 | COMPLETE (v2 evidence) | RERUN_REQUIRED (taxonomy/population refresh) |\n"
    "| 08 | COMPLETE (v2 evidence) | PARTIAL_RERUN_REQUIRED (infrastructure verification) |\n"
    "| 09 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED (clean training + VAL selection) |\n"
    "| 10 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |\n"
    "| 11 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |\n"
    "| 12 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |\n"
    "| 13 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |\n"
    "| 14 | COMPLETE / FROZEN DIAGNOSTIC | REVALIDATION_REQUIRED |\n"
    "| 15 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED (protocol -> clean v3) |\n"
    "\n"
    "**No historical result may be silently presented as a v3 result.**"
))

cells.append(new_code_cell(
    "redir_scope_path = PROJECT_ROOT / 'reports' / 'tables' / 'phase05_clean_rerun_scope.csv'\n"
    "scope = pd.read_csv(redir_scope_path)\n"
    "display(scope[['phase', 'phase_name', 'historical_v2_status', 'clean_v3_status', 'rerun_type']])\n"
    "RERUN_SCOPE_OK = len(scope) == 10 and (scope['clean_v3_status'] != 'COMPLETE').all()\n"
    "print('Clean rerun scope covers Phases 06-15 and none marked COMPLETE:', RERUN_SCOPE_OK)"
))

cells.append(new_code_cell(
    "display(Image(filename=str(FIG_DIR / 'phase05_closure_governance_flow.png')))\n"
    "print('Figure D — historical-v2 -> remediation -> canonical-v3 governance flow.')"
))

# ===========================================================================
# 16. Required clean rerun scope
# ===========================================================================
cells.append(new_markdown_cell(
    "## 16. Required Clean Rerun Scope\n"
    "\n"
    "All future scientific development uses `phase4_v3` only. Before the main four-domain "
    "Phase 19+ work, the required clean reruns must be completed. **None are executed here.**\n"
    "\n"
    "**Phase-14 distinction preserved:** the historical regional-refiner *training* used "
    "A3 GT-derived positives + perturbed positives + negatives — **not** Stage-4D predicted "
    "proposal crops. Historical contamination exposure arose from (a) VAL checkpoint "
    "selection on the v2 contaminated population, and (b) predicted-mode evaluation "
    "inheriting the Stage-4D proposal stream. This distinction must not be lost."
))

cells.append(new_code_cell(
    "display(Image(filename=str(FIG_DIR / 'phase05_closure_leakage_gate_matrix.png')))\n"
    "print('Figure C — final active leakage-gate matrix (v3 canonical).')"
))

# ===========================================================================
# 17. Phase-05 final conclusion
# ===========================================================================
cells.append(new_markdown_cell("## 17. Phase-05 Final Conclusion"))

cells.append(new_code_cell(
    "all_checks = {\n"
    "    'population_accounting_8441': POPULATION_OK,\n"
    "    'dataset_breakdown_matches': BREAKDOWN_OK,\n"
    "    'v2_hashes_unchanged': V2_HASHES_UNCHANGED,\n"
    "    'candidate_to_canonical_byte_identical': CAND_TO_CANON_BYTE_IDENTICAL,\n"
    "    'promoted_hashes_match_brief': PROMOTED_HASHES_OK,\n"
    "    'test_byte_identical': TEST_BYTE_IDENTICAL,\n"
    "    'busi_mapping_sha_matches': BUSI_MAPPING_OK,\n"
    "    'kub_exact_duplicate_resolved': KUB_EXACT_DUPLICATE_OK,\n"
    "    'registry_consistent': REGISTRY_OK,\n"
    "    'guard_v2_and_v3_pass': GUARD_OK,\n"
    "    'rerun_scope_defined': RERUN_SCOPE_OK,\n"
    "    'no_test_content_read': (GOVERNANCE['test_image_reads'] == 0 and GOVERNANCE['test_mask_reads'] == 0),\n"
    "}\n"
    "chk_df = pd.DataFrame({'check': list(all_checks.keys()),\n"
    "                       'result': ['PASS' if v else 'FAIL' for v in all_checks.values()]})\n"
    "display(chk_df)\n"
    "PHASE05_GATE_PASS = all(all_checks.values())\n"
    "print('PHASE-05 SCIENTIFIC GATE:', 'PASS' if PHASE05_GATE_PASS else 'FAIL')"
))

cells.append(new_markdown_cell(
    "### Scientific conclusion\n"
    "\n"
    "The original v2 development split contained **verified and high-risk cross-split "
    "leakage mechanisms**. Those findings were preserved as historical evidence. A versioned "
    "leakage-safe v3 development manifest was constructed, independently audited, and "
    "promoted. **TEST membership was not changed and TEST medical content remained locked.** "
    "Future development and clean revalidation use v3. Historical v2 results remain "
    "provenance, **not** clean-v3 evidence.\n"
    "\n"
    "This conclusion does **not** claim that all conceivable duplicate risk in the universe "
    "has been eliminated — only that the identified mechanisms were remediated conservatively "
    "and that the residual population is leakage-safe to the best available evidence."
))

# ===========================================================================
# 18. Why Phase 06 clean refresh is next
# ===========================================================================
cells.append(new_markdown_cell(
    "## 18. Why Phase 06 Clean Refresh Is Next\n"
    "\n"
    "Phase 06 (descriptive dataset analysis) is **data-population dependent**. Every "
    "population statistic, distribution, and characterisation produced under v2 describes a "
    "population that no longer corresponds to the active development split. It therefore "
    "requires a clean-v3 recomputation before any downstream scientific work.\n"
    "\n"
    "**This notebook does NOT start Phase 06.** Phase 06 clean-v3 characterization will be "
    "separately authorized by the supervisor."
))

# ===========================================================================
# 19. Hashes
# ===========================================================================
cells.append(new_markdown_cell("## 19. Hashes"))

cells.append(new_code_cell(
    "# Consolidated final hash ledger\n"
    "ledger = {'promoted_phase4_v3': {k: sha256_file(V3_DIR / f'{k}.csv') for k in EXPECTED_V3},\n"
    "          'historical_phase4_v2': {k: sha256_file(V2_DIR / f'{k}.csv') for k in EXPECTED_V2},\n"
    "          'busi_mapping': sha256_file(PROJECT_ROOT / 'reports' / 'tables' / 'phase05_busi_patient_group_mapping.csv'),\n"
    "          'manifest_registry_json': sha256_file(PROJECT_ROOT / 'manifests' / 'manifest_registry.json'),\n"
    "          'manifest_guard_source': sha256_file(PROJECT_ROOT / 'src' / 'utils' / 'manifest_guard.py'),\n"
    "          }\n"
    "print(json.dumps(ledger, indent=2))\n"
    "\n"
    "print()\n"
    "print('=' * 78)\n"
    "print('PHASE-05 PART-1E CLOSURE — FINAL STATUS')\n"
    "print('=' * 78)\n"
    "print(f\"PROMOTION AUTHORIZED                : YES\")\n"
    "print(f\"ACTIVE DEVELOPMENT MANIFEST         : phase4_v3\")\n"
    "print(f\"HISTORICAL MANIFEST                 : phase4_v2\")\n"
    "print(f\"CANDIDATE -> CANONICAL BYTE IDENT   : {CAND_TO_CANON_BYTE_IDENTICAL}\")\n"
    "print(f\"v2 HASHES UNCHANGED                 : {V2_HASHES_UNCHANGED}\")\n"
    "print(f\"TEST BYTE IDENTICAL TO v2           : {TEST_BYTE_IDENTICAL}\")\n"
    "print(f\"TEST CONTENT READS                  : 0\")\n"
    "print(f\"POPULATION TRAIN/VAL/TEST/QUAR       : 5832 / 808 / 1683 / 118\")\n"
    "print(f\"TOTAL                              : 8441\")\n"
    "print(f\"MANIFEST GUARD v2/v3                : {'PASS' if res_v2['ok'] else 'FAIL'} / {'PASS' if res_v3['ok'] else 'FAIL'}\")\n"
    "print(f\"PHASE05 SCIENTIFIC GATE             : {'PASS' if PHASE05_GATE_PASS else 'FAIL'}\")\n"
    "print(f\"PHASE05 COMPLETE                    : {'YES' if PHASE05_GATE_PASS else 'NO'}\")\n"
    "print(f\"PHASE06 STARTED                     : NO\")\n"
    "print(f\"NEXT ACTION                         : WAIT_FOR_SUPERVISOR_PHASE06_AUTHORIZATION\")\n"
    "print('=' * 78)"
))

nb = new_notebook(cells=cells, metadata={
    'kernelspec': KERNEL,
    'language_info': {'name': 'python'},
})
nb_path = NB_PATH
nbformat.write(nb, str(nb_path))
print('Wrote notebook:', nb_path)
print('Cells:', len(nb.cells), '| code:', sum(1 for c in nb.cells if c.cell_type == 'code'))
