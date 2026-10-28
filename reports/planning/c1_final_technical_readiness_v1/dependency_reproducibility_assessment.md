# C1 — Dependency Reproducibility Assessment v1.0

Status: `ASSESSED__NO_INSTALL_PERFORMED`
Scope: read-only inspection of the actual installed environment and dependency specifications.
No package installation, upgrade, downgrade, or replacement was performed.

---

## 1. Verified runtime identity

| Item | Measured value |
|---|---|
| Interpreter | `D:/Softfors/jup/.venv/Scripts/python.exe` |
| Python | 3.11.9 (CPython, MSC v.1938, 64-bit) |
| Platform | Windows-10-10.0.26200-SP0, AMD64 |
| torch | 2.6.0+cu124 (PyPI `pytorch_cu124` wheel index) |
| torchvision | 0.21.0+cu124 |
| CUDA build in torch | 12.4 |
| cuDNN | 9.1.0 (90100) |
| GPU | NVIDIA GeForce RTX 3060 Ti, CC 8.6, 8192 MiB |
| Driver | 610.88 |

The `+cu124` local version tag confirms the wheel came from the PyTorch CUDA-12.4
index, not from a stock PyPI `torch` wheel. This distinction matters: a plain
`pip install torch` on this host would resolve to a different build and is not a
reproducible substitute.

## 2. Classification of dependencies

### 2.1 Version-pinned and available — 15/15 direct dependencies

All direct dependencies declared in `requirements.txt` / `pyproject.toml` are
installed and importable. The exact installed set is recoverable from
`pip freeze` (77 packages total, including transitive).

| Package | Installed | Reproducible source |
|---|---|---|
| torch | 2.6.0+cu124 | pytorch cu124 index |
| torchvision | 0.21.0+cu124 | pytorch cu124 index |
| numpy | 2.4.6 | PyPI |
| pandas | 3.0.5 | PyPI |
| matplotlib | 3.11.2 | PyPI |
| scikit-learn | 1.9.1 | PyPI |
| tqdm | 4.70.1 | PyPI |
| pyyaml | 6.0.3 | PyPI |
| scikit-image | 0.26.0 | PyPI |
| tensorboard | 2.21.0 | PyPI |
| seaborn | 0.13.2 | PyPI |
| ipython | 9.17.1 | PyPI |
| nbformat | 5.11.1 | PyPI |
| nbclient | 0.11.0 | PyPI |
| ipykernel | 7.3.0 | PyPI |

### 2.2 Installed but NOT reproducibly specified — **the material gap**

`requirements.txt` and `pyproject.toml` contain **bare package names with zero
version specifiers**. There is no `==`, no `>=`, no constraint file, no lock
file, and no hash list.

Consequence: a fresh `pip install -r requirements.txt` today would resolve to
whatever is newest, which is **not** the verified set. The environment is
reproducible only via the captured `pip freeze` snapshot, not via the declared
specification. This is a *specification* gap, not an *installation* gap — the
current venv itself is intact and verified.

Notably, several installed versions are unusually far ahead of typical
research baselines (`pandas 3.0.5`, `numpy 2.4.6`, `scikit-learn 1.9.1`,
`matplotlib 3.11.2`). These are the versions against which the 34 synthetic
tests actually pass. Pinning must therefore reproduce **these** versions, not
"latest".

### 2.3 Workspace-local or untracked

| Path | Nature |
|---|---|
| `.venv/` | Virtual environment, gitignored, machine-local |
| `src/research/c1_film/` | Tracked in git at `ec51359` |
| `tests/test_c1_*.py` | Tracked in git at `ec51359` |
| `scripts/verification/` | New in this task, untracked |
| `reports/planning/c1_film_attribution_v1/` | Tracked (force-added; `reports/` is gitignored) |
| `reports/planning/c1_final_technical_readiness_v1/` | New in this task, gitignored |
| `reports/audits/c1_synthetic_cuda_verification_v1_0.json` | New in this task, gitignored |
| `manifests/phase4_v3/` | Data manifests, digest-bound, not a package dependency |
| `checkpoints/` | Gitignored; historical artifacts, not a dependency |

### 2.4 Missing or incompatible

**None detected.** All imports used by the C1 training path resolve:
`torch`, `numpy`, `pandas` (via dataset frames), `src.*` modules,
`scripts.training.phase21_common`.

The CUDA stack is compatible: torch cu124 ↔ driver 610.88 ↔ CC 8.6.
AMP (`torch.amp.autocast` / `GradScaler`) verified functional on this GPU.

## 3. Reproducible environment specification

Delivered as `reproducible_environment_spec.json` in this directory. It records:

- exact interpreter path and Python version,
- exact torch/torchvision builds with the correct wheel index URL,
- all 15 direct dependency pins,
- key transitive pins,
- the four-step reconstruction procedure,
- explicit exclusion of secrets, datasets, and checkpoints.

Reconstruction is a **two-stage** install: the CUDA wheels must come from the
PyTorch index first, then the remainder from PyPI. Installing torch from PyPI
would silently produce a different (possibly CPU-only or differently-CUDA'd)
build.

## 4. Constraints honoured

- No package was installed, upgraded, downgraded, or removed.
- No frozen dependency was silently replaced with a newer version.
- The specification contains no secrets, credentials, dataset contents, or
  checkpoints.
- The captured versions are the versions under which the 34 synthetic tests and
  23 subtests actually passed.

## 5. Residual risk

The environment is reproducible **only if** the `pip freeze` snapshot is treated
as authoritative. If a future operator runs `pip install -r requirements.txt`,
the resolved set will differ from the verified set. Before any authorized C1
training, the declaration files should be pinned to the verified versions — but
that edit is a specification change and is deliberately **not** made in this
readiness task.
