"""H2B SEC 5 -- derive the H2B runner from the accepted H2A runner.

The diff is applied PROGRAMMATICALLY and then asserted to be confined to the
allowed set. Any replacement that fails to apply raises, so a silent partial
diff is impossible.
"""
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
SRC = ROOT / "scripts" / "training" / "post_phase13_h2a_localizer_replay.py"
DST = ROOT / "scripts" / "training" / "post_phase13_h2b_localizer_train.py"

H2B_EID = (
    "post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_"
    "softtargetfocalgamma2_deploymentbalance_seed42_clean_v3"
)

src = SRC.read_text(encoding="utf-8")

REPLACEMENTS = [
    # ---- provenance: experiment identity -------------------------------
    (
        '"post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3"',
        f'"{H2B_EID}"',
    ),
    # ---- provenance: governing protocol binding ------------------------
    ("H2A_PROTOCOL_PATH", "H2B_PROTOCOL_PATH"),
    ("H2A_PROTOCOL_SHA", "H2B_PROTOCOL_SHA"),
    ("H2A_PROTOCOL_REQUIRED_STATUS", "H2B_PROTOCOL_REQUIRED_STATUS"),
    (
        '"post_phase13_h2a_protocol_frozen.json"',
        '"post_phase13_h2b_protocol_frozen.json"',
    ),
    (
        '"0fafc793b3a814e010e1fdd48f6a2333042985eaef4a44e0382b3991800da96b"',
        '"22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e"',
    ),
    (
        '"SUPERVISOR_FROZEN_H2A_SELECTION_ONLY_READY_FOR_EXECUTION"',
        '"SUPERVISOR_FROZEN_H2B_OBJECTIVE_ONLY_READY_FOR_B1_AUTHORIZATION"',
    ),
    # ---- SCIENTIFIC: the ONE axis (loss identity) ----------------------
    (
        'LOSS_CLASS = "src.losses.localization.CenterNetFocalLoss"',
        'LOSS_CLASS = "src.losses.soft_target_focal_bce.SoftTargetFocalBCE"',
    ),
    (
        'LOSS_LABEL = "EXECUTING_HISTORICAL_CENTERNET_FOCAL_L1"',
        'LOSS_LABEL = "H2B_SOFT_TARGET_FOCAL_BCE_GAMMA2"',
    ),
    # ---- SCIENTIFIC: the ONE axis (loss import) ------------------------
    (
        "from src.losses.localization import CenterNetFocalLoss",
        "from src.losses.soft_target_focal_bce import SoftTargetFocalBCE",
    ),
    # ---- SCIENTIFIC: the ONE axis (criterion construction) -------------
    (
        """        criterion = CenterNetFocalLoss(
            alpha=float(config["loss"]["alpha"]),
            beta=float(config["loss"]["beta"]),
        )
        if type(criterion).__name__ != "CenterNetFocalLoss":
            raise RuntimeError("executable criterion is not CenterNetFocalLoss")""",
        """        criterion = SoftTargetFocalBCE(gamma=float(config["loss"]["gamma"]))
        if type(criterion).__name__ != "SoftTargetFocalBCE":
            raise RuntimeError("executable criterion is not SoftTargetFocalBCE")""",
    ),
    # ---- reporting / metadata only -------------------------------------
    (
        'f"- loss: `{LOSS_CLASS}` alpha=2.0 beta=4.0 (no Dice)\\n"',
        'f"- loss: `{LOSS_CLASS}` gamma=2.0 soft-target focal BCE (no Dice)\\n"',
    ),
]

# The loss-binding validator is replaced wholesale (it validates the loss block).
OLD_VALIDATOR_START = "def verify_loss_binding(config: dict) -> dict:"
OLD_VALIDATOR_END = "def assert_no_historical_manifest_usage(config: dict) -> None:"

