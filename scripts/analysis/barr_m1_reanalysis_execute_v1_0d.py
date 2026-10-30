"""Retired unsafe v1.0d entrypoint. The separately versioned repair is disabled."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.analysis.barr_m1_v1_0d_repaired.__main__ import main
from scripts.analysis.barr_m1_v1_0d_repaired.authorization import production_authorization as load_and_verify_authorization
from scripts.analysis.barr_m1_v1_0d_repaired.analysis import validate_population, construct_deltas
from scripts.analysis.barr_m1_v1_0d_repaired.contracts import Refusal, CONFIG
AuthorizationError = ExecutionError = Refusal
N_EXPECTED = CONFIG["n"]
if __name__ == "__main__":
    raise SystemExit(main())
