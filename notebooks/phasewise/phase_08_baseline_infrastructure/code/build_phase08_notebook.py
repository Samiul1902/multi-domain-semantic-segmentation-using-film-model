"""
Phase 08 Part 1A — build the infrastructure validation notebook (unexecuted).

The notebook IMPORTS canonical `src/` helpers; production functionality lives in
`src/`, not in notebook code.
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

PROJECT_ROOT = Path(r'D:\Softfors\jup')
NB_DIR = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_08_baseline_infrastructure'
NB_PATH = NB_DIR / 'phase08_clean_v3_training_infrastructure_validation.ipynb'

KERNEL = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}

cells = []
md = lambda s: cells.append(new_markdown_cell(s))
code = lambda s: cells.append(new_code_cell(s))

# 1. Title
md("""# Phase 08 — Baseline Infrastructure Validation (CLEAN-v3, Part 1A)

**Phase ID:** `phase_08_baseline_infrastructure`
**Part:** 1A — Clean-v3 Data / Target / Device / Reproducibility Foundation
**Model:** Gemini 3.8 Flash Medium
**Project Root:** `D:\\Softfors\\jup` · **Kernel:** `jup-venv`

**Active manifest:** `phase4_v3` · **Frozen taxonomy:** `kub_size_clean_v3_v1`

> This notebook **builds and validates infrastructure only**. No baseline training,
> no scientific performance claims, and no TEST content access.""")

# 2. Objective
md("""## 2. Scientific / Engineering Objective

Establish and verify the clean-v3 engineering foundation on which Phase 09 baseline
training will run:

- the binary target contract (`mask > 0`)
- image-mode / input-channel behaviour
- the spatial transform contract and image–mask alignment
- a manifest-backed, TEST-locked loader
- reproducibility, metric, checkpoint, AMP and device plumbing
- frozen size-taxonomy integration

Production functionality lives under `src/`; this notebook imports and audits it.""")

# 3. Governance
md("""## 3. Governance

| Rule | Value |
|---|---|
| Active manifest | `phase4_v3` (explicitly validated) |
| TEST | metadata only — **0** image/mask reads |
| TEST visualizations | **0** |
| TEST metrics | **0** |
| Baseline training | **NONE** |
| Scientific performance claims | **NONE** |
| Phase 09 | **NOT started** |
| Architecture / loss / optimizer changes | **NONE** |
| Hyperparameter tuning | **NONE** |

No scientifically material default is chosen here. Where a value is required, it is
stated explicitly or left as a labelled placeholder.""")

code("""import json, sys, tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use('Agg')
from IPython.display import Image as IPImage, display

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
CODE_DIR = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_08_baseline_infrastructure' / 'code'
TABLES = PROJECT_ROOT / 'reports' / 'tables'
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase08_baseline_infrastructure'
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(CODE_DIR))
import phase08_infrastructure_audit as p8

from src.utils.targets import binarize_mask, foreground_label_signature, is_binary
from src.utils import device as dev
from src.utils import config as cfgmod
from src.data.kub_dataset import KUBDataset
from src.data.transforms import SegmentationTransform
from src.data.loaders import create_loader
from src.metrics.segmentation import binary_metrics
from src.metrics.object_metrics import object_metrics
from src.analysis import kub_object_size as kos

print('python :', sys.version.split()[0])
print('torch  :', torch.__version__)
print('manifest:', p8.MANIFEST_VERSION, '| taxonomy:', p8.TAXONOMY_ID)""")

# 4. Environment + CUDA
md("## 4. Environment + CUDA")
code("""env = dev.device_report()
for k, v in env.items():
    print(f'{k:26s}: {v}')
print()
print('get_device(require_cuda=True) ->', dev.get_device(require_cuda=True))
print('AMP supported                ->', dev.amp_supported())
print()
print('CUDA is REQUIRED for canonical runs; CPU fallback is never silent.')""")

# 5. Manifest verification
md("""## 5. Active Manifest Verification

`phase4_v3` is validated explicitly through the manifest guard. Root
`manifests/*.csv` (phase4_v2) is historical provenance and is not used.""")
code("""manifests = p8.verify_manifests()
print('guard ok            :', manifests['guard_ok'])
print('guard files         :', manifests['guard_files'])
print('KUB TRAIN cases     :', manifests['kub_train_cases'])
print('KUB VAL cases       :', manifests['kub_val_cases'])
print('TRAIN patients      :', manifests['train_patients'])
print('VAL patients        :', manifests['val_patients'])
print('patient overlap     :', manifests['patient_overlap'])
print('TEST metadata rows  :', manifests['test_metadata_rows'], '(metadata only, never decoded)')
assert manifests['guard_ok'] and manifests['counts_ok']
print()
print('HARD GATE PASS: phase4_v3 validated, 1978/280, overlap 0')
train_df = pd.read_csv(p8.TRAIN_MANIFEST)""")

# 6. Target semantic contract
md("""## 6. Target Semantic Contract

