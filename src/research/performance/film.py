"""§6 Functional verification of FiLM task conditioning.

The distinction this module exists to make
------------------------------------------
``GlobalMedFiLM``'s FiLM output projection is zero-initialised, so every site is
an exact identity at step 0 and ``gamma``/``beta`` are identically zero for every
task.  That is *permitted*, and it is also why an initialization test proves
nothing: a model whose conditioning branch is disconnected, mis-wired or dead
still passes it.  The mission says so directly, and this module therefore tests
the conditioning **after optimization** as well as before.

A second, less obvious consequence is measured rather than assumed.  Because the
output projection starts at zero, the gradient reaching the FiLM *hidden* layer
and the task embedding is **exactly zero** on the first step — it is multiplied
by ``W_output = 0``.  Only the output projection itself receives gradient
initially.  So "gradients reach the trainable FiLM projections" is true from step
0 for the last layer and only from step 1 for the rest, and the check states
which is which instead of averaging the two into a single green tick.

The functional test
-------------------
One fixed image, one target that depends on the task id (left half for task 0,
right half for task 1).  A task-independent network cannot fit both, so the loss
can only fall if the conditioning path actually carries the task signal.  The
same objective is then run on the C1 control arm, whose conditioning is frozen at
identity: if that arm fits the task pair equally well, the FiLM branch is not
doing the work and the treatment result would be meaningless.
"""
from __future__ import annotations

import copy
import hashlib
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import torch
from torch import nn

from src.models.film.global_medfilm import (GLOBAL_MEDFILM_ARCHITECTURE_ID,
                                            GlobalMedFiLM)
from src.research.c1_film import control as C1
from src.research.full_pipeline import seeds as SEEDS

from . import bench as B

EVIDENCE_CLASS = B.EVIDENCE_CLASS
FIXTURE_RESOLUTION = 64          # optimization fixture; the contract size is 512
TASK_PAIR = (0, 1)

#: The provable optimum for a *task-blind* model on the toy objective.  Each
#: pixel's target is 1 for one task and 0 for the other, and a task-blind model
#: must emit the same value for both, so its best possible prediction is 0.5
#: everywhere, i.e. a BCE of exactly ``ln 2``.  This is what makes the thresholds
#: below a criterion rather than a fitted tolerance: a treatment loss far below
#: ``ln 2`` cannot have been achieved without the task signal, and a control loss
#: sitting at ``ln 2`` is exactly what a disconnected conditioning path predicts.
TASK_BLIND_OPTIMUM = float(np.log(2.0))
#: A treatment must beat the task-blind optimum by a wide margin...
TREATMENT_LOSS_CEILING = 0.25
#: ...while a frozen-conditioning control must sit at it.
CONTROL_LOSS_FLOOR = 0.60
#: A materially different mask boundary.  1.0 in logit space is ~0.24 in
#: probability at the steepest point of the sigmoid, i.e. a real boundary shift,
#: not floating-point noise.
TASK_DIFFERENCE_FLOOR = 1.0


