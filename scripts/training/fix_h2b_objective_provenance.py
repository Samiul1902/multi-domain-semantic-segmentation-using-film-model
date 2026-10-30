"""H2B-B1 R0 -- execution-provenance repair.

Removes stale Phase-13 CenterNet objective identity from the H2B resume contract,
checkpoint metadata and start/completion audits; binds the H2B objective identity
instead. NO scientific parameter is changed.
"""
import hashlib
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
RUN = ROOT / "scripts" / "training" / "post_phase13_h2b_localizer_train.py"
CFG = (ROOT / "configs" / "phase13_clean_v3"
       / "post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_"
         "deploymentbalance_seed42_clean_v3.yaml")

H2B_PROTO_SHA = "22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e"
H2B_LOSS_SHA = "40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75"

s = RUN.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    if s.count(old) != count:
        raise SystemExit(f"FIX ABORTED -- expected {count} occurrence(s), found {s.count(old)}:\n{old[:120]!r}")
    s = s.replace(old, new)


# ---------------------------------------------------------------- constants
sub(
    'LOSS_LABEL = "H2B_SOFT_TARGET_FOCAL_BCE_GAMMA2"',
    'LOSS_LABEL = "H2B_SOFT_TARGET_FOCAL_BCE_GAMMA2"\n'
    'LOSS_MODULE_PATH = ROOT / "src" / "losses" / "soft_target_focal_bce.py"\n'
    'LOSS_MODULE_SHA = "40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75"\n'
    'OBJECTIVE_CHANGE_ID = "H2B_OBJECTIVE_ONLY_SOFT_TARGET_FOCAL_BCE_GAMMA2"\n'
    'H2B_PROTOCOL_IDENTITY = (\n'
    '    "H2B_OBJECTIVE_ONLY__H2A_DEPLOYMENT_BALANCED_SELECTION_CARRY_FORWARD"\n'
    ')',
)

# ------------------------------------------------------- stale docstring text
sub(
    "Loss objective (supervisor decision L1, amendment R2A_LOSS_BINDING)",
    "Loss objective (H2B frozen objective: CHANGE_H2B_001 -- objective only)",
)
sub(
    "There is no ``0.75/0.25`` weighting, no ``alpha 0.25`` and no ``gamma 2.0`` on\n"
    "the executable path. See\n"
    "``reports/audits/phase13_clean_v3_localizer_loss_binding_r2a.json``.",
    "The executable objective is ``SoftTargetFocalBCE(gamma=2.0)``. There is no alpha, no\n"
    "beta, no Dice term, no auxiliary objective and no gamma sweep on the executable path.\n"
    "The Phase-13 R2A CenterNet binding is retained as PARENT PROVENANCE ONLY (see\n"
    "``parent_provenance`` in the audits); it is NOT the active H2B objective.",
)
sub(
    "# Frozen loss objective (R2A_LOSS_BINDING).",
    "# Frozen H2B loss objective (CHANGE_H2B_001: objective only).",
)

# ------------------------------------------------------ resume extended identity
sub(
    '''        "loss_label": LOSS_LABEL,
        "loss_class": LOSS_CLASS,
        "loss_alpha": 2.0,
        "loss_beta": 4.0,
        "heatmap_resolution": HEATMAP_RESOLUTION,
    }''',
    '''        "loss_label": LOSS_LABEL,
        "loss_class": LOSS_CLASS,
        "loss_gamma": 2.0,
        "loss_modulation_detached": "NO",
        "loss_target_clamping": "NONE",
        "loss_target_binary_conversion": "NONE",
        "loss_dice_weight": "NONE",
        "objective_change_id": OBJECTIVE_CHANGE_ID,
        "h2b_protocol_sha": H2B_PROTOCOL_SHA,
        "h2b_loss_module_sha": LOSS_MODULE_SHA,
        "heatmap_resolution": HEATMAP_RESOLUTION,
    }''',
)

# --------------------------------------------------- checkpoint metadata write
sub(
    '''                "loss_class": LOSS_CLASS,
                "loss_label": LOSS_LABEL,
                "loss_alpha": 2.0,
                "loss_beta": 4.0,
                "loss_dice_weight": 0.0,
            }''',
    '''                "loss_class": LOSS_CLASS,
                "loss_label": LOSS_LABEL,
                "loss_gamma": 2.0,
                "loss_modulation_detached": "NO",
                "loss_target_clamping": "NONE",
                "loss_target_binary_conversion": "NONE",
                "loss_dice_weight": "NONE",
                "dice_term": "NONE",
                "auxiliary_loss": "NONE",
                "objective_change_id": OBJECTIVE_CHANGE_ID,
                "h2b_protocol_sha": H2B_PROTOCOL_SHA,
                "h2b_loss_module_sha": LOSS_MODULE_SHA,
                "selection_rule_source": "H2A_DEPLOYMENT_BALANCED_6TERM_CARRY_FORWARD",
                "parent_provenance": {
                    "historical_phase13_parent_provenance": {
                        "r2_protocol_sha": R2_PROTOCOL_SHA,
                        "r2a_loss_binding_sha": r2a_sha,
                        "note": ("Phase-13 parent lineage. NOT the active H2B objective. "
                                 "The Phase-13 parent objective was "
                                 "CenterNetFocalLoss(alpha=2.0, beta=4.0)."),
                    },
                },
            }''',
)

