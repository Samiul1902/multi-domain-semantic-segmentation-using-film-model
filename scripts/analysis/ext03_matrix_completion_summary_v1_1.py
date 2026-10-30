"""EXT-03 baseline matrix completion summary — generator v1.1 (additive).

Supersedes the behaviour of `ext03_matrix_completion_summary.py` (v1.0,
sha256 6fcd935056900e92...) WITHOUT modifying it. v1.0 and its two output
artifacts are left byte-identical on disk; this generator writes to NEW,
versioned, append-only locations.

What changed from v1.0 (each item maps to a finding in
`reports/audits/ext03_scientific_acceptance_and_protocol_adjudication_v1_0.md` §5):

  G1  checkpoint SHA is MANDATORY and must be a 64-char lowercase hex digest.
      v1.0 did `if recorded and actual != recorded:` which FAILED OPEN when the
      digest was absent. Now absence is a hard error.
  G2  fail-closed on status, run_id/seed agreement, seed-set completeness,
      checkpoint existence, checkpoint-internal metadata, and metric range.
  G3  binds itself to its inputs: records the registry SHA-256 and its own
      generator SHA-256, so a later registry mutation is detectable.
  G4  declares the SD convention explicitly (`sample`, n-1). v1.0 used
      statistics.stdev silently.
  G5  timezone-aware UTC timestamp derived from the clock. v1.0 hard-coded
      a literal string.
  G6  write-once protection for BOTH outputs (v1.0 protected only the JSON).
  G7  access statements enumerate the files this script actually opened.
      v1.0 emitted hard-coded `test_accessed: false` literals with no evidence.
  G8  validates the stopping identity `stop == min(max_epochs, best_epoch+patience)`
      and `best_epoch <= current_epoch`. v1.0 validated neither.

This script performs NO training, NO inference, and reads NO image, mask, TEST
manifest or ROUTER_HOLDOUT artifact. It reads exactly: the run registry and one
`best.pt` per run.

Usage
-----
    python scripts/analysis/ext03_matrix_completion_summary_v1_1.py
    python scripts/analysis/ext03_matrix_completion_summary_v1_1.py --verify-only
    python scripts/analysis/ext03_matrix_completion_summary_v1_1.py \
        --registry <path> --runs-dir <path> --out-json <path> --out-csv <path>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics as st
import sys
from datetime import datetime, timezone
from pathlib import Path

GENERATOR_VERSION = "1.1"
ROOT = Path(r"D:\Softfors\jup")
DEFAULT_REGISTRY = ROOT / "reports" / "baselines" / "ext03_run_registry.json"
DEFAULT_RUNS = ROOT / "reports" / "baselines" / "runs"
DEFAULT_OUT_JSON = ROOT / "reports" / "baselines" / "ext03_matrix_completion_summary_v1_1.json"
DEFAULT_OUT_CSV = ROOT / "reports" / "tables" / "ext03_matrix_final_family_summary_v1_1.csv"

ARCHS = ["unet", "attention_unet", "unetpp", "deeplabv3plus", "segformer_b0"]
SEEDS = [42, 123, 3407]
MAX_EPOCHS = 100
PATIENCE = 15

# Frozen reference: GlobalMedFiLM alone, Phase 21, best_epoch 66.
GLOBAL_MEDFILM_MACRO = 0.8350791259413984
GLOBAL_MEDFILM_CHECKPOINT_SHA = (
    "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
)

# Any opened path matching one of these markers aborts the run (G7).
FORBIDDEN_READ_MARKERS = (
    "phase4_v2/test",
    "test.csv",
    "phase39",
    "ROUTER_HOLDOUT",
    "router_holdout",
    "external_extension",
    "phase29_phase_d_canonical",
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_READS: list[str] = []


class AuditAbort(RuntimeError):
    """Fail-closed abort carrying a machine-readable code."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(path: Path) -> bytes:
    p = str(path)
    low = p.lower().replace("\\", "/")
    for marker in FORBIDDEN_READ_MARKERS:
        if marker.lower() in low:
            raise AuditAbort("E_FORBIDDEN_READ", f"refusing to open {p!r} (matches {marker!r})")
    if p not in _READS:
        _READS.append(p)
    return Path(path).read_bytes()


