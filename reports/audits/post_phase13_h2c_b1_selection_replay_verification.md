# H2C-B1 — Independent Selection Replay Verification

- **Status: PASS**
- experiment: `post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3`

- replayed best epoch: **57**
- stored best epoch: **57**
- mismatch count: **0**
- max abs term diff: `9.888e-17`
- final bad epochs: stored 15 / replayed 15
- early stop epoch: 72

## Checks

| check | pass | detail |
|---|---|---|
| history_rows_ge_1 | **True** | rows=72 |
| epochs_contiguous_from_1 | **True** | epochs 1..72 |
| no_duplicate_epochs | **True** | dupes=0 |
| history_required_columns | **True** | missing=[] |
| train_loss_all_finite | **True** |  |
| val_loss_all_finite | **True** |  |
| selection_quantities_all_finite | **True** | zero-proposal epochs legitimately carry 0.0 (not NaN) |
| no_nan_inf_events_recorded | **True** | events=0 |
| selection_replay_zero_mismatches | **True** | mismatches=0 | max_abs_term_diff=9.888e-17 | best_epoch 57 |
| replay_is_new_best_agrees_per_epoch | **True** |  |
| replay_bad_epochs_agrees_per_epoch | **True** |  |
| best_pt_bad_epochs_is_zero_at_best_save | **True** | best.pt bad_epochs=0 (state at best save) |
| final_bad_epochs_match | **True** | latest.pt=15 replayed=15 |
| history_final_bad_epochs_matches | **True** | history=15 replayed=15 |
| final_bad_epochs_reached_patience | **True** | patience=15 |
| early_stop_epoch_matches_history_end | **True** | replayed stop=72 history end=72 |
| latest_pt_is_final_epoch | **True** | latest.pt epoch=72 history end=72 |
| best_epoch_state_matches | **True** | latest.pt best_epoch=57 replayed=57 |
| checkpoint_loss_class_is_h2a_focal | **True** |  |
| checkpoint_loss_alpha_is_2.0 | **True** |  |
| checkpoint_loss_beta_is_4.0 | **True** |  |
| checkpoint_records_h2c_head_identity | **True** |  |
| checkpoint_records_h2c_protocol_sha | **True** | checkpoint=91166259c10a84e9... file=91166259c10a84e9... |
| checkpoint_records_h2c_head_structure | **True** |  |
| state_dict_has_h2c_conv3x3 | **True** |  |
| state_dict_has_h2c_conv1x1 | **True** |  |
| head_conv3x3_shape_is_16x16x3x3 | **True** |  |
| test_reads_zero | **True** | no TEST access performed |
| trajectory_reproduction_gate_absent | **True** | SEC 11: no loss-trajectory gate vs H2A/Phase13 (objective changed) |

**No trajectory-reproduction gate vs H2A or Phase-13** (SEC 11: the objective changed, so loss magnitudes are not comparable across branches).
