"""§5 Determinism, resume equivalence and export reproducibility.

The Phase B defect this module rechecks
---------------------------------------
``router_stage`` shuffles its fit loader with a **standalone**
``torch.Generator``.  ``capture_rng`` covers python, numpy, torch-CPU and
torch-CUDA, but not that generator, so a checkpoint restored with only
``restore_rng`` replays epoch 1's permutation for epoch 2 and the resumed
trajectory diverges (measured in Phase B: epoch-1 loss identical, epoch-2 loss
0.0053 versus 0.0084).  The fix records ``data_order_generator_state`` in the
envelope and refuses a checkpoint that lacks it.

This module does not take that on trust.  It runs the same mechanism on a toy
problem and ablates the fix: the uninterrupted run, the resumed run **with** the
generator state, and the resumed run **without** it.  If the ablation did not
separate, the fix would be unnecessary and saying so would be the honest result.

Where identity is exact and where tolerance is appropriate
----------------------------------------------------------
**Exact (bitwise, demonstrated here)**
    RNG replay; DataLoader permutation for a given generator state; checkpoint
    selection re-derived from persisted history; export bytes for a fixed record
    order; per-image metric values for a fixed mask pair; a repeated forward on
    *the same device* under ``use_deterministic_algorithms``.

**Tolerance only**
    CPU versus CUDA.  Two implementations of the same arithmetic in different
    kernels are not required to agree bitwise, and no cross-device bitwise claim
    is made anywhere in this repository.  :func:`parity` in
    :mod:`src.research.performance.stability` states the tolerances it uses.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
import platform
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from src.research.full_pipeline import seeds as SEEDS

from . import bench as B

EVIDENCE_CLASS = B.EVIDENCE_CLASS

#: Distinguishes an exact-identity check from a tolerance check, so a reader can
#: never mistake one for the other.
EXACT = "exact"
TOLERANCE = "tolerance"

TOY_SIDE = 16
TOY_SAMPLES = 64
TOY_BATCH = 8


# --------------------------------------------------------------------------- #
# Check records
# --------------------------------------------------------------------------- #
def _check(name: str, passed: bool, detail: str, *, identity: str,
           **extra: Any) -> Dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail,
            "identity_class": identity, **extra}


# --------------------------------------------------------------------------- #
# 1. Seeding
# --------------------------------------------------------------------------- #
def check_seeding(seed: int = 42) -> Dict[str, Any]:
    """Every RNG source is actually seeded, and two seeded runs agree exactly."""
    import random

    SEEDS.seed_everything(seed)
    first = (random.random(), float(np.random.random()), float(torch.rand(1)))
    SEEDS.seed_everything(seed)
    second = (random.random(), float(np.random.random()), float(torch.rand(1)))
    same = first == second
    return _check("seeding", same,
                  "python/numpy/torch draws reproduce exactly after re-seeding",
                  identity=EXACT, first=list(first), second=list(second),
                  configuration=SEEDS.determinism_report())


# --------------------------------------------------------------------------- #
# 2. RNG capture / restore
# --------------------------------------------------------------------------- #
def check_rng_replay(seed: int = 42) -> Dict[str, Any]:
    """capture -> consume -> restore -> replay reproduces every source."""
    import random

    SEEDS.seed_everything(seed)
    state = SEEDS.capture_rng()
    consumed = (random.random(), float(np.random.random()), float(torch.rand(3).sum()))
    SEEDS.restore_rng(state)
    replayed = (random.random(), float(np.random.random()), float(torch.rand(3).sum()))
    return _check("rng_capture_restore", consumed == replayed,
                  "all four RNG sources replay exactly from a captured state",
                  identity=EXACT, consumed=list(consumed), replayed=list(replayed),
                  sources=list(SEEDS.capture_rng()))


def check_empty_state_refused() -> Dict[str, Any]:
    """An absent RNG state is a hard error, not a silent fresh start."""
    try:
        SEEDS.restore_rng({})
    except ValueError as exc:
        return _check("empty_rng_state_refused", True, str(exc), identity=EXACT)
    return _check("empty_rng_state_refused", False,
                  "restore_rng accepted an empty state", identity=EXACT)


# --------------------------------------------------------------------------- #
# 3. Loader ordering — the mechanism behind the Phase B defect
# --------------------------------------------------------------------------- #
def _toy_data(seed: int = 42) -> Tuple[torch.Tensor, torch.Tensor]:
    gen = torch.Generator().manual_seed(seed)
    x = torch.randn((TOY_SAMPLES, TOY_SIDE), generator=gen)
    y = (x.sum(dim=1) > 0).float()
    return x, y


def _permutation(gen: torch.Generator, *, seed: int = 42) -> List[int]:
    """The order a shuffled loader would visit the samples in."""
    x, y = _toy_data(seed)
    loader = DataLoader(TensorDataset(x, y), batch_size=TOY_BATCH, shuffle=True,
                        generator=gen)
    order: List[int] = []
    for xb, _yb in loader:
        # identify each row by its first coordinate, which is unique in practice
        for row in xb:
            order.append(int((x[:, 0] == row[0]).nonzero()[0, 0]))
    return order


def check_loader_order(seed: int = 42) -> Dict[str, Any]:
    """The shuffled order is a pure function of the generator state — and only of it.

    Two consequences are demonstrated: the generator advances between epochs (so
    it must be captured), and restoring the state reproduces the order exactly
    (so capturing it is sufficient).
    """
    gen = torch.Generator().manual_seed(seed)
    first = _permutation(gen)
    second = _permutation(gen)
    advanced = first != second

    gen2 = torch.Generator().manual_seed(seed)
    first_again = _permutation(gen2)
    reproducible = first_again == first

    # restoring the captured state after a second draw reproduces the second order
    state = gen2.get_state()
    third = _permutation(gen2)
    gen2.set_state(state)
    third_again = _permutation(gen2)
    restore_exact = third == third_again

    passed = advanced and reproducible and restore_exact
    return _check(
        "loader_order", passed,
        ("the generator advances between epochs and a captured state reproduces the "
         "order exactly" if passed else
         "loader order was not a pure function of the captured generator state"),
        identity=EXACT, epochs_differ=advanced, reseed_reproduces=reproducible,
        state_restore_reproduces=restore_exact)


# --------------------------------------------------------------------------- #
# 4. Resume equivalence, with the fix ablated
# --------------------------------------------------------------------------- #
def _toy_training(seed: int, epochs: int, *, snapshot_at: Optional[int] = None,
                  resume_from: Optional[Mapping[str, Any]] = None,
                  restore_order: bool = True) -> Dict[str, Any]:
    """A minimal training loop with exactly the Phase B structure.

    ``seed_everything`` runs first, then a checkpoint (if any) is restored — the
    same order the real stage uses.  ``restore_order`` ablates the fix.
    """
    SEEDS.seed_everything(seed)
    torch.manual_seed(seed)
    x, y = _toy_data(seed)
    model = nn.Linear(TOY_SIDE, 1)
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    gen = torch.Generator()
    gen.manual_seed(seed)
    criterion = nn.BCEWithLogitsLoss()
    dataset = TensorDataset(x, y)

    start = 1
    if resume_from is not None:
        model.load_state_dict(resume_from["model"])
        opt.load_state_dict(resume_from["optimizer"])
        SEEDS.restore_rng(resume_from["rng"])
        if restore_order:
            gen.set_state(resume_from["order"])
        start = int(resume_from["epoch"]) + 1

    losses: List[float] = []
    snapshot: Optional[Dict[str, Any]] = None
    for epoch in range(start, epochs + 1):
        loader = DataLoader(dataset, batch_size=TOY_BATCH, shuffle=True, generator=gen)
        model.train()
        batch_losses: List[float] = []
        for xb, yb in loader:
            opt.zero_grad(set_to_none=True)
            loss = criterion(model(xb).squeeze(1), yb)
            loss.backward()
            opt.step()
            batch_losses.append(float(loss.item()))
        losses.append(float(np.mean(batch_losses)))
        if snapshot_at is not None and epoch == snapshot_at:
            snapshot = {"model": copy.deepcopy(model.state_dict()),
                        "optimizer": copy.deepcopy(opt.state_dict()),
                        "rng": SEEDS.capture_rng(),
                        "order": gen.get_state(),
                        "epoch": epoch}
    return {"losses": losses, "snapshot": snapshot,
            "weights_sha256": _state_sha(model.state_dict())}


def _state_sha(state: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for key in sorted(state):
        tensor = state[key].detach().to("cpu", torch.float64).contiguous()
        digest.update(key.encode())
        digest.update(np.ascontiguousarray(tensor.numpy()).tobytes())
    return digest.hexdigest()


def check_resume_equivalence(seed: int = 42, epochs: int = 3) -> Dict[str, Any]:
    """Uninterrupted vs resumed-with-fix vs resumed-without-fix.

    The two claims are separated on purpose:

    * the fix is **sufficient** — the resumed run reproduces the uninterrupted
      run's per-epoch losses exactly and ends on identical weights;
    * the fix is **necessary** — without the generator state the second epoch
      diverges, which is the Phase B observation reproduced from first principles.
    """
    uninterrupted = _toy_training(seed, epochs)
    _partial = _toy_training(seed, epochs, snapshot_at=1)
    snapshot = _partial["snapshot"]
    if snapshot is None:                                     # pragma: no cover - defensive
        raise RuntimeError("snapshot was not captured")

    with_fix = _toy_training(seed, epochs, resume_from=snapshot, restore_order=True)
    without_fix = _toy_training(seed, epochs, resume_from=snapshot, restore_order=False)

    resumed_tail = with_fix["losses"]
    expected_tail = uninterrupted["losses"][1:]
    exact = resumed_tail == expected_tail
    weights_equal = with_fix["weights_sha256"] == uninterrupted["weights_sha256"]
    divergence = (without_fix["losses"][0] != uninterrupted["losses"][1]
                  if without_fix["losses"] else False)

    passed = exact and weights_equal and divergence
    detail = ("resume with the generator state reproduces the uninterrupted trajectory "
              "exactly and ends on identical weights; without it the first resumed epoch "
              f"diverges ({without_fix['losses'][0]:.6f} vs "
              f"{uninterrupted['losses'][1]:.6f})" if passed else
              f"exact={exact} weights={weights_equal} divergence={divergence}")
    return _check("resume_equivalence", passed, detail, identity=EXACT,
                  uninterrupted=[round(v, 12) for v in uninterrupted["losses"]],
                  resumed_with_fix=[round(v, 12) for v in resumed_tail],
                  resumed_without_fix=[round(v, 12) for v in without_fix["losses"]],
                  weights_sha256_uninterrupted=uninterrupted["weights_sha256"],
                  weights_sha256_resumed=with_fix["weights_sha256"],
                  fix_necessary=divergence, fix_sufficient=exact and weights_equal)


# --------------------------------------------------------------------------- #
# 5. CUDA algorithm selection
# --------------------------------------------------------------------------- #
def check_cuda_algorithms(device: str = "cuda") -> Dict[str, Any]:
    """Deterministic algorithms are enabled, and a repeated forward is bitwise equal.

    A same-device repetition is the strongest determinism claim that can actually
    be demonstrated.  Cross-device bitwise equality is **not** claimed, and is
    tested for tolerance in :mod:`src.research.performance.stability`.
    """
    config = SEEDS.determinism_report()
    cuda = torch.cuda.is_available() and torch.device(device).type == "cuda"
    if not cuda:
        return _check("cuda_algorithms", bool(config["deterministic_algorithms"]),
                      "no CUDA device; configuration recorded only", identity=EXACT,
                      configuration=config, demonstrated_on="cpu")

    SEEDS.seed_everything(42)
    conv = nn.Conv2d(3, 8, 3, padding=1).to(device)
    image = B.synthetic_image(1, device=device)
    outputs = []
    with torch.no_grad():
        for _ in range(3):
            outputs.append(conv(image).detach().clone())
    identical = all(torch.equal(outputs[0], other) for other in outputs[1:])
    enabled = (bool(config["deterministic_algorithms"])
               and bool(config["cudnn_deterministic"])
               and not bool(config["cudnn_benchmark"])
               and config["cublas_workspace_config"] is not None)
    return _check("cuda_algorithms", enabled and identical,
                  ("deterministic algorithms on, cudnn deterministic, benchmark off, "
                   "CUBLAS workspace fixed; three repeats bitwise identical"
                   if enabled and identical else
                   f"enabled={enabled} identical={identical}"),
                  identity=EXACT, configuration=config,
                  demonstrated_on=torch.cuda.get_device_name(0))


# --------------------------------------------------------------------------- #
# 6. Checkpoint selection
# --------------------------------------------------------------------------- #
def _select(rows: Sequence[Mapping[str, Any]]) -> Tuple[int, float]:
    """The frozen rule: minimum monitor, ties keep the earlier epoch."""
    best_loss, best_epoch = float("inf"), -1
    for row in rows:
        monitor = float(row["monitor"])
        if monitor < best_loss - 1e-12:
            best_loss, best_epoch = monitor, int(row["epoch"])
    return best_epoch, best_loss


def check_checkpoint_selection(seed: int = 42) -> Dict[str, Any]:
    """Selection is a pure function of the persisted history, at full precision."""
    gen = np.random.default_rng(seed)
    rows = [{"epoch": e + 1, "monitor": float(v)}
            for e, v in enumerate(gen.random(12) * 0.5 + 0.2)]
    # A deliberate tie for the global minimum at epochs 4 and 6.  Both are forced
    # below every other row so the assertion is about tie-breaking, not about
    # where the random minimum happened to land.
    rows[3]["monitor"] = 0.1
    rows[5]["monitor"] = 0.1
    batch_epoch, batch_loss = _select(rows)
    stream_epoch, stream_loss = -1, float("inf")
    for row in rows:                                  # streaming must agree
        if float(row["monitor"]) < stream_loss - 1e-12:
            stream_loss, stream_epoch = float(row["monitor"]), int(row["epoch"])

    # the history is persisted as CSV and re-read; the selection must survive
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["epoch", "monitor"])
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)
    reread = [{"epoch": int(r["epoch"]), "monitor": float(r["monitor"])}
              for r in csv.DictReader(buffer)]
    reread_epoch, reread_loss = _select(reread)

    tie_earlier = batch_epoch == 4                   # epochs 4 and 6 tie -> epoch 4
    passed = (batch_epoch == stream_epoch and batch_loss == stream_loss
              and batch_epoch == reread_epoch and batch_loss == reread_loss
              and tie_earlier)
    return _check("checkpoint_selection", passed,
                  ("selection is identical in batch, streaming and after a CSV "
                   f"round-trip; a tie keeps the earlier epoch ({batch_epoch})"
                   if passed else
                   f"batch={batch_epoch} stream={stream_epoch} reread={reread_epoch} "
                   f"tie_earlier={tie_earlier}"),
                  identity=EXACT, best_epoch=batch_epoch, best_loss=batch_loss,
                  tie_epochs=[4, 6])


# --------------------------------------------------------------------------- #
# 7. Dependency identities
# --------------------------------------------------------------------------- #
def dependency_identity() -> Dict[str, Any]:
    """The exact build this measurement is valid for."""
    import pandas

    identity = {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version() if torch.cuda.is_available() else None,
        "numpy": np.__version__,
        "pandas": pandas.__version__,
        "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
    }
    for name in ("psutil", "PIL", "skimage"):
        try:
            module = __import__(name)
            identity[name] = getattr(module, "__version__", "unknown")
        except ImportError:                                  # pragma: no cover
            identity[name] = None
    blob = json.dumps(identity, sort_keys=True).encode("utf-8")
    identity["fingerprint_sha256"] = hashlib.sha256(blob).hexdigest()
    return identity


def check_dependency_identities() -> Dict[str, Any]:
    """A stable fingerprint, plus the unpinned-requirements finding.

    ``requirements.txt`` carries no version specifiers.  That is a genuine
    reproducibility gap and it is reported rather than silently "fixed", because
    pinning it would change every other environment in the project.
    """
    identity = dependency_identity()
    again = dependency_identity()
    stable = identity["fingerprint_sha256"] == again["fingerprint_sha256"]
    pinned = _requirements_are_pinned()
    return _check("dependency_identities", stable,
                  ("the dependency fingerprint is stable across two reads"
                   + ("" if pinned else "; requirements.txt is UNPINNED, so the "
                                        "environment is recorded rather than guaranteed")),
                  identity=EXACT, dependency=identity,
                  requirements_pinned=pinned)


def _requirements_are_pinned() -> bool:
    path = Path(__file__).resolve().parents[3] / "requirements.txt"
    if not path.is_file():                                   # pragma: no cover
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not any(spec in line for spec in ("==", "~=", ">=", "<=")):
            return False
    return True


# --------------------------------------------------------------------------- #
# 8. Prediction export
# --------------------------------------------------------------------------- #
def _mini_records(seed: int = 42) -> List[Dict[str, Any]]:
    from src.research.evaluation import metrics as MET
    from src.research.evaluation import protocol as P

    base = np.zeros((8, 8), np.uint8)
    base[2:6, 2:6] = 1
    shifted = np.zeros((8, 8), np.uint8)
    shifted[2:6, 3:7] = 1
    return [MET.score_prediction(sample_id=f"{domain}-1", domain=domain, task_id=3,
                                 final_probability=shifted.astype(np.float32),
                                 ground_truth=base)
            for domain in P.DOMAINS]


def check_prediction_export(seed: int = 42) -> Dict[str, Any]:
    """Two exports of the same records are byte-identical; order does not matter
    to the per-image values."""
    from src.research.evaluation import metrics as MET
    from src.research.evaluation import protocol as P
    from src.research.evaluation import provenance as PROV
    from src.research.evaluation import registry as REG

    records = _mini_records(seed)
    provenance = PROV.build_evaluation_provenance(
        model_key=REG.BASELINES[0], seed=seed, split=P.SPLIT_VAL,
        adapter_identity={"model_key": REG.BASELINES[0], "seed": seed,
                          "adapter_kind": "PLAIN",
                          "checkpoint_sha256": "SYNTHETIC::export_probe"},
        evidence_class=P.SYNTHETIC_EVIDENCE, split_manifest_sha256="0" * 64,
        n_images=len(records), evaluation_configuration=PROV.evaluation_config(),
        synthetic=True, training_performed=False)

    with tempfile.TemporaryDirectory(prefix="phase_d_export_") as td:
        first = Path(td) / "a"
        second = Path(td) / "b"
        summary = MET.aggregate_records(records)
        doc_a = PROV.publish_cell(first, records=records, provenance=provenance,
                                  summary=summary)
        doc_b = PROV.publish_cell(second, records=records, provenance=provenance,
                                  summary=summary)
        bytes_equal = ((first / PROV.PER_IMAGE_NAME).read_bytes()
                       == (second / PROV.PER_IMAGE_NAME).read_bytes())
        hash_equal = doc_a["per_image_sha256"] == doc_b["per_image_sha256"]
        seal_equal = doc_a[PROV.SEAL_FIELD] == doc_b[PROV.SEAL_FIELD]

    shuffled = list(reversed(records))
    summary_shuffled = MET.aggregate_records(shuffled)
    # compare by sample_id: pairing a record with a *different* image would test
    # nothing, and reversing the list is the point
    by_id = {r["sample_id"]: r for r in records}
    per_image_same = all(
        float(by_id[r["sample_id"]]["dice"]) == float(r["dice"]) for r in shuffled)
    aggregate_same = (summary_shuffled["equal_domain_macro_dice"]
                      == summary["equal_domain_macro_dice"])

    passed = bytes_equal and hash_equal and seal_equal and per_image_same and aggregate_same
    return _check("prediction_export", passed,
                  ("the same records export byte-identically (same per-image hash and "
                   "seal); per-image values and the aggregate are order-independent"
                   if passed else
                   f"bytes={bytes_equal} hash={hash_equal} seal={seal_equal} "
                   f"per_image={per_image_same} aggregate={aggregate_same}"),
                  identity=EXACT, per_image_sha256=doc_a["per_image_sha256"],
                  document_seal=doc_a[PROV.SEAL_FIELD])


# --------------------------------------------------------------------------- #
# 9. Per-image results
# --------------------------------------------------------------------------- #
def check_per_image_results(seed: int = 42) -> Dict[str, Any]:
    """Re-scoring the same mask pair yields identical per-image metrics."""
    from src.research.evaluation import metrics as MET

    base = np.zeros((16, 16), np.uint8)
    base[4:12, 4:12] = 1
    candidate = base.copy()
    candidate[4:12, 10:12] = 0
    first = MET.score_prediction(sample_id="s1", domain="KUB", task_id=3,
                                 final_probability=candidate.astype(np.float32),
                                 ground_truth=base)
    second = MET.score_prediction(sample_id="s1", domain="KUB", task_id=3,
                                  final_probability=candidate.astype(np.float32),
                                  ground_truth=base)
    identical = all(first[key] == second[key] for key in ("dice", "iou", "hd95"))
    # a float32-versus-float64 input is a numerical change, not an identity claim
    wider = MET.score_prediction(sample_id="s1", domain="KUB", task_id=3,
                                 final_probability=candidate.astype(np.float64),
                                 ground_truth=base)
    delta = abs(float(wider["dice"]) - float(first["dice"]))
    return _check("per_image_results", identical,
                  ("per-image Dice/IoU/HD95 are identical on repetition; the float64 "
                   f"path differs by {delta:.3e} (tolerance, not identity)"),
                  identity=EXACT, dice=float(first["dice"]), iou=float(first["iou"]),
                  hd95=first["hd95"], float64_dice_delta=delta)


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def reproducibility_report(*, device: str = "cuda", seed: int = 42) -> Dict[str, Any]:
    """Every §5 check, plus the statement of what identity each one asserts."""
    checks = [
        check_seeding(seed),
        check_rng_replay(seed),
        check_empty_state_refused(),
        check_loader_order(seed),
        check_resume_equivalence(seed),
        check_cuda_algorithms(device),
        check_checkpoint_selection(seed),
        check_dependency_identities(),
        check_prediction_export(seed),
        check_per_image_results(seed),
    ]
    failed = [c["check"] for c in checks if not c["passed"]]
    return {"schema": "phase_d_determinism_v1", "evidence_class": EVIDENCE_CLASS,
            "seed": int(seed), "device": device, "checks": checks,
            "n_checks": len(checks), "n_passed": len(checks) - len(failed),
            "failed": failed, "all_passed": not failed,
            "identity_policy": {
                "exact": ("RNG replay, loader permutation for a given generator state, "
                          "resume equivalence on the same device, checkpoint selection, "
                          "export bytes, per-image metrics, repeated same-device forward"),
                "tolerance": ("CPU versus CUDA only; no cross-device bitwise equality is "
                              "claimed, and the Phase B CPU/CUDA gate states its own "
                              "tolerances rather than relaxing them"),
            },
            "note": ("The Phase B data-order generator defect is rechecked by ablation: "
                     "the fix must be both necessary and sufficient.")}


__all__ = ["EVIDENCE_CLASS", "EXACT", "TOLERANCE", "check_checkpoint_selection",
           "check_cuda_algorithms", "check_dependency_identities", "check_empty_state_refused",
           "check_loader_order", "check_per_image_results", "check_prediction_export",
           "check_resume_equivalence", "check_rng_replay", "check_seeding",
           "dependency_identity", "reproducibility_report"]