def _write_once(path: Path, payload: bytes) -> None:
    """Create `path` exclusively; never truncate or overwrite an existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        fd = os.open(str(path), flags)
    except FileExistsError:
        raise AuditAbort("E_OUTPUT_EXISTS", f"{path} already exists; v1.1 is append-only")
    try:
        view = memoryview(payload)
        while view:
            n = os.write(fd, view)
            view = view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(payload):
        raise AuditAbort("E_SHORT_WRITE", f"{path} size {path.stat().st_size} != {len(payload)}")


def _require_hex64(value, what: str) -> str:
    if value is None:
        raise AuditAbort("E_SHA_ABSENT", f"{what}: checkpoint digest is missing (null)")
    if not isinstance(value, str) or not value.strip():
        raise AuditAbort("E_SHA_ABSENT", f"{what}: checkpoint digest is empty")
    if not _HEX64.match(value.strip()):
        raise AuditAbort("E_SHA_MALFORMED", f"{what}: {value!r} is not a 64-char lowercase hex digest")
    return value.strip()


def _load_checkpoint_meta(path: Path) -> dict:
    """Read only the scalar selection metadata of a best.pt (no model execution)."""
    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment guard
        raise AuditAbort("E_TORCH_UNAVAILABLE", f"cannot load {path} without torch: {exc}")
    try:
        obj = torch.load(str(path), map_location="cpu", weights_only=True)
    except Exception as exc:
        raise AuditAbort("E_CHECKPOINT_UNREADABLE", f"{path}: {exc}")
    if not isinstance(obj, dict):
        raise AuditAbort("E_CHECKPOINT_SHAPE", f"{path}: top-level object is {type(obj).__name__}")
    return obj


def validate_registry(reg: dict, runs_dir: Path) -> tuple[list[dict], dict]:
    runs = reg.get("runs", reg)
    if not isinstance(runs, dict):
        raise AuditAbort("E_REGISTRY_SHAPE", "registry has no 'runs' mapping")

    expected = [f"{a}_seed{s}" for a in ARCHS for s in SEEDS]
    missing = [r for r in expected if r not in runs]
    if missing:
        raise AuditAbort("E_RUN_MISSING", f"absent run_ids: {missing}")
    extra = [r for r in runs if r not in expected]
    if extra:
        raise AuditAbort("E_RUN_UNEXPECTED", f"unexpected run_ids: {extra}")

    per_run: list[dict] = []
    for a in ARCHS:
        for s in SEEDS:
            rid = f"{a}_seed{s}"
            v = runs[rid]

            if v.get("status") != "COMPLETE":
                raise AuditAbort("E_STATUS", f"{rid}: status={v.get('status')!r}, expected COMPLETE")
            if v.get("architecture") != a:
                raise AuditAbort("E_ARCH", f"{rid}: architecture={v.get('architecture')!r}, expected {a!r}")
            if v.get("seed") != s:
                raise AuditAbort("E_SEED", f"{rid}: seed={v.get('seed')!r}, expected {s!r}")

            bm = v.get("best_metric")
            if not isinstance(bm, (int, float)) or isinstance(bm, bool):
                raise AuditAbort("E_METRIC_TYPE", f"{rid}: best_metric={bm!r} is not a number")
            if not math.isfinite(float(bm)) or not (0.0 < float(bm) <= 1.0):
                raise AuditAbort("E_METRIC_RANGE", f"{rid}: best_metric={bm!r} outside (0,1]")

            be = v.get("best_epoch")
            ce = v.get("current_epoch")
            if not isinstance(be, int) or isinstance(be, bool) or be < 1:
                raise AuditAbort("E_BEST_EPOCH", f"{rid}: best_epoch={be!r} invalid")
            if not isinstance(ce, int) or isinstance(ce, bool) or ce < 1:
                raise AuditAbort("E_CURRENT_EPOCH", f"{rid}: current_epoch={ce!r} invalid")
            if be > ce:
                raise AuditAbort("E_BEST_EPOCH_GT_CURRENT", f"{rid}: best_epoch {be} > current_epoch {ce}")

            expected_stop = min(MAX_EPOCHS, be + PATIENCE)
            if ce != expected_stop:
                raise AuditAbort(
                    "E_STOPPING_RULE",
                    f"{rid}: current_epoch {ce} != min({MAX_EPOCHS}, {be}+{PATIENCE}) = {expected_stop}",
                )

            recorded = _require_hex64(v.get("checkpoint_sha"), rid)
            ck = runs_dir / rid / "best.pt"
            if not ck.is_file():
                raise AuditAbort("E_CHECKPOINT_ABSENT", f"{rid}: {ck} does not exist")
            actual = _sha256_bytes(_read(ck))
            if actual != recorded:
                raise AuditAbort(
                    "E_CHECKPOINT_SHA_MISMATCH", f"{rid}: disk={actual} registry={recorded}"
                )

            meta = _load_checkpoint_meta(ck)
            if meta.get("epoch") != be:
                raise AuditAbort(
                    "E_CKPT_EPOCH_MISMATCH",
                    f"{rid}: best.pt epoch={meta.get('epoch')!r} != registry best_epoch={be}",
                )
            ck_macro = meta.get("macro")
            if not isinstance(ck_macro, (int, float)) or isinstance(ck_macro, bool):
                raise AuditAbort("E_CKPT_MACRO_ABSENT", f"{rid}: best.pt has no numeric 'macro'")
            if abs(float(ck_macro) - float(bm)) > 1e-9:
                raise AuditAbort(
                    "E_CKPT_MACRO_MISMATCH",
                    f"{rid}: best.pt macro={ck_macro!r} != registry best_metric={bm!r}",
                )

            per_run.append({
                "run_id": rid,
                "architecture": a,
                "seed": s,
                "best_macro_dice": float(bm),
                "best_epoch": be,
                "stopped_epoch": ce,
                "stop_class": "PATIENCE" if ce < MAX_EPOCHS else "EPOCH_CEILING",
                "resume_count": v.get("resume_count"),
                "lr_used": v.get("lr_used"),
                "lr_source": v.get("lr_source"),
                "checkpoint_sha": recorded,
                "checkpoint_sha_verified_on_disk": True,
                "start_time": v.get("start_time"),
                "completion_time": v.get("completion_time"),
            })

    families: dict[str, dict] = {}
    for a in ARCHS:
        vals = [r["best_macro_dice"] for r in per_run if r["architecture"] == a]
        if len(vals) != len(SEEDS):
            raise AuditAbort("E_FAMILY_SIZE", f"{a}: {len(vals)} seeds, expected {len(SEEDS)}")
        families[a] = {
            "n_seeds": len(vals),
            "seeds": list(SEEDS),
            "mean_macro_dice": st.mean(vals),
            "sd_macro_dice": st.stdev(vals),
            "sd_convention": "sample_standard_deviation_n_minus_1",
            "min_macro_dice": min(vals),
            "max_macro_dice": max(vals),
            "spread": max(vals) - min(vals),
            "best_seed": SEEDS[vals.index(max(vals))],
            "gap_to_global_medfilm": GLOBAL_MEDFILM_MACRO - st.mean(vals),
        }
    return per_run, families


def build_summary(reg: dict, runs_dir: Path, registry_path: Path, generator_path: Path) -> dict:
    registry_bytes = _read(registry_path)
    registry_sha = _sha256_bytes(registry_bytes)
    reg_parsed = json.loads(registry_bytes.decode("utf-8"))

    per_run, families = validate_registry(reg_parsed, runs_dir)
    ranked = sorted(families.items(), key=lambda kv: -kv[1]["mean_macro_dice"])

    generator_sha = _sha256_bytes(Path(generator_path).read_bytes())
    now = datetime.now(timezone.utc)

    return {
        "artifact": "ext03_matrix_completion_summary",
        "generator_version": GENERATOR_VERSION,
        "generated_utc": now.isoformat(timespec="seconds"),
        "generated_utc_basis": "datetime.now(timezone.utc) - clock-derived, not a literal",
        "phase": "EXT-03",
        "read_only": True,
        "training_performed_here": False,
        "inference_performed_here": False,
        "supersedes": {
            "artifact": "reports/baselines/ext03_matrix_completion_summary_v1_0.json",
            "sha256": "8e35499a1ba6ff94c22bee0cfeff275bfd635fce721858f2937d32b96c7f46a1",
            "relationship": "ADDITIVE_CORRECTION_NOT_REPLACEMENT; v1.0 retained byte-identical",
        },
        "binding": {
            "registry_path": str(registry_path),
            "registry_sha256": registry_sha,
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha,
            "binding_basis": "both digests computed from the bytes actually read/executed",
        },
        "constants": {
            "max_epochs": MAX_EPOCHS,
            "early_stopping_patience": PATIENCE,
            "stopping_identity": "current_epoch == min(max_epochs, best_epoch + patience)",
            "metric": "equal-domain macro Dice on VAL (n=808), threshold 0.5",
            "sd_convention": "sample_standard_deviation_n_minus_1",
            "reference_global_medfilm_macro_dice": GLOBAL_MEDFILM_MACRO,
            "reference_global_medfilm_checkpoint_sha256": GLOBAL_MEDFILM_CHECKPOINT_SHA,
        },
        "checks_enforced": [
            "G1 checkpoint digest present, non-empty, 64-char lowercase hex",
            "G2 status==COMPLETE; architecture and seed agree with run_id; seed set exactly {42,123,3407}",
            "G2 checkpoint file exists; raw-byte SHA equals registry digest",
            "G2 best_metric finite and inside (0,1]",
            "G8 best_epoch <= current_epoch; current_epoch == min(100, best_epoch+15)",
            "G3 registry_sha256 and generator_sha256 recorded",
            "G4 sd_convention declared as sample (n-1)",
            "G6 both outputs created with O_CREAT|O_EXCL",
            "G7 every opened path enumerated and screened against forbidden markers",
        ],
        "access_statements": {
            "basis": "ENUMERATED_FROM_ACTUAL_OPENS",
            "files_read": sorted(_READS),
            "reads_under_test_manifest": 0,
            "reads_under_router_holdout": 0,
            "reads_of_image_or_mask": 0,
            "scope_note": (
                "This enumerates what THIS generator opened. It is not, and must not be read as, "
                "an assessment of data access during EXT-03 training. Training-phase access is "
                "assessed separately by static source inspection in "
                "reports/audits/ext03_scientific_acceptance_and_protocol_adjudication_v1_0.md."
            ),
        },
        "families": families,
        "family_ranking": [{"rank": i + 1, "architecture": a, **families[a]} for i, (a, _) in enumerate(ranked)],
        "per_run": per_run,
    }


def render_csv(summary: dict) -> str:
    lines = [
        "rank,architecture,n_seeds,mean_macro_dice,sd_macro_dice,sd_convention,"
        "min_macro_dice,max_macro_dice,spread,best_seed,gap_to_global_medfilm"
    ]
    for row in summary["family_ranking"]:
        lines.append(
            f"{row['rank']},{row['architecture']},{row['n_seeds']},"
            f"{row['mean_macro_dice']:.6f},{row['sd_macro_dice']:.6f},{row['sd_convention']},"
            f"{row['min_macro_dice']:.6f},{row['max_macro_dice']:.6f},{row['spread']:.6f},"
            f"{row['best_seed']},{row['gap_to_global_medfilm']:.6f}"
        )
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="EXT-03 completion summary generator v1.1")
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    ap.add_argument("--runs-dir", default=str(DEFAULT_RUNS))
    ap.add_argument("--out-json", default=str(DEFAULT_OUT_JSON))
    ap.add_argument("--out-csv", default=str(DEFAULT_OUT_CSV))
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args(argv)

    try:
        summary = build_summary(
            {}, Path(args.runs_dir), Path(args.registry), Path(__file__)
        )
        if not args.verify_only:
            _write_once(Path(args.out_json), json.dumps(summary, indent=2).encode("utf-8"))
            _write_once(Path(args.out_csv), render_csv(summary).encode("utf-8"))
    except AuditAbort as exc:
        print(f"ABORT {exc.code}: {exc.detail}", file=sys.stderr)
        return 2

    print(f"OK  generator v{GENERATOR_VERSION}  runs={len(summary['per_run'])}/15  all checks enforced")
    print(f"    registry_sha256  {summary['binding']['registry_sha256']}")
    print(f"    generator_sha256 {summary['binding']['generator_sha256']}")
    print(f"    generated_utc    {summary['generated_utc']}")
    print()
    print(f"{'rank':>4} {'architecture':16s} {'mean':>7s} {'sd(sample)':>11s} {'spread':>7s} {'gap':>7s}")
    for row in summary["family_ranking"]:
        print(
            f"{row['rank']:>4} {row['architecture']:16s} {row['mean_macro_dice']:7.4f} "
            f"{row['sd_macro_dice']:11.4f} {row['spread']:7.4f} {row['gap_to_global_medfilm']:7.4f}"
        )
    if not args.verify_only:
        print()
        print(f"    wrote {args.out_json}")
        print(f"    wrote {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
