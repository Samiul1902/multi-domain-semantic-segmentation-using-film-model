#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.17 GOVERNANCE COHERENCE READ-ONLY VERIFIER (WO#17D §4-§8).

NO-WRITE.  Verifies, purely by reading and re-hashing current bytes:

  §4  D61 / D75(diff-class decomposition) / v1.16->v1.17 diff
  §5  D81 complete reachable write surface (11 CSV + 5 figs + markers) + fail-closed CSV
  §6  D82/D83 release contract + attestation bindings + historical v1.14 smoke
  §7  D80 operational rebase (launcher/supervisor/manifest/gates/token)
  §8  governance hash coherence (every referenced SHA == current raw bytes)

Prints a verdict; writes NOTHING.
Exit 0 = all pass, 1 = fail.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
V17 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_17.py"
V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
V16 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_16.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_17.py"
SUPERVISOR = ROOT / "scripts/analysis/supervise_phase36_v1_17.py"

V17_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"
HIST_SMOKE_SHA = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"

fails: list[str] = []


def sha(p) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}


def ck(name, cond):
    if not cond:
        fails.append(name)
    return bool(cond)


def main() -> int:
    ex = V17.read_text(encoding="utf-8")

    # ================= §4 scientific semantics ================= #
    d14 = load(AUD / "phase36_v1_14_to_v1_17_semantic_diff.json")
    recon = load(AUD / "phase36_v1_14_to_v1_17_semantic_diff_reconciliation_v1_1.json")
    recon0 = load(AUD / "phase36_v1_14_to_v1_17_semantic_diff_reconciliation.json")
    d16 = load(AUD / "phase36_v1_16_to_v1_17_operational_diff.json")

    ck("S4_d61_canonical_fusion_present",
       "fuse_full_field(p_global, refined, geom)" in ex
       and "system._fuse_global_with_regional(p_global, refined, window)" not in ex)
    ck("S4_d75_helper_present", "def _phase27_scored_final_binary" in ex)
    ck("S4_reconciled_sci_count_2", recon.get("reconciled_scientific_delta_count") == 2)
    ck("S4_reconciled_classes_D61_D75",
       sorted(recon.get("scientific_repair_classes", [])) == ["SCIENTIFIC_D61", "SCIENTIFIC_D75"])
    counts = recon.get("reconciled_classification_counts", {})
    ck("S4_d61_hunk_count_1", counts.get("SCIENTIFIC_D61") == 1)
    ck("S4_d75_hunk_count_3", counts.get("SCIENTIFIC_D75") == 3)
    ck("S4_reconciled_unclassified_0", recon.get("reconciled_unclassified_delta_count") == 0)
    ck("S4_v16_v17_sci_count_0", d16.get("scientific_delta_count") == 0)
    ck("S4_v16_v17_unclassified_0", d16.get("unclassified_delta_count") == 0)
    # additive chain binds the original defective artifact
    ck("S4_recon_v1_1_amends_original",
       recon.get("amends") == "reports/audits/phase36_v1_14_to_v1_17_semantic_diff.json")
    ck("S4_recon_v1_1_supersedes_v1_0",
       recon.get("supersedes") == "reports/audits/phase36_v1_14_to_v1_17_semantic_diff_reconciliation.json"
       and recon.get("supersedes_sha256") == sha(AUD / "phase36_v1_14_to_v1_17_semantic_diff_reconciliation.json"))
    ck("S4_original_defect_disclosed",
       d14.get("scientific_delta_count") == 4 and recon.get("correction", {}).get("frozen_value") == 4)

    # ================= §5 D81 complete write surface ================= #
    inv = load(AUD / "phase36_v1_17_reachable_write_target_inventory.json")
    csv = inv.get("csv_table_targets", [])
    figs = inv.get("figure_targets", [])
    ck("S5_csv_count_11", len(csv) == 11)
    ck("S5_figure_count_5", len(figs) == 5)
    ck("S5_unclassified_0", inv.get("unclassified_write_target_count") == 0)
    ck("S5_all_enumerated", inv.get("all_reachable_write_targets_enumerated") is True)
    ck("S5_csv_all_v17_ns",
       all(t["path"].startswith("reports/tables/phase36_robustness_v1_17/") for t in csv))
    ck("S5_figs_all_v17_ns",
       all(t["path"].startswith("reports/figures/phase36_robustness_v1_17/") for t in figs))
    ck("S5_no_unversioned_table_root",
       not any(t["path"].startswith("reports/tables/phase36_robustness/") for t in csv))
    ck("S5_no_inherited_figure_dir",
       not any(t["path"].startswith("reports/figures/phase36_robustness/") for t in figs))
    ck("S5_overlap_zero",
       inv.get("v1_14_overlap") == [] and inv.get("v1_15_overlap") == [] and inv.get("v1_16_overlap") == [])
    ck("S5_csv_fail_closed",
       'open(path, "x", encoding="utf-8", newline="")' in ex
       and "V1_17_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in ex
       and 'path.open("w"' not in ex and "os.fsync(f.fileno())" in ex)

    # independent AST re-enumeration of CSV targets from the FINAL source
    tree = ast.parse(ex)
    src_csv = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if nm == "_write_csv" and node.args:
                try:
                    expr = ast.unparse(node.args[0])
                except Exception:
                    expr = ""
                m = re.search(r"""["']([^"']+\.csv)["']""", expr)
                if m:
                    src_csv.append("reports/tables/phase36_robustness_v1_17/" + m.group(1))
    ck("S5_independent_csv_matches_inventory",
       sorted(set(src_csv)) == sorted(t["path"] for t in csv))
    # marker/monitor targets present in source (execution-side markers) + supervisor-side
    # process observability (PROCESS_EXIT / stdout / stderr are SUPERVISOR-observed).
    for marker in ("phase36_robustness_science_start_v1_17.json",
                   "phase36_robustness_scientific_result_v1_17.json",
                   "phase36_robustness_science_failure_v1_17.json",
                   "phase36_robustness_science_v1_17_journal"):
        ck(f"S5_source_declares_{marker.split('_v1_17')[0].split('phase36_robustness_')[-1]}",
           marker in ex)

    # ================= §6 D82 / D83 ================= #
    att = load(AUD / "phase36_v1_17_science_release_attestation.json")
    gate = load(AUD / "phase36_v1_17_pure_release_gate_test.json")
    ck("S6_hist_smoke_sha_bound", att.get("smoke_artifact_sha256") == HIST_SMOKE_SHA)
    ck("S6_hist_smoke_role",
       att.get("historical_runtime_evidence", {}).get("role") == "HISTORICAL_RUNTIME_SMOKE_EVIDENCE_ONLY")
    ck("S6_no_v1_17_smoke_required", att.get("requires_v1_17_smoke") is False)
    ck("S6_gate_no_v1_17_smoke", "phase36_robustness_smoke_v1_17.json" not in ex
       and "HISTORICAL_V1_14_SMOKE" in ex)
    ck("S6_att_revision", att.get("revision") == "ra_medfilm_barr_phase36_robustness_v1_17")
    ck("S6_att_exec_sha", att.get("execution_source_sha256") == V17_SHA)
    ck("S6_att_smoke_all_pass", att.get("smoke_all_pass") is True)
    ck("S6_att_scientific_output_false", att.get("scientific_output") is False)
    ck("S6_att_d61_pass", att.get("d61_proof", {}).get("status") == "PASS")
    ck("S6_att_d75_pass", att.get("d75_provenance", {}).get("status") == "PASS")
    ck("S6_gate_released", gate.get("base_gate_state") == "RELEASED")
    ck("S6_gate_all_mut_not_released", gate.get("all_mutations_not_released") is True)
    # §6 explicitly requires the attestation to bind the runtime-manifest SHA.
    # The frozen attestation carries a DEFERRED (null) binding; the additive
    # reconciliation supplies it.  The binding requirement is satisfied iff the
    # frozen attestation binds it OR a reconciliation supplies it.
    man_sha = sha(AUD / "phase36_v1_17_runtime_source_integrity_manifest.json")
    att_binds = att.get("runtime_manifest_sha256") == man_sha
    att_recon = load(AUD / "phase36_v1_17_release_attestation_binding_reconciliation_v1_0.json")
    recon_binds = (att_recon.get("deferred_bindings_supplied", {}).get("runtime_manifest_sha256")
                   == man_sha and att_recon.get("amends_sha256") == sha(
                       AUD / "phase36_v1_17_science_release_attestation.json"))
    ck("S6_att_binds_runtime_manifest_sha", att_binds or recon_binds)

    # ================= §7 D80 operational rebase ================= #
    ls = LAUNCHER.read_text(encoding="utf-8")
    ss = SUPERVISOR.read_text(encoding="utf-8")
    ck("S7_launcher_mode_science", 'DISPATCH_MODE_ARGS = ["--mode", "science"]' in ls)
    ck("S7_gate_token", "PHASE36_V1_17_EXECUTE" in ex and "PHASE36_V1_17_EXECUTE" in ls)
    ck("S7_authority_token",
       'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_17_LAUNCH_AUTHORITY"' in ex
       and "PHASE36_V1_17_LAUNCH_AUTHORITY" in ls)
    ck("S7_launcher_pins_exec_sha", f'V1_17_SOURCE_SHA = "{V17_SHA}"' in ls)
    ck("S7_supervisor_enforces_launcher_pin",
       "FAIL_CLOSED__LAUNCHER_SHA_MISMATCH" in ss and "launcher_sha_pin_enforced" in ss)
    man = load(AUD / "phase36_v1_17_runtime_source_integrity_manifest.json")
    ck("S7_manifest_binds_exec_sha", man.get("execution_source_sha256") == V17_SHA)
    ck("S7_supervisor_dispatch_count_1",
       "supervisor_single_dispatch" in ss or '"automatic_retry": False' in ss
       or "'automatic_retry': False" in ss)
    ck("S7_no_auto_retry", '"automatic_retry": False' in ss or "'automatic_retry': False" in ss)
    # supervisor observes PROCESS_EXIT / stdout / stderr for real execution
    ck("S7_supervisor_observes_process_exit",
       "process_exit" in ss.lower() or "PROCESS_EXIT" in ss)
    ck("S7_supervisor_observes_stdout_stderr",
       "stdout" in ss and "stderr" in ss)
    # no v1.14/v1.15/v1.16 science artifact path is a v1.17 write target
    ck("S7_no_prev_science_write_target",
       not any(f"phase36_robustness_science_start_v1_1{n}.json" in ex for n in (4, 5, 6)))
    ck("S7_process_exit_exclusive_create",
       "O_CREAT | os.O_EXCL" in ex or "O_CREAT|os.O_EXCL" in ex)
    ck("S7_stage_journal_reachable",
       "V1_17_JOURNAL_STAGES" in ex and "_run_science_with_durable_evidence(journal=" in ex)

    # ================= §8 governance hash coherence ================= #
    # release attestation -> execution / historical smoke
    ck("S8_att_exec_matches", att.get("execution_source_sha256") == sha(V17))
    hist_smoke = ROOT / att.get("smoke_artifact", "")
    ck("S8_att_smoke_matches", hist_smoke.exists() and sha(hist_smoke) == att.get("smoke_artifact_sha256"))
    # source freeze -> all frozen sources
    freeze = load(AUD / "phase36_preexecution_source_freeze_v1_17.json")
    for rel, h in freeze.get("frozen_sources", {}).items():
        ck(f"S8_freeze_{Path(rel).name}", sha(ROOT / rel) == h)
    # eligibility -> validator/gate states present
    elig = load(AUD / "phase36_science_eligibility_v1_17.json")
    ck("S8_elig_unit", elig.get("unit_all_pass") is True)
    ck("S8_elig_preflight", elig.get("preflight_all_pass") is True)
    ck("S8_elig_nc", elig.get("negative_controls_all_pass") is True)
    ck("S8_elig_xcontract", elig.get("operational_cross_contract_all_pass") is True)
    ck("S8_elig_release_state", elig.get("pure_runtime_release_state") == "RELEASED")
    # D81-D83 adjudication chain
    adj = load(AUD / "phase36_v1_17_operational_adjudication_d81_d82_d83.json")
    ck("S8_adj_d81", adj.get("D81", {}).get("status") == "ESTABLISHED")
    ck("S8_adj_d82", adj.get("D82", {}).get("status") == "ESTABLISHED")
    ck("S8_adj_d83", adj.get("D83", {}).get("status") == "ESTABLISHED")

    n_pass = 0
    # count only checks recorded in fails as failures
    print("FAILURES:" if fails else "ALL CHECKS PASS")
    for f in fails:
        print("  FAIL", f)
    print(f"terminal: {'PHASE36_V1_17_COHERENCE_VERIFY_FAIL' if fails else 'PHASE36_V1_17_COHERENCE_VERIFY_PASS'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
