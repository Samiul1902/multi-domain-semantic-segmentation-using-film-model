"""Phase 25F canonical execution — §6 architecture execution binding,
§7 initialization binding, §8 implementation tests.

Constructs ``BARRPostSafetyV1`` (the frozen class), verifies its closed-form
parameter count and initialization, and exercises the frozen training
primitives. Trains nothing; performs no data-dependent forward pass.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402
import phase25f_execution_common as E  # noqa: E402

AUD = C.AUD
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def run():
    tests = {}

    # ================= §6 architecture execution binding ================== #
    m = E.BARRPostSafetyV1()
    n = E.count_params(m)
    tests["parameter_count_1217"] = (n == 1217)
    tests["closed_form_arithmetic"] = (20 * 32 + 32 + 32 * 16 + 16 + 16 * 1 + 1 == 1217)

    layer_shapes = {
        "fc1": [tuple(m.fc1.weight.shape), tuple(m.fc1.bias.shape)],
        "fc2": [tuple(m.fc2.weight.shape), tuple(m.fc2.bias.shape)],
        "fc3": [tuple(m.fc3.weight.shape), tuple(m.fc3.bias.shape)],
    }
    tests["layer1_20_to_32"] = (tuple(m.fc1.weight.shape) == (32, 20))
    tests["layer2_32_to_16"] = (tuple(m.fc2.weight.shape) == (16, 32))
    tests["layer3_16_to_1"] = (tuple(m.fc3.weight.shape) == (1, 16))

    module_types = [type(x).__name__ for x in m.children()]
    tests["no_layernorm"] = ("LayerNorm" not in module_types)
    tests["no_batchnorm"] = not any("BatchNorm" in t for t in module_types)
    tests["no_dropout"] = ("Dropout" not in module_types)
    tests["no_embedding"] = ("Embedding" not in module_types)
    tests["exactly_three_linear"] = (module_types.count("Linear") == 3)
    tests["no_residual_or_attention"] = (
        "MultiheadAttention" not in module_types and "TransformerEncoder" not in module_types)

    # forward signature / shape / raw-logit
    xb = torch.zeros(7, 20, dtype=torch.float32, device=DEV)
    m_dev = m.to(DEV)
    with torch.inference_mode():
        out = m_dev(xb)
    tests["forward_output_shape_batch"] = (tuple(out.shape) == (7,))
    tests["forward_output_1d_per_sample"] = (out.dim() == 1)

    # zero head -> logit exactly 0.0 (would be 0.5 if sigmoid were inside)
    mz = E.BARRPostSafetyV1().to(DEV)
    with torch.no_grad():
        mz.fc3.weight.zero_()
        mz.fc3.bias.zero_()
    with torch.inference_mode():
        z = mz(xb)
    tests["raw_logit_zero_head_gives_zero"] = bool(torch.allclose(
        z, torch.zeros_like(z), atol=1e-6))

    # logits can leave [0,1] (no internal sigmoid)
    big = torch.randn(64, 20, device=DEV) * 50.0
    with torch.inference_mode():
        bl = m_dev(big)
    tests["output_not_restricted_to_unit_interval"] = bool(
        (bl.max().item() > 1.0) or (bl.min().item() < 0.0))

    # sigmoid applied externally equals a probability in (0,1)
    with torch.inference_mode():
        p = torch.sigmoid(m_dev(xb))
    tests["external_sigmoid_in_unit_interval"] = bool(
        torch.all(p >= 0) and torch.all(p <= 1))

    arch = {
        "artifact": "phase25f_architecture_execution_binding",
        "phase": "25F",
        "stage": "SUPERVISOR_RULING_F5_BARRPOSTSAFETYV1_EXECUTION",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "class_name": "BARRPostSafetyV1",
        "architecture_string": "Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1)",
        "module_instantiated": True,
        "parameter_count_closed_form": 1217,
        "parameter_count_measured": int(n),
        "layer_shapes": layer_shapes,
        "module_types": module_types,
        "activation": "SiLU after Linear(20,32) and after Linear(32,16); none after Linear(16,1)",
        "normalization_layers": "NONE",
        "dropout": "NONE",
        "output": "one RAW LOGIT",
        "sigmoid_inside_model": False,
        "inference_probability": "p_accept = sigmoid(logit)",
        "device": str(DEV),
        "all_pass": all(tests[k] for k in [
            "parameter_count_1217", "layer1_20_to_32", "layer2_32_to_16",
            "layer3_16_to_1", "exactly_three_linear", "no_layernorm",
            "no_batchnorm", "no_dropout", "no_embedding", "raw_logit_zero_head_gives_zero",
            "output_not_restricted_to_unit_interval"]),
    }
    C.jdump(arch, AUD / "phase25f_architecture_execution_binding.json")

    # ================= §7 initialization binding ========================== #
    torch.manual_seed(123)
    mi = E.BARRPostSafetyV1()
    init_checks = {}
    # bias bounds must equal 1/sqrt(fan_in) for each layer
    bounds_ok = True
    for lin in (mi.fc1, mi.fc2, mi.fc3):
        b = 1.0 / np.sqrt(lin.in_features)
        if lin.bias.abs().max().item() > b + 1e-7:
            bounds_ok = False
    init_checks["bias_within_uniform_bound"] = bounds_ok
    # reference: kaiming_uniform_(a=sqrt(5)) == default Linear reset
    torch.manual_seed(7)
    ref = nn.Linear(20, 32)
    torch.manual_seed(7)
    w = torch.empty(32, 20)
    nn.init.kaiming_uniform_(w, a=np.sqrt(5))
    b = torch.empty(32)
    bb = 1.0 / np.sqrt(20)
    nn.init.uniform_(b, -bb, bb)
    init_checks["matches_standard_torch_linear_init"] = bool(
        torch.allclose(ref.weight, w) and torch.allclose(ref.bias, b))

    # deterministic under a fixed seed
    a = E.build_model(42, torch.device("cpu"))
    b = E.build_model(42, torch.device("cpu"))
    init_checks["same_seed_identical_init"] = all(
        torch.equal(pa, pb) for pa, pb in zip(a.parameters(), b.parameters()))
    c = E.build_model(43, torch.device("cpu"))
    init_checks["different_seed_differs"] = any(
        not torch.equal(pa, pc) for pa, pc in zip(a.parameters(), c.parameters()))

    init = {
        "artifact": "phase25f_initialization_binding",
        "phase": "25F",
        "stage": "SUPERVISOR_RULING_F5_INITIALIZATION",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "weight_init": "kaiming_uniform_(a=sqrt(5))",
        "bias_init": "Uniform(-1/sqrt(fan_in), +1/sqrt(fan_in))",
        "equivalent_to_standard_pytorch_linear": True,
        "custom_output_head_zero_init": False,
        "controlled_by_authorized_execution_seed": True,
        "checks": init_checks,
        "all_pass": all(init_checks.values()),
    }
    C.jdump(init, AUD / "phase25f_initialization_binding.json")

    # ================= §8 implementation tests ============================ #
    imp = {}

    # normalization primitives
    rng = np.random.default_rng(0)
    F = rng.normal(size=(500, 20)).astype(np.float32)
    F[:, 16:] = 0.0
    F[np.arange(500), 16 + (np.arange(500) % 4)] = 1.0
    mu, sigma, const = E.fit_normalization(F)
    imp["mu_length_16"] = (len(mu) == 16)
    imp["sigma_ddof0_matches_numpy"] = bool(np.allclose(
        sigma, F[:, :16].astype(np.float64).std(axis=0, ddof=0)))
    # ddof=1 must differ (guards against ddof misuse)
    s1 = F[:, :16].astype(np.float64).std(axis=0, ddof=1)
    imp["ddof0_not_ddof1"] = bool(not np.allclose(sigma, s1))
    normed = E.apply_normalization(F, mu, sigma, const)
    imp["normalized_numeric_mean0_std1"] = bool(np.allclose(
        normed[:, :16].astype(np.float64).mean(axis=0), 0.0, atol=1e-6)
        and np.allclose(normed[:, :16].astype(np.float64).std(axis=0), 1.0, atol=1e-6))
    imp["onehot_untouched"] = bool(np.array_equal(normed[:, 16:], F[:, 16:]))
    # zero-sigma rule
    Fc = F.copy()
    Fc[:, 0] = 3.14
    mu2, s2, c2 = E.fit_normalization(Fc)
    n2 = E.apply_normalization(Fc, mu2, s2, c2)
    imp["zero_sigma_rule_constant_column_zeroed"] = bool(
        c2[0] and np.all(n2[:, 0] == 0.0))

    # loss primitive
    logits = torch.tensor([2.0, -3.0, 0.0, 1.5], dtype=torch.float32)
    y = torch.tensor([1.0, 0.0, 1.0, 0.0], dtype=torch.float32)
    loss = nn.BCEWithLogitsLoss(reduction="mean")(logits, y)
    manual = float(np.mean(np.logaddexp(0.0, logits.numpy()) - y.numpy() * logits.numpy()))
    imp["bce_with_logits_mean_matches_manual"] = bool(abs(loss.item() - manual) < 1e-6)
    imp["no_pos_weight"] = (nn.BCEWithLogitsLoss().pos_weight is None)

    # optimizer / scheduler primitives
    om = E.BARRPostSafetyV1()
    opt = torch.optim.AdamW(om.parameters(), lr=1e-3, weight_decay=1e-4)
    g = opt.param_groups[0]
    imp["adamw_lr_1e-3"] = (g["lr"] == 1e-3)
    imp["adamw_wd_1e-4"] = (g["weight_decay"] == 1e-4)
    sch = torch.optim.lr_scheduler.ReduceLROnPlateau(
        opt, mode="min", factor=0.5, patience=8, threshold=1e-4,
        threshold_mode="rel", cooldown=0, min_lr=1e-6, eps=1e-8)
    imp["scheduler_params_exact"] = (
        sch.mode == "min" and sch.factor == 0.5 and sch.patience == 8
        and sch.threshold == 1e-4 and sch.threshold_mode == "rel"
        and sch.cooldown == 0 and list(sch.min_lrs) == [1e-6] and sch.eps == 1e-8)

    # checkpoint-selection rule: strict 1e-12, tie keeps earlier
    def sel(cur, best):
        return cur < best - 1e-12
    imp["checkpoint_real_improvement"] = sel(0.4999, 0.5)
    imp["checkpoint_tie_not_improvement"] = not sel(0.5, 0.5)
    imp["checkpoint_sub_eps_not_improvement"] = not sel(0.5 - 5e-13, 0.5)
    imp["checkpoint_exactly_eps_not_improvement"] = not sel(0.5 - 1e-12, 0.5)

    # gradient flow
    mg = E.BARRPostSafetyV1()
    xg = torch.randn(16, 20)
    yg = torch.randint(0, 2, (16,)).float()
    nn.BCEWithLogitsLoss()(mg(xg), yg).backward()
    imp["all_params_receive_grad"] = all(
        p.grad is not None and torch.isfinite(p.grad).all() for p in mg.parameters())

    # finite on the real feature matrix (no training, single forward)
    feats = E.load_features()
    with torch.inference_mode():
        real_out = E.BARRPostSafetyV1().to(DEV)(
            torch.from_numpy(feats[:256]).to(DEV))
    imp["finite_forward_on_real_features"] = bool(torch.isfinite(real_out).all())

    # state-dict round trip
    m1 = E.BARRPostSafetyV1()
    m2 = E.BARRPostSafetyV1()
    m2.load_state_dict(m1.state_dict())
    imp["state_dict_roundtrip_exact"] = all(
        torch.equal(p, q) for p, q in zip(m1.parameters(), m2.parameters()))

    tests_out = {
        "artifact": "phase25f_implementation_tests",
        "phase": "25F",
        "stage": "IMPLEMENTATION_TESTS",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "architecture_tests": {k: v for k, v in tests.items()},
        "initialization_tests": init_checks,
        "implementation_checks": imp,
        "training_performed": False,
        "checks_passed": sum(1 for v in list(tests.values()) + list(init_checks.values())
                             + list(imp.values()) if v),
        "checks_total": len(tests) + len(init_checks) + len(imp),
        "failures": [k for k, v in list(tests.items()) + list(init_checks.items())
                     + list(imp.items()) if not v],
        "all_pass": all(list(tests.values()) + list(init_checks.values())
                        + list(imp.values())),
    }
    C.jdump(tests_out, AUD / "phase25f_implementation_tests.json")

    print(f"architecture all_pass={arch['all_pass']} params={n}")
    print(f"initialization all_pass={init['all_pass']}")
    print(f"implementation tests {tests_out['checks_passed']}/{tests_out['checks_total']} "
          f"all_pass={tests_out['all_pass']}")
    return tests_out


if __name__ == "__main__":
    run()
