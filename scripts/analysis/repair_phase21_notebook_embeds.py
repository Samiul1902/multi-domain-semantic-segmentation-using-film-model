"""Post-Phase22 repair — Part A3/A4: guarantee embedded-image integrity.

Root cause established by measurement (see
``reports/audits/phase21_notebook_visual_integrity_before_repair.json`` and the
after-repair audit): the corrupted ``image/png`` payloads are ODD-LENGTH base64
strings that nevertheless end with a valid PNG terminator, i.e. they lost exactly
one character en route. ``nbformat`` write/read round-trips a long base64 string
losslessly, and the ``0x``-address normaliser does not match inside these
payloads, so the character loss happens in the kernel -> nbclient output-capture
path and is NOT a serialisation bug. It affects the LONGEST payloads only.

The only robust remedy is therefore to RE-DERIVE each embedded payload from its
source figure and write it back with ``nbformat`` directly (which is proven
lossless), then verify by strict base64 decode + PIL verify + full load.

This script:
  1. walks the notebook and, for every ``image/png`` output, identifies the
     source figure from the immediately preceding markdown label;
  2. re-encodes that source PNG with the same bounded transform the builder uses
     (so the visual content is unchanged) and overwrites the payload;
  3. re-writes the notebook via ``nbformat`` (lossless) and re-reads it;
  4. asserts every payload now decodes and verifies.

It never changes a scientific number: it only replaces a corrupt byte payload
with a valid encoding of the SAME figure file.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/repair_phase21_notebook_embeds.py
    ./.venv/Scripts/python.exe scripts/analysis/repair_phase21_notebook_embeds.py --check-only
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import nbformat  # noqa: E402
from PIL import Image  # noqa: E402

INVENTORY = ROOT / "reports/figures/phase21_global_medfilm/phase21_figure_inventory.csv"
NB_PATH = (ROOT / "notebooks/phasewise/phase_21_global_medfilm"
           / "phase21_global_medfilm_reference.ipynb")

FIG_EMBED_SAFE_B64 = 250_000
FIG_EMBED_MAX_PX = 1600
LABEL_PATH_RE = re.compile(r"`(reports/figures/[^`]+)`")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def bounded_png(path: Path, max_b64: int = FIG_EMBED_SAFE_B64,
                max_px: int = FIG_EMBED_MAX_PX) -> bytes:
    """Identical transform to the builder's ``_bounded_png``.

    Full source fidelity when the payload fits the measured-safe envelope;
    progressive downscale only for oversized payloads (multi-panel galleries).
    """
    raw = path.read_bytes()
    if len(base64.b64encode(raw)) <= max_b64:
        return raw
    with Image.open(path) as im:
        im = im.convert("RGB") if im.mode not in ("RGB", "L") else im.copy()
        scale = 1.0
        while True:
            w = max(1, int(round(im.width * scale)))
            h = max(1, int(round(im.height * scale)))
            if max(w, h) > max_px:
                scale *= 0.9
                continue
            buf = io.BytesIO()
            im.resize((w, h), Image.LANCZOS).save(buf, format="PNG", optimize=True)
            data = buf.getvalue()
            if len(base64.b64encode(data)) <= max_b64 or scale < 0.2:
                return data
            scale *= 0.85


def strict_decode(payload) -> tuple[bytes | None, str]:
    if isinstance(payload, list):
        payload = "".join(payload)
    if not isinstance(payload, str) or not payload:
        return None, "EMPTY"
    try:
        return base64.b64decode(payload, validate=True), ""
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def verify(raw: bytes) -> str:
    try:
        Image.open(io.BytesIO(raw)).verify()
        Image.open(io.BytesIO(raw)).load()
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    nb = nbformat.read(str(NB_PATH), as_version=4)
    changes, problems = [], []

    for ci, cell in enumerate(nb.cells):
        if cell.get("cell_type") != "code":
            continue
        label = ""
        for o in cell.get("outputs", []) or []:
            d = (o.get("data") or {})
            if "text/markdown" in d:
                md = d["text/markdown"]
                label = "".join(md) if isinstance(md, list) else str(md)
            if "image/png" not in d:
                continue
            raw, err = strict_decode(d["image/png"])
            verr = verify(raw) if raw else err
            if raw and not verr:
                continue                              # already healthy
            m = LABEL_PATH_RE.search(label)
            if not m:
                problems.append({"cell_index": ci,
                                 "issue": "NO_SOURCE_PATH_IN_LABEL",
                                 "label": label[:160],
                                 "error": err or ""})
                continue
            src = ROOT / m.group(1)
            if not src.exists():
                problems.append({"cell_index": ci, "issue": "SOURCE_MISSING",
                                 "source": m.group(1)})
                continue
            new_raw = bounded_png(src)
            new_b64 = base64.b64encode(new_raw).decode("ascii")
            assert len(new_b64) % 4 == 0
            # verify the replacement decodes and loads before committing
            assert not verify(base64.b64decode(new_b64)), "replacement invalid"
            changes.append({
                "cell_index": ci, "source": m.group(1),
                "old_base64_length": len(d["image/png"]) if isinstance(d["image/png"], str) else -1,
                "old_was_multiple_of_4": (len(d["image/png"]) % 4 == 0)
                if isinstance(d["image/png"], str) else False,
                "old_error": err or verr,
                "new_base64_length": len(new_b64),
                "old_sha256_decoded": sha(raw) if raw else None,
                "new_sha256_decoded": sha(new_raw),
            })
            if not args.check_only:
                d["image/png"] = new_b64

    print(f"cells requiring payload repair: {len(changes)}")
    for c in changes:
        print(f"  cell {c['cell_index']:>3} old_len={c['old_base64_length']:>8} "
              f"mult4={c['old_was_multiple_of_4']} -> new_len={c['new_base64_length']:>8} "
              f"| {c['source']}")
    if problems:
        print("UNRESOLVED PROBLEMS:")
        for p in problems:
            print("  ", p)

    if args.check_only:
        return 1 if (changes or problems) else 0

    if changes:
        nbformat.write(nb, str(NB_PATH))

    # ---- hard post-write verification (re-read from disk) ------------------ #
    back = nbformat.read(str(NB_PATH), as_version=4)
    n_img = valid = 0
    bad = []
    for ci, cell in enumerate(back.cells):
        for o in cell.get("outputs", []) or []:
            d = (o.get("data") or {})
            if "image/png" not in d:
                continue
            n_img += 1
            raw, err = strict_decode(d["image/png"])
            verr = verify(raw) if raw else err
            if raw and not verr:
                valid += 1
            else:
                bad.append({"cell_index": ci, "error": err or verr})
    print()
    print(f"POST-WRITE: image/png outputs={n_img} valid={valid} invalid={len(bad)}")
    for b in bad[:10]:
        print("   INVALID", b)
    print("notebook sha256:", sha(NB_PATH.read_bytes()))
    return 0 if (valid == n_img and not bad and not problems) else 2


if __name__ == "__main__":
    raise SystemExit(main())
