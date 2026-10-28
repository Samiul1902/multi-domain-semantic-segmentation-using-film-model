"""Phase-20 frozen checkpoint-selection rule (macro-domain mean VAL Dice).

Why not pooled Dice
-------------------
Pooled/micro Dice is dominated by the largest domains (ISIC 2556 / KUB 1978
TRAIN; ISIC 357 / KUB 280 VAL). Selecting on pooled volume would let ISIC and
KUB decide the checkpoint. Phase 20 therefore selects on

    macro_domain_dice = mean(Dice_ISIC, Dice_BUSI, Dice_KVASIR, Dice_KUB)

where each ``Dice_<domain>`` is that domain's **per-image macro** mean (unweighted
mean of per-image Dice), matching ``phase19_evaluation_contract_v1``.

Tie-break
---------
Exact ties in ``macro_domain_dice`` are broken deterministically by LOWER
validation loss. The rule is frozen BEFORE training and is replayed from saved
history only (no inference) after training.

Frozen rule id: ``phase20_macro_domain_mean_dice_v1``
"""
from __future__ import annotations

from typing import Dict, Iterable, List

__all__ = [
    "SELECTION_RULE_ID",
    "DOMAIN_ORDER",
    "TIE_TOLERANCE",
    "macro_domain_dice",
    "is_new_best",
    "select_best_epoch",
]

SELECTION_RULE_ID = "phase20_macro_domain_mean_dice_v1"
DOMAIN_ORDER = ("ISIC", "BUSI", "KVASIR", "KUB")
TIE_TOLERANCE = 1e-12


def macro_domain_dice(per_domain: Dict[str, float]) -> float:
    """Unweighted mean of the four per-domain VAL Dice values."""
    missing = [d for d in DOMAIN_ORDER if d not in per_domain]
    if missing:
        raise ValueError(f"macro-domain Dice requires all four domains; missing {missing}")
    values = [float(per_domain[d]) for d in DOMAIN_ORDER]
    return float(sum(values) / len(values))


def is_new_best(macro: float, val_loss: float, best_macro: float, best_val_loss: float) -> bool:
    """Strictly better macro Dice, or an exact tie broken by lower validation loss."""
    if macro > best_macro + TIE_TOLERANCE:
        return True
    if abs(macro - best_macro) <= TIE_TOLERANCE and val_loss < best_val_loss - TIE_TOLERANCE:
        return True
    return False


def select_best_epoch(history: Iterable[dict]) -> dict:
    """Replay the frozen rule over saved history rows (disk only, no inference).

    Returns the selected epoch and the trace of selection decisions so the
    trainer's stored ``best_epoch`` can be independently verified.
    """
    rows: List[dict] = list(history)
    if not rows:
        raise ValueError("history is empty; cannot select a checkpoint")
    best_macro = float("-inf")
    best_loss = float("inf")
    best_epoch = None
    trace = []
    for row in rows:
        macro = macro_domain_dice({d: row[f"val_dice_{d}"] for d in DOMAIN_ORDER})
        loss = float(row["val_loss"])
        improved = is_new_best(macro, loss, best_macro, best_loss)
        if improved:
            best_macro, best_loss, best_epoch = macro, loss, int(row["epoch"])
        trace.append({"epoch": int(row["epoch"]), "macro_domain_dice": macro,
                      "val_loss": loss, "improved": improved})
    return {"selection_rule_id": SELECTION_RULE_ID, "selected_epoch": best_epoch,
            "selected_macro_domain_dice": best_macro, "selected_val_loss": best_loss,
            "n_epochs_evaluated": len(rows), "n_improvements": sum(t["improved"] for t in trace),
            "trace": trace}