# ------------------------------------------------------------- start audit
sub('"artifact": "PHASE13_CLEAN_V3_LOCALIZER_TRAINING_START"',
    '"artifact": "POST_PHASE13_H2B_B1_TRAINING_START"')
sub('"protocol_identity": "R2 + R2A_LOSS_BINDING",\n'
    '                "r2_protocol_sha": R2_PROTOCOL_SHA,\n'
    '                "r2a_loss_sha": r2a_sha,',
    '"protocol_identity": H2B_PROTOCOL_IDENTITY,\n'
    '                "h2b_protocol_sha": H2B_PROTOCOL_SHA,\n'
    '                "h2b_loss_module_path": str(LOSS_MODULE_PATH.relative_to(ROOT)).replace("\\\\", "/"),\n'
    '                "h2b_loss_module_sha": LOSS_MODULE_SHA,\n'
    '                "objective_change_id": OBJECTIVE_CHANGE_ID,\n'
    '                "parent_provenance": {\n'
    '                    "r2_protocol_sha": R2_PROTOCOL_SHA,\n'
    '                    "r2a_loss_binding_sha": r2a_sha,\n'
    '                    "role": "PARENT_PROVENANCE_ONLY__NOT_ACTIVE_H2B_OBJECTIVE",\n'
    '                },')
sub('"scientific_parameter_changes": 0,\n'
    '                "test_reads": 0,\n'
    '                "scientific_changes": 0,',
    '"scientific_parameter_changes": 1,\n'
    '                "test_reads": 0,\n'
    '                "scientific_changes": 1,\n'
    '                "scientific_change_register": {\n'
    '                    "CHANGE_H2B_001": "loss/objective semantics only",\n'
    '                },')
sub('f"# PHASE-13 CLEAN-v3 LOCALIZER TRAINING START\\n\\n"',
    'f"# POST-PHASE-13 H2B-B1 LOCALIZER TRAINING START\\n\\n"')
sub('f"- protocol: R2 + R2A_LOSS_BINDING\\n"',
    'f"- protocol: {H2B_PROTOCOL_IDENTITY}\\n"')

# -------------------------------------------------------- completion audit
sub('"artifact": "PHASE13_CLEAN_V3_LOCALIZER_TRAINING_COMPLETION"',
    '"artifact": "POST_PHASE13_H2B_B1_TRAINING_COMPLETION"')
sub('"protocol_identity": "R2 + R2A_LOSS_BINDING",\n'
    '            "best_epoch": best_epoch,',
    '"protocol_identity": H2B_PROTOCOL_IDENTITY,\n'
    '            "h2b_protocol_sha": H2B_PROTOCOL_SHA,\n'
    '            "h2b_loss_module_sha": LOSS_MODULE_SHA,\n'
    '            "objective_change_id": OBJECTIVE_CHANGE_ID,\n'
    '            "parent_provenance": {\n'
    '                "r2_protocol_sha": R2_PROTOCOL_SHA,\n'
    '                "r2a_loss_binding_sha": r2a_sha,\n'
    '                "role": "PARENT_PROVENANCE_ONLY__NOT_ACTIVE_H2B_OBJECTIVE",\n'
    '            },\n'
    '            "best_epoch": best_epoch,')
sub('"grid_configurations_evaluated": 0,\n'
    '            "test_reads": 0,\n'
    '            "scientific_changes": 0,',
    '"grid_configurations_evaluated": 0,\n'
    '            "test_reads": 0,\n'
    '            "scientific_changes": 1,\n'
    '            "scientific_parameter_changes": 1,\n'
    '            "scientific_change_register": {\n'
    '                "CHANGE_H2B_001": "loss/objective semantics only",\n'
    '            },')
sub('f"# PHASE-13 CLEAN-v3 LOCALIZER TRAINING COMPLETION\\n\\n"',
    'f"# POST-PHASE-13 H2B-B1 LOCALIZER TRAINING COMPLETION\\n\\n"')

RUN.write_text(s, encoding="utf-8", newline="\n")
print("runner patched")

# ------------------------------------------------- config zero_denominator wording
c = CFG.read_text(encoding="utf-8")
old = '  zero_denominator_rule: "STOP / CHECK_REQUIRED BEFORE TRAINING"'
new = ('  zero_denominator_rule: >-\n'
       '    proposal_total_count == 0 -> PROPOSAL_PIXEL_ANY_HIT_PRECISION = 0.0,\n'
       '    deployment_balance_hmean = 0.0, and selection falls through to the later tuple\n'
       '    terms. This is the inherited frozen H2A/H2B selection semantics; it is NOT a\n'
       '    stopping condition and MUST NOT fail epochs in the early zero-proposal regime.')
if old not in c:
    raise SystemExit("config zero_denominator_rule not found")
c = c.replace(old, new)
CFG.write_text(c, encoding="utf-8", newline="\n")
print("config zero_denominator_rule corrected")

print("runner sha:", hashlib.sha256(RUN.read_bytes()).hexdigest())
print("config sha:", hashlib.sha256(CFG.read_bytes()).hexdigest())