def _check(name: str, passed: bool, detail: str, **extra: Any) -> Dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail, **extra}


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def toy_task_batch(*, size: int = FIXTURE_RESOLUTION, device: str = "cpu",
                   seed: int = 20261103) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """One image, two tasks, and a target that depends on the task id.

    The image is **constant** for both tasks, which is what makes the ablation
    decisive rather than merely suggestive: a task-blind network receives exactly
    the same input for task 0 and task 1, so it can only ever emit one map, and
    fitting a left-half target and a right-half target at once is impossible for
    it.  Any loss reduction therefore has to travel through the conditioning
    path.  A random image would work too, but a constant one removes the
    possibility that the backbone exploits spatial structure instead.
    """
    image = torch.full((2, 3, size, size), 0.5)
    task = torch.tensor(list(TASK_PAIR), dtype=torch.long)
    target = torch.zeros((2, 1, size, size))
    target[0, :, :, : size // 2] = 1.0                     # task 0 -> left half
    target[1, :, :, size // 2:] = 1.0                      # task 1 -> right half
    return image.to(device), task.to(device), target.to(device)


def _fit(model: nn.Module, *, steps: int, lr: float, size: int, device: str,
         seed: int = 42) -> Dict[str, Any]:
    """Train on the task-pair objective and return the loss trajectory."""
    SEEDS.seed_everything(seed)
    image, task, target = toy_task_batch(size=size, device=device)
    model.train()
    parameters = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=lr)
    criterion = nn.BCEWithLogitsLoss()
    losses: List[float] = []
    for _ in range(int(steps)):
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(image, task), target)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    return {"losses": losses, "first": losses[0] if losses else None,
            "last": losses[-1] if losses else None,
            "reduction": (losses[0] - losses[-1]) if losses else None,
            "trainable_parameters": sum(p.numel() for p in parameters)}


def _task_difference(model: nn.Module, *, size: int, device: str) -> Dict[str, Any]:
    """Forward the same image under two task ids and measure the difference.

    The repeat check re-runs the *identical* call.  Comparing a batch-2 slice
    against a separate batch-1 forward would conflate two different kernel
    selections with nondeterminism, and would fail for a reason that has nothing
    to do with conditioning.
    """
    image, task, _target = toy_task_batch(size=size, device=device)
    model.eval()
    with torch.no_grad():
        output = model(image, task)
        repeat = model(image, task)
    delta = (output[0:1] - output[1:2]).abs()
    return {"max_abs_difference": float(delta.max()),
            "mean_abs_difference": float(delta.mean()),
            "same_task_repeat_identical": bool(torch.equal(output, repeat)),
            "finite": bool(torch.isfinite(output).all())}


def _conditioning_state(model: nn.Module) -> Dict[str, torch.Tensor]:
    return {name: tensor.detach().clone()
            for name, tensor in model.state_dict().items() if C1.is_conditioning(name)}


def _backbone_state(model: nn.Module) -> Dict[str, torch.Tensor]:
    return {name: tensor.detach().clone()
            for name, tensor in model.state_dict().items() if not C1.is_conditioning(name)}


def _gradient_report(model: nn.Module, *, size: int, device: str) -> Dict[str, Any]:
    """Per-group gradient magnitude after one backward at the initial state."""
    SEEDS.seed_everything(42)
    image, task, target = toy_task_batch(size=size, device=device)
    model.zero_grad(set_to_none=True)
    nn.BCEWithLogitsLoss()(model(image, task), target).backward()

    def total(predicate) -> Tuple[float, int, int]:
        magnitude, present, nonzero = 0.0, 0, 0
        for name, parameter in model.named_parameters():
            if not predicate(name) or not parameter.requires_grad:
                continue
            if parameter.grad is None:
                continue
            present += 1
            value = float(parameter.grad.abs().sum())
            magnitude += value
            if value > 0.0:
                nonzero += 1
        return magnitude, present, nonzero

    output_layer = total(lambda n: n.startswith("film_layers.") and ".output." in n)
    hidden_layer = total(lambda n: n.startswith("film_layers.") and ".hidden." in n)
    embedding = total(lambda n: n.startswith("task_embedding."))
    backbone = total(lambda n: not C1.is_conditioning(n))
    model.zero_grad(set_to_none=True)
    return {"output_projection": {"magnitude": output_layer[0],
                                  "tensors": output_layer[1],
                                  "nonzero_tensors": output_layer[2]},
            "hidden_layer": {"magnitude": hidden_layer[0],
                             "tensors": hidden_layer[1],
                             "nonzero_tensors": hidden_layer[2]},
            "task_embedding": {"magnitude": embedding[0],
                               "tensors": embedding[1],
                               "nonzero_tensors": embedding[2]},
            "backbone": {"magnitude": backbone[0], "tensors": backbone[1],
                         "nonzero_tensors": backbone[2]}}


