# H2B-B1 — Independent Selection Replay Verification

- **Status: PASS**
- experiment: `post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_deploymentbalance_seed42_clean_v3`

- replayed best epoch: **31**
- stored best epoch: **31**
- mismatch count: **0**
- max abs term diff: `7.199e-17`
- final bad epochs: stored 15 / replayed 15
- early stop epoch: 46

## Checks

| check | pass | detail |
|---|---|---|
| history_rows_ge_1 | **True** | rows=46 |
| epochs_contiguous_from_1 | **True** | epochs 1..46 |
| no_duplicate_epochs | **True** | dupes=0 |
| history_required_columns | **True** | missing=[] |
| train_loss_all_finite | **True** |  |
| val_loss_all_finite | **True** |  |
| selection_quantities_all_finite | **True** | zero-proposal epochs legitimately carry 0.0 (not NaN) |
| no_nan_inf_events_recorded | **True** | events=0 |
| selection_replay_zero_mismatches | **True** | mismatches=0 | max_abs_term_diff=7.199e-17 | best_epoch 31 |
| replay_is_new_best_agrees_per_epoch | **True** |  |
| replay_bad_epochs_agrees_per_epoch | **True** |  |
| best_pt_bad_epochs_is_zero_at_best_save | **True** | best.pt bad_epochs=0 (state at best save) |
| final_bad_epochs_match | **True** | latest.pt=15 replayed=15 |
| history_final_bad_epochs_matches | **True** | history=15 replayed=15 |
| final_bad_epochs_reached_patience | **True** | patience=15 |
| early_stop_epoch_matches_history_end | **True** | replayed stop=46 history end=46 |
| latest_pt_is_final_epoch | **True** | latest.pt epoch=46 history end=46 |
| best_epoch_state_matches | **True** | latest.pt best_epoch=31 replayed=31 |
| checkpoint_has_no_stale_loss_alpha | **True** |  |
| checkpoint_has_no_stale_loss_beta | **True** |  |
| checkpoint_loss_gamma_is_2.0 | **True** |  |
| checkpoint_loss_class_is_h2b | **True** |  |
| checkpoint_loss_label_is_h2b | **True** |  |
| checkpoint_h2b_protocol_sha_bound | **True** |  |
| checkpoint_h2b_loss_module_sha_bound | **True** |  |
| checkpoint_objective_change_id | **True** |  |
| checkpoint_selection_rule_carried_from_h2a | **True** |  |
| no_phase13_parent_objective_as_active | **True** |  |
| test_reads_zero | **True** | no TEST access performed |
| trajectory_reproduction_gate_absent | **True** | SEC 11: no loss-trajectory gate vs H2A/Phase13 (objective changed) |

**No trajectory-reproduction gate vs H2A or Phase-13** (SEC 11: the objective changed, so loss magnitudes are not comparable across branches).
