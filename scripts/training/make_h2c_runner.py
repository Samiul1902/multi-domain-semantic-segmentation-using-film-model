"""Derive the H2C-B1 runner from the H2A runner with a confined, asserted diff.

The ONLY scientifically material executable change is the localizer head
(architecture + its frozen initialization). H2C branches from H2A, so the H2A
CenterNetFocalLoss objective is RETAINED (the H2B soft-target objective is NOT used).
"""
import math
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
SRC = ROOT / "scripts" / "training" / "post_phase13_h2a_localizer_replay.py"
DST = ROOT / "scripts" / "training" / "post_phase13_h2c_localizer_train.py"

EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
       "centernetfocal_deploymentbalance_seed42_clean_v3")
H2C_PROTO_SHA = "91166259c10a84e9526eda43e83b227cc760a37b8834a4d4a65fe3e5a90ba4b6"
H2C_PROTO_STATUS = "SUPERVISOR_FROZEN_H2C_HEAD_REDESIGN_READY_FOR_B1_AUTHORIZATION"
H2C_PROTOCOL_IDENTITY = "H2C_HEAD_REDESIGN__H2A_FOCAL_OBJECTIVE_AND_SELECTION_CARRY_FORWARD"

s = SRC.read_text(encoding="utf-8")


def sub(old, new, count=None):
    global s
    n = s.count(old)
    if n == 0:
        raise SystemExit(f"ABORT: not found:\n{old[:140]!r}")
    if count is not None and n != count:
        raise SystemExit(f"ABORT: expected {count} occurrence(s), found {n} for:\n{old[:140]!r}")
    s = s.replace(old, new)


# ---------------------------------------------------------------- identity
sub('"""Clean-v3 safe training runner for the POST-PHASE-13 H2-A-B1 localizer replay.',
    '"""Clean-v3 safe training runner for the POST-PHASE-13 H2-C-B1 localizer head redesign.')
sub('"post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3"',
    f'"{EID}"')

# ---------------------------------------------------------------- protocol binding
sub("H2A_PROTOCOL_PATH", "H2C_PROTOCOL_PATH")
sub("H2A_PROTOCOL_SHA", "H2C_PROTOCOL_SHA")
sub("H2A_PROTOCOL_REQUIRED_STATUS", "H2C_PROTOCOL_REQUIRED_STATUS")
sub('"post_phase13_h2a_protocol_frozen.json"', '"post_phase13_h2c_protocol_frozen.json"')
sub('"0fafc793b3a814e010e1fdd48f6a2333042985eaef4a44e0382b3991800da96b"',
    f'"{H2C_PROTO_SHA}"')
sub('"SUPERVISOR_FROZEN_H2A_SELECTION_ONLY_READY_FOR_EXECUTION"', f'"{H2C_PROTO_STATUS}"')
sub('LOSS_CLASS = "src.losses.localization.CenterNetFocalLoss"',
    'LOSS_CLASS = "src.losses.localization.CenterNetFocalLoss"  # H2C retains the H2A focal objective')
sub('LOSS_LABEL = "EXECUTING_HISTORICAL_CENTERNET_FOCAL_L1"',
    'LOSS_LABEL = "H2A_CENTERNET_FOCAL_L1_RETAINED_FOR_H2C"')

# ---------------------------------------------------------------- audit basenames
sub('TRAINING_START_BASENAME = "phase13_clean_v3_localizer_training_start"',
    'TRAINING_START_BASENAME = "post_phase13_h2c_b1_training_start"')
sub('TRAINING_COMPLETION_BASENAME = "phase13_clean_v3_localizer_training_completion"',
    'TRAINING_COMPLETION_BASENAME = "post_phase13_h2c_b1_training_completion"')

# ---------------------------------------------------------------- THE head axis
sub("from src.models.factory import create_model",
    "from src.models.factory import create_model")

HEAD_BLOCK = '''

# ===========================================================================
# H2C FROZEN HEAD -- CHANGE_H2C_001 (the ONLY scientifically material change)
# ===========================================================================
H2C_HEAD_NAME = "SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1"
H2C_HEAD_HIDDEN_WIDTH = 16
H2C_TERMINAL_INIT_BIAS = math.log(0.1 / 0.9)   # logit(0.1) = -2.1972245773362196


class FrozenH2CSpatialHead(nn.Module):
    """Frozen H2C prediction head: Conv3x3(16->16) + ReLU + Conv1x1(16->1).

    Initialization is part of the same frozen head-redesign axis:
      conv3x3.weight : kaiming_normal_(nonlinearity='relu')
      conv3x3.bias   : 0
      conv1x1.weight : ALL ZERO
      conv1x1.bias   : logit(0.1)
    No normalization, dropout, attention, residual, multi-scale or deep supervision.
    """

    def __init__(self, in_ch: int = 16, out_ch: int = 1):
        super().__init__()
        self.conv3x3 = nn.Conv2d(in_ch, in_ch, 3, stride=1, padding=1, bias=True)
        self.relu = nn.ReLU(inplace=False)
        self.conv1x1 = nn.Conv2d(in_ch, out_ch, 1, stride=1, padding=0, bias=True)
        nn.init.kaiming_normal_(self.conv3x3.weight, nonlinearity="relu")
        nn.init.zeros_(self.conv3x3.bias)
        nn.init.constant_(self.conv1x1.weight, 0.0)
        nn.init.constant_(self.conv1x1.bias, H2C_TERMINAL_INIT_BIAS)

    def forward(self, x):
        return self.conv1x1(self.relu(self.conv3x3(x)))


def build_frozen_h2c_head(in_ch: int = 16, out_ch: int = 1) -> nn.Module:
    return FrozenH2CSpatialHead(in_ch, out_ch)

'''
sub("from __future__ import annotations\n\nimport argparse",
    "from __future__ import annotations\n\nimport argparse")