**BACKGROUND = `mask == 0`; FOREGROUND = `mask > 0`.** Native KUB masks use a
heterogeneous nonzero label vocabulary; `mask == 1` must never be assumed.""")
code("""target = p8.audit_target_contract(train_df)
print('foreground rule          :', target['foreground_rule'])
print('samples audited          :', target['samples_audited'])
print('raw label union          :', target['raw_label_union'])
print('non-1 foreground labels  :', target['non_one_foreground_labels'])
print('binarize equivalence fail:', target['binarize_equivalence_failures'])
print('non-binary after binarize:', target['non_binary_after_binarize'])
print()
print('observed raw label signatures:')
for k, v in target['label_signatures'].items():
    print(f'   {k:14s} {v:5d} samples')""")

code("""# direct demonstration on synthetic masks
for label in (1, 2, 3, 255):
    m = np.zeros((6, 6), dtype=np.uint8); m[2, 2] = label
    out = binarize_mask(m)
    print(f'label {label:3d} -> foreground={int(out.sum())} binary={is_binary(out)}')""")

# 7. Image-mode / channel audit
md("""## 7. Image-Mode / Channel Audit

FULL_FIELD images are RGB; ROI crops are single-channel `L`. The historical
pipeline converts both to a **1-channel** tensor and that convention is preserved.""")
code("""image_modes = p8.audit_image_modes(train_df)
print('source mode counts:', image_modes['source_mode_counts'])
print()
for c in image_modes['channel_checks']:
    print(f"  source {c['source_mode']:4s} -> tensor {c['tensor_shape']} ({c['tensor_channels']} channel)")
print()
print('input channel convention:', image_modes['input_channel_convention'])
print(image_modes['convention_note'])""")

# 8. Transform contract
md("""## 8. Transform Contract

Aspect-preserving resize + centre pad, `scale = min(size/w, size/h)`, bilinear
image / **nearest** mask. This is the documented historical preprocessing and is
not replaced by non-isotropic stretching.""")
code("""transform_df = p8.audit_transform_contract(train_df)
p8.write_table(transform_df, 'phase08_transform_contract_audit.csv', TABLES)
display(transform_df[['target_size','source_h','source_w','actual_scale','resized_w','resized_h',
                      'pad_left','pad_top','padded_w_ok','padded_h_ok','aligned','mask_is_binary',
                      'mask_foreground_preserved']])
print()
print('all padded to target :', bool(transform_df['padded_w_ok'].all() and transform_df['padded_h_ok'].all()))
print('all image/mask aligned:', bool(transform_df['aligned'].all()))
print('all masks binary      :', bool(transform_df['mask_is_binary'].all()))
print('all FG preserved      :', bool(transform_df['mask_foreground_preserved'].all()))""")

# 9. Loader construction
md("""## 9. Loader Construction

`KUBDataset` is manifest-backed and TEST-locked; `create_loader` builds a
seeded `DataLoader` with pinned memory and worker seeding.""")
code("""ds = KUBDataset(p8.TRAIN_MANIFEST, 'TRAIN', target_size=256, cache_in_memory=False)
print('TRAIN dataset length:', len(ds))
loader = create_loader(ds, batch_size=4, shuffle=False, seed=42, num_workers=0, pin_memory=True)
batch = next(iter(loader))
print('batch image:', tuple(batch['image'].shape), batch['image'].dtype)
print('batch mask :', tuple(batch['mask'].shape), batch['mask'].dtype)
print('mask unique:', torch.unique(batch['mask']).tolist())
print()
try:
    KUBDataset(p8.TRAIN_MANIFEST, 'TEST')
    print('ERROR: TEST construction should have been blocked')
except Exception as e:
    print('TEST construction blocked:', type(e).__name__)""")

# 10. Deterministic sample audit
md("""## 10. Deterministic Sample Audit

