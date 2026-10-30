"""Derive the H2C-B2 downstream evaluation script from the H2B-B2 one (confined, asserted diff)."""
import hashlib
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
SRC = ROOT / "scripts" / "inference" / "post_phase13_h2b_downstream_eval.py"
DST = ROOT / "scripts" / "inference" / "post_phase13_h2c_downstream_eval.py"

H2C_EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
           "centernetfocal_deploymentbalance_seed42_clean_v3")

s = SRC.read_text(encoding="utf-8")


def sub(old, new, count=None):
    global s
    n = s.count(old)
    if n == 0:
        raise SystemExit(f"ABORT not found: {old[:120]!r}")
    if count is not None and n != count:
        raise SystemExit(f"ABORT count {n} != {count} for {old[:120]!r}")
    s = s.replace(old, new)


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


# ---- run identity / docstring
sub("POST-PHASE-13 H2-B-B2", "POST-PHASE-13 H2-C-B2")
sub("frozen H2B best-checkpoint localizer proposals (488 proposals)",
    "frozen H2C best-checkpoint localizer proposals (462 proposals)")
sub("Run id: post_phase13_h2b_downstream_best_native_policy",
    "Run id: post_phase13_h2c_downstream_best_native_policy")
sub('RUN_ID = "post_phase13_h2b_downstream_best_native_policy"',
    'RUN_ID = "post_phase13_h2c_downstream_best_native_policy"')

# ---- bindings: H2C protocol / B1 eval / best.pt / H2A-focal loss module
sub('''    "h2b_protocol": ("reports/audits/post_phase13_h2b_protocol_frozen.json",
                     "22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e"),
    "h2b_b1_eval": ("reports/audits/post_phase13_h2b_b1_training_evaluation.json",
                    "34a52942ea4ef9da21c4aa450a925c8c59ada771e08f99ab99c3ec669c1e2175"),
    "h2b_best_pt": ("checkpoints/post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_"
                    "softtargetfocalgamma2_deploymentbalance_seed42_clean_v3/best.pt",
                    "a9147ad7d1835a6e4ef8d66cc04c063db85b2f9a65585a4a34ae2acfef05f028"),
    "h2b_loss_module": ("src/losses/soft_target_focal_bce.py",
                        "40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75"),''',
    f'''    "h2c_protocol": ("reports/audits/post_phase13_h2c_protocol_frozen.json",
                     "{sha('reports/audits/post_phase13_h2c_protocol_frozen.json')}"),
    "h2c_b1_eval": ("reports/audits/post_phase13_h2c_b1_training_evaluation.json",
                    "{sha('reports/audits/post_phase13_h2c_b1_training_evaluation.json')}"),
    "h2c_best_pt": ("checkpoints/{H2C_EID}/best.pt",
                    "{sha(f'checkpoints/{H2C_EID}/best.pt')}"),
    "h2c_frozen_head_module": ("scripts/training/post_phase13_h2c_localizer_train.py",
                               "{sha('scripts/training/post_phase13_h2c_localizer_train.py')}"),
    "h2c_objective_module": ("src/losses/localization.py",
                             "{sha('src/losses/localization.py')}"),''')

# ---- artifact paths / identifiers
sub("post_phase13_h2b_best_checkpoint_", "post_phase13_h2c_best_checkpoint_")
sub("post_phase13_h2b_downstream_", "post_phase13_h2c_downstream_")
for a, b in (("h2b_case_cohorts", "h2c_case_cohorts"), ("h2b_case_idx", "h2c_case_idx"),
             ("h2b_metrics", "h2c_metrics"),
             ("h2b_det", "h2c_det"), ("h2b_case", "h2c_case"), ("h2b_prop", "h2c_prop"),
             ("h2b_comp", "h2c_comp"), ("h2b_predicted", "h2c_predicted"),
             ("h2b_minus_", "h2c_minus_"), ("GLOBAL_TO_H2B_", "GLOBAL_TO_H2C_"),
             ("PHASE13_TO_H2B_", "PHASE13_TO_H2C_"), ("H2B_ORACLE_", "H2C_ORACLE_"),
             ("DELTA_H2B_", "DELTA_H2C_"), ("h2b_localizer", "h2c_localizer"),
             ("h2b_geom_from_row", "h2c_geom_from_row"), ("H2A_TO_H2B_", "H2A_TO_H2C_"),
             ("h2b_coverage_fraction", "h2c_coverage_fraction"),
             ("h2b_covered90", "h2c_covered90"), ("h2b_covered50", "h2c_covered50"),
             ("h2b_any_overlap", "h2c_any_overlap")):
    sub(a, b)

