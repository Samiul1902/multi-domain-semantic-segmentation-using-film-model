"""Generator: Phase36 robustness-science v1.15 from frozen v1.14.

Deterministic, minimal-source transformation.  Applies EXACTLY TWO scientific-semantic
repairs and nothing else:

REPAIR 1 (D61):  ACCEPT fusion call -> canonical Phase27 fuse_full_field(p_global, refined, geom)
REPAIR 2 (D75/POLICY_B): every authoritative segmentation binary path thresholds the
                 float16-recast float32 representation (live f32 -> f16 -> f32 -> >= 0.50),
                 via ONE helper `_phase27_scored_final_binary`, used by BOTH the central
                 core binary producer and the clean evaluation.

All other content is copied byte-for-byte from v1.14.

Run:  python build_phase36_robustness_execution_v1_15.py
Writes (write-once):  scripts/analysis/phase36_robustness_execution_v1_15.py
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
OUT = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_15.py"

SRC_SHA_EXPECTED = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"

# ---- exact anchors (each MUST be unique in v1.14) ------------------------- #
A_FUSION = "        fused = system._fuse_global_with_regional(p_global, refined, window)"
A_CORE_BIN = (
    '    res["final_binary"] = (prob >= float(system.segmentation_output_threshold)).astype(np.float32)'
)
A_CLEAN_BIN = (
    "    final_binary = (final_prob >= SEGMENTATION_OUTPUT_THRESHOLD).astype(np.float32)"
)
A_THRESHOLD_ANCHOR = "SEGMENTATION_OUTPUT_THRESHOLD = 0.50"

# ---- replacement blocks --------------------------------------------------- #
R_FUSION = (
    "        # v1.15 REPAIR 1 (D61): canonical Phase27 pad-aware ACCEPT fusion.\n"
    "        fused = fuse_full_field(p_global, refined, geom)"
)
R_CORE_BIN = (
    '    res["final_binary"] = _phase27_scored_final_binary(prob)'
)
R_CLEAN_BIN = (
    "    final_binary = _phase27_scored_final_binary(final_prob)"
)

# POLICY_B helper inserted immediately after the SEGMENTATION_OUTPUT_THRESHOLD line.
POLICY_B_HELPER = '''SEGMENTATION_OUTPUT_THRESHOLD = 0.50


# --------------------------------------------------------------------------- #
# v1.15 REPAIR 2 (D75 / POLICY_B): AUTHORITATIVE segmentation scoring.
#
# The historical Phase27 Phase-B scored authority thresholds the PERSISTED float16
# representation recast up to float32 (f16 -> f32 -> >= 0.50).  v1.14 clean scoring
# thresholded the LIVE float32 value, which diverges at the f16==0.5 boundary.
#
# v1.15 makes the authoritative scored binary representation = live f32 -> f16 ->
# f32 -> >= 0.50, UNIFORMLY for clean and ALL perturbation conditions.  This is a
# SCORING-REPRESENTATION change ONLY: the live `out["final_probability"]` remains
# the canonical live float32 and is NEVER fed back into router / ROI / R_psi /
# S_omega / fusion / safety / geometry / proposal generation.
# --------------------------------------------------------------------------- #
def _phase27_scored_final_binary(p_final_live):
    """POLICY_B authoritative segmentation binary.

    LIVE FLOAT32 -> FLOAT16 -> FLOAT32 -> >= SEGMENTATION_OUTPUT_THRESHOLD (0.50).
    """
    p = np.asarray(p_final_live, dtype=np.float32)
    p_f16 = p.astype(np.float16)
    p_scored = p_f16.astype(np.float32)
    return (p_scored >= np.float32(SEGMENTATION_OUTPUT_THRESHOLD)).astype(np.float32)
'''


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_once(path: Path, payload: bytes) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags)
    try:
        written = 0
        while written < len(payload):
            n = os.write(fd, payload[written:])
            if n <= 0:
                raise IOError("short write")
            written += n
        os.fsync(fd)
    finally:
        os.close(fd)
    st = os.stat(str(path))
    if st.st_size != len(payload):
        raise IOError(f"post-write size mismatch {st.st_size} != {len(payload)}")


def main() -> int:
    if OUT.exists():
        print(f"REFUSE_OVERWRITE: {OUT} already exists")
        return 2

    src_bytes = SRC.read_bytes()
    src_sha = sha256_bytes(src_bytes)
    if src_sha != SRC_SHA_EXPECTED:
        print(f"FAIL_CLOSED: v1.14 sha mismatch {src_sha} != {SRC_SHA_EXPECTED}")
        return 3

    text = src_bytes.decode("utf-8")

    # Require each anchor to be present EXACTLY ONCE (fail closed otherwise).
    for name, anchor in [
        ("A_FUSION", A_FUSION),
        ("A_CORE_BIN", A_CORE_BIN),
        ("A_CLEAN_BIN", A_CLEAN_BIN),
        ("A_THRESHOLD_ANCHOR", A_THRESHOLD_ANCHOR),
    ]:
        c = text.count(anchor)
        if c != 1:
            print(f"FAIL_CLOSED: anchor {name} count={c} (expected 1)")
            return 3

    # REPAIR 1 (D61).
    text = text.replace(A_FUSION, R_FUSION, 1)
    # REPAIR 2 (POLICY_B) central core binary.
    text = text.replace(A_CORE_BIN, R_CORE_BIN, 1)
    # REPAIR 2 (POLICY_B) clean binary.
    text = text.replace(A_CLEAN_BIN, R_CLEAN_BIN, 1)
    # REPAIR 2 (POLICY_B) helper, inserted after the threshold line.
    text = text.replace(A_THRESHOLD_ANCHOR, POLICY_B_HELPER, 1)

    # Version banner marker (governance/observability only — not scientific).
    banner_old = '"""Phase36'
    if text.startswith(banner_old):
        pass  # leave the original module docstring intact; version is tracked by path+diff.

    out_bytes = text.encode("utf-8")

    # Post-conditions: old call absent, new call present, helper wired to both paths.
    if "system._fuse_global_with_regional(p_global, refined, window)" in text:
        print("FAIL_CLOSED: old fusion call still present")
        return 3
    if "fuse_full_field(p_global, refined, geom)" not in text:
        print("FAIL_CLOSED: canonical fusion call missing")
        return 3
    if text.count("_phase27_scored_final_binary(") != 3:  # 1 def + 2 call sites
        print(f"FAIL_CLOSED: helper wiring count={text.count('_phase27_scored_final_binary(')} (expected 3)")
        return 3

    write_once(OUT, out_bytes)
    print("V1_15_SOURCE_WRITTEN")
    print(f"path={OUT.relative_to(ROOT)}")
    print(f"bytes={len(out_bytes)}")
    print(f"v1_15_source_sha256={sha256_bytes(out_bytes)}")
    print(f"v1_14_source_sha256={src_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
