# POST-PHASE-13 H2-A-B1 — TRAINING TRAJECTORY REPRODUCTION

- status: **PASS**
- H2A history SHA: `ed96c4b617a8940c30df30d9a9b8f562819e31d1370b31ee60776142fd077b99`
- Phase-13 history SHA: `344cfc016fd88e7e697c6afa0ffbf839b3d3b3c16b54024dc3537586528d4c5b`

| quantity | value |
|---|---|
| overlapping epochs | 68 |
| epochs aligned | True |
| max abs train_loss diff | 4.441e-16 |
| max abs val_loss diff | 0.000e+00 |
| train_loss exact match | False |
| val_loss exact match | True |
| LR mismatches | 0 |
| gradient semantics changed | **NO** |

## Checkpoint model-state cross-checks

| epoch | reference | tensors | max abs diff | mismatching | material |
|---|---|---|---|---|---|
| — | no overlapping historical checkpoint reached | — | — | — | — |

The H2A run changes CHECKPOINT SELECTION ONLY. Its gradient-update semantics must therefore be identical to the Phase-13 clean-v3 run, so train_loss/val_loss must agree epoch-by-epoch until the two runs' early stopping diverges.

Model tensors are compared, NOT whole-file SHAs, because the checkpoint metadata/selection tuple legitimately differs.
