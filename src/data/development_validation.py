"""Reusable TRAIN/VAL pairing, geometry, duplicate and group-leakage validation.

Unlike historical audit scripts, importing this module performs no I/O. Every
row's split is checked before any image/mask file is opened. KUB category remains
reporting metadata and is never passed into preprocessing or model inputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
from PIL import Image

TASKS = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}


class DevelopmentValidationError(ValueError):
    pass


def validate_rows(rows: Iterable[Mapping[str, Any]]) -> dict:
    rows = list(rows)
    if not rows:
        raise DevelopmentValidationError("empty manifest")
    ids = set()
    for row in rows:
        if row.get("split") not in {"TRAIN", "VAL"}:
            raise PermissionError("only explicitly declared TRAIN/VAL rows are permitted")
        required = {"sample_id", "dataset", "task_id", "image_path", "mask_path"}
        if not required.issubset(row) or not str(row["sample_id"]).strip():
            raise DevelopmentValidationError("incomplete sample identity/pair")
        if row["sample_id"] in ids:
            raise DevelopmentValidationError("duplicate sample identity")
        ids.add(row["sample_id"])
        if row["dataset"] not in TASKS or int(row["task_id"]) != TASKS[row["dataset"]]:
            raise DevelopmentValidationError("domain/task mismatch")
    # No pixel access before the complete manifest passes the split/identity gate.
    images, groups = defaultdict(list), defaultdict(list)
    samples = []
    for row in rows:
        with Image.open(row["image_path"]) as image, Image.open(row["mask_path"]) as mask:
            if image.size != mask.size:
                raise DevelopmentValidationError(f"image/mask geometry mismatch: {row['sample_id']}")
            pixel = np.asarray(image.convert("RGB"))
            foreground = np.asarray(mask.convert("L")) > 0
            h = hashlib.sha256(str(pixel.shape).encode() + pixel.tobytes()).hexdigest()
        images[h].append((row["sample_id"], row["split"]))
        group = row.get("group_key") or row.get("patient_id")
        if group:
            groups[(row["dataset"], str(group))].append((row["sample_id"], row["split"]))
        samples.append({"sample_id": row["sample_id"], "dataset": row["dataset"],
                        "split": row["split"], "decoded_image_sha256": h,
                        "foreground_pixels": int(foreground.sum()), "shape": list(foreground.shape)})
    duplicates = [members for members in images.values() if len(members) > 1]
    cross_image = [members for members in duplicates if len({split for _, split in members}) > 1]
    cross_group = [members for members in groups.values() if len({split for _, split in members}) > 1]
    return {"status": "LEAKAGE_DETECTED" if cross_image or cross_group else "VALIDATED_DEVELOPMENT_ONLY",
            "samples": samples, "duplicate_image_groups": duplicates,
            "cross_split_image_groups": cross_image, "cross_split_patient_groups": cross_group,
            "test_pixel_reads": 0, "kub_category_role": "REPORTING_ONLY"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    # Reject obvious protected manifest paths before opening their metadata too.
    if any("test" in p.stem.lower() or "holdout" in p.stem.lower() for p in args.manifest):
        raise PermissionError("protected manifest names are not accepted")
    rows = []
    for path in args.manifest:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows.extend(csv.DictReader(stream))
    result = validate_rows(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    return int(result["status"] == "LEAKAGE_DETECTED")


if __name__ == "__main__":
    raise SystemExit(main())