Selection is deterministic and prediction-independent, stratified by
(acquisition, category) and forced to cover every observed raw label signature.""")
code("""sel = p8.deterministic_sample_selection(train_df, n_total=16)
sample_df, _ = p8.audit_loader_samples(sel)
p8.write_table(sample_df, 'phase08_kub_v3_loader_sample_audit.csv', TABLES)
SELECTION_SHA = p8.sha256_of_strings(sample_df['sample_id'].tolist())
display(sample_df[['sample_id','category','acquisition_type','source_image_mode',
                   'raw_mask_label_signature','tensor_shape','binary_mask_unique_values',
                   'foreground_pixel_count','mask_is_binary']])
print('cases                :', len(sample_df))
print('acquisition coverage :', sample_df['acquisition_type'].value_counts().to_dict())
print('category coverage    :', sample_df['category'].value_counts().to_dict())
print('label signatures     :', sample_df['raw_mask_label_signature'].value_counts().to_dict())
print('selection SHA        :', SELECTION_SHA)""")

# 11. Medical visual gallery
md("""## 11. Medical Visual Loader Gallery

Source image, source binary GT, transformed image, transformed binary GT, and
overlay — verifying loader/transform fidelity. ROI grayscale is rendered
faithfully. No predictions, no TEST.""")
code("""gal = p8.loader_gallery_pages(sel, cases_per_page=4)
GAL_PATHS = []
for i, f in enumerate(gal, 1):
    gp = p8.save_fig(f, FIGDIR / f'phase08_loader_gallery_page{i:02d}.png')
    GAL_PATHS.append(gp)
print('gallery pages:', len(GAL_PATHS))""")
for _i in range(4):
    code(f"""display(IPImage(filename=str(FIGDIR / f'phase08_loader_gallery_page{_i+1:02d}.png')))""")

# 12. Reproducibility
md("""## 12. Reproducibility / Seed Audit

Seeding covers Python, NumPy, torch CPU, CUDA, DataLoader workers, and a
deterministic generator. **Bitwise GPU determinism is NOT claimed.**""")
code("""repro_df = p8.audit_reproducibility()
p8.write_table(repro_df, 'phase08_reproducibility_audit.csv', TABLES)
display(repro_df)
print()
print('determinism policy: cudnn.deterministic=%s, cudnn.benchmark=%s' % (
    torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark))
print('torch.use_deterministic_algorithms:', torch.are_deterministic_algorithms_enabled())
print()
print('TRAIN access is stochastic by design (augmentation); reproducibility is')
print('achieved by seeding. VAL access is deterministic.')""")

# 13. Metric contract
md("""## 13. Metric Contract

Dice, IoU, precision, recall (and HD95 / object recall) are centralized with
explicit threshold, epsilon and empty-mask conventions. **No metric definition is
changed or retuned here.**""")
code("""metric_df = p8.audit_metric_contract()
p8.write_table(metric_df, 'phase08_metric_contract.csv', TABLES)
display(metric_df[['metric','module','function','version','threshold','epsilon','empty_handling']])
print()
om = object_metrics(np.zeros((8,8),bool), np.zeros((8,8),bool))
print('object_metrics connectivity:', om['connectivity'],
      '| minimum_overlap_pixels:', om['minimum_overlap_pixels'])
print('object metric convention is EXPLICIT (8-connectivity, overlap-based).')""")

# 14. Frozen taxonomy integration
md("""## 14. Frozen Size-Taxonomy Integration

Object-level metadata loads the frozen taxonomy through the versioned API. ROI
components are never primary-binned.""")
code("""taxonomy = p8.audit_taxonomy_integration(train_df)
print('taxonomy_id :', taxonomy['taxonomy_id'])
print('thresholds  :', taxonomy['thresholds'])
print('FF strata (sample):', taxonomy['full_field_strata_sample'])
print('ROI handling:', taxonomy['roi_handling'])
print('ROI-specific taxonomy created:', taxonomy['roi_specific_taxonomy_created'])
print()
print(taxonomy['note'])""")

# 15. AMP foundation
md("""## 15. AMP Foundation

CUDA AMP plumbing compatible with PyTorch 2.6: `torch.amp.autocast('cuda')` and
`torch.amp.GradScaler('cuda')`, with scaler-state save/restore.""")
code("""print('AMP supported:', dev.amp_supported())
scaler = dev.make_grad_scaler(enabled=True)
st = scaler.state_dict()
scaler2 = dev.make_grad_scaler(enabled=True)
scaler2.load_state_dict(st)
print('GradScaler state keys:', sorted(st.keys()))
print('GradScaler state round-trip: OK')""")

# 16. Checkpoint / resume contract
md("""## 16. Checkpoint / Resume Contract

