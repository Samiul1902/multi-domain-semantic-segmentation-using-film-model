# Phase 11-R1 — Training Provenance, Manual Inference, and Auto-Domain Interface

**Status: PASS**  
**Scope: utility / presentation / interface patch only; no retraining or metric changes**

## Provenance and Interface Summary

| Component | Status / Path | Details |
| --- | --- | --- |
| UNet++ Training History | experiments/phase10_kub_unetpp_seed42_512/history.csv | SHA256: `143acaeab463c7d156b612e52f09ca782dc7faa79ce59a88ea2719ff3a8760fd` (92 epochs, best epoch 77) |
| UNet++ Loss Curve | reports/figures/phase11_kub_failure_analysis/phase11_unetpp_training_loss_provenance.png | 300+ DPI PNG/SVG/PDF generated |
| UNet++ VAL Dice Curve | reports/figures/phase11_kub_failure_analysis/phase11_unetpp_val_dice_provenance.png | 300+ DPI PNG/SVG/PDF generated |
| UNet++ LR Curve | reports/figures/phase11_kub_failure_analysis/phase11_unetpp_lr_provenance.png | 300+ DPI PNG/SVG/PDF generated |
| Manual KUB Predictor | src/inference/kub_predict.py | predict_kub & show_kub_prediction (threshold 0.5, UNet++ best.pt) |
| Generic Predict Interface | src/inference/predict.py | predict(..., task='auto') raises NotImplementedError safely |
| Demo Notebook | notebooks/09b_kub_manual_prediction_demo.ipynb | SHA256: `529dbc7d1564cd64f85914e06c8a2edb85dba74b0b53351d427c0cb6be862841` (executed without errors/training) |
| Failure Analysis Notebook | notebooks/09_kub_failure_analysis.ipynb | SHA256: `1b362ab4680205fd7b5fb66327de4844c77850c40a23de338b8e6147eb8929d3` (provenance section added) |

## Key Integrity Declarations
- **Retraining**: NO
- **Metrics Changed**: NO
- **TEST Accessed**: NO (0 reads; blocked by `TestAccessError`)
- **External Data Accessed**: NO
- **Experiment A Modified**: NO
- **Phase 12 Executed**: NO
- **Auto Domain Router Trained**: NO (Interface design & safety exception enforced)
