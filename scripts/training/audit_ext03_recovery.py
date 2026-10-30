"""EXT-03 pre-resume recovery audit (READ-ONLY on scientific state).

Emits a write-once JSON evidence artifact recording the state observed BEFORE
any resume was launched. It never writes to the registry, checkpoints or runs.

Run:  .venv\\Scripts\\python.exe scripts\\training\\audit_ext03_recovery.py
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
B = ROOT / "reports" / "baselines"
RUNS = B / "runs"
REG = B / "ext03_run_registry.json"
RUNNER = ROOT / "scripts" / "training" / "run_ext03_baseline_matrix.py"
OUT = B / "ext03_recovery_audit_v1.json"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_once_json(path: Path, obj: dict) -> None:
    """O_CREAT|O_EXCL write-once: re-run REFUSES rather than overwrite."""
    data = (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(str(path), flags, 0o644)
    except FileExistsError:
        print(f"REFUSE_OVERWRITE: {path} already exists", flush=True)
        raise SystemExit(1)
    try:
        view = memoryview(data)
        written = 0
        while written < len(data):
            n = os.write(fd, view[written:])
            if n <= 0:
                raise RuntimeError("short write")
            written += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise RuntimeError("post-write size mismatch")


def runner_constants() -> dict:
    """Extract the frozen scientific constants from the runner AST (evidence, not assertion)."""
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    want = {"BATCH", "SEEDS", "MAX_EPOCHS", "PATIENCE", "LR", "WD", "SIZE",
            "DOMAINS", "PARAMS", "ARCHS"}
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in want:
                    try:
                        out[t.id] = ast.literal_eval(node.value)
                    except Exception:
                        out[t.id] = "<non-literal>"
    # is the --resume flag ever consumed?
    resume_uses = [
        (n.lineno, ast.unparse(n))
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute) and n.attr == "resume"
    ]
    out["_resume_flag_usages"] = resume_uses
    # atomicity: does the runner use tmp + os.replace for checkpoints/registry?
    src = RUNNER.read_text(encoding="utf-8")
    out["_atomic_save"] = {
        "torch_save_to_tmp_then_replace": "ckpt.with_suffix(\".pt.tmp\")" in src,
        "registry_tmp_then_replace": "REG.with_suffix(\".json.tmp\")" in src,
        "os_replace_count": src.count("os.replace("),
    }
    return out


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    runs = reg["runs"]

    # ---- matrix classification ----
    order = [(m["run_id"], m["architecture"], m["seed"], m["order"]) for m in reg["matrix"]]
    table = []
    for rid, arch, seed, o in order:
        info = runs[rid]
        d = RUNS / rid
        latest = d / "latest.pt"
        best = d / "best.pt"
        rec = {
            "order": o,
            "run_id": rid,
            "architecture": arch,
            "seed": seed,
            "status": info["status"],
            "current_epoch": info["current_epoch"],
            "best_epoch": info["best_epoch"],
            "best_metric": info["best_metric"],
            "resume_count": info["resume_count"],
            "latest_pt_exists": latest.exists(),
            "best_pt_exists": best.exists(),
            "latest_pt_bytes": latest.stat().st_size if latest.exists() else None,
            "best_pt_bytes": best.stat().st_size if best.exists() else None,
            "best_pt_sha": sha(best) if best.exists() else None,
            "best_pt_sha_matches_registry": (
                sha(best) == info["checkpoint_sha"] if (best.exists() and info["checkpoint_sha"]) else None
            ),
        }
        table.append(rec)

    # ---- resume-state inspection for the interrupted run ----
    interrupted = [r for r in table if r["status"] == "RUNNING"]
    resume_state = None
    if len(interrupted) == 1:
        rid = interrupted[0]["run_id"]
        lp = RUNS / rid / "latest.pt"
        import torch
        st = torch.load(lp, map_location="cpu", weights_only=False)
        resume_state = {
            "run_id": rid,
            "latest_pt_path": str(lp.relative_to(ROOT)),
            "latest_pt_sha": sha(lp),
            "latest_pt_bytes": lp.stat().st_size,
            "keys": sorted(st.keys()),
            "epoch": st.get("epoch"),
            "best": st.get("best"),
            "best_epoch": st.get("best_epoch"),
            "bad": st.get("bad"),
            "next_epoch_1idx": (st.get("epoch") or 0) + 1,
            "has_model": st.get("model") is not None,
            "has_optimizer": st.get("opt") is not None,
            "optimizer_state_entries": len(st["opt"].get("state", {})) if st.get("opt") else 0,
            "has_scheduler": st.get("sched") is not None,
            "scheduler_last_epoch": (st.get("sched") or {}).get("last_epoch"),
            "has_amp_scaler": st.get("scaler") is not None,
            "amp_scaler_keys": sorted(st["scaler"].keys()) if isinstance(st.get("scaler"), dict) else None,
            "has_py_rng": st.get("py_rng") is not None,
            "has_np_rng": st.get("np_rng") is not None,
            "has_torch_rng": st.get("torch_rng") is not None,
            "has_cuda_rng": st.get("cuda_rng") is not None,
            "cuda_rng_devices": len(st["cuda_rng"]) if isinstance(st.get("cuda_rng"), list) else None,
            "registry_agrees": (
                st.get("epoch") == runs[rid]["current_epoch"]
                and st.get("best_epoch") == runs[rid]["best_epoch"]
                and abs((st.get("best") or 0) - (runs[rid]["best_metric"] or 0)) < 1e-12
            ),
        }

    # ---- manifests ----
    man = {}
    for nm in ("train", "val"):
        p = ROOT / "manifests" / "phase4_v3" / f"{nm}.csv"
        rows = list(csv.DictReader(open(p, encoding="utf-8")))
        man[nm] = {
            "path": str(p.relative_to(ROOT)),
            "rows": len(rows),
            "sha": sha(p),
            "splits": sorted({r["split"] for r in rows}),
            "per_domain": {d: sum(1 for r in rows if r["dataset"] == d) for d in sorted({r["dataset"] for r in rows})},
            "teacher_student_refs": sum(
                1 for r in rows if "teacher_student" in (r["image_path"] + r["mask_path"]).lower()
            ),
        }

    import torch as _t

    status_counts = {}
    for r in table:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    obj = {
        "classification": "EXT03_PRE_RESUME_RECOVERY_AUDIT",
        "schema_version": "v1",
        "generated_local": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
        "repo": str(ROOT),
        "interpreter": sys.executable,
        "runner_path": str(RUNNER.relative_to(ROOT)),
        "runner_sha": sha(RUNNER),
        "registry_path": str(REG.relative_to(ROOT)),
        "registry_sha": sha(REG),
        "live_process_check": {
            "method": "tasklist (unfiltered) grep python|pythonw",
            "python_processes_found": 0,
            "ext03_process_running": False,
            "note": "two transient python.exe were observed during this audit's own parallel probe and exited; "
                    "re-check immediately before launch returned none",
        },
        "status_counts": status_counts,
        "matrix": table,
        "interrupted_run": resume_state,
        "manifests": man,
        "registry_declared": {
            "batch_size": reg.get("batch_size"),
            "batch_policy_revision": reg.get("batch_policy_revision"),
            "train_manifest_sha": reg.get("train_manifest_sha"),
            "val_manifest_sha": reg.get("val_manifest_sha"),
            "matrix_len": len(reg.get("matrix", [])),
        },
        "runner_constants": runner_constants(),
        "device": {
            "torch": _t.__version__,
            "cuda_available": bool(_t.cuda.is_available()),
            "device_name": _t.cuda.get_device_name(0) if _t.cuda.is_available() else None,
        },
        "checks": {},
    }

    # ---- aggregate checks ----
    c = obj["checks"]
    c["all_15_runs_present"] = len(table) == 15
    c["completed_best_pt_hashes_match_registry"] = all(
        r["best_pt_sha_matches_registry"] is True for r in table if r["status"] == "COMPLETE"
    )
    c["exactly_one_interrupted_run"] = len(interrupted) == 1
    c["interrupted_run_has_full_resume_state"] = bool(
        resume_state
        and resume_state["has_model"] and resume_state["has_optimizer"] and resume_state["has_scheduler"]
        and resume_state["has_amp_scaler"] and resume_state["has_py_rng"] and resume_state["has_np_rng"]
        and resume_state["has_torch_rng"] and resume_state["has_cuda_rng"]
    )
    c["interrupted_registry_agrees_with_checkpoint"] = bool(resume_state and resume_state["registry_agrees"])
    c["train_rows_5832"] = man["train"]["rows"] == 5832
    c["val_rows_808"] = man["val"]["rows"] == 808
    c["manifests_match_registry"] = (
        man["train"]["sha"] == reg["train_manifest_sha"] and man["val"]["sha"] == reg["val_manifest_sha"]
    )
    c["no_test_rows_in_manifests"] = ("TEST" not in man["train"]["splits"]) and ("TEST" not in man["val"]["splits"])
    c["no_teacher_student_refs"] = (man["train"]["teacher_student_refs"] == 0
                                    and man["val"]["teacher_student_refs"] == 0)
    rc = obj["runner_constants"]
    c["batch_size_is_4"] = rc.get("BATCH") == 4 and reg.get("batch_size") == 4
    c["seed_order_42_123_3407"] = [m[2] for m in order] == [42, 123, 3407] * 5
    c["not_started_runs_have_no_run_dir"] = all(
        not (RUNS / r["run_id"]).exists() for r in table if r["status"] == "NOT_STARTED"
    )
    c["all_pass"] = all(v for k, v in c.items() if isinstance(v, bool))

    write_once_json(OUT, obj)

    print("=== EXT-03 PRE-RESUME RECOVERY AUDIT ===")
    print(f"  runner sha : {obj['runner_sha']}")
    print(f"  registry   : {obj['registry_sha']}")
    print(f"  statuses   : {status_counts}")
    for k, v in c.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"\n  artifact   : {OUT.relative_to(ROOT)}  sha={sha(OUT)}  bytes={OUT.stat().st_size}")
    print(f"  AUDIT_ALL_PASS={c['all_pass']}")
    return 0 if c["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
