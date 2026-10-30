# Phase 09 Baseline Training — Code Directory

## Structure

- `train_phase09_clean_v3.py` — **FROZEN execution provenance**. This is the canonical
  scientific training runner that executed the clean-v3 UNet baseline. It was run once,
  produced the checkpoint and history, and must not be modified, moved, or reformatted.
  SHA-256: `28fb9a536873a441ae68f4bad47f3a4309a5ea531b1834a7ac1669304432a5b4`

- `phase09_training_review.py` — **Read-only reviewer / analysis support**. Contains
  reusable functions for loading history, verifying checkpoint provenance, generating
  training curves, and deterministic VAL gallery selection. It does NOT train.

## What happened in Part 1A

The actual clean-v3 scientific training was executed by `train_phase09_clean_v3.py`.
No other training implementation exists for this experiment.

Experiment: `phase9_kub_unet_baseline_seed42_512_clean_v3`

## What Part 1B does

Part 1B packages the completed run for reviewer inspection:
- Verifies artifact SHAs against recorded provenance
- Confirms history integrity (contiguous epochs, strict-max best epoch, early-stop consistency)
- Confirms checkpoint metadata matches history and config
- Generates training-curve figures
- Creates a deterministic VAL prediction gallery
- Produces the reviewer notebook

## Boundaries

- **No training** in the reviewer notebook or support code.
- **TEST remains locked** — no TEST images, masks, metrics, or visualizations.
- **No Phase-10 models** (`attention_unet`, `unetpp`, `deeplabv3plus`) are involved.
- Historical v2 checkpoints remain immutable.
