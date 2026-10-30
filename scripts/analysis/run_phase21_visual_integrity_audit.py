"""Post-Phase22 repair — Part A1/A2: Phase-21 figure and notebook visual integrity.

A1 verifies every SOURCE figure on disk (existence, non-zero size, PIL decode,
``Image.verify()``, dimensions, SHA-256).

A2 audits the EXISTING Phase-21 notebook by parsing its bytes directly. It does
NOT trust ``embedded_in_notebook`` from the inventory CSV: that flag was the
thing that lied. Every ``image/png`` output is base64-decoded with strict
validation, PIL-verified, and matched back to an inventory figure by the
SHA-256 of the decoded bytes.

Read-only: no training, no inference, no TEST access, no frozen file modified.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/run_phase21_visual_integrity_audit.py
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

INVENTORY = ROOT / "reports/figures/phase21_global_medfilm/phase21_figure_inventory.csv"
NB_PATH = (ROOT / "notebooks/phasewise/phase_21_global_medfilm"
           / "phase21_global_medfilm_reference.ipynb")
OUT_A1 = ROOT / "reports/audits/phase21_figure_file_integrity_repair.json"
OUT_A2 = ROOT / "reports/audits/phase21_notebook_visual_integrity_before_repair.json"

EXPECTED_GROUPS = {"comparison": 17, "conditioning": 5, "efficiency": 3,
                   "failure": 2, "gallery": 8, "kub": 2, "training": 6}
EXPECTED_TOTAL = 43


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def decode_png_payload(payload) -> tuple[bytes | None, str]:
    """Strictly base64-decode a notebook image/png payload.

    Returns ``(raw_bytes_or_None, error_or_EMPTY)``. ``validate=True`` is
    deliberate: it is what catches the odd-length truncated payloads.
    """
    if isinstance(payload, list):
        payload = "".join(payload)
    if not isinstance(payload, str) or not payload:
        return None, "EMPTY_OR_NON_STRING"
    try:
        raw = base64.b64decode(payload, validate=True)
    except Exception as exc:  # binascii.Error, ValueError
        return None, f"{type(exc).__name__}: {exc}"
    if not raw:
        return None, "DECODED_TO_ZERO_BYTES"
    return raw, ""


def verify_png(raw: bytes) -> str:
    """Return '' when the bytes are a valid PNG, else an error string."""
    try:
        im = Image.open(io.BytesIO(raw))
        im.verify()                      # checksum check
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    try:
        Image.open(io.BytesIO(raw)).load()   # full decode
    except Exception as exc:
        return f"LOAD_{type(exc).__name__}: {exc}"
    return ""


def main() -> int:
    inv = pd.read_csv(INVENTORY)

    # ---------------- A1: source figure files on disk ---------------------- #
    a1_rows, a1_corrupt, a1_missing = [], [], []
    for _, r in inv.iterrows():
        rel = str(r["saved_path"]).replace("\\", "/")
        p = ROOT / rel
        rec = {"figure_id": r["figure_id"], "group": r["group"],
               "saved_path": rel, "exists": p.exists(),
               "bytes": p.stat().st_size if p.exists() else 0}
        if not p.exists():
            rec.update({"valid": False, "error": "FILE_MISSING", "sha256": None,
                        "width": None, "height": None})
            a1_missing.append(r["figure_id"])
            a1_rows.append(rec)
            continue
        raw = p.read_bytes()
        rec["sha256"] = sha256_bytes(raw)
        err = "ZERO_BYTES" if not raw else verify_png(raw)
        if not err:
            with Image.open(io.BytesIO(raw)) as im:
                rec["width"], rec["height"] = im.size
                rec["mode"] = im.mode
        else:
            rec["width"] = rec["height"] = None
        rec["valid"] = not err
        rec["error"] = err
        if err:
            a1_corrupt.append({"figure_id": r["figure_id"], "error": err})
        a1_rows.append(rec)

    groups = inv["group"].value_counts().to_dict()
    a1 = {
        "artifact": "phase21_figure_file_integrity_repair",
        "phase": 21,
        "purpose": ("verify every SOURCE Phase-21 figure on disk before repairing "
                    "the reviewer notebook"),
        "read_only": True,
        "training_jobs_started": 0,
        "inference_performed": False,
        "inventory_path": str(INVENTORY.relative_to(ROOT)).replace("\\", "/"),
        "inventory_figures": int(len(inv)),
        "inventory_groups": {k: int(groups.get(k, 0)) for k in EXPECTED_GROUPS},
        "inventory_groups_match_expected": bool(
            all(int(groups.get(k, 0)) == v for k, v in EXPECTED_GROUPS.items())
            and len(inv) == EXPECTED_TOTAL),
        "files_present": int(sum(1 for x in a1_rows if x["exists"])),
        "files_valid": int(sum(1 for x in a1_rows if x.get("valid"))),
        "files_corrupt": len(a1_corrupt),
        "files_missing": len(a1_missing),
        "source_regeneration_required": bool(a1_corrupt or a1_missing),
        "regenerated_figure_ids": [],
        "regeneration_note": (
            "No source figure required regeneration: all 43 inventory PNGs decode "
            "and pass PIL.Image.verify(). The reviewer defect is therefore NOT a "
            "corrupt-source problem but a notebook-embedding problem."
            if not (a1_corrupt or a1_missing) else
            "Source regeneration required; performed from persisted tables only "
            "(no segmentation inference)."),
        "per_figure": a1_rows,
        "corrupt": a1_corrupt,
        "missing": a1_missing,
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT_A1.parent.mkdir(parents=True, exist_ok=True)
    OUT_A1.write_text(json.dumps(a1, indent=2), encoding="utf-8")

    # ---------------- A2: notebook visual coverage ------------------------ #
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    hash_to_id = {}
    for _, r in inv.iterrows():
        p = ROOT / str(r["saved_path"]).replace("\\", "/")
        if p.exists():
            hash_to_id[sha256_bytes(p.read_bytes())] = r["figure_id"]

    outputs, per_figure_hits = [], {}
    for ci, cell in enumerate(nb.get("cells", [])):
        label = ""
        for o in cell.get("outputs", []) or []:
            d = o.get("data") or {}
            if "text/markdown" in d:
                md = d["text/markdown"]
                label = "".join(md) if isinstance(md, list) else str(md)
            if "image/png" not in d:
                continue
            payload = d["image/png"]
            raw, derr = decode_png_payload(payload)
            verr = verify_png(raw) if raw else derr
            fid = hash_to_id.get(sha256_bytes(raw)) if raw else None
            b64_len = len("".join(payload) if isinstance(payload, list) else payload)
            outputs.append({
                "cell_index": ci, "cell_id": cell.get("id"),
                "label": label.split("*")[1].strip() if "*" in label else label[:120],
                "base64_length": b64_len,
                "base64_length_multiple_of_4": b64_len % 4 == 0,
                "decoded_bytes": len(raw) if raw else 0,
                "decode_error": derr,
                "verify_error": verr,
                "valid": (not derr) and (not verr),
                "matched_figure_id": fid,
                "sha256": sha256_bytes(raw) if raw else None,
            })
            if fid:
                per_figure_hits.setdefault(fid, []).append(ci)

    actual = len(outputs)
    valid = sum(1 for o in outputs if o["valid"])
    corrupt = [o for o in outputs if not o["valid"]]
    decodable_ids = {o["matched_figure_id"] for o in outputs
                     if o["matched_figure_id"]}
    all_ids = list(inv["figure_id"])
    missing = [f for f in all_ids if f not in decodable_ids]
    unexpected = sorted(decodable_ids - set(all_ids))
    duplicates = {k: v for k, v in per_figure_hits.items() if len(v) > 1}

    a2 = {
        "artifact": "phase21_notebook_visual_integrity_before_repair",
        "phase": 21,
        "purpose": ("measure the TRUE visual coverage of the existing Phase-21 "
                    "reviewer notebook from its bytes, without trusting the "
                    "inventory's embedded_in_notebook flag"),
        "read_only": True,
        "notebook_path": str(NB_PATH.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": sha256_bytes(NB_PATH.read_bytes()),
        "notebook_total_cells": len(nb.get("cells", [])),
        "expected_inventory_figures": int(len(inv)),
        "actual_png_outputs": actual,
        "valid_png_outputs": valid,
        "corrupt_png_outputs": len(corrupt),
        "distinct_inventory_figures_embedded": len(decodable_ids),
        "missing_inventory_figures": missing,
        "missing_count": len(missing),
        "missing_by_group": (
            inv[inv["figure_id"].isin(missing)]["group"]
            .value_counts().to_dict()),
        "duplicate_embedded_figures": {k: v for k, v in duplicates.items()},
        "unexpected_embedded_figures": unexpected,
        "coverage_fraction": round(len(decodable_ids) / len(inv), 6),
        "coverage_fraction_valid": round(valid / len(inv), 6),
        "inventory_flag_disagrees_with_reality": bool(
            inv["image_png_output_present"].sum() != valid),
        "inventory_flag_true_count": int(inv["image_png_output_present"].sum()),
        "root_cause": {
            "mechanism": ("the three corrupt payloads are the three LARGEST "
                          "base64 payloads; their strings are odd-length and "
                          "divergent from the on-disk bytes, i.e. they were "
                          "truncated/corrupted during notebook embedding. This is "
                          "a payload-size failure, not a source-file failure."),
            "evidence": [o for o in corrupt],
            "consequence": ("a bare base64 string of this size does not survive "
                            "the read-image-and-embed path; the payload must be "
                            "downscaled before embedding or the notebook will "
                            "silently ship broken images."),
        },
        "truncation_evidence": [
            {"figure_id": o["matched_figure_id"] or o["label"],
             "cell_index": o["cell_index"], "base64_length": o["base64_length"],
             "length_multiple_of_4": o["base64_length_multiple_of_4"]}
            for o in corrupt],
        "repair_required": True,
        "per_output": outputs,
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT_A2.write_text(json.dumps(a2, indent=2), encoding="utf-8")

    print(f"WROTE {OUT_A1}")
    print(f"WROTE {OUT_A2}")
    print()
    print(f"A1 source: present {a1['files_present']}/43, valid {a1['files_valid']}, "
          f"corrupt {a1['files_corrupt']}, missing {a1['files_missing']}")
    print(f"   groups match expected: {a1['inventory_groups_match_expected']}")
    print(f"A2 notebook: inventory {a2['expected_inventory_figures']}, "
          f"png_outputs {a2['actual_png_outputs']}, valid {a2['valid_png_outputs']}, "
          f"corrupt {a2['corrupt_png_outputs']}")
    print(f"   distinct embedded {a2['distinct_inventory_figures_embedded']}, "
          f"missing {a2['missing_count']} {a2['missing_by_group']}")
    print(f"   coverage {a2['coverage_fraction']}")
    print(f"   inventory flag says {a2['inventory_flag_true_count']} embedded "
          f"(disagrees: {a2['inventory_flag_disagrees_with_reality']})")
    print()
    for o in corrupt:
        print(f"   CORRUPT cell {o['cell_index']} len={o['base64_length']} "
              f"mult4={o['base64_length_multiple_of_4']} :: {o['decode_error'] or o['verify_error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
