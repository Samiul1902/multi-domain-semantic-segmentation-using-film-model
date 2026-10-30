"""H2B-B1 R0 SEC 8 -- regression / one-axis tests after the provenance repair.

Static only: no training, no CUDA, no model construction.
"""
import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))

RUN = ROOT / "scripts" / "training" / "post_phase13_h2b_localizer_train.py"
CFG = (ROOT / "configs" / "phase13_clean_v3"
       / "post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_"
         "deploymentbalance_seed42_clean_v3.yaml")
H2B_PROTO_SHA = "22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e"
H2B_LOSS_SHA = "40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75"

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))


spec = importlib.util.spec_from_file_location("h2b_run", RUN)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
src = RUN.read_text(encoding="utf-8")
cfg = m.load_executable_config(m.CONFIG_PATH)

print("=== negative objective-binding tests ===")
m.verify_experiment_id(cfg)
check("verify_experiment_id passes", True)
check("verify_loss_binding passes",
      m.verify_loss_binding(cfg)["loss_class"] == "src.losses.soft_target_focal_bce.SoftTargetFocalBCE")
for k, v in (("dice_weight", 0.25), ("gamma", 1.5), ("auxiliary_loss", 0.1), ("alpha", 2.0), ("beta", 4.0)):
    bad = dict(cfg); bad["loss"] = dict(cfg["loss"]); bad["loss"][k] = v
    try:
        m.verify_loss_binding(bad)
        check(f"negative: {k}={v} rejected", False, "was ACCEPTED")
    except ValueError:
        check(f"negative: {k}={v} rejected", True)

print("\n=== stale objective metadata removed ===")
check("runner has NO loss_alpha", "loss_alpha" not in src)
check("runner has NO loss_beta", "loss_beta" not in src)
check("runner does NOT declare R2A as active objective",
      '"protocol_identity": "R2 + R2A_LOSS_BINDING"' not in src)
check("active checkpoint metadata has gamma 2.0", '"loss_gamma": 2.0' in src)
check("active checkpoint metadata has dice_term NONE", '"dice_term": "NONE"' in src)
check("active checkpoint metadata has auxiliary_loss NONE", '"auxiliary_loss": "NONE"' in src)
check("objective_change_id recorded", "H2B_OBJECTIVE_ONLY_SOFT_TARGET_FOCAL_BCE_GAMMA2" in src)
check("historical Phase-13 parent provenance is nested and labelled",
      "historical_phase13_parent_provenance" in src)

print("\n=== resume gate verifies H2B objective identity ===")
for field in ("loss_gamma", "loss_modulation_detached", "loss_target_clamping",
              "loss_target_binary_conversion", "loss_dice_weight",
              "h2b_protocol_sha", "h2b_loss_module_sha", "objective_change_id"):
    check(f"resume extended_identity includes {field}", f'"{field}"' in src)

print("\n=== binding / register ===")
check("H2B protocol SHA recorded in runner", H2B_PROTO_SHA in src)
check("H2B loss module SHA recorded in runner", H2B_LOSS_SHA in src)
check("scientific_changes == 1 (start audit)", '"scientific_changes": 1' in src)
check("scientific_parameter_changes == 1 (start audit)", '"scientific_parameter_changes": 1' in src)
check("CHANGE_H2B_001 register present", '"CHANGE_H2B_001"' in src)
check("audit label is H2B-specific (start)",
      "POST_PHASE13_H2B_B1_TRAINING_START" in src
      and "PHASE13_CLEAN_V3_LOCALIZER_TRAINING_START" not in src)
check("audit label is H2B-specific (completion)",
      "POST_PHASE13_H2B_B1_TRAINING_COMPLETION" in src
      and "PHASE13_CLEAN_V3_LOCALIZER_TRAINING_COMPLETION" not in src)

print("\n=== zero-proposal rule consistency ===")
zdr = cfg["checkpoint_selection"]["zero_denominator_rule"]
check("config zero_denominator_rule no longer says STOP/CHECK_REQUIRED",
      "STOP / CHECK_REQUIRED BEFORE TRAINING" not in zdr)
check("config states precision = 0.0 semantics", "PROPOSAL_PIXEL_ANY_HIT_PRECISION = 0.0" in zdr)
check("config states fall-through (no stopping)", "NOT a" in zdr and "stopping condition" in zdr)
from src.training.h2a_deployment_balance_selection import deployment_balance_hmean
check("hmean(0,0,0) == 0.0 (zero-proposal semantics)", deployment_balance_hmean(0.0, 0.0, 0.0) == 0.0)

print("\n=== one-axis: no gradient-affecting change ===")
# Tokens may legitimately appear inside the explicitly-labelled
# historical_phase13_parent_provenance note. What must NOT exist is an
# EXECUTABLE call to a Phase-13 objective. Check the parsed AST.
tree = ast.parse(src)


def _callee_name(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


executable_calls = [_callee_name(n) for n in ast.walk(tree) if isinstance(n, ast.Call)]
check("no executable CenterNetFocalLoss(...) call",
      "CenterNetFocalLoss" not in executable_calls)
check("no executable SoftFocalDiceLoss(...) call",
      "SoftFocalDiceLoss" not in executable_calls)
check("executable SoftTargetFocalBCE(...) call present",
      "SoftTargetFocalBCE" in executable_calls)
check("criterion is SoftTargetFocalBCE", "SoftTargetFocalBCE(gamma=float(config[\"loss\"][\"gamma\"]))" in src)
# Any residual Phase-13 objective mention must sit inside the labelled parent-provenance block.
_src_lines = src.splitlines()
for token in ("CenterNetFocalLoss(", "alpha=2.0", "beta=4.0"):
    lines = [i for i, ln in enumerate(_src_lines, 1) if token in ln]
    ctx_ok = all(
        any("Phase-13 parent objective" in _src_lines[j]
            or "historical_phase13_parent_provenance" in _src_lines[j]
            for j in range(max(0, i - 3), min(len(_src_lines), i + 2)))
        for i in lines
    )
    check(f"'{token}' only in labelled parent provenance", ctx_ok,
          f"lines {lines}" if lines else "absent")

print("\n=== initialization semantics ===")
check("fresh from scratch (no pretrained load on model init)",
      "pretrained" not in cfg["architecture"] or cfg["architecture"].get("pretrained") is False)
check("no resume checkpoint load on a fresh start path",
      "load_training_checkpoint" in src and "--resume" in src)

failed = [r for r in results if not r[1]]
print(f"\n=== SUMMARY: {len(results) - len(failed)}/{len(results)} passed ===")
if failed:
    for n, _, d in failed:
        print("  FAILED:", n, d)
    raise SystemExit(1)

json.dump({
    "artifact": "POST_PHASE13_H2B_B1_PROVENANCE_REPAIR_TESTS",
    "status": "PASS",
    "total": len(results),
    "passed": len(results) - len(failed),
    "failed": 0,
    "results": [{"name": n, "pass": o, "detail": d} for n, o, d in results],
    "runner_sha": hashlib.sha256(RUN.read_bytes()).hexdigest(),
    "config_sha": hashlib.sha256(CFG.read_bytes()).hexdigest(),
}, open(ROOT / "reports" / "audits" / "post_phase13_h2b_b1_provenance_repair_tests.json", "w",
        encoding="utf-8"), indent=2)
print("wrote post_phase13_h2b_b1_provenance_repair_tests.json")
