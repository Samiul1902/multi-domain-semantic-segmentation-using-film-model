# Reproducibility Guide

Two very different activities live in this repository. Keep them apart:

| | Analysis-only (safe, supported) | Training (gated, not supported here) |
|---|---|---|
| What it does | reads saved artifacts, recomputes metrics, rebuilds figures | runs optimisers, writes checkpoints |
| Command | `full_doc_report/Scripts/*.py` | `scripts/training/*.py` |
| Requires | repository + saved evidence | GPU, datasets, **authorization** |
| Status | works out of the box | not authorised; C1/C2/C3 blocked |

---

## 1. Environment

Verified working configuration:

| Component | Version |
|---|---|
| Python | 3.11.9 |
| PyTorch | 2.6.0+cu124 |
| CUDA | 12.4 |
| GPU used for the recorded runs | NVIDIA GeForce RTX 3060 Ti (8 GB) |
| OS | Windows (paths below assume PowerShell) |

Dependency specification: [`requirements.txt`](../requirements.txt),
[`pyproject.toml`](../pyproject.toml).

```powershell
# from the repository root
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> **Dependency gap (verified).** `requirements.txt` omits two packages that the
> analysis scripts import: **`scipy`** (used for HD95 surface distances) and
> **`Pillow`** (image I/O). `torchvision` usually pulls Pillow in, but `scipy`
> does not come from any listed package. If `build_metrics.py` fails with
> `ModuleNotFoundError: scipy`, run
> `.\.venv\Scripts\python.exe -m pip install scipy`.
> This is a real defect in the manifest, recorded rather than silently patched.

### Interpreter note for this host

On the machine where the results were produced, launching the venv interpreter
directly from an MSYS2/Git-Bash parent crashes with `0xC0000005` (a sandbox hook
DLL fault, external to Python). Launching from a native Windows parent works:

```powershell
# native parent — this is the supported invocation
.\.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"
```

If you hit the same fault, run everything from PowerShell or `cmd.exe` rather
than Git Bash.

---

## 2. Locate the training configuration

Every run wrote a closure or run record next to its history:

| File | Contains |
|---|---|
| `experiments/<run>/closure.json` | architecture, loss, optimizer, scheduler, epochs, best epoch, checkpoint SHA-256 |
| `experiments/<run>/run.json` | fold-level run metadata, parameter count, bindings |
| `experiments/<run>/history.csv` | per-epoch metrics (the ground truth for all curves) |

Example:

```powershell
Get-Content experiments\phase21_global_medfilm_fourdomain_seed42_clean_v3\closure.json
```

---

## 3. Inspect checkpoint references (without the weights)

Weights are **not** in the repository (`checkpoints/` and `*.pt` are ignored).
Identity is recorded as SHA-256:

```powershell
Get-Content full_doc_report\REMEDFILM_FULL_COMPONENT_REGISTRY.json
```

That file records, per component: implementation class, checkpoint path,
measured parameter count (re-derived from the state dict), and SHA-256.

If you do hold the weights, verify them with:

```powershell
Get-FileHash checkpoints\phase21_global_medfilm_fourdomain_seed42_clean_v3\best.pt -Algorithm SHA256
# expect 286689FDD5C63AD75A383151D267AF8B476E7A98327632DE292CE6ED5B5BA1B7
```

---

## 4. Run the safe analysis notebooks

`ANALYSIS_ONLY` is enforced, not merely declared. Each notebook installs a
`sys.addaudithook` that blocks process launches, writes outside the report
directory, and reads of the protected TEST manifest; it also replaces
`torch.optim.*` constructors and `Module.train(True)` with raising callables.
Four negative controls must print `blocked` or the notebook aborts.

```powershell
# execute the whole verified notebook family (22 notebooks)
.\.venv\Scripts\python.exe full_doc_report\Scripts\execute_notebooks.py
```

Expected tail:

```
TOTAL 22 notebooks | 292/292 cells | OK
```

Individual notebooks can be opened and run in Jupyter; they will refuse to train.

---

## 5. Rebuild the figures

```powershell
# research figures (45+ panels into full_doc_report/figures/<section>/)
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_figures.py

# methodology diagrams (assets/figures/*.svg|pdf|png)
.\.venv\Scripts\python.exe assets\figures\generate_methodology.py
```

Both are deterministic given the saved evidence.

---

## 6. Recompute the historical metrics

```powershell
# re-score the 808 saved VAL808 masks -> REMEDFILM_INTERNAL_METRICS.csv
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_metrics.py

# rebuild every table from source artifacts
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_training_history.py
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_tables_extra.py
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_component_parameters.py
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_required_tables.py
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_verified_tables.py
```

`build_metrics.py` is the strongest check available: it reproduces the frozen
Phase 27 paired macro Δ Dice to **1.8 × 10⁻⁷** from masks alone.

---

## 7. Verify everything

```powershell
.\.venv\Scripts\python.exe full_doc_report\Scripts\verify_verified.py   # 38/38
.\.venv\Scripts\python.exe full_doc_report\Scripts\verify_reconstruction.py  # 36/36
```

Results land in `full_doc_report/REMEDFILM_FINAL_QA_CHECKS.json` and
`full_doc_report/FINAL_QA_CHECKS.json`.

---

## 8. Run the tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ -q
```

Some tests require weights or GPU and will skip or fail without them. A test
that merely constructs a synthetic tensor is **not** evidence that an experiment
ran.

---

## 9. What you must not do

| Action | Why |
|---|---|
| Run `scripts/training/*.py` | writes checkpoints, needs authorisation |
| Re-run Phase 39 | the one-shot TEST1683 access is consumed |
| Launch C1 / C2 / C3 | not authorised; see [`PENDING_CONTROLLED_EXPERIMENTS.md`](../full_doc_report/PENDING_CONTROLLED_EXPERIMENTS.md) |
| Modify `manifests/phase4_v3/` | frozen splits |
| Edit `reports/audits/*.json` | frozen evidence |

Nothing in this guide launches an unapproved experiment.

---

## 10. Known reproduction limits

| Limit | Consequence |
|---|---|
| Weights not distributed | FULL-system inference cannot be re-run from this repo alone |
| Datasets not distributed | TRAIN/VAL/TEST cannot be rebuilt; see dataset licences |
| Host clock was unsynchronised | absolute timestamps carry an unquantified offset; only ordering is trustworthy |
| Three "seeds" share one frozen backbone | they measure downstream stability, not end-to-end replication |
| Full-pipeline latency | `NOT_RECORDED` — only forward-only GPU timing exists |
