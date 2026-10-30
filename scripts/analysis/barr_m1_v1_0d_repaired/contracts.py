"""Frozen authority import, without invoking its real-data validation routines."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "scripts/analysis/barr_m1_reanalysis_gate_v1_0c.py"
GATE_SHA = "e82ecdb781a56355a9a0a1ebabd948932fee0e15e71d90770bbd0b8459e96c32"
PROTOCOL_SHA = "a1a59cffc83e7b167b6ae28f75123167abf06d37d080e09c3cc0cdf519419a42"
ERRATUM_SHA = "7653cefd5b1bf6a1e28e5c9f65e1850a561f7316d48226dfb0859195c1c38f45"


class Refusal(ValueError):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(code + (": " + detail if detail else ""))


def require(ok, code, detail=""):
    if not ok:
        raise Refusal(code, detail)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


require(digest(GATE.read_bytes()) == GATE_SHA, "E_FROZEN_GATE_SHA")
spec = importlib.util.spec_from_file_location("barr_frozen_authority", GATE)
authority = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authority)
SOURCES = {k: v for k, v in authority.SOURCES.items() if k != "phase28_table_02"}
# Source identified by the completed lineage audit. Digest observed during this
# repair, not misrepresented as a prior release-manifest entry; approval binds it.
SOURCES["patient_grouping"] = ("manifests/phase4_v3/train.csv",
    "28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6")
INPUT_SHAS = {k: v[1] for k, v in SOURCES.items()}
CHECKPOINT_SHAS = {k: v[1] for k, v in authority.COMPONENTS.items()}
CONFIG = dict(K=1239, budget=0.25, population="ROUTER_DEVELOPMENT", n=4957,
              arms=["A0", "A1", "A8"], bootstrap_reps=2000, seed=42)
DOMAINS = ("BUSI", "ISIC", "KUB", "KVASIR")
COUNTS = dict(BUSI=512, ISIC=2173, KUB=1680, KVASIR=592)
EXCLUSIONS = sorted(["A7", "BARR-M2", "FiLM-off training control", "EXT-03B baseline training",
    "EXT-04 onward", "training", "model construction", "forward inference", "TEST",
    "ROUTER_HOLDOUT", "external-data evaluation", "new retrospective arms"])


def validate_config(config, environment=None):
    import os
    env = os.environ if environment is None else environment
    require(not any(k.upper().startswith("BARR_M1_") for k in env), "E_CONFIG_ENV_OVERRIDE")
    require(type(config) is dict and canonical(config) == canonical(CONFIG), "E_CONFIG_FROZEN")
    return dict(CONFIG)


def bundle_sha():
    """Binds every runtime module plus the retired-entrypoint shim, not one file."""
    paths = sorted(Path(__file__).parent.glob("*.py"))
    paths.append(Path(__file__).parent / "requirements.txt")
    paths.append(ROOT / "scripts/analysis/barr_m1_reanalysis_execute_v1_0d.py")
    return digest(canonical({p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in paths}))
