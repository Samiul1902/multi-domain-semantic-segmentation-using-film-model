# Phase 14 Part 2C — Source Continuity & Final Training Closure Audit

**Experiment ID:** `phase14_diag_regional_unet_oracletrain_a3_seed42_v1`  
**Training Validity Decision:** `VALID_SAME_EXPERIMENT`  
**Phase 14 Part 2 Status:** COMPLETE (Training and Checkpoint Selection Finished)

---

## 1. Source-Timestamp & Continuity Investigation

### Timeline of Key Events
- **Original Source Written:** `2026-09-18 12:35:46` (`scripts/training/train_phase14_refiner.py`)
- **Original Process Started:** `2026-09-18 12:35:58` (Task `task-2627`, PID 13412)
- **12:38 Activity:** At `12:38:04–12:38:15`, `write_to_file` created a separate reporting script `scripts/training/finalize_part2_reporting.py` in the same directory. No modifications were made to `train_phase14_refiner.py` during the initial execution.
- **Power Interruption:** Server restart interrupted the run after epoch 25 was safely committed to `latest.pt`.
- **Pre-Resume Edit:** `2026-09-18 20:23:28` (Two minor edits to restore and persist `loader_generator_states` in checkpoint dictionaries).
- **Resumed Process Started:** `2026-09-18 20:24:30` (Task `task-2711`)

### Exact Code Differences
Line-by-line unified diff between the initial source (`SHA-256: 21090b6753d9aaf07240ae8414a5b35c5a509765f5398e967de7fd778af94cff`) and the resumed source (`SHA-256: b3824384b1bd1e7e0e0e45b3ae732c2460a49cc64f8df00f24619b00be13ee79`):
1. **Lines 149–151:** Restored `generator.set_state(...)` from `state['loader_generator_states']` if present (evaluated to `False` on epoch 25 resume because RNG state was already restored via `restore_random_state`).
2. **Lines 264–267:** Passed `loader_generator_states={'train': generator.get_state()}` into `save_training_checkpoint`.
3. **Line 287:** Trailing newline.

**Finding:** **ZERO scientific training semantics changed.** The model architecture, loss function, optimizer, learning rate schedule, data sampling, batch size, AMP, and early stopping rules were 100% identical between epochs 1–25 and epochs 26–29.

---

## 2. Mathematical & State Continuity Verifications

| Checkpoint / Metric | Pre-Resume (Epoch 25) | Resumed / Final (Epoch 29) | Status |
| :--- | :--- | :--- | :--- |
| **Completed Epochs** | 25 | 29 | Continuous (26–29 appended) |
| **Batches per Epoch** | 629 | 629 | PASS |
| **Global Step** | 15,725 ($25 \times 629$) | 18,241 ($29 \times 629$) | PASS |
| **Early Stopping Progression** | Bad Epochs = 11 | Bad Epochs = 15 (Ep 26: 12, Ep 27: 13, Ep 28: 14, Ep 29: 15) | PASS |
| **Stop Reason** | In Progress | `EARLY_STOPPING_PATIENCE_15` | Normal termination |
| **Scheduler Trajectory** | `lr = 8.6448e-05` (Ep 25) | `lr = 8.5355e-05` (Ep 26) $\to$ `8.1871e-05` (Ep 29) | Exact CosineAnnealingLR ($\Delta < 10^{-19}$) |
| **Best Epoch** | 14 | 14 | Preserved |
| **Best Val Crop Dice** | `0.8437233057743712` | `0.8437233057743712` | Preserved |
| **Best Checkpoint SHA-256** | `89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0` | `89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0` | Unchanged |
| **Latest Checkpoint SHA-256**| `5a39cde21ee8e61f78f94b72006d9e15b1d3c675c02ce87912670d03f695ee22` | `7cb4eb5c8316b1d6e2dba90ace9b49fea30432a4f825d515b7be15e79f80c5af` | Updated to Ep 29 |

---

## 3. Governance and Final Status
- **Training Executed in Part 2C:** NO (Audit and verification only)
- **Optimizer Steps in Part 2C:** 0
- **TEST Content Reads:** 0
- **TEST Metrics:** NONE
- **External Data Access:** NO
- **Experiment A Modified:** NO
- **Full Diagnostic Evaluation Executed:** NO (Deferred to prospective Part 3)
- **Phase 15 Status:** NOT AUTHORIZED
- **Validity Decision:** `VALID_SAME_EXPERIMENT`

