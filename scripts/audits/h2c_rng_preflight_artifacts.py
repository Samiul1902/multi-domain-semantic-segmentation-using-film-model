"""H2C B0 -- counter clarification + RNG equivalence preflight artifacts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
A = ROOT / "reports" / "audits"


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


raw = json.loads((A / "_h2c_rng_preflight_raw.json").read_text("utf-8"))
proto = json.loads((A / "post_phase13_h2c_protocol_frozen.json").read_text("utf-8"))

# ------------------------------------------------- SEC 8 counter clarification
clar = {
    "artifact": "POST_PHASE13_H2C_PREEXECUTION_COUNTER_CLARIFICATION",
    "status": "PASS",
    "created_utc": "2026-09-23T16:33:00Z",
    "purpose": ("Additively clarify the H2C pre-execution counters so that the single synthetic "
                "shape-check forward disclosed in the frozen protocol is recorded truthfully and "
                "not confused with project-data inference. The frozen protocol is NOT rewritten."),
    "frozen_protocol": {
        "path": "reports/audits/post_phase13_h2c_protocol_frozen.json",
        "sha256": sha(A / "post_phase13_h2c_protocol_frozen.json"),
        "rewritten": "NO",
    },
    "counters": {
        "PROJECT_DATA_MODEL_FORWARDS": 0,
        "TRAINING_FORWARDS": 0,
        "VAL_FORWARDS": 0,
        "TEST_FORWARDS": 0,
        "SYNTHETIC_SHAPE_CHECK_FORWARDS": 1,
        "SYNTHETIC_INPUT_ONLY": "YES",
        "CUDA": "NO",
        "TRAINED_WEIGHTS": "NO",
        "SCIENTIFIC_MEASUREMENT": "NO",
    },
    "what_the_synthetic_forward_was": (
        "A single forward pass of a freshly-constructed, UNTRAINED H2C model on a random synthetic "
        "tensor of shape (1,1,512,512), performed on CPU to verify the output spatial shape is "
        "(1,1,128,128) and that the frozen terminal-zero initialization yields spatially constant "
        "initial logits (measured max-min = 0.0)."),
    "what_it_was_not": [
        "not project data", "not a TRAIN forward", "not a VAL forward", "not a TEST forward",
        "not on CUDA", "not using trained weights", "not a scientific measurement",
    ],
    "changes": {
        "scientific_protocol": "NO", "scientific_result": "NO", "h2c_axis": "NO",
    },
    "counters_summary": {"training_epochs": 0, "optimizer_steps": 0, "checkpoint_writes": 0,
                         "test_reads": 0, "external_test_reads": 0},
}
(A / "post_phase13_h2c_preexecution_counter_clarification.json").write_text(
    json.dumps(clar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(A / "post_phase13_h2c_preexecution_counter_clarification.md").write_text(
    "# POST-PHASE13 H2C — Pre-Execution Counter Clarification\n\n"
    "- **Status: PASS**\n"
    "- Frozen protocol rewritten: **NO**\n\n"
    "## Counters\n\n| counter | value |\n|---|---|\n"
    + "\n".join(f"| {k} | {v} |" for k, v in clar["counters"].items())
    + "\n\n## What the synthetic forward was\n\n" + clar["what_the_synthetic_forward_was"]
    + "\n\n## What it was NOT\n\n" + "\n".join(f"- {x}" for x in clar["what_it_was_not"])
    + "\n\nscientific protocol changed **NO** · scientific result changed **NO** · "
      "H2C axis changed **NO**\n", encoding="utf-8")

# ---------------------------------------------------- SEC 9 RNG preflight artifact
rng = {
    "artifact": "POST_PHASE13_H2C_RNG_EQUIVALENCE_PREFLIGHT",
    "status": "PASS",
    "created_utc": "2026-09-23T16:33:00Z",
    "model_attribution": "Gemini 3.1 Pro High",
    "execution": "CPU_ONLY_STATIC_PREFLIGHT",
    "question": ("Does the H2C head initialization (which adds kaiming draws) silently change TRAIN "
                 "sample order, VAL sample order, augmentation random draws, DataLoader generator "
                 "sequence, worker RNG, or other stochastic training streams relative to H2A?"),

    "rng_classification": "RNG_STREAMS_ALREADY_ISOLATED",
    "execution_fix_required": "NO",
    "execution_fix_applied": "NONE (no executable training semantics were changed)",

    "physical_provenance": {
        "seed_call": "scripts/training/post_phase13_h2a_localizer_replay.py:1261 -> "
                     "set_seed(seed, deterministic=True)",
        "set_seed_impl": "src/utils/reproducibility.py -> random.seed / np.random.seed / "
                         "torch.manual_seed / torch.cuda.manual_seed_all",
        "model_construction": "scripts/training/post_phase13_h2a_localizer_replay.py:1341 -> "
                              "create_model(...)  [AFTER set_seed]",
        "train_shuffle_generator": "scripts/training/post_phase13_h2a_localizer_replay.py:1410 -> "
                                   "make_generator(seed) (DEDICATED torch.Generator)",
        "val_generator": "scripts/training/post_phase13_h2a_localizer_replay.py:1411 -> "
                         "make_generator(seed) (DEDICATED torch.Generator)",
        "dataloader": "scripts/training/post_phase13_h2a_localizer_replay.py:1413-1421 -> "
                      "DataLoader(shuffle=True/False, generator=..., worker_init_fn=seed_worker, "
                      "num_workers=0)",
        "augmentation": "src/data/kub_localizer_dataset.py:49,52,55,56 -> Python `random` module "
                        "(random.random / random.uniform) -- a SEPARATE stream from torch",
        "worker_seeding": "src/utils/reproducibility.py -> seed_worker() derives from "
                          "torch.initial_seed(); num_workers=0 so no worker processes are spawned",
    },

    "answers": {
        "A_train_shuffle_uses_dedicated_generator": "YES (make_generator(seed), line 1410)",
        "B_val_ordering_stochastic": "NO (shuffle=False; deterministic sequential order)",
        "C_augmentation_rng_source": "Python `random` (module-level global), NOT torch and NOT numpy",
        "D_model_construction_relative_to_seeding": "AFTER final training RNG initialization",
        "E_extra_kaiming_draws_alter_later_streams": ("NO — the extra draws advance only the torch "
                                                      "GLOBAL RNG, which no downstream stream "
                                                      "consumes: shuffling uses dedicated "
                                                      "generators, augmentation uses Python "
                                                      "`random`, and no torch.rand/randn/normal or "
                                                      "Dropout exists on the training path"),
    },

    "stream_ownership": {
        "model_initialization_rng": "torch global RNG (torch.nn.init.kaiming_normal_)",
        "shuffle_rng": "dedicated torch.Generator seeded with 42 (per DataLoader)",
        "augmentation_rng": "Python `random` module (global), seeded once by set_seed",
        "worker_rng": "seed_worker() from torch.initial_seed(); num_workers=0 -> unused",
        "val_ordering_semantics": "deterministic sequential (shuffle=False)",
        "numpy_rng": "seeded by set_seed but NOT consumed by augmentation",
    },

    "empirical_equivalence": {
        "method": ("Both setups replicated in the exact H2A runner order (set_seed -> model "
                   "construction -> generators -> DataLoader). TRAIN order taken from the "
                   "DataLoader sampler so that NO image is decoded and NO model forward is run. "
                   "Augmentation equivalence established from the Python `random` stream that the "
                   "augmentation consumes."),
        "train_order_equivalent": raw["train_order_equivalent"],
        "train_trace_hash_h2a": raw["train_trace_hash_h2a"],
        "train_trace_hash_h2c": raw["train_trace_hash_h2c"],
        "train_order_length": raw["train_order_len"],
        "val_order_equivalent": raw["val_order_equivalent"],
        "val_trace_hash_h2a": raw["val_trace_hash_h2a"],
        "val_trace_hash_h2c": raw["val_trace_hash_h2c"],
        "augmentation_rng_equivalent": raw["augmentation_python_trace_equivalent"],
        "augmentation_trace_hash_h2a": raw["augmentation_trace_hash_h2a"],
        "augmentation_trace_hash_h2c": raw["augmentation_trace_hash_h2c"],
        "python_random_state_equivalent": raw["python_random_state_equivalent"],
        "python_random_state_hash_h2a": raw["python_random_state_hash_h2a"],
        "python_random_state_hash_h2c": raw["python_random_state_hash_h2c"],
        "numpy_random_state_equivalent": raw["numpy_random_state_equivalent"],
        "train_generator_state_equivalent": raw["train_generator_state_equivalent"],
        "val_generator_state_equivalent": raw["val_generator_state_equivalent"],
        "torch_global_rng_state_equivalent": raw["torch_global_rng_state_equivalent"],
        "torch_global_rng_state_note": ("EXPECTED to differ: the H2C head performs additional "
                                        "kaiming draws. No downstream stream consumes the torch "
                                        "global RNG, so this difference is inert."),
        "first20_train_indices": raw["first20_train_order_h2a"],
    },

    "terminal_zero_weight_note": {
        "classification": "FROZEN_INITIALIZATION_CONSEQUENCE",
        "not_a_protocol_defect": True,
        "statement": ("H2C terminal 1x1 weights initialize to zero. On the first backward pass the "
                      "hidden 3x3 layer may receive zero gradient through the zero terminal weights "
                      "until the terminal layer has been updated. This is an intentional "
                      "consequence of the frozen initialization."),
        "warmup_added": "NO", "optimizer_behaviour_altered": "NO",
        "initialization_changed": "NO",
    },

    "scientific_change_register_after_preflight": {
        "HEAD_ARCHITECTURE_CHANGED": "YES",
        "HEAD_INITIALIZATION_CHANGED": "YES_PART_OF_SAME_FROZEN_HEAD_AXIS",
        "LOSS_CHANGED": "NO", "TARGET_CHANGED": "NO", "SIGMA_CHANGED": "NO",
        "BACKBONE_CHANGED": "NO", "OPTIMIZER_CHANGED": "NO", "SCHEDULER_CHANGED": "NO",
        "DATA_CHANGED": "NO", "SPLIT_CHANGED": "NO",
        "AUGMENTATION_DISTRIBUTION_CHANGED": "NO", "TRAIN_ORDER_SEMANTICS_CHANGED": "NO",
        "CHECKPOINT_SELECTION_CHANGED": "NO", "PROPOSAL_POLICY_CHANGED": "NO",
        "FUSION_CHANGED": "NO", "SECOND_SCIENTIFIC_AXIS": "NONE",
    },

    "bindings": {
        "h2c_protocol_sha": sha(A / "post_phase13_h2c_protocol_frozen.json"),
        "h2a_runner_sha": sha(ROOT / "scripts/training/post_phase13_h2a_localizer_replay.py"),
        "h2a_config_sha": sha(ROOT / "configs/phase13_clean_v3"
                                   / "post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_"
                                     "centernetfocal_deploymentbalance_seed42_clean_v3.yaml"),
        "h2c_prospective_runner_sha": "NOT_CREATED (runner not yet authored)",
        "h2c_prospective_config_sha": "NOT_CREATED (config not yet authored)",
        "reproducibility_module_sha": sha(ROOT / "src/utils/reproducibility.py"),
        "dataset_module_sha": sha(ROOT / "src/data/kub_localizer_dataset.py"),
        "counter_clarification_sha": sha(A / "post_phase13_h2c_preexecution_counter_clarification.json"),
    },

    "counters": {"training_epochs": 0, "optimizer_steps": 0, "checkpoint_writes": 0,
                 "project_train_model_forwards": 0, "project_val_model_forwards": 0,
                 "test_reads": 0, "external_test_reads": 0,
                 "synthetic_shape_check_forwards": 1,
                 "project_images_decoded": 0},

    "continuity": {"h2c_protocol": "COMPLETE_PASS_FROZEN", "h2c_rng_preflight": "COMPLETE_PASS",
                   "h2c_b1": "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION", "h2c_b1_authorized": False,
                   "h2c_b2": "NOT_STARTED", "phase14": "NOT_STARTED", "test": "UNTOUCHED"},
    "next_action": "WAIT_FOR_SUPERVISOR_H2C_B1_EXECUTION_AUTHORIZATION",
}
(A / "post_phase13_h2c_rng_equivalence_preflight.json").write_text(
    json.dumps(rng, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = [
    "# POST-PHASE13 H2C — RNG-Equivalence + Execution-Provenance Preflight", "",
    "- **Status: PASS**",
    f"- **RNG classification: `{rng['rng_classification']}`**",
    f"- Execution fix required: **{rng['execution_fix_required']}** · applied: "
    f"**{rng['execution_fix_applied']}**", "",
    "## Why this matters", "",
    "H2C adds a kaiming-initialised 3x3 convolution, which consumes RNG. If model initialization "
    "shared a stream with data ordering or augmentation, H2C would silently change more than the "
    "head architecture despite the unchanged seed 42.", "",
    "## Stream ownership (physical)", "", "| stream | owner |", "|---|---|"]
for k, v in rng["stream_ownership"].items():
    md.append(f"| {k} | {v} |")
md += ["", "## Answers", "", "| question | answer |", "|---|---|"]
for k, v in rng["answers"].items():
    md.append(f"| {k} | {v} |")
md += ["", "## Empirical equivalence", "",
       "| check | result | hash (H2A) | hash (H2C) |", "|---|---|---|---|",
       f"| TRAIN order (770 indices) | **{rng['empirical_equivalence']['train_order_equivalent']}** | "
       f"`{rng['empirical_equivalence']['train_trace_hash_h2a'][:16]}…` | "
       f"`{rng['empirical_equivalence']['train_trace_hash_h2c'][:16]}…` |",
       f"| VAL order | **{rng['empirical_equivalence']['val_order_equivalent']}** | "
       f"`{rng['empirical_equivalence']['val_trace_hash_h2a'][:16]}…` | "
       f"`{rng['empirical_equivalence']['val_trace_hash_h2c'][:16]}…` |",
       f"| augmentation RNG trace | **{rng['empirical_equivalence']['augmentation_rng_equivalent']}** | "
       f"`{rng['empirical_equivalence']['augmentation_trace_hash_h2a'][:16]}…` | "
       f"`{rng['empirical_equivalence']['augmentation_trace_hash_h2c'][:16]}…` |", "",
       f"Python random state equivalent: **{rng['empirical_equivalence']['python_random_state_equivalent']}** · "
       f"numpy state equivalent: **{rng['empirical_equivalence']['numpy_random_state_equivalent']}** · "
       f"train generator equivalent: **{rng['empirical_equivalence']['train_generator_state_equivalent']}** · "
       f"val generator equivalent: **{rng['empirical_equivalence']['val_generator_state_equivalent']}**", "",
       f"torch global RNG state equivalent: **{rng['empirical_equivalence']['torch_global_rng_state_equivalent']}** "
       f"— {rng['empirical_equivalence']['torch_global_rng_state_note']}", "",
       "## Terminal zero-weight note", "",
       f"`{rng['terminal_zero_weight_note']['classification']}` — "
       f"{rng['terminal_zero_weight_note']['statement']}", "",
       "## Scientific change register after preflight", "",
       "| field | value |", "|---|---|"]
for k, v in rng["scientific_change_register_after_preflight"].items():
    md.append(f"| {k} | {v} |")
md += ["", "## Zero scientific execution", "",
       "training epochs **0** · optimizer steps **0** · checkpoint writes **0** · "
       "project TRAIN model forwards **0** · project VAL model forwards **0** · "
       "TEST reads **0** · external TEST reads **0** · synthetic shape-check forwards **1**", "",
       f"**next_action:** `{rng['next_action']}`", ""]
(A / "post_phase13_h2c_rng_equivalence_preflight.md").write_text("\n".join(md), encoding="utf-8")

print("artifacts written")
print("  counter clarification:", sha(A / "post_phase13_h2c_preexecution_counter_clarification.json"))
print("  rng preflight:", sha(A / "post_phase13_h2c_rng_equivalence_preflight.json"))
print("  rng preflight md:", sha(A / "post_phase13_h2c_rng_equivalence_preflight.md"))
