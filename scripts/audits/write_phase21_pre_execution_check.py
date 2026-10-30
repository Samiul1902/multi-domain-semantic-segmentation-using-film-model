"""Phase 21 — pre-execution sanity checks -> reports/audits/phase21_pre_execution_check.json.

Fail-closed. Runs BEFORE the single authorized training run.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.training.phase21_common import CONFIG, EXPERIMENT_ID, sha256_file
from src.data.loaders import create_loader
from src.data.multidomain_dataset import DATASET_ORDER, MultiDomainDataset, harmonized_collate
from src.models.film import GlobalMedFiLM
from src.utils.test_lock import verify_test_lock

OUT = ROOT / "reports" / "audits" / "phase21_pre_execution_check.json"
MANIFEST_DIR = ROOT / "manifests/phase4_v3"
BINDING = ROOT / "reports" / "audits" / "phase21_global_medfilm_architecture_binding.json"


def main() -> int:
    checks: dict = {}

    def rec(name, passed, detail):
        checks[name] = {"passed": bool(passed), "detail": detail}
        return bool(passed)

    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    model_sha = sha256_file(ROOT / "src/models/film/global_medfilm.py")
    rec("architecture_binding_present",
        binding.get("verdict") == "PHASE21_ARCHITECTURE_FROZEN",
        {"verdict": binding.get("verdict")})
    rec("model_file_sha_matches_binding", model_sha == binding.get("model_file_sha256"),
        {"repo": model_sha, "binding": binding.get("model_file_sha256")})

    torch.manual_seed(42)
    model = GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1,
                          channels=tuple(CONFIG["model"]["channels"]),
                          task_embedding_dim=32, film_hidden_dim=64)
    n_params = int(sum(p.numel() for p in model.parameters() if p.requires_grad))
    rec("parameter_count_matches_binding", n_params == binding.get("measured_parameter_count"),
        {"measured": n_params, "binding": binding.get("measured_parameter_count")})

    # ---- 1. shape contract ------------------------------------------------ #
    model.eval()
    x = torch.randn(2, 3, 512, 512)
    with torch.no_grad():
        y = model(x, torch.tensor([0, 3]))
    rec("forward_shape", tuple(y.shape) == (2, 1, 512, 512), {"out_shape": list(y.shape)})
    rec("output_spatial_matches_input", tuple(y.shape[-2:]) == tuple(x.shape[-2:]),
        {"in": list(x.shape[-2:]), "out": list(y.shape[-2:])})
    rec("single_output_channel", y.shape[1] == 1, {"out_channels": int(y.shape[1])})

    # ---- 2. task-ID validation ------------------------------------------- #
    ok_invalid = False
    try:
        model(x, torch.tensor([0, 4]))
    except ValueError:
        ok_invalid = True
    rec("unknown_task_id_rejected", ok_invalid, {"attempted": [0, 4], "task_count": 4})

    ok_wrong_shape = False
    try:
        model(x, torch.tensor([0]))
    except ValueError:
        ok_wrong_shape = True
    rec("task_id_shape_enforced", ok_wrong_shape, {"attempted": "[1] for batch 2"})

    all_valid = True
    for tid in range(4):
        try:
            model(x, torch.full((2,), tid, dtype=torch.long))
        except Exception as exc:  # noqa: BLE001
            all_valid = False
            checks["all_four_task_ids_accepted"] = {"passed": False, "detail": str(exc)}
    if "all_four_task_ids_accepted" not in checks:
        rec("all_four_task_ids_accepted", all_valid, {"task_ids": [0, 1, 2, 3]})

    # ---- 3. FiLM identity at initialisation ------------------------------ #
    with torch.no_grad():
        y_isic = model(x, torch.zeros(2, dtype=torch.long))
        y_kub = model(x, torch.full((2,), 3, dtype=torch.long))
    max_diff = float((y_isic - y_kub).abs().max())
    rec("film_identity_at_init", max_diff == 0.0,
        {"max_abs_output_diff_across_tasks": max_diff,
         "meaning": "zero-initialised FiLM output projection -> exact identity before training"})

    with torch.no_grad():
        params = model.film_parameters_for_tasks(torch.arange(4))
    gamma_max = max(float(g.abs().max()) for g, _ in params.values())
    beta_max = max(float(b.abs().max()) for _, b in params.values())
    rec("film_parameters_zero_at_init", gamma_max == 0.0 and beta_max == 0.0,
        {"max_abs_gamma": gamma_max, "max_abs_beta": beta_max, "sites": list(params)})

    # ---- 4. conditioning path is wired (task sensitivity after perturbation) #
    with torch.no_grad():
        for layer in model.film_layers.values():
            layer.output.weight.normal_(0.0, 0.5)
            layer.output.bias.normal_(0.0, 0.2)
        y_a = model(x, torch.zeros(2, dtype=torch.long))
        y_b = model(x, torch.full((2,), 3, dtype=torch.long))
    wired = float((y_a - y_b).abs().max())
    rec("conditioning_path_wired", wired > 1e-6,
        {"max_abs_output_diff_after_film_perturbation": wired,
         "meaning": "task embedding -> FiLM -> features is a live, non-degenerate path"})
    model = GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1,
                          channels=tuple(CONFIG["model"]["channels"]),
                          task_embedding_dim=32, film_hidden_dim=64)

    # ---- 5. gradient path into the FiLM conditioning ---------------------- #
    # At initialisation the FiLM output projection is exactly zero, so the
    # transformation is the identity and d(loss)/d(task_embedding) is EXACTLY
    # zero. The projection itself DOES receive gradient at step 0 (because
    # d(gamma_raw)/dW_output = hidden(embedding) != 0). After ONE optimizer step
    # the projection leaves zero and the embedding path opens. Both facts are
    # recorded honestly.
    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=1e-4)
    t_batch = torch.tensor([0, 3])
    opt.zero_grad(set_to_none=True)
    loss = model(x, t_batch).mean()
    loss.backward()
    g_emb_0 = model.task_embedding.weight.grad
    g_out_0 = model.film_layers["bridge"].output.weight.grad
    rec("film_output_projection_receives_gradient_at_init",
        g_out_0 is not None and float(g_out_0.abs().sum()) > 0.0,
        {"bridge_output_grad_norm": float(g_out_0.norm()) if g_out_0 is not None else None})
    rec("task_embedding_gradient_zero_at_init_by_construction",
        g_emb_0 is not None and float(g_emb_0.abs().sum()) == 0.0,
        {"embedding_grad_norm_at_step0": float(g_emb_0.norm()) if g_emb_0 is not None else None,
         "meaning": "zero-initialised FiLM output projection => exact identity => no gradient "
                    "reaches the embedding before the first step; conditioning is LEARNED"})
    opt.step()
    opt.zero_grad(set_to_none=True)
    loss2 = model(x, t_batch).mean()
    loss2.backward()
    g_emb_1 = model.task_embedding.weight.grad
    rec("task_embedding_receives_gradient_after_one_step",
        g_emb_1 is not None and float(g_emb_1.abs().sum()) > 0.0,
        {"embedding_grad_norm_after_step1": float(g_emb_1.norm()) if g_emb_1 is not None else None,
         "meaning": "the conditioning path is trainable end-to-end"})

    model = GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1,
                          channels=tuple(CONFIG["model"]["channels"]),
                          task_embedding_dim=32, film_hidden_dim=64)

    # ---- 6. determinism ---------------------------------------------------- #
    def run(seed):
        torch.manual_seed(seed)
        m = GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1)
        m.eval()
        with torch.no_grad():
            return m(x, torch.tensor([1, 2]))
    d1, d2 = run(42), run(42)
    rec("determinism_same_seed", bool(torch.equal(d1, d2)),
        {"max_abs_diff": float((d1 - d2).abs().max())})

    # ---- 7. forbidden metadata / modules ---------------------------------- #
    names = [n for n, _ in model.named_modules()]
    forbidden = ["localizer", "proposal", "roi", "regional", "refiner", "benefit", "router"]
    hits = {t: [n for n in names if t in n.lower()] for t in forbidden}
    hits = {k: v for k, v in hits.items() if v}
    rec("no_forbidden_modules", not hits, {"hits": hits})

    import inspect
    sig = list(inspect.signature(GlobalMedFiLM.forward).parameters)
    rec("forward_accepts_only_image_and_task_id", sig == ["self", "images", "task_ids"],
        {"signature": sig,
         "meaning": "no mask-derived metadata, no ROI coordinates, no category can enter the model"})

    ds_val = MultiDomainDataset(MANIFEST_DIR / "val.csv", "VAL", size=512, train=False,
                                channel_policy="RGB_3CH")
    sample = ds_val[0]
    rec("dataset_exposes_task_id_separately", hasattr(sample, "task_id"),
        {"task_id": int(sample.task_id), "dataset": sample.dataset})

    batch = next(iter(create_loader(ds_val, batch_size=2, shuffle=False, seed=42, num_workers=0,
                                    collate_fn=harmonized_collate)))
    rec("collate_returns_task_id_and_image_separately",
        set(["image", "mask", "dataset", "task_id"]).issubset(batch.keys()),
        {"keys": sorted(batch.keys())})
    rec("image_channels_3", int(batch["image"].shape[1]) == 3,
        {"shape": list(batch["image"].shape)})

    test_rejected = False
    try:
        MultiDomainDataset(MANIFEST_DIR / "test.csv", "TEST", size=512, train=False,
                           channel_policy="RGB_3CH")
    except Exception:  # noqa: BLE001
        test_rejected = True
    rec("test_split_rejected_by_dataset", test_rejected, {"attempted_split": "TEST"})

    # ---- 8. TEST lock ------------------------------------------------------ #
    try:
        verify_test_lock(str(ROOT))
        lock_ok = True
        lock_detail = "manifests/test.csv sha256 matches the frozen lock"
    except Exception as exc:  # noqa: BLE001
        lock_ok = False
        lock_detail = str(exc)
    rec("test_lock_verified", lock_ok, {"detail": lock_detail})

    ckpt_dir = ROOT / "checkpoints" / EXPERIMENT_ID
    rec("no_checkpoints_before_training",
        not (ckpt_dir.exists() and list(ckpt_dir.glob("*.pt"))),
        {"checkpoint_dir": str(ckpt_dir.relative_to(ROOT))})

    # ---- 9. domain populations -------------------------------------------- #
    ds_train = MultiDomainDataset(MANIFEST_DIR / "train.csv", "TRAIN", size=512, train=True,
                                  channel_policy="RGB_3CH")
    dist = ds_train.class_distribution()
    rec("train_population_5832", len(ds_train) == 5832, {"n": len(ds_train)})
    rec("val_population_808", len(ds_val) == 808, {"n": len(ds_val)})
    rec("four_domains_present", sorted(dist.keys()) == sorted(DATASET_ORDER),
        {"distribution": dist})

    n_passed = sum(1 for c in checks.values() if c["passed"])
    verdict = ("PHASE21_PRE_EXECUTION_CHECK_PASS" if n_passed == len(checks)
               else "PHASE21_PRE_EXECUTION_CHECK_FAIL")
    artifact = {
        "artifact": "phase21_pre_execution_check",
        "phase": 21,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_id": EXPERIMENT_ID,
        "fail_closed": True,
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": n_passed,
        "verdict": verdict,
        "training_may_start": verdict.endswith("PASS"),
        "test_reads": 0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("passed", n_passed, "/", len(checks))
    for k, v in checks.items():
        if not v["passed"]:
            print("  FAIL", k, v["detail"])
    print("verdict", verdict)
    return 0 if verdict.endswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
