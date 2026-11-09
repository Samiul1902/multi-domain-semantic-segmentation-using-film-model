# PHASE-13 PART-1B-R0-R1 — STATIC / UNIT VALIDATION (RESOLVED)

**Artifact type:** `NON_SCIENTIFIC_STATIC_UNIT_VALIDATION_RESOLVED`
**Experiment ID:** `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3`
**Overall status:** `PASS` · **Gate:** `PASS_READY_FOR_SUPERVISOR_TRAINING_REAUTHORIZATION`

---

## 1. Supersession

Additive. The prior validation pair is **preserved on disk**:

| Artifact | SHA-256 | State |
|---|---|---|
| `…_execution_binding_validation.json` | `294f568a…673` | PRESERVED (prior status `CHECK_REQUIRED`) |
| `…_execution_binding_validation.md` | `97530789…bab` | PRESERVED |

The prior `CHECK_REQUIRED` was caused by exactly one unresolved loss-binding ambiguity. That ambiguity is resolved; the prior audit is retained as history rather than edited.

---

## 2. Execution governance

No training · no optimizer · no forward pass · no VAL/TRAIN inference · no proposals · no grid search · no TEST access · no CUDA request · no model construction · no run lock · no checkpoint write. Importing the runner touches CUDA **zero** times (instrumented `torch.cuda.is_available` call count = 0).

---

## 3. Gate results (A–P)

| Gate | Requirement | Result |
|---|---|---|
| A | `CenterNetFocalLoss` is the only executable criterion | **PASS** |
| B | `alpha == 2.0` | **PASS** |
| C | `beta == 4.0` | **PASS** |
| D | No `SoftFocalDiceLoss` on the executable path | **PASS** |
| E | No `NotImplementedError` on the executable path | **PASS** |
| F | Exactly one proposal configuration | **PASS** |
| G | No product / grid loop | **PASS** |
| H | 4-term selection tuple unchanged | **PASS** |
| I | Diagnostics structurally excluded from selection | **PASS** |
| J | `set_seed` before model construction | **PASS** |
| K | TRAIN loader generator exists | **PASS** |
| L | Generator state persisted | **PASS** |
| M | Resume mismatch fails loudly | **PASS** |
| N | Manifest hashes non-empty | **PASS** |
| O | `heatmap_resolution = 128` explicit | **PASS** |
| P | Binding CSV parses with pandas | **PASS** |

**Test suites:** R0-R1 gate suite 17/17 passed; selection suite 17/17 passed; **combined 34/34 passed, 0 failed.**

---

## 4. Binding CSV repair

| Property | Value |
|---|---|
| Path | `reports/tables/phase13_clean_v3_executable_config_binding.csv` |
| SHA-256 | `52b16c7f…652` |
| Prior defect | `ParserError: Expected 6 fields in line 66, saw 7` (unquoted comma inside `scientific_source`) |
| Repair method | real CSV writer (`pandas.DataFrame.to_csv`) |
| `pandas.read_csv` with no special options | **SUCCEEDS** (130 rows × 6 cols) |
| Prior `CHECK_REQUIRED` rows preserved | 9 (role `SUPERSEDED_PRIOR_CHECK_REQUIRED_AUDIT`) |
| Loss rows updated to | `R2A_LOSS_BINDING_EXECUTING` |
| Repair script | `scripts/audits/repair_phase13_clean_v3_binding_csv.py` |

---

## 5. Resume safety

Resume requires **all** of: `--resume`, `latest.pt` present, `history.csv` present, contiguous history, final epoch matching `latest.pt`, and matching identity on `experiment_id` / `manifest_version` / `taxonomy_id` / `input_resolution` / `seed` / R2 SHA / R2A SHA / config SHA / loss label / loss class / alpha / beta / heatmap resolution / proposal config / selection term names / manifest hashes.

Failure mode is a **loud `RuntimeError`** — never a silent restart. `--resume` absent while scientific state exists → **STOP** (no overwrite).

---

## 6. State

Training **NOT STARTED** · regional gate **NOT_DECIDED** · Phase 14 **NOT STARTED**
**Next action:** `WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_REAUTHORIZATION`
