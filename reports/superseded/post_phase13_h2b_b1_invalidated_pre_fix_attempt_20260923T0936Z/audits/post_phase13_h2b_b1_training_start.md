# PHASE-13 CLEAN-v3 LOCALIZER TRAINING START

- experiment_id: `post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_deploymentbalance_seed42_clean_v3`
- protocol: R2 + R2A_LOSS_BINDING
- loss: `src.losses.soft_target_focal_bce.SoftTargetFocalBCE` gamma=2.0 soft-target focal BCE (no Dice)
- config_sha: `2ceaa71d614475fed54248c353e247848f41df3ace423e3c36aba63d59431152`
- population: TRAIN 770 / VAL 103
- TEST reads: 0