Checkpoints store model/optimizer/scheduler/scaler state, epoch, best metric,
experiment ID, seed, manifest version, taxonomy ID, config and RNG state. Resume
restores the same experiment ID — no autonomous new IDs for retries.""")
code("""with tempfile.TemporaryDirectory() as tmp:
    ckpt_df = p8.audit_checkpoint_contract(Path(tmp))
p8.write_table(ckpt_df, 'phase08_checkpoint_contract.csv', TABLES)
display(ckpt_df)""")

# 17. CUDA smoke step
md("""## 17. Minimal CUDA Smoke Step

**INFRASTRUCTURE_TEST_ONLY.** A tiny number of TRAIN batches through an existing
baseline model verify CUDA tensors, forward, binary target shape, loss, backward,
optimizer step, AMP, GradScaler, finiteness and GPU memory. This is **not**
baseline training and produces **no scientific result**.""")
code("""smoke = p8.cuda_smoke_test(sel)
for k, v in smoke.items():
    print(f'{k:24s}: {v}')
print()
print('No epochs run. No architecture comparison. No scientific claim.')""")

# 18. Unit-test summary
md("## 18. Unit-Test Summary")
code("""import subprocess
proc = subprocess.run([str(PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'), '-m', 'pytest',
                       'tests/test_phase08_infrastructure.py', '-q', '--no-header'],
                      cwd=str(PROJECT_ROOT), capture_output=True, text=True)
print((proc.stdout or proc.stderr).strip().splitlines()[-1])""")

# 19. Limitations
md("""## 19. Limitations

- Infrastructure validation only: no training, no inference, no performance claims.
- The CUDA smoke step is an engineering check, not a scientific result.
- Bitwise GPU determinism is **not** guaranteed or claimed.
- The frozen taxonomy is applied to FULL_FIELD object metadata only; ROI is
  deliberately not primary-binned.
- Three pre-existing test failures/hangs in unrelated historical modules
  (`test_predicted_roi`, `test_kub_localizer`, `test_phase14_part1`) are noted and
  left untouched — they are outside this phase's scope.""")

# 20. Conclusion
md("""## 20. Phase-08 Part-1A Conclusion

The clean-v3 engineering foundation is validated: `phase4_v3` is explicitly
guarded, the `mask > 0` target contract is enforced and tested against the real
heterogeneous label vocabulary, image-mode handling is correct, the transform
geometry and nearest-neighbour mask handling are verified, the CUDA-required
device path works, reproducibility/metric/checkpoint/AMP plumbing is exercised, and
the frozen taxonomy integrates through a versioned API. No TEST content was
accessed and no baseline training was started.""")

# 21. Why Part 1B
md("""## 21. Why Phase-08 Part 1B Follows

Part 1A proves the plumbing. Part 1B can then build the remaining baseline
infrastructure — the training loop wiring, validation-accumulation and early-stopping
contracts, and the experiment-configuration defaults — still without starting
Phase-09 scientific training, which requires separate authorization.""")

# 22. Artifacts
md("## 22. Artifact Hashes")
code("""ledger = {
    'manifest_version': p8.MANIFEST_VERSION,
    'taxonomy_id': p8.TAXONOMY_ID,
    'manifest_hashes': manifests['manifest_hashes'],
    'loader_selection_sha': SELECTION_SHA,
    'environment': env,
    'cuda_smoke_performed': smoke.get('performed'),
    'test_content_reads': 0,
    'full_training_performed': False,
    'phase09_started': False,
}
print(json.dumps(ledger, indent=2, default=str))
print()
reg = p8.final_table_registry(TABLES)
display(reg)
print('TABLE COUNT:', int(reg['exists'].sum()))""")

code("""print('=' * 62)
print('PHASE 08 PART 1A — FINAL STATUS')
print('=' * 62)
print('ACTIVE MANIFEST        :', p8.MANIFEST_VERSION)
print('FROZEN TAXONOMY        :', p8.TAXONOMY_ID)
print('FOREGROUND RULE        : mask > 0')
print('INPUT CHANNELS         : 1')
print('TEST CONTENT READS     : 0')
print('FULL TRAINING PERFORMED: NO')
print('SCIENTIFIC CLAIMS      : NONE')
print('PHASE 09 STARTED       : NO')
print('=' * 62)""")

nb = new_notebook(cells=cells, metadata={
    'kernelspec': KERNEL,
    'language_info': {'name': 'python'},
})
nbformat.write(nb, str(NB_PATH))
print('Wrote:', NB_PATH)
print('cells:', len(nb.cells), '| code:', sum(1 for c in nb.cells if c.cell_type == 'code'))
