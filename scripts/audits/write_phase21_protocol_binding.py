"""Phase 21 — write reports/audits/phase21_protocol_binding.json.

Binds the Phase-21 Global MedFiLM run to the FROZEN Phase-20 protocol on disk.
Every inherited scientific value must be identical; any difference must be an
explicitly declared intentional architectural difference. The artifact must
report ``unintentional_differences = []``.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.training.phase21_common import CONFIG, EXPERIMENT_ID, PROTOCOL_PATH, PROTOCOL_SHA256, sha256_file

OUT = ROOT / "reports" / "audits" / "phase21_protocol_binding.json"


def main() -> int:
    proto_path = ROOT / PROTOCOL_PATH
    proto = json.loads(proto_path.read_text(encoding="utf-8"))
    proto_sha = sha256_file(proto_path)
    assert proto_sha == PROTOCOL_SHA256, f"frozen protocol SHA drift: {proto_sha}"

    inherited = {}

    def chk(name, proto_value, phase21_value, source):
        inherited[name] = {
            "phase20_protocol_value": proto_value,
            "phase21_value": phase21_value,
            "identical": proto_value == phase21_value,
            "source": source,
        }
        return proto_value == phase21_value

    checks = []
    checks.append(chk("manifest_version", proto["dataset_populations"]["manifest_version"],
                      CONFIG["manifest_version"], "dataset_populations.manifest_version"))
    checks.append(chk("task_ids", proto["dataset_populations"]["task_ids"], {
        "ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}, "dataset_populations.task_ids"))
    checks.append(chk("train_total", proto["dataset_populations"]["TRAIN_total"], 5832,
                      "dataset_populations.TRAIN_total"))
    checks.append(chk("val_total", proto["dataset_populations"]["VAL_total"], 808,
                      "dataset_populations.VAL_total"))
    checks.append(chk("input_channel_policy", proto["input_representation"]["channel_policy"],
                      CONFIG["input_channel_policy"], "input_representation.channel_policy"))
    checks.append(chk("input_resolution", proto["input_resolution"], CONFIG["input_resolution"],
                      "input_resolution"))
    checks.append(chk("sampling_policy", proto["sampling_policy"]["policy_id"],
                      CONFIG["training"]["sampling_policy"], "sampling_policy.policy_id"))
    checks.append(chk("loss", proto["loss"], CONFIG["loss"], "loss"))
    checks.append(chk("optimizer", proto["optimizer"], CONFIG["optimizer"], "optimizer"))
    checks.append(chk("learning_rate", proto["learning_rate"],
                      CONFIG["optimizer"]["learning_rate"], "learning_rate"))
    checks.append(chk("weight_decay", proto["weight_decay"],
                      CONFIG["optimizer"]["weight_decay"], "weight_decay"))
    checks.append(chk("scheduler", proto["scheduler"], CONFIG["scheduler"], "scheduler"))
    checks.append(chk("batch_size", proto["batch_size"], CONFIG["training"]["batch_size"],
                      "batch_size"))
    checks.append(chk("eval_batch_size", proto["eval_batch_size"],
                      CONFIG["training"]["eval_batch_size"], "eval_batch_size"))
    checks.append(chk("num_workers", proto["num_workers"], CONFIG["training"]["num_workers"],
                      "num_workers"))
    checks.append(chk("amp", proto["amp"], CONFIG["training"]["amp"], "amp"))
    checks.append(chk("seed", proto["seed"], CONFIG["training"]["seed"], "seed"))
    checks.append(chk("max_epochs", proto["max_epochs"], CONFIG["training"]["max_epochs"],
                      "max_epochs"))
    checks.append(chk("early_stopping_patience", proto["early_stopping"]["patience"],
                      CONFIG["training"]["early_stopping_patience"], "early_stopping.patience"))
    checks.append(chk("checkpoint_selection_rule", proto["checkpoint_selection"]["rule_id"],
                      CONFIG["training"]["checkpoint_metric"], "checkpoint_selection.rule_id"))
    checks.append(chk("evaluation_threshold", proto["evaluation_metrics"]["threshold"],
                      CONFIG["training"]["threshold"], "evaluation_metrics.threshold"))
    checks.append(chk("bootstrap", proto["evaluation_metrics"]["bootstrap"], {
        "n_boot": 2000, "seed": 42, "alpha": 0.05, "unit": "image"},
        "evaluation_metrics.bootstrap"))
    checks.append(chk("metrics_implementation", proto["evaluation_metrics"]["implementation"],
                      "src.metrics.evaluation_metrics", "evaluation_metrics.implementation"))
    checks.append(chk("test_locks", proto["test_locks"]["test_image_reads"], 0, "test_locks"))

    # Intentional (architectural) differences — declared, not accidental.
    intentional = [
        {
            "field": "architecture",
            "phase20_protocol_value": proto["architecture"],
            "phase21_value": CONFIG["architecture"],
            "reason": (
                "Phase 21 is the task-conditioned Global MedFiLM reference. The shared UNet++ "
                "architecture is replaced by the reconstructed historical GLOBAL MedFiLM "
                "(residual shared encoder-decoder + 5 FiLM sites + ONE shared head)."
            ),
            "class": "INTENTIONAL_ARCHITECTURAL",
        },
        {
            "field": "experiment_id",
            "phase20_protocol_value": proto["experiment_id"],
            "phase21_value": EXPERIMENT_ID,
            "reason": "New phase, new experiment identity and new isolated output directories.",
            "class": "INTENTIONAL_IDENTITY",
        },
        {
            "field": "model.input_channels_consumed",
            "phase20_protocol_value": "RGB_3CH (in_channels=3)",
            "phase21_value": "RGB_3CH (in_channels=3)",
            "reason": (
                "No change: the Phase-20 RGB_3CH channel policy is inherited EXACTLY. Listed here "
                "only to record that the legacy MedFiLM's 3-channel encoder first stage required no "
                "adapter."
            ),
            "class": "INTENTIONAL_NO_CHANGE_DOCUMENTED",
        },
        {
            "field": "task_id_role",
            "phase20_protocol_value": "sampling_only__never_a_model_input",
            "phase21_value": "CONDITIONING_ALLOWED (FiLM task embedding is the ONLY task signal)",
            "reason": (
                "The defining Phase-21 change: task_id is permitted as a CONDITIONING input only. "
                "It is never a channel, never concatenated to the image, never a separate head, and "
                "no mask-derived metadata enters the model."
            ),
            "class": "INTENTIONAL_ARCHITECTURAL",
        },
        {
            "field": "output_isolation",
            "phase20_protocol_value": proto["output_isolation"],
            "phase21_value": {
                "experiment_dir": f"experiments/{EXPERIMENT_ID}",
                "checkpoint_dir": f"checkpoints/{EXPERIMENT_ID}",
                "overwrites_phase20_checkpoints": False,
            },
            "reason": "Isolated output directories; no frozen artifact is overwritten.",
            "class": "INTENTIONAL_IDENTITY",
        },
    ]

    unintentional = [c for c, ok in zip(inherited, checks) if not ok]

    artifact = {
        "artifact": "phase21_protocol_binding",
        "phase": 21,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_id": EXPERIMENT_ID,
        "authoritative_source": {
            "path": PROTOCOL_PATH,
            "sha256": proto_sha,
            "sha256_expected": PROTOCOL_SHA256,
            "sha_matches": proto_sha == PROTOCOL_SHA256,
            "role": "AUTHORITATIVE_ON_DISK",
        },
        "inherited_values": inherited,
        "n_inherited_checks": len(inherited),
        "n_inherited_identical": int(sum(checks)),
        "all_inherited_identical": bool(all(checks)),
        "intentional_differences": intentional,
        "unintentional_differences": unintentional,
        "unintentional_differences_count": len(unintentional),
        "test_reads": 0,
        "training_performed_at_binding_time": False,
    }
    artifact["verdict"] = (
        "PHASE21_PROTOCOL_BINDING_PASS" if all(checks) and not unintentional
        else "PHASE21_PROTOCOL_BINDING_FAIL"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("inherited_identical", int(sum(checks)), "/", len(inherited))
    print("unintentional_differences", unintentional)
    print("verdict", artifact["verdict"])
    return 0 if artifact["verdict"].endswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
