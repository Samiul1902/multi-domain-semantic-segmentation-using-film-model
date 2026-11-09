# POST-PHASE-13 H2B-B1 LOCALIZER TRAINING START

- experiment_id: `post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_deploymentbalance_seed42_clean_v3`
- protocol: H2B_OBJECTIVE_ONLY__H2A_DEPLOYMENT_BALANCED_SELECTION_CARRY_FORWARD
- loss: `src.losses.soft_target_focal_bce.SoftTargetFocalBCE` gamma=2.0 soft-target focal BCE (no Dice)
- config_sha: `0ee34404c67e36aa27ef880c59295208f662908af996cf634f6a922875340f12`
- population: TRAIN 770 / VAL 103
- TEST reads: 0