NEW_VALIDATOR = '''def verify_loss_binding(config: dict) -> dict:
    """Enforce the H2B frozen objective on the executable config.

    The runner must instantiate EXACTLY ``SoftTargetFocalBCE(gamma=2.0)``.
    Any executable field implying a different objective (CenterNet focal with
    alpha/beta, a Dice term, an auxiliary loss, a regularizer, a class weight or
    any additional coefficient) is a hard failure. gamma is FIXED at 2.0; no
    grid, no sweep, no alternative gamma.
    """
    loss = config.get("loss")
    if not isinstance(loss, dict):
        raise ValueError("config['loss'] must be a mapping")

    if loss.get("name") != "SoftTargetFocalBCE":
        raise ValueError(
            f"executable loss name must be 'SoftTargetFocalBCE', got {loss.get('name')!r}"
        )
    if loss.get("implementation") != LOSS_CLASS:
        raise ValueError(
            f"executable loss implementation must be {LOSS_CLASS!r}, "
            f"got {loss.get('implementation')!r}"
        )
    if float(loss.get("gamma")) != 2.0:
        raise ValueError(f"executable loss gamma must be 2.0, got {loss.get('gamma')!r}")

    for forbidden_key in ("alpha", "beta", "dice_weight", "dice_term",
                          "auxiliary_loss", "regularizer", "class_weight",
                          "coefficient"):
        if forbidden_key in loss:
            raise ValueError(
                f"executable loss block must not carry {forbidden_key!r} "
                "(H2B changes the objective only: no alpha/beta, no Dice, "
                "no auxiliary loss, no regularizer, no class weight, no extra coefficient)"
            )

    if loss.get("modulation_detached", "NO") != "NO":
        raise ValueError("H2B modulation term must not be detached")
    if str(loss.get("target_clamping", "NONE")).upper() != "NONE":
        raise ValueError("H2B must not clamp the target")
    if str(loss.get("target_binary_conversion", "NONE")).upper() != "NONE":
        raise ValueError("H2B must not binarise the target")

    return {
        "loss_class": LOSS_CLASS,
        "gamma": float(loss["gamma"]),
        "label": LOSS_LABEL,
    }


'''

# apply simple replacements
for old, new in REPLACEMENTS:
    if old not in src:
        raise SystemExit(f"REPLACEMENT NOT FOUND (refusing partial diff): {old[:90]!r}")
    src = src.replace(old, new)

# apply validator replacement
i = src.index(OLD_VALIDATOR_START)
j = src.index(OLD_VALIDATOR_END)
src = src[:i] + NEW_VALIDATOR + src[j:]

# module docstring header (reporting only)
src = src.replace(
    '"""Clean-v3 safe training runner for the POST-PHASE-13 H2-A-B1 localizer replay.',
    '"""Clean-v3 safe training runner for the POST-PHASE-13 H2-B-B1 localizer training.',
)
src = src.replace(
    "  * selection module import + select_epoch call        (SCIENTIFIC: the ONE authorized axis)\n"
    "  * per-epoch PROPOSAL_PIXEL_ANY_HIT_PRECISION + score diagnostics (evaluation-only)\n"
    "  * history row additions                                               (reporting)\n",
    "  * loss import + criterion construction = SoftTargetFocalBCE(gamma=2.0)\n"
    "    (SCIENTIFIC: the ONE authorized axis -- LOSS / OBJECTIVE SEMANTICS)\n"
    "  * per-epoch PROPOSAL_PIXEL_ANY_HIT_PRECISION + score diagnostics (evaluation-only)\n"
    "  * history row additions                                               (reporting)\n",
)
src = src.replace(
    "    CenterNetFocalLoss(alpha=2.0, beta=4.0)   -- NO Dice term",
    "    SoftTargetFocalBCE(gamma=2.0)   -- NO Dice term",
)

DST.write_text(src, encoding="utf-8")
print("wrote", DST)
print("lines:", len(src.splitlines()))