# --------------------------------------------------------------------------- #
# 1. Identity propagation through every intended site
# --------------------------------------------------------------------------- #
def check_identity_propagation(*, size: int = FIXTURE_RESOLUTION,
                               device: str = "cpu") -> Dict[str, Any]:
    """Every declared FiLM site is reached, and with the embedding of the right task.

    At initialization ``gamma`` and ``beta`` are zero for all tasks, so the output
    cannot reveal whether the task id arrived.  A forward hook on each site can:
    it records the embedding tensor the site actually received, which is compared
    against ``task_embedding(task_ids)``.
    """
    model = GlobalMedFiLM().to(device).eval()
    image, task, _target = toy_task_batch(size=size, device=device)
    with torch.no_grad():
        expected = model.task_embedding(task)

    seen: Dict[str, List[torch.Tensor]] = {name: [] for name in model.film_locations}

    def make_hook(name: str):
        def hook(_module: nn.Module, inputs: Sequence[Any], _output: Any) -> None:
            seen[name].append(inputs[1].detach().clone())
        return hook

    handles = [model.film_layers[name].register_forward_hook(make_hook(name))
               for name in model.film_locations]
    try:
        with torch.no_grad():
            model(image, task)
    finally:
        for handle in handles:
            handle.remove()

    reached = {name: len(calls) for name, calls in seen.items()}
    all_reached = all(count == 1 for count in reached.values())
    embedding_correct = all(
        bool(torch.equal(calls[0], expected)) for calls in seen.values() if calls)
    return _check(
        "identity_propagation", all_reached and embedding_correct,
        (f"all {len(model.film_locations)} declared sites ran once and received the "
         "task embedding for the requested ids" if all_reached and embedding_correct
         else f"reached={reached} embedding_correct={embedding_correct}"),
        sites=list(model.film_locations), call_counts=reached,
        embedding_matches_expected=embedding_correct,
        identity_at_init=_identity_at_init(model, device=device))


def _identity_at_init(model: GlobalMedFiLM, *, device: str) -> Dict[str, Any]:
    """The permitted-but-uninformative property: identity, for every task."""
    with torch.no_grad():
        params = model.film_parameters_for_tasks(
            torch.arange(model.task_count, device=device))
    worst_gamma = max(float(gamma.abs().max()) for gamma, _beta in params.values())
    worst_beta = max(float(beta.abs().max()) for _gamma, beta in params.values())
    return {"max_abs_gamma": worst_gamma, "max_abs_beta": worst_beta,
            "identity_at_init": worst_gamma == 0.0 and worst_beta == 0.0,
            "note": ("identity at initialization is permitted and expected; it is not "
                     "evidence that conditioning works after optimization")}


