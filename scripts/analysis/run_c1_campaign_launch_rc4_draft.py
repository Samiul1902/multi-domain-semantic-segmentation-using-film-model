"""DRAFT RC4 campaign preflight CLI. Not an authorized release; cannot start training.

Usage (preflight only):
  python scripts/analysis/run_c1_campaign_launch_rc4_draft.py \
      --release-digest <RC4 digest approved by the institution> \
      --owner-key-fingerprint <fingerprint published by the institution out of band> \
      --approval ... --instruction ... --budget ... --time-proof-dir ... --recovery-dir ...
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.c1_rc4_candidate import campaign_rc4_draft as draft  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--release-digest", required=True)
    p.add_argument("--owner-key-fingerprint", required=True)
    p.add_argument("--approval", type=Path, required=True)
    p.add_argument("--instruction", type=Path, required=True)
    p.add_argument("--budget", type=Path, required=True)
    p.add_argument("--time-proof-dir", type=Path, required=True)
    p.add_argument("--recovery-dir", type=Path, required=True)
    p.add_argument("--output-root", type=Path, default=ROOT / "experiments/c1_film_attribution_v1")
    p.add_argument("--execute", action="store_true", help="Refused: this draft is not authorized.")
    a = p.parse_args()
    artifacts = draft.load_artifacts(
        approval=a.approval, instruction=a.instruction, budget=a.budget,
        time_proof_dir=a.time_proof_dir, recovery_dir=a.recovery_dir)
    draft.execute_campaign(
        expected_release_digest=a.release_digest, owner_key_fingerprint=a.owner_key_fingerprint,
        artifacts=artifacts, output_root=a.output_root, execute=a.execute)
    print("RC4 preflight PASSED for all six runs. No training was started.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
