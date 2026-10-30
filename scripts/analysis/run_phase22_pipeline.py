"""Phase 22 — pipeline orchestrator.

Runs the whole Phase-22 chain in the frozen protocol's own ``required_outputs`` order,
fail-closed. Never trains. Never touches TEST. Does not start Phase 23.

Order
-----
  1.  freeze the diagnostic protocol            (skip if already frozen)
  2.  bind every identity to the frozen Phase-21 reference (fail-closed)
  3.  audit the decision rule (float16 prob vs uint8 pred)
  4.  global failure atlas
  5.  scale probe 256 / 512 / 768 / 1024        (heavy; skippable once persisted)
  6.  regional intervention (oracle + predicted)
  7.  benefit heterogeneity / ceiling / routing regret / harm
  8.  resource frontier / derived ROI / uncertainty / gap / envelopes / CPU baseline
  9.  KUB TINY / domain preservation / statistics / scale-vs-regional
 10.  figures + inventory
 11.  no-new-training audit + label contract + candidate evidence
 12.  report (markdown)
 13.  notebook x3 -> byte-identical determinism proof
 14.  final freeze (two-pass: provisional, then verified)
 15.  additive governance sync

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/run_phase22_pipeline.py
    ./.venv/Scripts/python.exe scripts/analysis/run_phase22_pipeline.py --device cuda
    ./.venv/Scripts/python.exe scripts/analysis/run_phase22_pipeline.py \
        --skip-scale --skip-regional      # when the persisted probe outputs already exist
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
AUD = ROOT / "reports" / "audits"
NB_PATH = (ROOT / "notebooks/phasewise/phase_22_resource_gap"
           / "phase22_resource_gap_analysis.ipynb")
DETERMINISM = AUD / "phase22_notebook_determinism.json"
FREEZE = AUD / "phase22_final_freeze.json"
REPORT = ROOT / "reports/phase22_resource_gap_report.md"


def run(step: str, args: list[str], allow_rc: tuple[int, ...] = (0,)) -> int:
    print(f"\n=== [{step}] {' '.join(args)} ===", flush=True)
    t0 = time.time()
    r = subprocess.run([PY, *args], cwd=str(ROOT))
    dt = time.time() - t0
    print(f"=== [{step}] rc={r.returncode} ({dt:.0f}s) ===", flush=True)
    if r.returncode not in allow_rc:
        raise SystemExit(f"FAIL-CLOSED: step '{step}' exited {r.returncode}")
    return r.returncode


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--skip-protocol", action="store_true")
    ap.add_argument("--skip-scale", action="store_true",
                    help="reuse persisted probe NPZ + tables (do not re-run the probe)")
    ap.add_argument("--skip-regional", action="store_true",
                    help="reuse the persisted regional table (do not re-infer)")
    ap.add_argument("--skip-notebook", action="store_true")
    args = ap.parse_args()

    # 1 -------------------------------------------------------------------- #
    if not args.skip_protocol and not (AUD / "phase22_diagnostic_protocol.json").exists():
        run("freeze_protocol", ["scripts/analysis/run_phase22_freeze_protocol.py"])
    proto = json.loads((AUD / "phase22_diagnostic_protocol.json").read_text(encoding="utf-8"))
    print(f"protocol {proto['protocol_id']} frozen={proto.get('frozen')}")

    # 2 -------------------------------------------------------------------- #
    run("reference_binding", ["scripts/analysis/run_phase22_reference_binding.py"])

    # 3 -------------------------------------------------------------------- #
    run("threshold_audit", ["scripts/analysis/run_phase22_threshold_audit.py"])

    # 4 -------------------------------------------------------------------- #
    run("failure_atlas", ["-m", "src.analysis.phase22_failure_atlas"])

    # 5 -------------------------------------------------------------------- #
    if not args.skip_scale:
        run("scale_probe",
            ["src/analysis/phase22_scale.py", "--device", args.device])
    else:
        p = ROOT / "reports/tables/phase22_scale_sensitivity_per_image.csv"
        if not p.exists():
            raise SystemExit("FAIL-CLOSED: --skip-scale but scale tables are absent")
        print(f"reusing persisted scale tables ({sf_rows(p)} rows)")

    # 6 -------------------------------------------------------------------- #
    if not args.skip_regional:
        run("regional_intervention",
            ["src/analysis/phase22_regional.py", "--device", args.device])
    else:
        p = ROOT / "reports/tables/phase22_regional_intervention_per_image.csv"
        if not p.exists():
            raise SystemExit("FAIL-CLOSED: --skip-regional but the regional table is absent")
        print("reusing persisted regional table")

    # 7 -------------------------------------------------------------------- #
    run("benefit", ["-m", "src.analysis.phase22_benefit"])

    # 8 -------------------------------------------------------------------- #
    run("resource", ["-m", "src.analysis.phase22_resource"])

    # 9 -------------------------------------------------------------------- #
    run("kub_domain", ["-m", "src.analysis.phase22_kub_domain"])

    # 10 ------------------------------------------------------------------- #
    print("\n=== [figures] building ===", flush=True)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.analysis import phase22_figures as F
    built = F.build_all(progress=print)
    inv = F.write_inventories()
    print("figures:", inv)

    # 11 ------------------------------------------------------------------- #
    run("no_training_audit", ["scripts/analysis/run_phase22_no_training_audit.py"])

    # 12 ------------------------------------------------------------------- #
    run("report", ["scripts/analysis/write_phase22_report.py"])

    # 13-14 ---------------------------------------------------------------- #
    # Two-pass freeze, exactly as in Phase 21: the notebook asserts the terminal
    # state the freeze records, while the freeze requires the 3-build determinism
    # proof. Resolve with: pass 1 (provisional, determinism pending) -> 3 builds
    # -> pass 2 (verified).
    print("\n=== [freeze pass 1/2 - provisional] ===", flush=True)
    run("freeze_provisional",
        ["scripts/analysis/write_phase22_freeze.py", "--allow-pending-notebook"],
        allow_rc=(0, 2))
    if not FREEZE.exists():
        raise SystemExit("FAIL-CLOSED: freeze pass 1 did not write phase22_final_freeze.json")

    if not args.skip_notebook:
        seed = {
            "artifact": "phase22_notebook_determinism",
            "phase": 22,
            "notebook_path": str(NB_PATH.relative_to(ROOT)).replace("\\", "/"),
            "builds": 0, "sha256_per_build": [],
            "three_builds_byte_identical": None,
            "status": "PENDING_FINAL_THREE_BUILD_PROOF",
            "test_reads": 0,
        }
        DETERMINISM.write_text(json.dumps(seed, indent=2), encoding="utf-8")

        shas = []
        for i in (1, 2, 3):
            print(f"\n=== [notebook build {i}/3] ===", flush=True)
            r = run(f"notebook_build_{i}",
                    ["scripts/notebooks/build_phase22_notebook.py"])
            if r != 0:
                raise SystemExit(f"FAIL-CLOSED: notebook build {i} exited {r}")
            shas.append(sha(NB_PATH))
            print(f"build {i} sha256 = {shas[-1]}")

        identical = len(set(shas)) == 1
        DETERMINISM.write_text(json.dumps({
            "artifact": "phase22_notebook_determinism",
            "phase": 22,
            "notebook_path": str(NB_PATH.relative_to(ROOT)).replace("\\", "/"),
            "builds": 3,
            "sha256_per_build": shas,
            "three_builds_byte_identical": identical,
            "deterministic_practices": [
                "deterministic cell ids (p22000..p22NNN)",
                "stripped metadata.execution",
                "coalesced stream outputs",
                "fixed pandas Styler uuids via set_uuid",
                "normalised object memory addresses (0x... -> 0xADDR)",
                "stable output ordering",
            ],
            "test_reads": 0,
        }, indent=2), encoding="utf-8")
        if not identical:
            raise SystemExit("FAIL-CLOSED: notebook builds are NOT byte-identical")
        print("3-build determinism: PASS")
    else:
        print("--skip-notebook: determinism proof not re-run")

    print("\n=== [freeze pass 2/2 - verified] ===", flush=True)
    run("freeze_verified", ["scripts/analysis/write_phase22_freeze.py"])

    # 15 ------------------------------------------------------------------- #
    # The governance sync both (a) is listed among the protocol's required_outputs
    # and (b) reads the freeze to decide the terminal state, so it must run BOTH
    # before the freeze (to satisfy presence, recording a provisional state) and
    # after it (to record the verified terminal state). Running it twice is
    # idempotent and additive.
    if (ROOT / "scripts/analysis/sync_phase22_governance.py").exists():
        run("governance_sync", ["scripts/analysis/sync_phase22_governance.py"])
        run("governance_sync_final", ["scripts/analysis/sync_phase22_governance.py"])
        # the freeze records the governance-sync SHA, so refresh it once more
        run("freeze_refresh", ["scripts/analysis/write_phase22_freeze.py"])
    else:
        print("governance sync script absent - skipping (additive, non-blocking)")

    ff = json.loads(FREEZE.read_text(encoding="utf-8"))
    print("\n=== PHASE 22 PIPELINE COMPLETE ===")
    print("terminal_state:", ff.get("terminal_state"))
    print("freeze_verified:", ff.get("freeze_verified"),
          f"({ff.get('n_passed')}/{ff.get('n_checks')})")
    print("generated_utc:", datetime.now(timezone.utc).isoformat())
    print("\nPhase 23 is ELIGIBLE but NOT STARTED. STOP.")
    return 0


def sf_rows(p: Path) -> int:
    try:
        import pandas as pd
        return len(pd.read_csv(p))
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
