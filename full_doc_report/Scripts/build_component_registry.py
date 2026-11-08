"""Verify the four ReMedFiLM components from their actual checkpoint bytes.

Loads each checkpoint read-only, counts parameters from the state dict, checks the
recorded SHA-256, and records the training completion evidence. Produces
REMEDFILM_FULL_COMPONENT_REGISTRY.json.

No model is instantiated for inference and no weights are modified.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import torch

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


COMPONENTS = [
    {
        "symbol": "G",
        "run_id": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
        "name": "GlobalMedFiLM (task-conditioned FiLM backbone)",
        "class": "GlobalMedFiLM",
        "source": "src/models/film/global_medfilm.py",
        "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
        "experiment": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
        "closure": "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/closure.json",
        "expected_params": 3523001,
        "seed": 42,
        "interface_in": "image [B,3,512,512] + task_id [B]",
        "interface_out": "foreground probability [B,1,512,512]",
        "conditional": False,
    },
    {
        "symbol": "R_psi",
        "run_id": "phase25a_barr_regional_refiner_v1_1_roi030__final_refit",
        "name": "Regional Residual Refiner",
        "class": "BARRRegionalRefinerV1",
        "source": "src/models/barr/regional_refiner.py",
        "checkpoint": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
        "experiment": "phase25a_barr_regional_refiner_v1_1_roi030",
        "closure": "experiments/phase25a_barr_regional_refiner_v1_1_roi030/final_refit/run.json",
        "expected_params": 1276401,
        "seed": 42,
        "interface_in": "ROI crop + global probability patch",
        "interface_out": "refined residual for the ROI",
        "conditional": True,
    },
    {
        "symbol": "B_phi",
        "run_id": "phase25d_barr_benefit_router_v1_2_1_seed42__final",
        "name": "Learned Benefit Router",
        "class": "BARRBenefitRouterV1",
        "source": "src/models/barr/router_variants.py",
        "checkpoint": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
        "experiment": "phase25d_barr_benefit_router_v1_2_1_seed42",
        "closure": "experiments/phase25d_barr_benefit_router_v1_2_1_seed42/final/",
        "expected_params": 36801,
        "seed": 42,
        "interface_in": "GT-free candidate features",
        "interface_out": "utility score (scalar per candidate)",
        "conditional": True,
    },
    {
        "symbol": "S_omega",
        "run_id": "phase25f_barr_post_safety_v1_0_seed42__final",
        "name": "Post-Safety Gate",
        "class": "BARRPostSafetyV1",
        "source": "src/models/barr/ra_medfilm_barr.py",
        "checkpoint": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
        "experiment": "phase25f_barr_post_safety_v1_0_seed42",
        "closure": "experiments/phase25f_barr_post_safety_v1_0_seed42/final/",
        "expected_params": 1217,
        "seed": 42,
        "interface_in": "candidate features + refiner delta statistics",
        "interface_out": "accept / reject probability",
        "conditional": True,
    },
]


def inspect_state(ck: object) -> tuple[int, list[str], dict]:
    """Return (n_params, top-level keys, metadata dict)."""
    meta = {}
    if not isinstance(ck, dict):
        return 0, [], {"note": f"checkpoint is {type(ck).__name__}"}
    sd = (ck.get("model_state") or ck.get("model_state_dict")
          or ck.get("state_dict") or ck)
    if not isinstance(sd, dict):
        return 0, list(ck.keys())[:20], meta
    n = sum(v.numel() for v in sd.values() if hasattr(v, "numel"))
    for k, v in ck.items():
        if k in ("model_state", "model_state_dict", "state_dict", "optimizer_state",
                 "scheduler_state", "grad_scaler_state", "random_state", "history"):
            continue
        if hasattr(v, "numel"):
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            meta[k] = v
        elif isinstance(v, dict):
            meta[k] = {kk: vv for kk, vv in list(v.items())[:8]
                       if isinstance(vv, (str, int, float, bool))}
    return n, list(sd.keys()), meta


def main() -> None:
    entries = []
    for c in COMPONENTS:
        cp = ROOT / c["checkpoint"]
        rec = {
            "symbol": c["symbol"],
            "name": c["name"],
            "implementation_class": c["class"],
            "implementation_source": c["source"],
            "conditional": c["conditional"],
            "interface_input": c["interface_in"],
            "interface_output": c["interface_out"],
            "training_experiment": c["experiment"],
            "seed": c["seed"],
            "checkpoint_path": c["checkpoint"],
            "checkpoint_exists": cp.exists(),
        }
        if not cp.exists():
            rec["status"] = "CHECKPOINT_MISSING"
            entries.append(rec)
            continue

        rec["checkpoint_bytes"] = cp.stat().st_size
        rec["checkpoint_sha256"] = sha256(cp)
        rec["expected_parameters"] = c["expected_params"]

        try:
            ck = torch.load(cp, map_location="cpu", weights_only=False)
            n, keys, meta = inspect_state(ck)
            rec["measured_parameters"] = n
            rec["parameter_match"] = (n == c["expected_params"])
            rec["state_dict_entries"] = len(keys)
            rec["state_dict_prefixes"] = sorted({k.split(".")[0] for k in keys})[:12]
            rec["checkpoint_metadata"] = meta
        except Exception as exc:  # noqa: BLE001
            rec["load_error"] = f"{type(exc).__name__}: {exc}"
            rec["parameter_match"] = None

        # training completion evidence
        cl = ROOT / c["closure"]
        if cl.exists():
            if cl.is_file():
                d = json.loads(cl.read_text(encoding="utf-8"))
            else:
                d = {}
                for cand in ("run.json", "run_complete.json", "closure.json"):
                    q = cl / cand
                    if q.exists():
                        d = json.loads(q.read_text(encoding="utf-8"))
                        break
                # fall back to the epoch count in the recorded history
                if not d.get("epochs_completed") and not d.get("total_completed_epochs"):
                    h = cl / "history.csv"
                    if h.exists():
                        d["epochs_completed"] = sum(1 for _ in h.open(encoding="utf-8")) - 1
            rec["training_completion"] = {
                "epochs_completed": d.get("total_completed_epochs") or d.get("epochs_completed"),
                "best_epoch": d.get("best_epoch"),
                "stop_reason": d.get("stop_reason"),
                "training_performed": d.get("training_performed"),
                "recorded_best_sha256": d.get("best_checkpoint_sha256")
                                       or (d.get("checkpoint_sha256") or {}).get("final.pt"),
            }
            # cross-reference the derived best epoch from the run registry
            try:
                import csv as _csv
                with (OUT / "tables/TRAINING_RUN_REGISTRY.csv").open(encoding="utf-8") as fh:
                    for rr in _csv.DictReader(fh):
                        if rr["run_id"] == c.get("run_id"):
                            rec["training_completion"]["best_epoch_registry"] = rr["best_epoch"]
                            rec["training_completion"]["best_epoch_source"] = rr["best_epoch_source"]
                            if rec["training_completion"].get("best_epoch") in (None, -1):
                                rec["training_completion"]["best_epoch"] = rr["best_epoch"]
                            break
            except Exception:
                pass
            rb = rec["training_completion"].get("recorded_best_sha256")
            if rb:
                rec["sha_matches_record"] = (rb == rec["checkpoint_sha256"])
        else:
            rec["training_completion"] = {"status": "CLOSURE_METADATA_MISSING"}

        rec["status"] = ("VERIFIED" if rec.get("parameter_match") else
                         "PRESENT_PARAMETER_MISMATCH")
        entries.append(rec)
        print(f"{c['symbol']:8s} params={rec.get('measured_parameters'):>9} "
              f"expected={c['expected_params']:>9} match={rec.get('parameter_match')} "
              f"sha={rec['checkpoint_sha256'][:12]}")

    total = sum(e.get("measured_parameters") or 0 for e in entries)
    print(f"\nmeasured component sum: {total}")

    registry = {
        "artifact": "REMEDFILM_FULL_COMPONENT_REGISTRY",
        "system": "ReMedFiLM FULL = G + R_psi + B_phi + S_omega",
        "assembly": ("Components are trained sequentially, each against a frozen upstream, "
                     "and assembled for inference. This is NOT a jointly trained network."),
        "verified_total_parameters": total,
        "contract_total_parameters": 4837420,
        "total_matches_contract": total == 4837420,
        "all_components_verified": all(e.get("status") == "VERIFIED" for e in entries),
        "verification_method": ("Each checkpoint was loaded read-only with torch.load, "
                                "parameter counts were summed from the state dict, and "
                                "the file SHA-256 was compared with the recorded value."),
        "components": entries,
        "not_established": [
            "C1 learned-vs-identity FiLM attribution (0/6 runs)",
            "C2 causal component attribution (A8 vs A7 CI includes zero)",
            "C3 eight-model x three-seed benchmark (0/24 cells)",
        ],
    }
    (OUT / "REMEDFILM_FULL_COMPONENT_REGISTRY.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8")
    print("all verified:", registry["all_components_verified"])
    print("total matches contract:", registry["total_matches_contract"])


if __name__ == "__main__":
    main()
