"""Phase 20B - build per-architecture binding + pre-execution check (FAIL CLOSED).

For each Phase-20B model this writes TWO artifacts BEFORE any training:

    reports/audits/phase20b_<slug>_architecture_binding.json
    reports/audits/phase20b_<slug>_pre_execution_check.json

The binding freezes *which* architecture is being trained and pins the SHA256 of
the repository implementation that defines it. The pre-execution check runs real
verification (construction, forward shape at the frozen 512 px / RGB_3CH contract,
forbidden-module scan, single output head, finite loss, population integrity, TEST
lock, sampler balance, frozen hyperparameters) and records pass/fail per check.

``train_phase20b_shared_baseline.py`` refuses to start unless the binding's model
source SHA still matches the file on disk AND the check reports
``all_checks_passed == true``. That is the fail-closed gate.

Scientific config is NOT decided here: it is read from the frozen Phase-20
protocol so every Phase-20B model shares one protocol.

Usage
-----
    python scripts/audits/build_phase20b_bindings.py --model-key unet
    python scripts/audits/build_phase20b_bindings.py --all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.data.domain_balanced_sampler import (
    BALANCED_SAMPLING_POLICY_ID,
    build_domain_balanced_sampler,
    derive_epoch_seed,
    expected_domain_proportions,
)
from src.data.multidomain_dataset import DATASET_ORDER, MultiDomainDataset
from src.losses.segmentation import BCEDiceLoss
from src.training.phase20_selection import SELECTION_RULE_ID
from src.utils.test_lock import verify_test_lock

sys.path.insert(0, str(ROOT / "scripts" / "training"))
from train_phase20b_shared_baseline import (  # noqa: E402
    MODEL_REGISTRY,
    ORDER,
    PROTOCOL_PATH,
    PROTOCOL_SHA256,
    build_config,
    resolve_model_class,
    sha256_file,
)

AUDIT_DIR = ROOT / "reports/audits"
MANIFEST_VERSION = "phase4_v3"
MANIFEST_DIR = ROOT / "manifests/phase4_v3"
FORBIDDEN_TOKENS = ("film", "localizer", "proposal", "roi", "regional",
                    "domain_embedding", "task_embedding", "routing")


def chk(checks: dict, name: str, expected, observed, passed: bool) -> None:
    checks[name] = {"expected": expected, "observed": observed, "pass": bool(passed)}


def build_one(model_key: str, selection_basis: str, notes: list) -> dict:
    spec = MODEL_REGISTRY[model_key]
    cfg = build_config(model_key)
    src_rel = spec["source_file"]
    src_path = ROOT / src_rel

    checks: dict = {}

    # --- protocol ----------------------------------------------------------- #
    obs_protocol = sha256_file(PROTOCOL_PATH)
    chk(checks, "phase20_protocol_sha256_unchanged", PROTOCOL_SHA256, obs_protocol,
        obs_protocol == PROTOCOL_SHA256)

    # --- model source ------------------------------------------------------- #
    chk(checks, "model_source_exists", True, src_path.exists(), src_path.exists())
    if not src_path.exists():
        raise SystemExit(f"FAIL CLOSED: missing {src_rel}")
    model_src_sha = sha256_file(src_path)

    # --- construct ---------------------------------------------------------- #
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ModelClass = resolve_model_class(model_key)
    model = ModelClass(in_channels=cfg["model"]["in_channels"],
                       out_channels=cfg["model"]["out_channels"],
                       base_channels=cfg["model"]["base_channels"])
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    chk(checks, "model_constructs", True, f"{spec['class_name']} params={n_params:,}", True)
    chk(checks, "trainable_param_count_positive", "> 0", n_params, n_params > 0)

    # --- forbidden modules -------------------------------------------------- #
    names = [n.lower() for n, _ in model.named_modules()]
    hits = sorted({t for t in FORBIDDEN_TOKENS for n in names if t in n})
    chk(checks, "no_forbidden_modules", [], hits, len(hits) == 0)
    chk(checks, "no_film_module", [], [n for n in names if "film" in n],
        not any("film" in n for n in names))

    # --- forward pass at the frozen contract -------------------------------- #
    model.eval()
    with torch.no_grad():
        x = torch.randn(2, 3, 512, 512, device=device)
        model = model.to(device)
        y = model(x)
    chk(checks, "input_shape_BxCxHxW", [2, 3, 512, 512], list(x.shape), list(x.shape) == [2, 3, 512, 512])
    chk(checks, "output_shape_Bx1xHxW", [2, 1, 512, 512], list(y.shape), list(y.shape) == [2, 1, 512, 512])

    head = getattr(model, "head", None)
    head_out = head.out_channels if hasattr(head, "out_channels") else (
        head[-1].out_channels if head is not None else None)
    if head_out is None:
        # DeepLabV3+ uses a Sequential decoder whose last layer is the 1x1 head.
        dec = getattr(model, "decoder", None)
        head_out = dec[-1].out_channels if dec is not None else None
    chk(checks, "single_output_head", 1, f"head.out_channels={head_out}", head_out == 1)

    # --- task_id never a model input ---------------------------------------- #
    import inspect
    sig = str(inspect.signature(model.forward))
    chk(checks, "task_id_not_a_model_input", "forward(x) only", f"forward{sig}",
        "task" not in sig and "dataset" not in sig)

    # --- loss finite -------------------------------------------------------- #
    model.train()
    criterion = BCEDiceLoss(cfg["loss"]["bce_weight"], cfg["loss"]["dice_weight"],
                            cfg["loss"]["dice_epsilon"])
    with torch.no_grad():
        logits = model(torch.randn(2, 3, 512, 512, device=device))
        loss_val = float(criterion(logits, (torch.rand(2, 1, 512, 512, device=device) > 0.5).float()).item())
    chk(checks, "loss_finite_positive", "finite > 0", loss_val,
        np.isfinite(loss_val) and loss_val > 0)
    del model
    if device.type == "cuda":
        torch.cuda.empty_cache()

    # --- populations -------------------------------------------------------- #
    ds_train = MultiDomainDataset(MANIFEST_DIR / "train.csv", "TRAIN", size=512, train=True,
                                  channel_policy="RGB_3CH")
    ds_val = MultiDomainDataset(MANIFEST_DIR / "val.csv", "VAL", size=512, train=False,
                                channel_policy="RGB_3CH")
    chk(checks, "train_population_5832", 5832, len(ds_train), len(ds_train) == 5832)
    chk(checks, "val_population_808", 808, len(ds_val), len(ds_val) == 808)
    tr_domains = sorted(ds_train.frame["dataset"].unique().tolist())
    va_domains = sorted(ds_val.frame["dataset"].unique().tolist())
    chk(checks, "four_domains_present", sorted(DATASET_ORDER),
        f"TRAIN={tr_domains} VAL={va_domains}",
        tr_domains == sorted(DATASET_ORDER) and va_domains == sorted(DATASET_ORDER))
    chk(checks, "channel_policy_frozen", "RGB_3CH", ds_train.channel_policy, ds_train.channel_policy == "RGB_3CH")
    chk(checks, "resolution_frozen", 512, ds_train.size, int(ds_train.size) == 512)

    # --- TEST lock ---------------------------------------------------------- #
    verify_test_lock(str(ROOT))
    n_test = sum(1 for _ in open(ROOT / "manifests" / MANIFEST_VERSION / "test.csv", encoding="utf-8")) - 1
    chk(checks, "test_lock_verified", 1683, f"count={n_test}", n_test == 1683)

    # --- sampler ------------------------------------------------------------ #
    probs = expected_domain_proportions(ds_train.frame["dataset"].tolist())
    share = {k: float(v["expected_sampling_proportion"]) for k, v in probs.items()}
    chk(checks, "sampler_balances_domains", "all == 0.25",
        {k: round(v, 6) for k, v in share.items()},
        all(abs(v - 0.25) < 1e-9 for v in share.values()))
    chk(checks, "sampler_policy_frozen", BALANCED_SAMPLING_POLICY_ID, BALANCED_SAMPLING_POLICY_ID,
        BALANCED_SAMPLING_POLICY_ID == "phase20_domain_balanced_uniform_v1")
    sampler = build_domain_balanced_sampler(ds_train.frame["dataset"].tolist(), 42, 1)
    chk(checks, "sampler_num_samples_equals_train_size", 5832, len(sampler),
        len(sampler) == 5832)

    # --- frozen hyperparameters --------------------------------------------- #
    t = cfg["training"]
    chk(checks, "frozen_batch_size", 4, t["batch_size"], t["batch_size"] == 4)
    chk(checks, "frozen_eval_batch_size", 8, t["eval_batch_size"], t["eval_batch_size"] == 8)
    chk(checks, "frozen_num_workers", 4, t["num_workers"], t["num_workers"] == 4)
    chk(checks, "frozen_amp", True, t["amp"], t["amp"] is True)
    chk(checks, "frozen_seed", 42, t["seed"], t["seed"] == 42)
    chk(checks, "frozen_max_epochs", 100, t["max_epochs"], t["max_epochs"] == 100)
    chk(checks, "frozen_patience", 15, t["early_stopping_patience"], t["early_stopping_patience"] == 15)
    chk(checks, "frozen_threshold", 0.5, t["threshold"], t["threshold"] == 0.5)
    chk(checks, "frozen_loss", {"bce": 0.5, "dice": 0.5, "eps": 1e-6},
        cfg["loss"], cfg["loss"]["bce_weight"] == 0.5 and cfg["loss"]["dice_weight"] == 0.5
        and cfg["loss"]["dice_epsilon"] == 1e-6)
    chk(checks, "frozen_optimizer", {"AdamW": 1e-4, "wd": 1e-4}, cfg["optimizer"],
        cfg["optimizer"]["name"] == "AdamW" and cfg["optimizer"]["learning_rate"] == 1e-4
        and cfg["optimizer"]["weight_decay"] == 1e-4)
    chk(checks, "frozen_scheduler", {"CosineAnnealingLR": 100}, cfg["scheduler"],
        cfg["scheduler"]["name"] == "CosineAnnealingLR" and cfg["scheduler"]["T_max"] == 100)
    chk(checks, "frozen_selection_rule", SELECTION_RULE_ID, t["checkpoint_metric"],
        t["checkpoint_metric"] == SELECTION_RULE_ID)

    # --- resumability ------------------------------------------------------- #
    s5 = derive_epoch_seed(42, 5)
    s5b = derive_epoch_seed(42, 5)
    s6 = derive_epoch_seed(42, 6)
    chk(checks, "resume_mechanism_safe", "deterministic per-epoch seed",
        f"derive_epoch_seed(42,5)={s5} stable; epoch 6 differs", s5 == s5b and s5 != s6)

    # --- output directories must be pre-run --------------------------------- #
    exp_dir = ROOT / "experiments" / cfg["experiment_id"]
    ckpt_dir = ROOT / "checkpoints" / cfg["experiment_id"]
    pre_run = not (exp_dir / "history.csv").exists() and not (ckpt_dir / "latest.pt").exists()
    chk(checks, "output_directories_pre_run", "no history.csv / latest.pt",
        f"history={ (exp_dir/'history.csv').exists() } latest={(ckpt_dir/'latest.pt').exists()}",
        pre_run)

    failed = [k for k, v in checks.items() if not v["pass"]]
    return {
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": len(checks) - len(failed),
        "failed_checks": failed,
        "all_checks_passed": len(failed) == 0,
        "training_authorized": len(failed) == 0,
        "fail_closed": True,
        "model_source_sha256": model_src_sha,
        "n_trainable_params": n_params,
        "notes": notes,
        "selection_basis": selection_basis,
        "config": cfg,
    }


def write_artifacts(model_key: str, selection_basis: str, notes: list) -> bool:
    spec = MODEL_REGISTRY[model_key]
    slug = spec["binding_slug"]
    result = build_one(model_key, selection_basis, notes)

    binding = {
        "artifact": "phase20b_architecture_binding",
        "phase": 20,
        "subphase": "20B",
        "model_key": model_key,
        "model_display_name": spec["display_name"],
        "experiment_id": spec["experiment_id"],
        "repository_implementation": spec["source_file"],
        "model_source_sha256": result["model_source_sha256"],
        "class_name": spec["class_name"],
        "module": spec["module"],
        "factory_key": None,
        "architecture_descriptor": spec["architecture"],
        "model_contract": {
            "in_channels": 3,
            "out_channels": 1,
            "base_channels": 32,
            "output": "single binary segmentation logit channel",
            "shared_parameters_across_domains": True,
            "forbidden_modules": ["FiLM", "task_embedding", "domain_embedding", "regional_branch",
                                  "localizer", "ROI_proposal", "routing", "dataset_specific_decoder",
                                  "dataset_specific_head"],
            "forbidden_modules_present": result["checks"]["no_forbidden_modules"]["observed"],
        },
        "n_trainable_params": result["n_trainable_params"],
        "selection_basis": selection_basis,
        "selection_time": "PRE_TRAINING",
        "current_phase20_results_used_for_selection": False,
        "protocol_path": "reports/audits/phase20_shared_global_baseline_protocol.json",
        "protocol_sha256": PROTOCOL_SHA256,
        "phase20a_reference_experiment": "phase20_shared_unetpp_fourdomain_seed42_clean_v3",
        "immutability": {
            "architecture_will_not_be_switched_after_training": True,
            "no_architecture_search_in_phase20b": True,
            "no_per_model_recipe_change": True,
            "no_per_model_threshold_tuning": True,
            "no_post_hoc_restart_from_epoch_1": True,
        },
        "notes": notes,
    }

    check = {
        "artifact": "phase20b_pre_execution_check",
        "phase": 20,
        "subphase": "20B",
        "model_key": model_key,
        "model_display_name": spec["display_name"],
        "experiment_id": spec["experiment_id"],
        "protocol_path": "reports/audits/phase20_shared_global_baseline_protocol.json",
        "protocol_sha256": PROTOCOL_SHA256,
        "architecture_binding_path": f"reports/audits/phase20b_{slug}_architecture_binding.json",
        "checks": result["checks"],
        "n_checks": result["n_checks"],
        "n_passed": result["n_passed"],
        "failed_checks": result["failed_checks"],
        "all_checks_passed": result["all_checks_passed"],
        "training_authorized": result["training_authorized"],
        "fail_closed": True,
        "test_reads_during_check": {"test_image_reads": 0, "test_mask_reads": 0},
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    b_path = AUDIT_DIR / f"phase20b_{slug}_architecture_binding.json"
    c_path = AUDIT_DIR / f"phase20b_{slug}_pre_execution_check.json"
    b_path.write_text(json.dumps(binding, indent=2), encoding="utf-8")
    c_path.write_text(json.dumps(check, indent=2), encoding="utf-8")

    print(f"[{spec['display_name']}] binding -> {b_path.name}  sha={sha256_file(b_path)[:16]}")
    print(f"[{spec['display_name']}] check   -> {c_path.name}  "
          f"{result['n_passed']}/{result['n_checks']} passed  "
          f"authorized={result['training_authorized']}")
    if result["failed_checks"]:
        for k in result["failed_checks"]:
            print(f"    FAIL {k}: expected={result['checks'][k]['expected']!r} "
                  f"observed={result['checks'][k]['observed']!r}")
    return result["all_checks_passed"]


# --------------------------------------------------------------------------- #
SELECTION_BASIS = {
    "unet": "LEGACY_TESTED_PROJECT_PRIOR_EVIDENCE",
    "attention_unet": "LEGACY_TESTED_PROJECT_PRIOR_EVIDENCE",
    "deeplabv3plus": "LEGACY_TESTED_PROJECT_PRIOR_EVIDENCE",
    "transformer_mit_unet": "LOCAL_RANDOM_INIT_IMPLEMENTATION__NO_OFFICIAL_PRETRAINED_WEIGHTS",
}

NOTES = {
    "unet": [
        "Already implemented and tested in this repository (src/models/unet.py, Phase-10 clean-v3).",
        "Classic four-stage encoder/decoder with plain skip concatenation, base width 32.",
        "Clean image-only reference with no task conditioning.",
    ],
    "attention_unet": [
        "Already implemented and tested in this repository (src/models/attention_unet.py, Phase-10 clean-v3).",
        "Additive attention gates on all four encoder skip connections; base width 32.",
        "Intrinsic to the conventional Attention U-Net definition; not a new design.",
    ],
    "deeplabv3plus": [
        "Already implemented and tested in this repository (src/models/deeplabv3plus.py, Phase-10 clean-v3).",
        "ResNet-50 output-stride-16 backbone, canonical ASPP rates (6,12,18), canonical decoder width 256.",
        "Backbone is RANDOMLY INITIALIZED: torchvision weights=None. No pretrained weights are loaded.",
        "base_channels=32 is accepted for a uniform factory signature and deliberately unused (canonical width).",
    ],
    "transformer_mit_unet": [
        "No official pretrained MiT / SegFormer checkpoint is available in this environment.",
        "timm / transformers / segmentation-models-pytorch are NOT installed; the only cached torchvision",
        "weights are resnet34-b627a593.pth, which is unrelated to MiT.",
        "This is a LOCAL, RANDOMLY INITIALIZED MiT-style U-Net encoder+decoder, NOT official pretrained MiT-B1.",
        "It must never be described as 'official pretrained MiT-B1'.",
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Phase-20B architecture bindings + pre-execution checks.")
    ap.add_argument("--model-key", choices=ORDER, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    keys = ORDER if args.all else ([args.model_key] if args.model_key else [])
    if not keys:
        ap.error("pass --model-key or --all")

    ok_all = True
    for k in keys:
        ok = write_artifacts(k, SELECTION_BASIS[k], NOTES[k])
        ok_all = ok_all and ok
        print()
    print(f"OVERALL: {'ALL_CHECKS_PASSED' if ok_all else 'FAILURES_PRESENT'}")
    return 0 if ok_all else 2


if __name__ == "__main__":
    raise SystemExit(main())