# ---- counts: 488 -> 462, 1952 -> 1848
sub("== 488", "== 462"); sub("!= 488", "!= 462")
sub("expected 1952", "expected 1848"); sub("== 1952", "== 1848"); sub("!= 1952", "!= 1848")
sub('"proposal_count": 488,', '"proposal_count": 462,')
sub('"h2c_proposal_count": 488,', '"h2c_proposal_count": 462,')

# ---- residual naming
sub("H2B case rows", "H2C case rows")
sub("H2B proposal rows", "H2C proposal rows")
sub("H2B component rows", "H2C component rows")
sub("# Load H2B proposal artifacts", "# Load H2C proposal artifacts")
sub("Aggregate H2B per-case cohort flags", "Aggregate H2C per-case cohort flags")
sub("Stage R — H2B predicted-region inference (488 x 4 = 1952 crops)",
    "Stage R — H2C predicted-region inference (462 x 4 = 1848 crops)")
sub('"artifact": "POST_PHASE13_H2B_B2_DOWNSTREAM_INTEGRITY"',
    '"artifact": "POST_PHASE13_H2C_B2_DOWNSTREAM_INTEGRITY"')
sub('"h2b_protocol_sha": bind["h2b_protocol"]["sha"],',
    '"h2c_protocol_sha": bind["h2c_protocol"]["sha"],')
sub('"h2b_b1_evaluation_sha": bind["h2b_b1_eval"]["sha"],',
    '"h2c_b1_evaluation_sha": bind["h2c_b1_eval"]["sha"],')
sub('"h2b_best_pt_sha": bind["h2b_best_pt"]["sha"],',
    '"h2c_best_pt_sha": bind["h2c_best_pt"]["sha"],')
sub('"h2b_loss_module_sha": bind["h2b_loss_module"]["sha"],',
    '"h2c_frozen_head_module_sha": bind["h2c_frozen_head_module"]["sha"],\n'
    '        "h2c_objective_module_sha": bind["h2c_objective_module"]["sha"],')
sub("""          f"- H2B protocol: `{bind['h2b_protocol']['sha']}`",
          f"- H2B B1 evaluation: `{bind['h2b_b1_eval']['sha']}`",
          f"- H2B best.pt: `{bind['h2b_best_pt']['sha']}`",
          f"- H2B loss module: `{bind['h2b_loss_module']['sha']}`",""",
    """          f"- H2C protocol: `{bind['h2c_protocol']['sha']}`",
          f"- H2C B1 evaluation: `{bind['h2c_b1_eval']['sha']}`",
          f"- H2C best.pt: `{bind['h2c_best_pt']['sha']}`",
          f"- H2C frozen head module: `{bind['h2c_frozen_head_module']['sha']}`",
          f"- H2C objective module (H2A focal, retained): `{bind['h2c_objective_module']['sha']}`",""")
sub('f"**next_action: WAIT_FOR_SUPERVISOR_H2B_OUTCOME_ADJUDICATION_AUTHORIZATION**", ""]',
    'f"**next_action: WAIT_FOR_SUPERVISOR_H2C_OUTCOME_ADJUDICATION_AUTHORIZATION**", ""]')
sub('print("\\n=== H2B-B2 COMPLETE ===", flush=True)',
    'print("\\n=== H2C-B2 COMPLETE ===", flush=True)')

# ---- audit filename (source already carries _b2_)
sub("post_phase13_h2b_b2_downstream_integrity", "post_phase13_h2c_b2_downstream_integrity")

# ---- final sweep: this script has NO legitimate H2B reference (H2B was never a comparator here)
s = s.replace("h2b", "h2c").replace("H2B", "H2C")

DST.write_text(s, encoding="utf-8", newline="\n")
print("wrote", DST)
print("lines:", len(s.splitlines()))