# --------------------------------------------------------------------------- #
# 2 and 3. Gradients, then parameter updates
# --------------------------------------------------------------------------- #
def check_gradients_and_updates(*, size: int = FIXTURE_RESOLUTION,
                                device: str = "cpu", steps: int = 30,
                                lr: float = 1e-2, seed: int = 42) -> Dict[str, Any]:
    """Gradient reach at step 0, gradient reach after one step, and real movement.

    The two-phase result is the honest one: the zero-initialised output projection
    blocks gradient to the hidden layer and the embedding on the first backward,
    so those groups only start learning after the output projection moves.
    """
    model = GlobalMedFiLM().to(device)
    at_init = _gradient_report(model, size=size, device=device)
    init_conditioning = _conditioning_state(model)

    # one optimizer step, then inspect gradients again
    SEEDS.seed_everything(seed)
    image, task, target = toy_task_batch(size=size, device=device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=lr)
    optimizer.zero_grad(set_to_none=True)
    criterion(model(image, task), target).backward()
    optimizer.step()
    after_one = _gradient_report(model, size=size, device=device)

    trajectory = _fit(model, steps=steps - 1, lr=lr, size=size, device=device, seed=seed)
    final_conditioning = _conditioning_state(model)

    output_moved = any(
        not torch.equal(init_conditioning[name], final_conditioning[name])
        for name in init_conditioning if ".output." in name)
    hidden_moved = any(
        not torch.equal(init_conditioning[name], final_conditioning[name])
        for name in init_conditioning if ".hidden." in name)
    embedding_moved = any(
        not torch.equal(init_conditioning[name], final_conditioning[name])
        for name in init_conditioning if name.startswith("task_embedding."))

    output_off_zero = all(
        int(torch.count_nonzero(value)) > 0
        for name, value in final_conditioning.items() if ".output.weight" in name)

    passed = (at_init["output_projection"]["nonzero_tensors"] > 0
              and at_init["hidden_layer"]["magnitude"] == 0.0
              and at_init["task_embedding"]["magnitude"] == 0.0
              and after_one["hidden_layer"]["nonzero_tensors"] > 0
              and after_one["task_embedding"]["nonzero_tensors"] > 0
              and output_moved and hidden_moved and embedding_moved and output_off_zero)
    return _check(
        "gradients_and_updates", passed,
        ("at step 0 only the FiLM output projection receives gradient (the zero "
         "initialisation blocks the hidden layer and the embedding); from step 1 all "
         "three do, and all three parameters move off their initial values"
         if passed else
         f"at_init={at_init['output_projection']} hidden0={at_init['hidden_layer']} "
         f"after1={after_one['hidden_layer']} moved=({output_moved},{hidden_moved},"
         f"{embedding_moved}) off_zero={output_off_zero}"),
        gradients_at_init=at_init, gradients_after_one_step=after_one,
        parameters_moved={"output": output_moved, "hidden": hidden_moved,
                          "embedding": embedding_moved},
        output_projection_off_zero=output_off_zero,
        trajectory={k: trajectory[k] for k in ("first", "last", "reduction")})


# --------------------------------------------------------------------------- #
# 4. Learned state produces task-dependent differences
# --------------------------------------------------------------------------- #
def check_learned_task_dependence(*, size: int = FIXTURE_RESOLUTION,
                                  device: str = "cpu", steps: int = 150,
                                  lr: float = 1e-2, seed: int = 42,
                                  contract_size: Optional[int] = None) -> Dict[str, Any]:
    """After optimization the same image produces different masks per task.

    The criterion is not a tuned tolerance: the toy objective's task-blind optimum
    is exactly ``ln 2`` (see ``TASK_BLIND_OPTIMUM``), so a loss far below it can
    only be reached by using the task id, and a task-dependent output difference
    is then the mechanism that made it possible.
    """
    model = GlobalMedFiLM().to(device)
    before = _task_difference(model, size=size, device=device)
    fit = _fit(model, steps=steps, lr=lr, size=size, device=device, seed=seed)
    after = _task_difference(model, size=size, device=device)

    beat_optimum = fit["last"] is not None and fit["last"] < TREATMENT_LOSS_CEILING
    diverged = after["max_abs_difference"] >= TASK_DIFFERENCE_FLOOR
    learned = beat_optimum and diverged and after["same_task_repeat_identical"]
    contract = None
    if contract_size:
        contract = _task_difference(model, size=int(contract_size), device=device)

    passed = bool(learned and after["finite"]
                  and (contract is None
                       or contract["max_abs_difference"] >= TASK_DIFFERENCE_FLOOR))
    return _check(
        "learned_task_dependence", passed,
        (f"loss fell {fit['first']:.4f} -> {fit['last']:.4f}, below the task-blind "
         f"optimum ln 2 = {TASK_BLIND_OPTIMUM:.4f}; the same image under task 0 and "
         f"task 1 now differs by max |delta| {after['max_abs_difference']:.2f} in logit "
         f"space (was {before['max_abs_difference']:.2e} at initialization), and a "
         "same-task repeat is bitwise identical"
         if passed else
         f"before={before['max_abs_difference']} after={after['max_abs_difference']} "
         f"last_loss={fit['last']} beat_optimum={beat_optimum} diverged={diverged}"),
        fixture_resolution=int(size), steps=int(steps), learning_rate=float(lr),
        task_blind_optimum=TASK_BLIND_OPTIMUM,
        difference_before_init=before, difference_after_optimization=after,
        loss=fit, at_contract_resolution=contract,
        note=("the fixture resolution is smaller than the 512 contract for speed; the "
              "contract-resolution forward is reported separately"))


