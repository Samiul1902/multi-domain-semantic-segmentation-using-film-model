# PHASE-13 CLEAN-v3 LOCALIZER TRAINING START

- experiment_id: `post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3`
- protocol: R2 + R2A_LOSS_BINDING
- loss: `src.losses.localization.CenterNetFocalLoss` alpha=2.0 beta=4.0 (no Dice)
- config_sha: `b96223eecade2938a9ca9733ddcfba1bbd2f7cd34155ab4d48a1fba51f09bc33`
- population: TRAIN 770 / VAL 103
- TEST reads: 0
