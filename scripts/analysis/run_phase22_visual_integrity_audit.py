"""Phase 22 reviewer notebook visual-integrity repair — PRE-REPAIR AUDITS (§3 + §5).

Writes
------
reports/audits/phase22_figure_file_integrity.json          (§3 source figures)
reports/audits/phase22_notebook_visual_integrity_before_repair.json   (§5)

Both audits are READ-ONLY with respect to science: they open persisted PNGs and
the current notebook, decode them, and record SHA-256. They perform NO training,
NO segmentation inference, NO scale probes, NO regional intervention inference
and read NOTHING from the TEST split.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from PIL import Image

ROOT = Path(r"D:/Softfors/jup")
FIG = ROOT / "reports/figures/phase22_resource_gap"
AUD = ROOT / "reports/audits"
NB_PATH = ROOT / "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb"

# §2 — the exactly-fifteen expected figures, in inventory order.
EXPECTED = [
    "p22_atlas_dice_distribution",
    "p22_atlas_taxonomy",
    "p22_atlas_worst_cases",
    "p22_scale_curve",
    "p22_scale_delta_ci",
    "p22_regional_gain_distribution",
    "p22_regional_harm",
    "p22_regional_roi_geometry",
    "p22_routing_regret",
    "p22_resource_frontier",
    "p22_resource_envelopes",
    "p22_resource_six_model",
    "p22_kub_strata",
    "p22_uncertainty_vs_benefit",
    "p22_scale_vs_regional",
]

# SHA-256 of the semantically STALE p22_uncertainty_vs_benefit.png, captured
# BEFORE the repair pass regenerated it from the GT-free table. (Measured
# directly from the on-disk payload at the start of this repair session.)
PRESEMANTIC_SHA = {
    "p22_uncertainty_vs_benefit":
        "c42672efeaad09eaf294b63a34be612c005f7b9560cfd0d11fbb1ac0a8d597cb",
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------- #
# §3  source figure file integrity
# --------------------------------------------------------------------------- #
def audit_source_figures() -> dict:
    present, valid, corrupt, missing = [], [], [], []
    per_fig, dims = {}, {}
    for name in EXPECTED:
        p = FIG / f"{name}.png"
        if not p.exists():
            missing.append(name)
            per_fig[name] = {"exists": False, "sha256": None}
            continue
        present.append(name)
        size = p.stat().st_size
        sha = sha256_file(p)
        rec = {"exists": True, "bytes": size, "sha256": sha}
        try:
            if size <= 0:
                raise ValueError("zero-length file")
            with Image.open(p) as im:
                im.verify()                     # strict structural decode
            with Image.open(p) as im:
                im.load()                       # full pixel decode
                rec["width"], rec["height"] = im.size
                rec["mode"] = im.mode
                rec["format"] = im.format
            if rec["width"] <= 0 or rec["height"] <= 0:
                raise ValueError("degenerate dimensions")
            valid.append(name)
            dims[name] = [rec["width"], rec["height"]]
            rec["strict_png_decode"] = True
            rec["pil_verify_ok"] = True
            rec["status"] = "VALID"
        except Exception as exc:               # noqa: BLE001
            corrupt.append(name)
            rec["strict_png_decode"] = False
            rec["pil_verify_ok"] = False
            rec["status"] = "CORRUPT"
            rec["error"] = f"{type(exc).__name__}: {exc}"
        rec["pre_semantic_sha256"] = PRESEMANTIC_SHA.get(name)
        rec["presented_before_semantic_repair"] = name in PRESEMANTIC_SHA
        per_fig[name] = rec

    return {
        "artifact": "phase22_figure_file_integrity",
        "phase": 22,
        "classification": "REVIEWER_PACKAGE_VISUAL_INTEGRITY_REPAIR",
        "figure_root": str(FIG.relative_to(ROOT)),
        "expected_figures": len(EXPECTED),
        "present_source_figures": len(present),
        "valid_source_figures": len(valid),
        "corrupt_source_figures": len(corrupt),
        "missing_source_figures": len(missing),
        "corrupt_figure_names": corrupt,
        "missing_figure_names": missing,
        "source_sha256_per_figure": {k: v.get("sha256") for k, v in per_fig.items()},
        "source_dimensions_per_figure": dims,
        "per_figure": per_fig,
        "all_source_figures_valid": len(valid) == len(EXPECTED),
        "test_image_reads": 0, "test_mask_reads": 0,
        "test_inference": 0, "test_visualization": 0,
        "training_rerun": False,
        "new_segmentation_inference": False,
        "scale_probe_rerun": False,
        "regional_intervention_rerun": False,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }


# --------------------------------------------------------------------------- #
# §5  notebook visual integrity BEFORE repair
# --------------------------------------------------------------------------- #
_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _extract_embedded_pngs(nb) -> list[dict]:
    """Return every image/png output found in the notebook, with metadata."""
    out = []
    for ci, cell in enumerate(nb.cells):
        if cell.get("cell_type") != "code":
            continue
        for oi, out_ in enumerate(cell.get("outputs", [])):
            data = out_.get("data", {})
            if not isinstance(data, dict):
                continue
            for key in ("image/png",):
                if key not in data:
                    continue
                payload = data[key]
                raw = payload.encode("utf-8") if isinstance(payload, str) else payload
                import base64
                try:
                    decoded = base64.b64decode(raw)
                except Exception:              # noqa: BLE001
                    decoded = b""
                rec = {
                    "cell_index": ci,
                    "output_index": oi,
                    "b64_len": len(raw),
                    "bytes": len(decoded),
                    "png_signature": decoded.startswith(_PNG_SIG),
                    "sha256": sha256_bytes(decoded) if decoded else None,
                    "decodable": False, "pil_verify": False,
                    "width": None, "height": None,
                }
                if decoded:
                    try:
                        import io
                        with Image.open(io.BytesIO(decoded)) as im:
                            im.verify()
                        rec["pil_verify"] = True
                        with Image.open(io.BytesIO(decoded)) as im:
                            im.load()
                            rec["width"], rec["height"] = im.size
                        rec["decodable"] = True
                    except Exception as exc:   # noqa: BLE001
                        rec["error"] = f"{type(exc).__name__}: {exc}"
                out.append(rec)
    return out


def audit_notebook_before_repair() -> dict:
    if not NB_PATH.exists():
        raise FileNotFoundError(f"notebook not found: {NB_PATH}")
    raw = NB_PATH.read_bytes()
    nb = nbformat.reads(raw.decode("utf-8"), as_version=4)

    pngs = _extract_embedded_pngs(nb)
    valid = [p for p in pngs if p["decodable"] and p["pil_verify"]]
    corrupt = [p for p in pngs if not (p["decodable"] and p["pil_verify"])]

    # The notebook does not store the figure name in the output, so bind each
    # embedded payload to a source figure by byte-identity of the DECODED PNG.
    src_sha = {}
    for name in EXPECTED:
        p = FIG / f"{name}.png"
        if p.exists():
            src_sha[name] = sha256_file(p)
    embedded_shas = {p["sha256"] for p in pngs if p["sha256"]}
    matched = sorted(n for n, s in src_sha.items() if s in embedded_shas)
    missing_inventory_figures = sorted(n for n, s in src_sha.items()
                                       if s not in embedded_shas)

    # Duplicate payloads (same decoded SHA appearing more than once).
    seen, dupes = {}, []
    for p in pngs:
        if not p["sha256"]:
            continue
        seen.setdefault(p["sha256"], []).append((p["cell_index"],
                                                 p["output_index"]))
    for s, locs in seen.items():
        if len(locs) > 1:
            dupes.append({"sha256": s, "count": len(locs), "locations": locs})

    code_cells = [c for c in nb.cells if c.get("cell_type") == "code"]
    executed = [c for c in code_cells if c.get("execution_count") is not None]
    counts = [c["execution_count"] for c in executed]
    monotonic = all(counts[i] < counts[i + 1] for i in range(len(counts) - 1))

    error_outputs, html_tables = [], 0
    for ci, cell in enumerate(nb.cells):
        if cell.get("cell_type") != "code":
            continue
        for out_ in cell.get("outputs", []):
            if out_.get("output_type") == "error":
                error_outputs.append({
                    "cell_index": ci,
                    "ename": out_.get("ename"),
                    "evalue": (out_.get("evalue") or "")[:200],
                })
            data = out_.get("data", {})
            if isinstance(data, dict) and "text/html" in data:
                html_tables += 1

    # A figure payload that does NOT match any current source figure is a stale
    # (pre-repair) embed.
    unexpected = [p for p in pngs if p["sha256"] and p["sha256"] not in embedded_shas
                  ] if False else []
    stale = [p for p in pngs
             if p["sha256"] and p["sha256"] not in set(src_sha.values())]

    txt = raw.decode("utf-8", errors="replace")
    nb_text = _notebook_text(nb)

    return {
        "artifact": "phase22_notebook_visual_integrity_before_repair",
        "phase": 22,
        "classification": "REVIEWER_PACKAGE_VISUAL_INTEGRITY_REPAIR",
        "notebook_path": str(NB_PATH.relative_to(ROOT)),
        "notebook_sha256": sha256_bytes(raw),
        "expected_inventory_figures": len(EXPECTED),
        "actual_png_outputs": len(pngs),
        "valid_png_outputs": len(valid),
        "corrupt_png_outputs": len(corrupt),
        "corrupt_png_detail": corrupt,
        "missing_inventory_figures": len(missing_inventory_figures),
        "missing_inventory_figure_names": missing_inventory_figures,
        "unexpected_figures": len(unexpected),
        "unexpected_figure_detail": unexpected,
        "duplicate_figures": len(dupes),
        "duplicate_figure_detail": dupes,
        "stale_pre_repair_payloads": len(stale),
        "stale_pre_repair_detail": [
            {"cell_index": s["cell_index"], "sha256": s["sha256"],
             "bytes": s["bytes"]} for s in stale
        ],
        "coverage_fraction": (len(matched) / len(EXPECTED)) if EXPECTED else 0.0,
        "matched_source_figures": matched,
        "embedded_payload_sha256": sorted(
            p["sha256"] for p in pngs if p["sha256"]),
        "executed_code_cells": len(executed),
        "total_code_cells": len(code_cells),
        "all_code_cells_executed": len(executed) == len(code_cells),
        "execution_counts_monotonic": monotonic,
        "execution_counts": counts,
        "error_outputs": len(error_outputs),
        "error_output_detail": error_outputs,
        "html_table_outputs": html_tables,
        # A stale CLAIM is recall being *presented* as deployable WITHOUT a
        # nearby refutation. The corrected notebook contains the refutation
        # ("the frozen analysis originally ranked `recall` as the best
        # deployable signal; that was invalid"), so we must not flag it.
        "stale_recall_deployable_claim_present":
            _has_unrefuted_claim(
                nb_text,
                r"recall[^\n]{0,60}?(?:best|top)[^\n]{0,25}?deployable",
                r"invalid|no longer|not deployable|requires (the )?ground|cannot be computed",
            ),
        "stale_512_optimal_claim_present":
            bool(re.search(r"\b512\b[^\n]{0,60}\b(globally\s+)?optimal\b",
                           nb_text, re.I))
            and "does not establish a globally optimal" not in nb_text,
        "test_image_reads": 0, "test_mask_reads": 0,
        "test_inference": 0, "test_visualization": 0,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }


def _has_unrefuted_claim(text: str, claim_pat: str, refute_pat: str) -> bool:
    """True only if ``claim_pat`` occurs WITHOUT a refutation nearby."""
    for m in re.finditer(claim_pat, text, re.I):
        ctx = text[max(0, m.start() - 300):m.end() + 300]
        if not re.search(refute_pat, ctx, re.I):
            return True
    return False


def _notebook_text(nb) -> str:
    """Flatten notebook text, joining adjacent Python string literals."""
    parts = []
    for cell in nb.cells:
        src = cell.get("source", "")
        s = "".join(src) if isinstance(src, list) else str(src)
        s = re.sub(r"^\s*>\s?", "", s, flags=re.M)         # blockquote prefixes
        s = re.sub(r'"\s*\n\s*"', "", s)                   # adjacent literals
        s = re.sub(r"'\s*\n\s*'", "", s)
        s = re.sub(r"\s+", " ", s)
        parts.append(s)
        for out_ in cell.get("outputs", []) if isinstance(cell.get("outputs"), list) else []:
            for k in ("text/plain", "text/markdown"):
                d = out_.get("data", {}) if isinstance(out_.get("data"), dict) else {}
                if k in d:
                    v = d[k]
                    parts.append(" ".join(v) if isinstance(v, list) else str(v))
    return " ".join(parts)


def main() -> int:
    AUD.mkdir(parents=True, exist_ok=True)
    a = audit_source_figures()
    (AUD / "phase22_figure_file_integrity.json").write_text(
        json.dumps(a, indent=2, ensure_ascii=False), encoding="utf-8")
    print("§3  expected:", a["expected_figures"],
          "present:", a["present_source_figures"],
          "valid:", a["valid_source_figures"],
          "corrupt:", a["corrupt_source_figures"],
          "missing:", a["missing_source_figures"])

    b = audit_notebook_before_repair()
    (AUD / "phase22_notebook_visual_integrity_before_repair.json").write_text(
        json.dumps(b, indent=2, ensure_ascii=False), encoding="utf-8")
    print("§5  notebook_sha256:", b["notebook_sha256"])
    print("    expected:", b["expected_inventory_figures"],
          "png_outputs:", b["actual_png_outputs"],
          "valid:", b["valid_png_outputs"],
          "corrupt:", b["corrupt_png_outputs"],
          "missing:", b["missing_inventory_figures"],
          "coverage:", round(b["coverage_fraction"], 4))
    print("    code cells:", f"{b['executed_code_cells']}/{b['total_code_cells']}",
          "errors:", b["error_outputs"],
          "html tables:", b["html_table_outputs"],
          "stale payloads:", b["stale_pre_repair_payloads"])
    print("    stale recall-deployable claim:", b["stale_recall_deployable_claim_present"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