# --------------------------------------------------------------------------- #
# 5 and 6. C1 identity control, and unrelated components
# --------------------------------------------------------------------------- #
def check_c1_identity_control(*, size: int = FIXTURE_RESOLUTION, device: str = "cpu",
                              seed: int = 42, steps: int = 150,
                              lr: float = 1e-2) -> Dict[str, Any]:
    """The frozen-conditioning arm is an exact identity and cannot fake conditioning.

    ``build_matched_arms`` copies the treatment before optimization, so the two
    arms have identical weights and identical total parameter counts; only
    ``requires_grad`` differs on the 90,768 conditioning tensors.  Freezing never
    removes parameters, and this check never asserts a total-parameter difference.
    """
    treatment, control = C1.build_matched_arms(seed)
    treatment, control = treatment.to(device), control.to(device)

    # (a) identical initial state, and the control's conditioning is frozen
    initial_identical = all(
        torch.equal(treatment.state_dict()[name], control.state_dict()[name])
        for name in treatment.state_dict())
    treatment_counts = C1.parameter_accounting(treatment)
    control_counts = C1.parameter_accounting(control)
    frozen = all(not p.requires_grad for name, p in control.named_parameters()
                 if C1.is_conditioning(name))
    totals_equal = treatment_counts["total"] == control_counts["total"]

    # (b) at step 0 the two arms are functionally identical on the task pair
    image, task, _target = toy_task_batch(size=size, device=device)
    with torch.no_grad():
        treatment_out = treatment(image, task)
        control_out = control(image, task)
    identical_at_init = bool(torch.equal(treatment_out, control_out))

    # (c) the control stays identity under optimization: its conditioning never moves
    before_conditioning = _conditioning_state(control)
    before_backbone = _backbone_state(control)
    control_fit = _fit(control, steps=steps, lr=lr, size=size, device=device, seed=seed)
    after_conditioning = _conditioning_state(control)
    after_backbone = _backbone_state(control)
    conditioning_frozen = all(
        torch.equal(before_conditioning[name], after_conditioning[name])
        for name in before_conditioning)
    backbone_moved = any(
        not torch.equal(before_backbone[name], after_backbone[name])
        for name in before_backbone)
    control_difference = _task_difference(control, size=size, device=device)

    # (d) the treatment, on the same objective, does condition
    treatment_fit = _fit(treatment, steps=steps, lr=lr, size=size, device=device, seed=seed)
    treatment_difference = _task_difference(treatment, size=size, device=device)

    control_flat = control_difference["max_abs_difference"] == 0.0
    treatment_conditions = (treatment_difference["max_abs_difference"]
                            >= TASK_DIFFERENCE_FLOOR)
    # the ablation, stated against the task-blind optimum rather than a fitted gap
    control_at_optimum = (control_fit["last"] is not None
                          and control_fit["last"] > CONTROL_LOSS_FLOOR)
    treatment_beats_optimum = (treatment_fit["last"] is not None
                               and treatment_fit["last"] < TREATMENT_LOSS_CEILING)

    passed = (initial_identical and frozen and totals_equal and identical_at_init
              and conditioning_frozen and backbone_moved and control_flat
              and treatment_conditions and control_at_optimum and treatment_beats_optimum)
    return _check(
        "c1_identity_control", passed,
        ("the arms start bitwise identical with equal total parameter counts; the "
         "control's conditioning is frozen and never moves, so its two task outputs "
         f"are identical (max |delta| = 0) and it stays at the task-blind optimum "
         f"(loss {control_fit['last']:.4f} vs ln 2 = {TASK_BLIND_OPTIMUM:.4f}), while "
         f"the treatment conditions (max |delta| "
         f"{treatment_difference['max_abs_difference']:.2f}, loss "
         f"{treatment_fit['last']:.4f})"
         if passed else
         f"identical={initial_identical} frozen={frozen} totals={totals_equal} "
         f"init_out={identical_at_init} frozen_after={conditioning_frozen} "
         f"backbone_moved={backbone_moved} control_flat={control_flat} "
         f"treatment_conditions={treatment_conditions} "
         f"control_at_optimum={control_at_optimum} "
         f"treatment_beats_optimum={treatment_beats_optimum}"),
        parameter_counts={"treatment": treatment_counts, "control": control_counts},
        totals_equal=totals_equal,
        initial_state_identical=initial_identical,
        conditioning_frozen_after_training=conditioning_frozen,
        backbone_moved_in_control=backbone_moved,
        control_task_difference=control_difference,
        treatment_task_difference=treatment_difference,
        control_loss=control_fit["last"], treatment_loss=treatment_fit["last"],
        note=("freezing never reduces the total parameter count: both arms hold "
              f"{treatment_counts['total']} parameters, and the 90,768 conditioning "
              "tensors are identical in value at step 0"))


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _state_digest(model: nn.Module) -> str:
    """Order-independent digest of every parameter and buffer in a module."""
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode("utf-8"))
        digest.update(tensor.detach().to("cpu").contiguous().numpy().tobytes())
    return digest.hexdigest()