# insert the head block (with its own `from torch import nn`) before ROOT
_anchor = "ROOT = Path(__file__).resolve().parents[2]"
sub(_anchor, "import math\nfrom torch import nn\n\n" + HEAD_BLOCK.strip("\n") + "\n\n" + _anchor)

# swap the head immediately after model construction
sub("""        if getattr(model, "heatmap_resolution", None) != HEATMAP_RESOLUTION:
            raise RuntimeError("model did not accept heatmap_resolution=128 explicitly")""",
    """        if getattr(model, "heatmap_resolution", None) != HEATMAP_RESOLUTION:
            raise RuntimeError("model did not accept heatmap_resolution=128 explicitly")

        # ---------- H2C FROZEN HEAD SWAP (CHANGE_H2C_001) ----------
        # The backbone is constructed exactly as in H2A and is left UNCHANGED; only the
        # prediction head is replaced by the prospectively frozen H2C head.
        if type(model.head).__name__ != "Conv2d":
            raise RuntimeError(f"unexpected H2A head type {type(model.head).__name__!r}")
        _h2a_head_params = sum(p.numel() for p in model.head.parameters())
        model.head = build_frozen_h2c_head(16, 1).to(device)
        if type(model.head).__name__ != "FrozenH2CSpatialHead":
            raise RuntimeError("H2C head swap failed")
        _h2c_head_params = sum(p.numel() for p in model.head.parameters())
        if (_h2a_head_params, _h2c_head_params) != (17, 2337):
            raise RuntimeError(
                f"head parameter contract violated: {_h2a_head_params} -> {_h2c_head_params}")""")

# ------------------------------------------------- audit payload identity (H2C)
sub('"artifact": "PHASE13_CLEAN_V3_LOCALIZER_TRAINING_START"',
    '"artifact": "POST_PHASE13_H2C_B1_TRAINING_START"')
sub('"artifact": "PHASE13_CLEAN_V3_LOCALIZER_TRAINING_COMPLETION"',
    '"artifact": "POST_PHASE13_H2C_B1_TRAINING_COMPLETION"')
sub('"protocol_identity": "R2 + R2A_LOSS_BINDING",\n'
    '                "r2_protocol_sha": R2_PROTOCOL_SHA,\n'
    '                "r2a_loss_sha": r2a_sha,',
    '"protocol_identity": H2C_PROTOCOL_IDENTITY,\n'
    '                "h2c_protocol_sha": H2C_PROTOCOL_SHA,\n'
    '                "h2c_head_name": H2C_HEAD_NAME,\n'
    '                "objective_change_id": "CHANGE_H2C_001",\n'
    '                "parent_provenance": {\n'
    '                    "r2_protocol_sha": R2_PROTOCOL_SHA,\n'
    '                    "r2a_loss_binding_sha": r2a_sha,\n'
    '                    "role": "PARENT_PROVENANCE_ONLY__H2C_RETAINS_H2A_FOCAL_OBJECTIVE",\n'
    '                },')
sub('"scientific_parameter_changes": 0,\n'
    '                "test_reads": 0,\n'
    '                "scientific_changes": 0,',
    '"scientific_parameter_changes": 1,\n'
    '                "test_reads": 0,\n'
    '                "scientific_changes": 1,\n'
    '                "scientific_change_register": {"CHANGE_H2C_001": "localizer prediction-head architecture (incl. its frozen initialization)"},')
sub('f"# PHASE-13 CLEAN-v3 LOCALIZER TRAINING START\\n\\n"',
    'f"# POST-PHASE-13 H2C-B1 LOCALIZER TRAINING START\\n\\n"')
sub('f"- protocol: R2 + R2A_LOSS_BINDING\\n"',
    'f"- protocol: {H2C_PROTOCOL_IDENTITY}\\n"')
sub('"protocol_identity": "R2 + R2A_LOSS_BINDING",\n'
    '            "best_epoch": best_epoch,',
    '"protocol_identity": H2C_PROTOCOL_IDENTITY,\n'
    '            "h2c_protocol_sha": H2C_PROTOCOL_SHA,\n'
    '            "h2c_head_name": H2C_HEAD_NAME,\n'
    '            "objective_change_id": "CHANGE_H2C_001",\n'
    '            "parent_provenance": {\n'
    '                "r2_protocol_sha": R2_PROTOCOL_SHA,\n'
    '                "r2a_loss_binding_sha": r2a_sha,\n'
    '                "role": "PARENT_PROVENANCE_ONLY__H2C_RETAINS_H2A_FOCAL_OBJECTIVE",\n'
    '            },\n'
    '            "best_epoch": best_epoch,')
sub('"grid_configurations_evaluated": 0,\n'
    '            "test_reads": 0,\n'
    '            "scientific_changes": 0,',
    '"grid_configurations_evaluated": 0,\n'
    '            "test_reads": 0,\n'
    '            "scientific_changes": 1,\n'
    '            "scientific_parameter_changes": 1,\n'
    '            "scientific_change_register": {"CHANGE_H2C_001": "localizer prediction-head architecture (incl. its frozen initialization)"},')
sub('f"# PHASE-13 CLEAN-v3 LOCALIZER TRAINING COMPLETION\\n\\n"',
    'f"# POST-PHASE-13 H2C-B1 LOCALIZER TRAINING COMPLETION\\n\\n"')

DST.write_text(s, encoding="utf-8", newline="\n")
print("wrote", DST)
print("lines:", len(s.splitlines()))
print("head params: old 17 -> new 2337 | logit(0.1) =", math.log(0.1 / 0.9))