def _film_site_names(model: nn.Module) -> Tuple[str, ...]:
    """The FiLM modules the model actually instantiated, in definition order."""
    return tuple(name for name, _module in model.named_modules()
                 if name.startswith("film_layers."))


def check_unrelated_components_untouched(*, size: int = FIXTURE_RESOLUTION,
                                         device: str = "cpu", seed: int = 42,
                                         steps: int = 30,
                                         lr: float = 1e-2) -> Dict[str, Any]:
    """§6 check 6: the conditioning experiment must not disturb anything else.

    Optimising a FiLM model is only meaningful if it is the *only* thing that
    changed.  This check snapshots components the experiment has no business
    touching — a second, unrelated model instance, the declared FiLM site list,
    the architecture identity, and the frozen C1 arm construction — runs a real
    optimization on the treatment, and requires every snapshot to be bitwise
    unchanged.  It also requires that the treatment *did* move, so a no-op
    experiment cannot pass by leaving the world untouched.
    """
    unrelated = GlobalMedFiLM().to(device)      # a separate instance, never optimised
    before_digest = _state_digest(unrelated)
    before_sites = _film_site_names(unrelated)
    before_architecture = (GLOBAL_MEDFILM_ARCHITECTURE_ID,
                           C1.ARCHITECTURE_SHA256,
                           tuple(C1.CONDITIONING_PREFIXES))
    before_counts = dict(C1.EXPECTED_COUNTS)
    before_arms = [_state_digest(arm) for arm in C1.build_matched_arms(seed)]

    treatment = GlobalMedFiLM().to(device)
    treatment_before = _state_digest(treatment)
    fit = _fit(treatment, steps=steps, lr=lr, size=size, device=device, seed=seed)
    treatment_after = _state_digest(treatment)

    after_digest = _state_digest(unrelated)
    after_sites = _film_site_names(unrelated)
    after_architecture = (GLOBAL_MEDFILM_ARCHITECTURE_ID,
                          C1.ARCHITECTURE_SHA256,
                          tuple(C1.CONDITIONING_PREFIXES))
    after_counts = dict(C1.EXPECTED_COUNTS)
    after_arms = [_state_digest(arm) for arm in C1.build_matched_arms(seed)]

    unrelated_unchanged = before_digest == after_digest
    sites_present = len(before_sites) >= 5
    sites_unchanged = before_sites == after_sites
    architecture_unchanged = before_architecture == after_architecture
    counts_unchanged = before_counts == after_counts
    arms_unchanged = before_arms == after_arms
    treatment_moved = treatment_before != treatment_after

    passed = bool(unrelated_unchanged and sites_present and sites_unchanged
                  and architecture_unchanged and counts_unchanged and arms_unchanged
                  and treatment_moved)
    return _check(
        "unrelated_components_untouched", passed,
        ("a second model instance, the FiLM site list, the architecture id, the expected "
         "parameter counts and the C1 matched-arm construction are all bitwise unchanged "
         f"after {steps} optimization steps, while the treatment itself moved "
         f"({treatment_before[:12]} -> {treatment_after[:12]})"
         if passed else
         f"unrelated={unrelated_unchanged} sites_present={sites_present} "
         f"sites={sites_unchanged} "
         f"architecture={architecture_unchanged} counts={counts_unchanged} "
         f"arms={arms_unchanged} treatment_moved={treatment_moved}"),
        steps=int(steps), learning_rate=float(lr),
        unrelated_instance_digest={"before": before_digest, "after": after_digest},
        treatment_digest={"before": treatment_before, "after": treatment_after},
        film_sites_unchanged=sites_unchanged,
        architecture_id_unchanged=architecture_unchanged,
        expected_counts_unchanged=counts_unchanged,
        matched_arms_unchanged=arms_unchanged,
        treatment_moved=treatment_moved,
        loss=fit,
        note=("this check is about the experiment's blast radius, not about the model's "
              "own backbone: the treatment's non-FiLM weights are expected to change "
              "during optimization and are not asserted stable"))


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def film_report(*, device: str = "cpu", seed: int = 42,
                size: int = FIXTURE_RESOLUTION,
                contract_size: Optional[int] = 512) -> Dict[str, Any]:
    """Every §6 check, with the initialization-only limitation stated up front."""
    checks = [
        check_identity_propagation(size=size, device=device),
        check_gradients_and_updates(size=size, device=device, seed=seed),
        check_learned_task_dependence(size=size, device=device, seed=seed,
                                      contract_size=contract_size),
        check_c1_identity_control(size=size, device=device, seed=seed),
        check_unrelated_components_untouched(size=size, device=device, seed=seed),
    ]
    failed = [c["check"] for c in checks if not c["passed"]]
    return {"schema": "phase_d_film_conditioning_v1", "evidence_class": EVIDENCE_CLASS,
            "architecture_id": GLOBAL_MEDFILM_ARCHITECTURE_ID,
            "seed": int(seed), "device": device,
            "fixture_resolution": int(size), "checks": checks,
            "n_checks": len(checks), "n_passed": len(checks) - len(failed),
            "failed": failed, "all_passed": not failed,
            "expected_counts": dict(C1.EXPECTED_COUNTS),
            "limitation": ("identity at initialization is permitted but proves nothing "
                           "about conditioning; the functional and ablation checks above "
                           "are what establish that the task signal is carried"),
            "note": ("Synthetic fixture, reduced resolution for the optimization loop. "
                     "No accuracy claim follows, and no real training was performed.")}


__all__ = ["EVIDENCE_CLASS", "FIXTURE_RESOLUTION", "TASK_PAIR", "check_c1_identity_control",
           "check_gradients_and_updates", "check_identity_propagation",
           "check_learned_task_dependence", "check_unrelated_components_untouched",
           "film_report", "toy_task_batch"]
