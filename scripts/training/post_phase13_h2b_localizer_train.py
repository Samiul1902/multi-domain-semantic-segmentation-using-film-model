"""Clean-v3 safe training runner for the POST-PHASE-13 H2-B-B1 localizer training.

H2-A-B1 = DETERMINISTIC TRAINING REPLAY WITH DEPLOYMENT-BALANCED CHECKPOINT SELECTION.
This file is the frozen Phase-13 clean-v3 runner with a CONFINED diff:
  * experiment identity / config path                                   (provenance)
  * H2A protocol binding gate replaces the Phase-13 R2C runner-SHA gate (provenance)
  * loss import + criterion construction = SoftTargetFocalBCE(gamma=2.0)
    (SCIENTIFIC: the ONE authorized axis -- LOSS / OBJECTIVE SEMANTICS)
  * per-epoch PROPOSAL_PIXEL_ANY_HIT_PRECISION + score diagnostics (evaluation-only)
  * history row additions                                               (reporting)
NO gradient-update code is modified: loss, optimizer, scheduler, AMP, data, augmentation,
seeding, batching and the training-loop body are IDENTICAL to the Phase-13 runner.

Original module docstring follows.

Clean-v3 safe training runner for the Phase-13 KUB localizer.

Phase 13 Part 1B-R0 CREATED this runner. Part 1B-R0-R1 completes it so that it
is genuinely TRAINING-READY: every executable code path is implemented. No
unresolved execution stub, placeholder, dummy or fabricated metric remains on
the executable path (the only exception is genuine scientific error raising).

This module is the clean-v3 replacement for the historical trainer
``scripts/training/train_phase13b_localizer.py`` which remains IMMUTABLE.
Likewise ``src/inference/learned_roi.py`` remains IMMUTABLE and is NOT used
here (it omits ``heatmap_resolution=128``); this runner uses the clean-v3-safe
paths only.

Loss objective (H2B frozen objective: CHANGE_H2B_001 -- objective only)
-------------------------------------------------------------------
The primary clean-v3 objective is the historical EXECUTING objective:

    SoftTargetFocalBCE(gamma=2.0)   -- NO Dice term

The executable objective is ``SoftTargetFocalBCE(gamma=2.0)``. There is no alpha, no
beta, no Dice term, no auxiliary objective and no gamma sweep on the executable path.
The Phase-13 R2A CenterNet binding is retained as PARENT PROVENANCE ONLY (see
``parent_provenance`` in the audits); it is NOT the active H2B objective.

Differences from the historical trainer (all required by R2 / clean-v3)
-----------------------------------------------------------------------
  * binds the supervisor-supplied clean-v3 experiment ID (no ID derivation)
  * validates ``phase4_v3`` strictly via ``validate_manifest_version_strict``
  * filters TRAIN/VAL through the phase4_v3 manifest (no historical v2 manifest)
  * asserts the clean-v3 population 770/103 and patient overlap 0
  * constructs ``KUBLocalizer`` with ``heatmap_resolution=128`` EXPLICITLY
  * asserts the 128x128 output / target / equality contract loudly
  * uses EXACTLY ONE fixed proposal configuration (no 20-config grid)
  * applies the frozen 4-term strict-lexicographic selection rule
  * computes secondary diagnostics but structurally excludes them from selection
  * deterministic seeding + real loader generator-state persistence
  * authoritative manifest SHAs written into the checkpoint
  * full resume safety gates (mismatch fails LOUDLY, never silently restarts)
  * code paths for training start / completion audits
  * atomic single-row-per-epoch history writes
  * never constructs TEST data

WHAT THIS MODULE DOES ON IMPORT
-------------------------------
Nothing. Importing performs no CUDA request, no model construction, no data
iteration, no forward pass, no optimizer creation, no run-lock acquisition and
no checkpoint write. All of that lives inside ``main()``.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths / frozen identity
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = (
    "post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_deploymentbalance_seed42_clean_v3"
)

CONFIG_PATH = (
    ROOT / "configs" / "phase13_clean_v3"
    / f"{EXPERIMENT_ID}.yaml"
)

R2_PROTOCOL_PATH = (
    ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_protocol_frozen_r2.json"
)
R2_PROTOCOL_SHA = "ab451e03366c589fae5c303ebf1382e086f4f115b97768eb36d491256a3b5e53"

# ---- H2-A-B1 protocol binding (the governing frozen artifact for this run) ----
H2B_PROTOCOL_PATH = (
    ROOT / "reports" / "audits" / "post_phase13_h2b_protocol_frozen.json"
)
H2B_PROTOCOL_SHA = "22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e"
H2B_PROTOCOL_REQUIRED_STATUS = "SUPERVISOR_FROZEN_H2B_OBJECTIVE_ONLY_READY_FOR_B1_AUTHORIZATION"
H2A_SCORE_PATH_AUDIT_PATH = (
    ROOT / "reports" / "audits" / "post_phase13_h2a_localizer_score_path_audit.json"
)
H2A_SCORE_PATH_AUDIT_SHA = "3d9fea04ba8ca8b603314bd72f84ce2176ad33c5cc0bfed8f5b6dae1e64bec99"
H2A_SCORE_PATH_REQUIRED_VERDICT = "SCORE_PATH_IMPLEMENTATION_VALID"
R2_REQUIRED_STATUS = "SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING"

R2A_LOSS_PATH = (
    ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_loss_binding_r2a.json"
)

MANIFEST_VERSION = "phase4_v3"
TAXONOMY_ID = "kub_size_clean_v3_v1"

EXPECTED_TRAIN_CASES = 770
EXPECTED_TRAIN_COMPONENTS = 1161
EXPECTED_VAL_CASES = 103
EXPECTED_VAL_COMPONENTS = 152
EXPECTED_VAL_STRATA = {"TINY": 72, "SMALL": 28, "MEDIUM": 36, "LARGE": 16}

HEATMAP_RESOLUTION = 128
INPUT_RESOLUTION = 512

# Clean-v3 VAL GT component source. Explicitly NOT the stale kub_size_v1 table
# (``kub_*_components_sized.csv``) and NOT the historical v2 manifest.
VAL_COMPONENT_TABLE = ROOT / "reports" / "tables" / "phase12_clean_v3_oracle_geometry.csv"
VAL_COMPONENT_TABLE_SHA = (
    "29326d5b9a3bf71add74d8743750511f146d8c4dfbd1dc5b04a5e1b647c37cc0"
)

# Physical source sample tables used for KUB FULL_FIELD metadata
# (patient_id / image_path / mask_path / view_type) BEFORE the phase4_v3 join.
# Hashed verbatim by the manifest-provenance binding (see amendment
# NON_SCIENTIFIC_PROVENANCE_BINDING). Never hashed for image content.
TRAIN_SAMPLE_TABLE = ROOT / "reports" / "tables" / "kub_train_samples_sized.csv"
VAL_SAMPLE_TABLE = ROOT / "reports" / "tables" / "kub_val_samples_sized.csv"

MANIFEST_PROVENANCE_BINDING_PATH = (
    ROOT / "reports" / "audits"
    / "phase13_clean_v3_localizer_manifest_provenance_binding.json"
)
MANIFEST_PROVENANCE_BINDING_SHA = (
    "436831dbaf3305e632e6b4a34adb0eb1b4b1edf962e74354d337ec1328bfdd5a"
)
MANIFEST_PROVENANCE_BINDING_STATUS = "PROVENANCE_BINDING_APPROVED_FOR_PART1B"

HARD_TINY_PATH = ROOT / "reports" / "tables" / "phase13_clean_v3_hard_tiny_replication_set.csv"
HARD_TINY_SHA = "2f9828d77c008e7c90cd69e82d0af3568902ca9d508fdfcb9d8ccf8abd569538"
HARD_TINY_COUNT = 15
GLOBAL_EMPTY_PATH = ROOT / "reports" / "tables" / "phase13_clean_v3_global_empty_replication_set.csv"
GLOBAL_EMPTY_SHA = "a0b332cad6bca4466ccc528cbe18cc527ef6503603ab69c55b9d699d7979f0ea"
GLOBAL_EMPTY_COUNT = 5

# ---- R2B metric-semantics implementation correction (VAL evaluation ONLY) ----
# Corrects the VAL evaluator to the already-frozen metric definitions. No
# scientific definition, threshold, loss, architecture or target changes.
R2B_AMENDMENT_PATH = (
    ROOT / "reports" / "audits"
    / "phase13_clean_v3_localizer_metric_semantics_r2b.json"
)
R2B_AMENDMENT_NAME = "R2B_METRIC_SEMANTICS_IMPLEMENTATION_CORRECTION"
# The runner identity stored in the epoch-28 checkpoint (pre-R2B).
PRE_R2B_RUNNER_SHA = (
    "f9d8c0d4166b283f279a43102083ad2d898724385729ab30ab6a3723fc4744f0"
)

# ---- R2C coverage-semantics arbitration -----------------------------------
# PRIMARY checkpoint-selection coverage is the EXPLICIT historical executing
# bbox semantics. Pixel-mask coverage is retained as a SECONDARY sensitivity
# metric only and MUST NOT enter select_epoch / best_score / bad_epochs.
R2C_AMENDMENT_PATH = (
    ROOT / "reports" / "audits"
    / "phase13_clean_v3_localizer_coverage_semantics_r2c.json"
)
R2C_AMENDMENT_NAME = "R2C_HISTORICAL_EXECUTING_COVERAGE_ARBITRATION"
PRIMARY_COVERAGE_SEMANTICS = "HISTORICAL_EXECUTING_BBOX_COVERAGE"
SECONDARY_COVERAGE_SEMANTICS = "PIXEL_MASK_COMPONENT_SENSITIVITY_ONLY"
# The runner identity stored in the epoch-31 checkpoint (R2B pixel semantics).
PRE_R2C_RUNNER_SHA = (
    "15a0c2f0cf02916f96f60b7cf3d148fac4d931df11d5e119eb9c76f22a0c889b"
)
CANONICAL_SELECTION_HISTORY_PATH = (
    ROOT / "reports" / "tables" / "phase13_part1b_canonical_selection_history.csv"
)

# The single frozen proposal configuration. Encoded ONCE, as a scalar tuple.
PROPOSAL_THRESHOLD = 0.10
PROPOSAL_MARGIN = 0.20
PROPOSAL_TOP_K = 5
PROPOSAL_NMS_IOU = 0.30
PROPOSAL_CONFIGURATION_COUNT = 1  # primary training: exactly one config
GRID_SEARCH_ENABLED = False       # no loop over the historical 20-config grid

# Frozen H2B loss objective (CHANGE_H2B_001: objective only).
LOSS_CLASS = "src.losses.soft_target_focal_bce.SoftTargetFocalBCE"
LOSS_LABEL = "H2B_SOFT_TARGET_FOCAL_BCE_GAMMA2"
LOSS_MODULE_PATH = ROOT / "src" / "losses" / "soft_target_focal_bce.py"
LOSS_MODULE_SHA = "40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75"
OBJECTIVE_CHANGE_ID = "H2B_OBJECTIVE_ONLY_SOFT_TARGET_FOCAL_BCE_GAMMA2"
H2B_PROTOCOL_IDENTITY = (
    "H2B_OBJECTIVE_ONLY__H2A_DEPLOYMENT_BALANCED_SELECTION_CARRY_FORWARD"
)

# Audit artifact names emitted by the training start / completion code paths.
TRAINING_START_BASENAME = "post_phase13_h2b_b1_training_start"
TRAINING_COMPLETION_BASENAME = "post_phase13_h2b_b1_training_completion"
AUDIT_DIR = ROOT / "reports" / "audits"


# ---------------------------------------------------------------------------
# Pure helpers (safe: no I/O side effects beyond reading the named file)
# ---------------------------------------------------------------------------
def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def load_executable_config(config_path=CONFIG_PATH) -> dict:
    """Parse the clean-v3 executable YAML."""
    import yaml

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"clean-v3 executable config missing: {config_path}")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("clean-v3 executable config did not parse to a mapping")
    return config


def verify_experiment_id(config: dict) -> str:
    """The config experiment_id MUST equal the supervisor-supplied exact string."""
    from_config = config.get("experiment_id")
    if from_config != EXPERIMENT_ID:
        raise ValueError(
            "experiment_id mismatch: config has "
            f"{from_config!r}, required {EXPERIMENT_ID!r}. Refusing to proceed."
        )
    for forbidden_suffix in (
        "_retry", "_fix", "_new", "_v2", "_v3b", "_r1", "_r2",
    ):
        if EXPERIMENT_ID.endswith(forbidden_suffix):
            raise ValueError(
                f"experiment_id must not carry the suffix {forbidden_suffix!r}"
            )
    return from_config


def verify_r2_protocol() -> dict:
    """Re-verify the frozen R2 protocol SHA and status."""
    if not R2_PROTOCOL_PATH.exists():
        raise FileNotFoundError(f"R2 protocol missing: {R2_PROTOCOL_PATH}")
    actual = sha256_file(R2_PROTOCOL_PATH)
    if actual != R2_PROTOCOL_SHA:
        raise ValueError(
            f"R2 protocol SHA mismatch: expected {R2_PROTOCOL_SHA}, got {actual}"
        )
    protocol = json.loads(R2_PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol.get("status") != R2_REQUIRED_STATUS:
        raise ValueError(
            f"R2 status is {protocol.get('status')!r}, required {R2_REQUIRED_STATUS!r}"
        )
    return protocol


def verify_loss_binding(config: dict) -> dict:
    """Enforce the H2B frozen objective on the executable config.

    The runner must instantiate EXACTLY ``SoftTargetFocalBCE(gamma=2.0)``.
    Any executable field implying a different objective (CenterNet focal with
    alpha/beta, a Dice term, an auxiliary loss, a regularizer, a class weight or
    any additional coefficient) is a hard failure. gamma is FIXED at 2.0; no
    grid, no sweep, no alternative gamma.
    """
    loss = config.get("loss")
    if not isinstance(loss, dict):
        raise ValueError("config['loss'] must be a mapping")

    if loss.get("name") != "SoftTargetFocalBCE":
        raise ValueError(
            f"executable loss name must be 'SoftTargetFocalBCE', got {loss.get('name')!r}"
        )
    if loss.get("implementation") != LOSS_CLASS:
        raise ValueError(
            f"executable loss implementation must be {LOSS_CLASS!r}, "
            f"got {loss.get('implementation')!r}"
        )
    if float(loss.get("gamma")) != 2.0:
        raise ValueError(f"executable loss gamma must be 2.0, got {loss.get('gamma')!r}")

    # Keys that must be explicitly declared ABSENT (NONE/0) or omitted entirely.
    # An explicit ``NONE`` is a valid frozen declaration; any actual value is a
    # hard failure because H2B changes the objective only.
    for forbidden_key in ("alpha", "beta", "dice_weight", "dice_term",
                          "auxiliary_loss", "regularizer", "class_weight",
                          "coefficient"):
        if forbidden_key not in loss:
            continue
        value = loss[forbidden_key]
        if isinstance(value, str) and value.strip().upper() == "NONE":
            continue  # explicit frozen declaration of absence
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0:
            continue  # zero weight == absent
        raise ValueError(
            f"executable loss block must not carry an active {forbidden_key!r} "
            f"(got {value!r}); H2B changes the objective only: no alpha/beta, no Dice, "
            "no auxiliary loss, no regularizer, no class weight, no extra coefficient"
        )

    if loss.get("modulation_detached", "NO") != "NO":
        raise ValueError("H2B modulation term must not be detached")
    if str(loss.get("target_clamping", "NONE")).upper() != "NONE":
        raise ValueError("H2B must not clamp the target")
    if str(loss.get("target_binary_conversion", "NONE")).upper() != "NONE":
        raise ValueError("H2B must not binarise the target")

    return {
        "loss_class": LOSS_CLASS,
        "gamma": float(loss["gamma"]),
        "label": LOSS_LABEL,
    }


def assert_no_historical_manifest_usage(config: dict) -> None:
    """Guard against any executable phase4_v2 / root-manifest binding.

    Only *executable* string values are scanned. Keys whose purpose is to
    DECLARE or DOCUMENT historical tokens (denylists, provenance notes,
    defects, provenance chains) are excluded, otherwise the guard would trip on
    its own declarations rather than on a real binding.
    """
    _NON_EXECUTABLE_KEYS = {
        "forbidden_executable_manifest",
        "forbidden",
        "provenance_note",
        "physical_batch_provenance",
        "historical_helper_defect",
        "provenance",
        "provenance_source",
        "note",
        "description",
        "contract_provenance",
        "authority_rank_1",
        "authority_rank_2",
        "authority_rank_3",
        "historical_executing_source",
        "frozen_contract_provenance",
        "loss_binding_discrepancy",
        "superseded_composite_contract",
        "non_primary_implementation_defect",
        "historical_source",
        "documented_provenance",
        "documented_string",
    }
    forbidden = ("phase4_v2", "manifests/train.csv", "manifests/val.csv")

    def _walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in _NON_EXECUTABLE_KEYS or str(key).endswith("_provenance"):
                    continue
                _walk(value, path + [str(key)])
        elif isinstance(node, list):
            for index, value in enumerate(node):
                _walk(value, path + [f"[{index}]"])
        elif isinstance(node, str):
            for token in forbidden:
                if token in node:
                    raise ValueError(
                        "clean-v3 config contains a forbidden historical manifest "
                        f"token {token!r} at executable path "
                        f"{'.'.join(path)}: {node!r}"
                    )

    _walk(config, [])


def filtered_sample_ids_digest(frame) -> str:
    """Deterministic membership digest of a filtered FULL_FIELD sample-id set.

    Contract (Phase-13 Part-1B §3):
      1. take final post-join FULL_FIELD sample_id values
      2. cast to canonical string
      3. require uniqueness
      4. sort lexicographically
      5. join exactly with "\\n"
      6. UTF-8 encode
      7. SHA-256

    This is a MEMBERSHIP binding. It is NOT an image-content hash. The digest is
    invariant to row order and excludes metrics, predictions, GT, and pixels.
    """
    if "sample_id" not in frame.columns:
        raise ValueError("sample table has no 'sample_id' column; refusing empty digest")
    ids = [str(value) for value in frame["sample_id"].tolist()]
    if not ids:
        raise ValueError("filtered sample-id set is empty; refusing empty digest")
    if len(set(ids)) != len(ids):
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        raise ValueError(
            f"filtered sample_id values are not unique; duplicates: {duplicates[:10]}"
        )
    joined = "\n".join(sorted(ids))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def compute_manifest_hashes(
    manifest_version: str,
    train_frame,
    val_frame,
    *,
    train_sample_table=None,
    val_sample_table=None,
) -> dict:
    """Authoritative provenance / membership binding written into every checkpoint.

    Phase-13 Part-1B manifest-provenance amendment
    (``NON_SCIENTIFIC_PROVENANCE_BINDING``).

    The superseded contract derived ``train_table_sha256`` / ``val_table_sha256``
    from a per-sample ``image_sha256`` column that does not exist in this
    repository (status ``SUPERSEDED_UNRESOLVABLE_FIELD_SEMANTICS``). It is
    replaced by explicit fields whose names state exactly what they mean.

    This function does NOT require ``image_sha256`` and never claims to hash
    image content.
    """
    from src.utils.manifest_guard import get_manifest_path

    train_manifest_path = Path(get_manifest_path(manifest_version, "train"))
    val_manifest_path = Path(get_manifest_path(manifest_version, "val"))

    if train_sample_table is None:
        train_sample_table = TRAIN_SAMPLE_TABLE
    if val_sample_table is None:
        val_sample_table = VAL_SAMPLE_TABLE
    train_sample_table = Path(train_sample_table)
    val_sample_table = Path(val_sample_table)

    for label, path in (
        ("TRAIN manifest", train_manifest_path),
        ("VAL manifest", val_manifest_path),
        ("TRAIN sample table", train_sample_table),
        ("VAL sample table", val_sample_table),
    ):
        if not path.exists():
            raise FileNotFoundError(f"{label} missing: {path}. STOP / CHECK_REQUIRED.")

    train_count = int(len(train_frame))
    val_count = int(len(val_frame))
    if train_count != EXPECTED_TRAIN_CASES:
        raise ValueError(
            f"filtered TRAIN membership count is {train_count}, "
            f"expected {EXPECTED_TRAIN_CASES}. STOP / CHECK_REQUIRED."
        )
    if val_count != EXPECTED_VAL_CASES:
        raise ValueError(
            f"filtered VAL membership count is {val_count}, "
            f"expected {EXPECTED_VAL_CASES}. STOP / CHECK_REQUIRED."
        )

    provenance = {
        "manifest_version": manifest_version,
        # --- physical file provenance (bytes on disk) ---
        "train_manifest_file_sha256": sha256_file(train_manifest_path),
        "val_manifest_file_sha256": sha256_file(val_manifest_path),
        "train_sample_table_file_sha256": sha256_file(train_sample_table),
        "val_sample_table_file_sha256": sha256_file(val_sample_table),
        # --- filtered membership binding (post-join FULL_FIELD) ---
        "train_filtered_sample_ids_sha256": filtered_sample_ids_digest(train_frame),
        "val_filtered_sample_ids_sha256": filtered_sample_ids_digest(val_frame),
        "train_filtered_sample_count": train_count,
        "val_filtered_sample_count": val_count,
        # --- physical paths (for auditability) ---
        "train_manifest_path": str(train_manifest_path),
        "val_manifest_path": str(val_manifest_path),
        "train_sample_table_path": str(train_sample_table),
        "val_sample_table_path": str(val_sample_table),
    }

    # Fail loudly on any unresolvable required field.
    for key in (
        "train_manifest_file_sha256",
        "val_manifest_file_sha256",
        "train_sample_table_file_sha256",
        "val_sample_table_file_sha256",
        "train_filtered_sample_ids_sha256",
        "val_filtered_sample_ids_sha256",
    ):
        if not provenance[key]:
            raise ValueError(
                f"manifest provenance {key!r} resolved empty; refusing empty hashes"
            )

    # The superseded field names MUST NOT be reintroduced silently.
    for forbidden in ("train_table_sha256", "val_table_sha256"):
        if forbidden in provenance:
            raise RuntimeError(
                f"superseded field {forbidden!r} present in executable provenance; "
                "see NON_SCIENTIFIC_PROVENANCE_BINDING amendment"
            )
    return provenance


def history_contiguity(rows) -> bool:
    """True iff epoch numbers form a contiguous 1..N sequence with no gaps/dupes."""
    if not rows:
        return True
    epochs = [int(row.get("epoch", -1)) for row in rows]
    return epochs == list(range(1, len(epochs) + 1))


def write_history_atomic(path, rows) -> None:
    """Canonical atomic CSV write: one completed epoch == exactly one row.

    Writes to a sibling ``.tmp`` file and atomically replaces the target, so a
    partially-written ``history.csv`` can never be observed. Prior rows are
    preserved because every row is carried in ``rows``.
    """
    import pandas as pd

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(list(rows))
    if "epoch" in frame.columns:
        frame = frame.sort_values("epoch").reset_index(drop=True)
        if frame["epoch"].duplicated().any():
            raise ValueError("history contains duplicate epoch rows; refusing to write")
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def assert_resumable_or_absent(args, exp_dir: Path, chk_dir: Path) -> None:
    """Refuse to silently overwrite existing scientific state.

    * ``--resume`` absent but a scientific state exists  -> STOP.
    * ``--resume`` present but state incomplete          -> STOP.
    """
    latest = chk_dir / "latest.pt"
    history_path = exp_dir / "history.csv"
    state_exists = latest.exists() or history_path.exists()
    if state_exists and not args.resume:
        raise RuntimeError(
            "existing clean-v3 scientific state detected "
            f"(latest.pt={latest.exists()}, history.csv={history_path.exists()}) "
            "but --resume was NOT supplied. Refusing to overwrite. STOP."
        )
    if args.resume:
        if not latest.exists():
            raise RuntimeError(
                "--resume supplied but latest.pt is missing. Cannot resume. STOP."
            )
        if not history_path.exists():
            raise RuntimeError(
                "--resume supplied but history.csv is missing. Cannot resume. STOP."
            )


def load_history_csv(history_path: Path):
    import pandas as pd

    frame = pd.read_csv(history_path)
    return frame.to_dict(orient="records")


def load_r2b_amendment(current_runner_sha: str) -> dict:
    """Load and verify the R2B metric-semantics amendment (supervisor §20).

    The amendment must physically declare BOTH the pre-repair and the
    post-repair runner SHAs. The post-repair value must equal the SHA of the
    runner currently executing, so a runner edited after R2B was frozen cannot
    silently inherit the transition.
    """
    if not R2B_AMENDMENT_PATH.exists():
        return {"authorized": False, "sha": None, "reason": "R2B_AMENDMENT_MISSING"}
    payload = json.loads(R2B_AMENDMENT_PATH.read_text(encoding="utf-8"))
    checks = {
        "amendment_name": payload.get("amendment") == R2B_AMENDMENT_NAME,
        "pre_repair_runner_sha": payload.get("pre_repair_runner_sha") == PRE_R2B_RUNNER_SHA,
        "post_repair_runner_sha": payload.get("post_repair_runner_sha") == current_runner_sha,
        "scientific_definitions_changed": (
            payload.get("scientific_definitions_changed") == "NO"
        ),
    }
    return {
        "authorized": all(checks.values()),
        "sha": sha256_file(R2B_AMENDMENT_PATH),
        "payload": payload,
        "checks": checks,
        "reason": None if all(checks.values()) else "R2B_IDENTITY_MISMATCH",
    }


def load_r2c_amendment(current_runner_sha: str) -> dict:
    """Load and verify the R2C coverage-semantics arbitration amendment.

    R2C authorizes exactly ONE controlled runner-SHA transition: from the R2B
    pixel-semantics runner stored in the epoch-31 checkpoint to this R2C runner.
    """
    if not R2C_AMENDMENT_PATH.exists():
        return {"authorized": False, "sha": None, "reason": "R2C_AMENDMENT_MISSING"}
    payload = json.loads(R2C_AMENDMENT_PATH.read_text(encoding="utf-8"))
    checks = {
        "amendment_name": payload.get("amendment") == R2C_AMENDMENT_NAME,
        "pre_repair_runner_sha": payload.get("pre_repair_runner_sha") == PRE_R2C_RUNNER_SHA,
        "post_repair_runner_sha": payload.get("post_repair_runner_sha") == current_runner_sha,
        "primary_coverage_semantics": (
            payload.get("primary_coverage_semantics") == PRIMARY_COVERAGE_SEMANTICS
        ),
    }
    return {
        "authorized": all(checks.values()),
        "sha": sha256_file(R2C_AMENDMENT_PATH),
        "payload": payload,
        "checks": checks,
        "reason": None if all(checks.values()) else "R2C_IDENTITY_MISMATCH",
    }


def assert_resume_identity(state: dict, config: dict, manifest_hashes: dict, seed: int) -> None:
    """Every scientific identity field must match or resume fails LOUDLY."""
    # Top-level scientific identity (native checkpoint keys).
    top_level_identity = {
        "experiment_id": EXPERIMENT_ID,
        "manifest_version": MANIFEST_VERSION,
        "taxonomy_id": TAXONOMY_ID,
        "input_resolution": INPUT_RESOLUTION,
        "seed": seed,
    }
    # Extended execution metadata is persisted inside ``configuration``
    # (see the checkpoint-save block) because save_training_checkpoint has a
    # fixed signature.
    stored_configuration = state.get("configuration") or {}
    stored_exec = stored_configuration.get("_phase13_execution_metadata") or {}
    extended_identity = {
        "r2_protocol_sha": R2_PROTOCOL_SHA,
        "r2a_loss_sha": sha256_file(R2A_LOSS_PATH),
        "config_sha": sha256_file(CONFIG_PATH),
        "provenance_amendment_sha": sha256_file(MANIFEST_PROVENANCE_BINDING_PATH),
        "loss_label": LOSS_LABEL,
        "loss_class": LOSS_CLASS,
        "loss_gamma": 2.0,
        "loss_modulation_detached": "NO",
        "loss_target_clamping": "NONE",
        "loss_target_binary_conversion": "NONE",
        "loss_dice_weight": "NONE",
        "objective_change_id": OBJECTIVE_CHANGE_ID,
        "h2b_protocol_sha": H2B_PROTOCOL_SHA,
        "h2b_loss_module_sha": LOSS_MODULE_SHA,
        "heatmap_resolution": HEATMAP_RESOLUTION,
    }
    mismatches = []
    for key, value in top_level_identity.items():
        stored = state.get(key)
        if stored is None:
            mismatches.append(f"{key}: missing in checkpoint (expected {value!r})")
        elif str(stored) != str(value):
            mismatches.append(f"{key}: checkpoint={stored!r} expected={value!r}")

    for key, value in extended_identity.items():
        stored = stored_exec.get(key)
        if stored is None:
            mismatches.append(
                f"_phase13_execution_metadata.{key}: missing in checkpoint "
                f"(expected {value!r})"
            )
        elif str(stored) != str(value):
            mismatches.append(
                f"_phase13_execution_metadata.{key}: checkpoint={stored!r} "
                f"expected={value!r}"
            )

    # ---- R2B controlled runner-SHA transition (supervisor §20) ----
    # Patching the evaluator changed the runner SHA. The epoch-28 checkpoint
    # legitimately stores the PRE-R2B runner identity. Exactly ONE transition is
    # authorized, and only when the R2B amendment physically declares BOTH the
    # pre- and post-repair runner SHAs. There is no generic bypass: any other
    # runner-SHA difference is a loud failure.
    current_runner_sha = sha256_file(Path(__file__))
    stored_runner_sha = stored_exec.get("runner_sha")
    r2b = load_r2b_amendment(current_runner_sha)
    r2c = load_r2c_amendment(current_runner_sha)
    runner_sha_transition = None
    if str(stored_runner_sha) == current_runner_sha:
        pass
    elif str(stored_runner_sha) == PRE_R2B_RUNNER_SHA and r2b["authorized"]:
        runner_sha_transition = {
            "from": PRE_R2B_RUNNER_SHA,
            "to": current_runner_sha,
            "authorized_by": R2B_AMENDMENT_NAME,
            "r2b_sha": r2b["sha"],
        }
    elif str(stored_runner_sha) == PRE_R2C_RUNNER_SHA and r2c["authorized"]:
        # R2C controlled epoch-31 metadata rebind: bbox semantics become primary.
        runner_sha_transition = {
            "from": PRE_R2C_RUNNER_SHA,
            "to": current_runner_sha,
            "authorized_by": R2C_AMENDMENT_NAME,
            "r2c_sha": r2c["sha"],
        }
    else:
        mismatches.append(
            f"_phase13_execution_metadata.runner_sha: checkpoint={stored_runner_sha!r} "
            f"expected={current_runner_sha!r} — no authorized R2B/R2C transition "
            f"(r2b={r2b['authorized']}, r2c={r2c['authorized']})"
        )
    state["_r2b_runner_sha_transition"] = runner_sha_transition
    state["_r2c_amendment_sha"] = r2c["sha"]

    stored_proposal = stored_exec.get("proposal_config") or {}
    for key, value in (
        ("threshold", PROPOSAL_THRESHOLD),
        ("margin", PROPOSAL_MARGIN),
        ("top_k", PROPOSAL_TOP_K),
        ("nms_iou", PROPOSAL_NMS_IOU),
    ):
        if str(stored_proposal.get(key)) != str(value):
            mismatches.append(
                f"proposal_config.{key}: checkpoint={stored_proposal.get(key)!r} "
                f"expected={value!r}"
            )

    stored_terms = state.get("selection_term_names")
    if stored_terms is not None:
        from src.training.clean_v3_selection import SELECTION_TERM_NAMES

        if tuple(stored_terms) != tuple(SELECTION_TERM_NAMES):
            mismatches.append(
                f"selection_term_names: checkpoint={tuple(stored_terms)!r} "
                f"expected={tuple(SELECTION_TERM_NAMES)!r}"
            )

    stored_manifest = state.get("manifest_hashes") or {}
    for key in (
        "train_manifest_file_sha256",
        "val_manifest_file_sha256",
        "train_sample_table_file_sha256",
        "val_sample_table_file_sha256",
        "train_filtered_sample_ids_sha256",
        "val_filtered_sample_ids_sha256",
        "train_filtered_sample_count",
        "val_filtered_sample_count",
    ):
        if key in manifest_hashes and str(stored_manifest.get(key)) != str(manifest_hashes[key]):
            mismatches.append(
                f"manifest_hashes.{key}: checkpoint={stored_manifest.get(key)!r} "
                f"expected={manifest_hashes[key]!r}"
            )
    # Superseded fields must not be required (they were never resolvable).
    for forbidden in ("train_table_sha256", "val_table_sha256"):
        if forbidden in manifest_hashes:
            mismatches.append(
                f"superseded field {forbidden!r} present in executable provenance"
            )

    if mismatches:
        raise RuntimeError(
            "RESUME IDENTITY MISMATCH — refusing to resume. Mismatches:\n  - "
            + "\n  - ".join(mismatches)
        )


def final_epoch_matches(state: dict, history_rows) -> None:
    if not history_rows:
        raise RuntimeError("resume history.csv is empty; cannot verify epoch contiguity")
    last_epoch = int(history_rows[-1]["epoch"])
    stored_epoch = int(state.get("epoch", -1))
    if last_epoch != stored_epoch:
        raise RuntimeError(
            f"resume mismatch: history.csv ends at epoch {last_epoch} but "
            f"latest.pt is at epoch {stored_epoch}. STOP."
        )


def write_audit_json_md(basename: str, payload: dict, markdown: str) -> dict:
    """Write a JSON + markdown audit pair into reports/audits/."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = AUDIT_DIR / f"{basename}.json"
    md_path = AUDIT_DIR / f"{basename}.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return {
        "json_path": str(json_path),
        "json_sha": sha256_file(json_path),
        "md_path": str(md_path),
        "md_sha": sha256_file(md_path),
    }


# ---------------------------------------------------------------------------
# VAL evaluation at the ONE frozen proposal configuration
# ---------------------------------------------------------------------------
def evaluate_fixed_config_localizer(model, loader, criterion, device, config,
                                    val_component_frame=None,
                                    val_sample_frame=None):
    """VAL evaluation at the ONE frozen proposal configuration.

    Fully implemented (no placeholder). Returns ``(val_loss, metrics)`` where
    ``metrics`` carries:

    PRIMARY       : tiny_recall90, overall_recall90, mean_roi_area_fraction
    SECONDARY     : hard_tiny_recovered90, global_empty_images_covered90,
                    multi_component_recall90, mean_proposals_per_image
    DESCRIPTIVE   : overall_recall50, any_overlap_recall, mean_coverage
    CONTROL       : zero_denominator

    Only the PRIMARY terms (plus ``val_loss``) are ever passed to
    ``select_epoch``. Secondary diagnostics are recorded and structurally
    excluded.

    GT is used ONLY after proposals are generated. The proposal generator
    itself accepts no ground truth.
    """
    import numpy as np
    import torch
    from scipy.ndimage import label

    from PIL import Image

    from src.data.transforms import SegmentationTransform
    from src.inference.predicted_roi import (
        generate_predicted_rois,
        union_roi_area_fraction,
    )
    # R2C arbitration: PRIMARY coverage is the EXPLICIT historical bbox semantics
    # (what the historical executing code actually did). Pixel-mask coverage is
    # retained as an explicitly named SECONDARY sensitivity metric only.
    from src.inference.clean_v3_coverage import (
        BBOX_SEMANTICS,
        PIXEL_SEMANTICS,
        evaluate_historical_bbox_coverage,
        evaluate_pixel_mask_coverage,
    )

    if PROPOSAL_CONFIGURATION_COUNT != 1 or GRID_SEARCH_ENABLED:
        raise RuntimeError(
            "clean-v3 VAL evaluation must use exactly one fixed proposal "
            "configuration; grid search must stay disabled."
        )

    # ---- GT components with FULL native masks (R2B canonical extraction) ----
    # Pre-R2B this block carried only a bbox, so ``evaluate_roi_coverage``
    # silently fell back to bbox-intersection coverage. R2B reconstructs the
    # native 8-connected components from the real VAL mask and attaches the full
    # native boolean mask, per the frozen pixel-coverage definition.
    from src.inference.clean_v3_components import (
        assert_component_contract,
        build_clean_v3_val_components,
    )
    from src.inference.clean_v3_metrics import (
        aggregate_clean_v3_metrics,
        multi_component_ids,
    )
    # H2A: this module-level function needs its own binding (main()'s lazy import
    # is not in scope here).
    from src.training.h2a_deployment_balance_selection import deployment_balance_hmean

    if val_component_frame is None or not len(val_component_frame):
        raise RuntimeError("clean-v3 VAL evaluation requires the geometry table. STOP.")
    if val_sample_frame is None or not len(val_sample_frame):
        raise RuntimeError("clean-v3 VAL evaluation requires the VAL sample table. STOP.")

    hard_tiny_keys, global_empty_ids = _load_hard_sets()

    grouped = build_clean_v3_val_components(
        val_component_frame,
        val_sample_frame,
        hard_tiny_keys=hard_tiny_keys,
        global_empty_ids=global_empty_ids,
    )
    component_contract = assert_component_contract(
        grouped, hard_tiny_keys=hard_tiny_keys, global_empty_ids=global_empty_ids
    )
    multi_ids = multi_component_ids(
        [c for comps in grouped.values() for c in comps]
    )

    model.eval()
    transform = SegmentationTransform(INPUT_RESOLUTION, False)

    total_val_loss = 0.0
    n_batches = 0
    per_image_proposals = []
    roial_area_fractions = []
    component_rows = []       # PRIMARY: historical bbox coverage
    pixel_component_rows = []  # SECONDARY: pixel-mask sensitivity
    covered_samples = set()
    # H2A: PROPOSAL_PIXEL_ANY_HIT_PRECISION accounting (primary new quantity).
    proposal_pixel_hit_count = 0
    proposal_total_count = 0
    proposal_bbox_hit_count = 0
    score_hit_pairs = []  # (score, pixel_any_hit) per generated proposal

    with torch.inference_mode():
        for batch in loader:
            images = batch["image"].to(device)
            targets = batch["heatmap"].to(device)
            with torch.amp.autocast("cuda"):
                logits = model(images)
                loss = criterion(logits, targets)
            total_val_loss += float(loss.item())
            n_batches += 1

            probabilities = torch.sigmoid(logits.float()).cpu().numpy()
            for index, sample_id in enumerate(batch["sample_id"]):
                sample_id = str(sample_id)
                original_shape = (
                    int(batch["original_height"][index]),
                    int(batch["original_width"][index]),
                )
                probability_map = probabilities[index, 0]
                _assert_native_geometry(probability_map)

                image_path = Path(str(batch["image_path"][index]))
                with Image.open(image_path) as handle:
                    native = handle.convert("L")
                _image, _mask, metadata = transform(native, Image.new("L", native.size))

                proposals = _generate_proposals_fixed_config(
                    probability_map, metadata, original_shape,
                    generate_predicted_rois=generate_predicted_rois,
                )
                per_image_proposals.append(len(proposals))

                if proposals:
                    union_fraction, _max_fraction = union_roi_area_fraction(
                        proposals, original_shape
                    )
                else:
                    union_fraction = 0.0
                roial_area_fractions.append(float(union_fraction))

                components = grouped.get(sample_id, [])
                if not components:
                    # All 103 clean-v3 FULL_FIELD VAL cases carry >=1 native GT
                    # component. A case with none is a contract violation, not a
                    # diagnostic branch. R2B removed the old "no components"
                    # global-empty shortcut (GLOBAL_EMPTY_GT_EMPTY_BRANCH_ERROR).
                    raise RuntimeError(
                        f"VAL case {sample_id} has no clean-v3 GT component; the "
                        "frozen contract requires 103/103 cases with components. STOP."
                    )

                # ---- H2A: PROPOSAL_PIXEL_ANY_HIT_PRECISION -------------------
                # Proposals were generated GT-FREE above; GT is consulted ONLY now.
                gt_union = np.zeros(original_shape, dtype=bool)
                gt_boxes = []
                for _component in components:
                    _cmask = _component.get("mask")
                    if _cmask is not None:
                        gt_union |= np.asarray(_cmask, dtype=bool)
                    gt_boxes.append((
                        int(_component["min_y"]), int(_component["min_x"]),
                        int(_component["max_y"]), int(_component["max_x"]),
                    ))
                for _proposal in proposals:
                    _geom = _proposal["crop_geometry"]
                    _cy1, _cy2 = int(_geom["clip_y1"]), int(_geom["clip_y2"])
                    _cx1, _cx2 = int(_geom["clip_x1"]), int(_geom["clip_x2"])
                    _hit = bool(gt_union[_cy1:_cy2, _cx1:_cx2].any())
                    proposal_total_count += 1
                    if _hit:
                        proposal_pixel_hit_count += 1
                    _py1, _px1, _py2, _px2 = (int(v) for v in _proposal["proposal_bbox"])
                    if any(not (_py2 < _by1 or _py1 > _by2 or _px2 < _bx1 or _px1 > _bx2)
                           for (_by1, _bx1, _by2, _bx2) in gt_boxes):
                        proposal_bbox_hit_count += 1
                    score_hit_pairs.append((float(_proposal["score"]), _hit))

                # PRIMARY (R2C): explicit historical bbox coverage.
                bbox_rows = evaluate_historical_bbox_coverage(proposals, components)
                # SECONDARY: pixel-mask sensitivity (never a selection term).
                pixel_rows = evaluate_pixel_mask_coverage(proposals, components)

                def _row(coverage_row, component):
                    return {
                        "sample_id": sample_id,
                        "component_id": int(component["component_id"]),
                        "size_stratum": component["size_stratum"],
                        "hard_tiny": bool(component["hard_tiny"]),
                        "global_empty_image": bool(component["global_empty_image"]),
                        "coverage_fraction": float(coverage_row["coverage_fraction"]),
                        "covered90": bool(coverage_row["covered90"]),
                        "covered50": bool(coverage_row["covered50"]),
                        "any_overlap": bool(coverage_row["any_overlap"]),
                    }

                for coverage_row, component in zip(bbox_rows, components):
                    component_rows.append(_row(coverage_row, component))
                    if coverage_row["covered90"]:
                        covered_samples.add(sample_id)
                for coverage_row, component in zip(pixel_rows, components):
                    pixel_component_rows.append(_row(coverage_row, component))

    if n_batches == 0:
        raise RuntimeError("VAL loader produced zero batches")

    if len(component_rows) != EXPECTED_VAL_COMPONENTS:
        raise RuntimeError(
            f"VAL coverage rows are {len(component_rows)}, expected "
            f"{EXPECTED_VAL_COMPONENTS}. STOP."
        )

    # ---- PRIMARY: historical executing bbox coverage (R2C canonical) ----
    bbox_metrics = aggregate_clean_v3_metrics(
        component_rows,
        per_image_proposals,
        roial_area_fractions,
        multi_ids=multi_ids,
    )
    # ---- SECONDARY: pixel-mask sensitivity (never a selection term) ----
    pixel_metrics = aggregate_clean_v3_metrics(
        pixel_component_rows,
        per_image_proposals,
        roial_area_fractions,
        multi_ids=multi_ids,
    )

    metrics = dict(bbox_metrics)
    # Canonical selection aliases: the unsuffixed primary names ARE bbox values.
    metrics["bbox_tiny_recall90"] = bbox_metrics["tiny_recall90"]
    metrics["bbox_overall_recall90"] = bbox_metrics["overall_recall90"]
    metrics["hard_tiny_recovered90_bbox"] = bbox_metrics["hard_tiny_recovered90"]
    metrics["global_empty_images_covered90_bbox"] = bbox_metrics[
        "global_empty_images_covered90"
    ]
    metrics["multi_component_recall90_bbox"] = bbox_metrics["multi_component_recall90"]

    # Pixel sensitivity counterparts (descriptive only; NEVER selection terms).
    metrics["pixel_tiny_recall90"] = pixel_metrics["tiny_recall90"]
    metrics["pixel_overall_recall90"] = pixel_metrics["overall_recall90"]
    metrics["pixel_mean_roi_area_fraction"] = pixel_metrics["mean_roi_area_fraction"]
    metrics["hard_tiny_recovered90_pixel"] = pixel_metrics["hard_tiny_recovered90"]
    metrics["global_empty_images_covered90_pixel"] = pixel_metrics[
        "global_empty_images_covered90"
    ]
    metrics["multi_component_recall90_pixel"] = pixel_metrics["multi_component_recall90"]

    metrics["coverage_semantics_primary"] = BBOX_SEMANTICS
    metrics["coverage_semantics_secondary"] = PIXEL_SEMANTICS
    metrics["component_contract"] = component_contract
    metrics["covered_samples"] = len(covered_samples)

    # ---- H2A: PROPOSAL_PIXEL_ANY_HIT_PRECISION + score diagnostics ----------
    metrics["proposal_pixel_hit_count"] = int(proposal_pixel_hit_count)
    metrics["proposal_total_count"] = int(proposal_total_count)
    metrics["proposal_pixel_any_hit_precision"] = (
        float(proposal_pixel_hit_count) / float(proposal_total_count)
        if proposal_total_count > 0 else 0.0
    )
    metrics["proposal_bbox_any_hit_precision"] = (
        float(proposal_bbox_hit_count) / float(proposal_total_count)
        if proposal_total_count > 0 else 0.0
    )
    metrics["proposal_count_per_image"] = (
        float(proposal_total_count) / float(EXPECTED_VAL_CASES)
    )
    _scores = np.asarray([p[0] for p in score_hit_pairs], dtype=float)
    _hits = np.asarray([1 if p[1] else 0 for p in score_hit_pairs], dtype=int)
    if _scores.size:
        _max = float(_scores.max())
        metrics["proposal_score_mean"] = float(_scores.mean())
        metrics["proposal_score_median"] = float(np.median(_scores))
        metrics["proposal_score_q25"] = float(np.percentile(_scores, 25))
        metrics["proposal_score_q75"] = float(np.percentile(_scores, 75))
        metrics["proposal_score_max"] = _max
        metrics["proposal_score_iqr"] = float(
            np.percentile(_scores, 75) - np.percentile(_scores, 25)
        )
        metrics["fraction_proposals_exactly_at_epoch_max_score"] = float(
            np.mean(_scores >= _max - 1e-12)
        )
        metrics["hit_proposal_score_mean"] = (
            float(_scores[_hits == 1].mean()) if int(_hits.sum()) else float("nan")
        )
        metrics["miss_proposal_score_mean"] = (
            float(_scores[_hits == 0].mean()) if int((_hits == 0).sum()) else float("nan")
        )
        metrics["proposal_roc_auc_score_to_pixel_any_hit"] = _roc_auc(_scores, _hits)
        metrics["proposal_pr_auc_score_to_pixel_any_hit"] = _pr_auc(_scores, _hits)
    else:
        for _name in ("proposal_score_mean", "proposal_score_median", "proposal_score_q25",
                      "proposal_score_q75", "proposal_score_max", "proposal_score_iqr",
                      "fraction_proposals_exactly_at_epoch_max_score",
                      "hit_proposal_score_mean", "miss_proposal_score_mean",
                      "proposal_roc_auc_score_to_pixel_any_hit",
                      "proposal_pr_auc_score_to_pixel_any_hit"):
            metrics[_name] = float("nan")
    metrics["deployment_balance_hmean"] = deployment_balance_hmean(
        metrics["proposal_pixel_any_hit_precision"],
        metrics["tiny_recall90"],
        metrics["overall_recall90"],
    )
    return float(total_val_loss / n_batches), metrics


def _generate_proposals_fixed_config(probability_map, metadata, original_shape,
                                     generate_predicted_rois):
    """Generate proposals with the ONE frozen configuration (scalar tuple)."""
    return generate_predicted_rois(
        probability_map,
        metadata,
        original_shape,
        PROPOSAL_THRESHOLD,
        PROPOSAL_MARGIN,
        PROPOSAL_TOP_K,
        PROPOSAL_NMS_IOU,
    )


def _assert_native_geometry(probability_map) -> None:
    """Fail loud if the model emitted anything other than 128x128."""
    import numpy as np

    array = np.asarray(probability_map)
    if array.shape[-2:] != (HEATMAP_RESOLUTION, HEATMAP_RESOLUTION):
        raise RuntimeError(
            f"VAL probability map spatial shape {array.shape[-2:]} is not "
            f"({HEATMAP_RESOLUTION}, {HEATMAP_RESOLUTION})"
        )


def _load_hard_sets():
    """Load the frozen hard-Tiny / global-empty cohorts for diagnostics only.

    R2B correction:
      * hard-Tiny membership is COMPONENT-level: the identity is
        ``(sample_id, native_component_id)`` — NOT sample_id alone.
      * global-empty membership is IMAGE-level: a frozen set of image IDs whose
        UNet++ GLOBAL prediction was empty. These images DO still contain GT
        components, so this cohort must never be reduced to a "no components"
        branch.

    Returns ``(hard_tiny_keys, global_empty_ids)``.
    """
    import pandas as pd

    for path, expected_sha, label in (
        (HARD_TINY_PATH, HARD_TINY_SHA, "hard-Tiny"),
        (GLOBAL_EMPTY_PATH, GLOBAL_EMPTY_SHA, "global-empty"),
    ):
        if not path.exists():
            raise FileNotFoundError(f"{label} cohort table missing: {path}. STOP.")
        actual = sha256_file(path)
        if actual != expected_sha:
            raise ValueError(
                f"{label} cohort table SHA mismatch: expected {expected_sha}, "
                f"got {actual}. STOP."
            )

    hard_frame = pd.read_csv(HARD_TINY_PATH)
    if "native_component_id" not in hard_frame.columns:
        raise ValueError(
            "hard-Tiny cohort has no 'native_component_id'; component-level "
            "membership cannot be established. STOP."
        )
    hard_tiny_keys = {
        (str(sample_id), int(component_id))
        for sample_id, component_id in zip(
            hard_frame["sample_id"], hard_frame["native_component_id"]
        )
    }
    if len(hard_tiny_keys) != HARD_TINY_COUNT:
        raise ValueError(
            f"hard-Tiny component identities are {len(hard_tiny_keys)}, "
            f"expected {HARD_TINY_COUNT}. STOP."
        )

    empty_frame = pd.read_csv(GLOBAL_EMPTY_PATH)
    global_empty_ids = {str(value) for value in empty_frame["sample_id"].tolist()}
    if len(global_empty_ids) != GLOBAL_EMPTY_COUNT:
        raise ValueError(
            f"global-empty image IDs are {len(global_empty_ids)}, "
            f"expected {GLOBAL_EMPTY_COUNT}. STOP."
        )

    return hard_tiny_keys, global_empty_ids


# ---------------------------------------------------------------------------
# Execution (never entered without supervisor training authorization)
# ---------------------------------------------------------------------------
def _roc_auc(scores, hits) -> float:
    """ROC-AUC of score -> binary hit, tie-aware. Diagnostic only."""
    import numpy as np

    scores = np.asarray(scores, dtype=float)
    hits = np.asarray(hits, dtype=int)
    n1 = int(hits.sum()); n0 = int(len(hits) - n1)
    if n0 == 0 or n1 == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    import pandas as pd

    ranks = pd.Series(ranks).groupby(pd.Series(scores)).transform("mean").to_numpy()
    return float((ranks[hits == 1].sum() - n1 * (n1 + 1) / 2) / (n0 * n1))


def _pr_auc(scores, hits) -> float:
    """PR-AUC (trapezoidal) of score -> binary hit. Diagnostic only."""
    import numpy as np

    scores = np.asarray(scores, dtype=float)
    hits = np.asarray(hits, dtype=int)
    order = np.argsort(-scores, kind="mergesort")
    ys = hits[order]
    tp = np.cumsum(ys)
    fp = np.cumsum(1 - ys)
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / max(int(tp[-1]), 1)
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return float(trap(precision, recall))


def main(argv=None) -> int:
    """Run clean-v3 localizer training."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)

    # --- Lazy imports: keep module import free of heavy/CUDA-touching deps ---
    import numpy as np
    import pandas as pd
    import torch
    from torch.utils.data import DataLoader

    from src.data.kub_localizer_dataset import KUBLocalizerDataset
    from src.losses.soft_target_focal_bce import SoftTargetFocalBCE
    from src.models.factory import create_model
    from src.training.h2a_deployment_balance_selection import (
        DIAGNOSTIC_TERM_NAMES,
        deployment_balance_hmean,
        select_epoch,
    )
    from src.utils.checkpointing import (
        load_training_checkpoint,
        save_training_checkpoint,
    )
    from src.utils.device import get_device
    from src.utils.manifest_guard import (
        get_manifest_path,
        validate_manifest_version_strict,
    )
    from src.utils.reproducibility import make_generator, seed_worker, set_seed
    from src.utils.run_lock import acquire_lock, release_lock
    from src.utils.test_lock import verify_test_lock

    # ---------- 1. static binding gates ----------
    config = load_executable_config(args.config)
    verify_experiment_id(config)
    verify_r2_protocol()
    loss_binding = verify_loss_binding(config)
    assert_no_historical_manifest_usage(config)

    if config.get("manifest_version") != MANIFEST_VERSION:
        raise ValueError(f"manifest_version must be {MANIFEST_VERSION}")
    if config.get("taxonomy_id") != TAXONOMY_ID:
        raise ValueError(f"taxonomy_id must be {TAXONOMY_ID}")
    if config.get("test_allowed") is not False:
        raise ValueError("test_allowed must be false")

    validate_manifest_version_strict(MANIFEST_VERSION)
    verify_test_lock(ROOT)  # TEST remains locked; no TEST data is constructed

    seed = int(config["training"]["seed"])

    # Deterministic seeding BEFORE any model construction / data iteration.
    set_seed(seed, deterministic=True)

    # ---------- 2. population binding ----------
    manifest_train = pd.read_csv(get_manifest_path(MANIFEST_VERSION, "train"))
    manifest_val = pd.read_csv(get_manifest_path(MANIFEST_VERSION, "val"))
    train_ids = set(manifest_train["sample_id"].astype(str))
    val_ids = set(manifest_val["sample_id"].astype(str))

    data_cfg = config["data"]
    train_frame = pd.read_csv(ROOT / data_cfg["sample_table_train"])
    val_frame = pd.read_csv(ROOT / data_cfg["sample_table_val"])
    train_frame = train_frame[
        train_frame["view_type"].eq("FULL_FIELD")
        & train_frame["sample_id"].astype(str).isin(train_ids)
    ].reset_index(drop=True)
    val_frame = val_frame[
        val_frame["view_type"].eq("FULL_FIELD")
        & val_frame["sample_id"].astype(str).isin(val_ids)
    ].reset_index(drop=True)

    if len(train_frame) != EXPECTED_TRAIN_CASES:
        raise ValueError(
            f"TRAIN FULL_FIELD is {len(train_frame)}, expected {EXPECTED_TRAIN_CASES}"
        )
    if len(val_frame) != EXPECTED_VAL_CASES:
        raise ValueError(
            f"VAL FULL_FIELD is {len(val_frame)}, expected {EXPECTED_VAL_CASES}"
        )

    train_patients = set(train_frame["patient_id"].astype(str))
    val_patients = set(val_frame["patient_id"].astype(str))
    overlap = train_patients & val_patients
    if overlap:
        raise ValueError(f"TRAIN/VAL patient overlap must be 0, got {len(overlap)}")

    # ---------- 2b. clean-v3 VAL component source (NOT kub_size_v1, NOT v2) ----
    if not VAL_COMPONENT_TABLE.exists():
        raise FileNotFoundError(
            f"clean-v3 VAL component table missing: {VAL_COMPONENT_TABLE} "
            "— STOP / CHECK_REQUIRED"
        )
    val_component_sha = sha256_file(VAL_COMPONENT_TABLE)
    if val_component_sha != VAL_COMPONENT_TABLE_SHA:
        raise ValueError(
            f"clean-v3 VAL component table SHA mismatch: expected "
            f"{VAL_COMPONENT_TABLE_SHA}, got {val_component_sha}. STOP."
        )
    val_components = pd.read_csv(VAL_COMPONENT_TABLE)
    val_components = val_components[
        val_components["sample_id"].astype(str).isin(val_ids)
    ].reset_index(drop=True)
    if len(val_components) != EXPECTED_VAL_COMPONENTS:
        raise ValueError(
            f"clean-v3 VAL components are {len(val_components)}, "
            f"expected {EXPECTED_VAL_COMPONENTS}"
        )
    if val_components["sample_id"].astype(str).nunique() != EXPECTED_VAL_CASES:
        raise ValueError("clean-v3 VAL component table case count mismatch")
    strata = val_components["size_stratum"].value_counts().to_dict()
    if {str(key): int(value) for key, value in strata.items()} != EXPECTED_VAL_STRATA:
        raise ValueError(
            f"clean-v3 VAL strata mismatch: got {strata}, expected {EXPECTED_VAL_STRATA}"
        )

    # ---------- 3. device + run lock (only inside real training) ----------
    device = get_device(require_cuda=True)

    exp_dir = ROOT / "experiments" / EXPERIMENT_ID
    chk_dir = ROOT / "checkpoints" / EXPERIMENT_ID
    exp_dir.mkdir(parents=True, exist_ok=True)
    chk_dir.mkdir(parents=True, exist_ok=True)

    latest = chk_dir / "latest.pt"
    history_path = exp_dir / "history.csv"
    assert_resumable_or_absent(args, exp_dir, chk_dir)

    acquire_lock(exp_dir, EXPERIMENT_ID, recover_stale=False)

    try:
        # ---------- 4. model with EXPLICIT 128 heatmap resolution ----------
        model = create_model(
            "kub_localizer",
            in_channels=1,
            out_channels=1,
            base_channels=16,
            heatmap_resolution=HEATMAP_RESOLUTION,
        ).to(device)
        if getattr(model, "heatmap_resolution", None) != HEATMAP_RESOLUTION:
            raise RuntimeError("model did not accept heatmap_resolution=128 explicitly")

        sigma = float(config["target"]["sigma"])
        train_ds = KUBLocalizerDataset(
            train_frame, "TRAIN", INPUT_RESOLUTION, sigma,
            heatmap_resolution=HEATMAP_RESOLUTION,
        )
        val_ds = KUBLocalizerDataset(
            val_frame, "VAL", INPUT_RESOLUTION, sigma,
            heatmap_resolution=HEATMAP_RESOLUTION,
        )
        if len(train_ds) != EXPECTED_TRAIN_CASES or len(val_ds) != EXPECTED_VAL_CASES:
            raise ValueError("dataset length does not match the clean-v3 population")

        # Fail-loud shape contract on the FIRST item (one item only; no epoch loop).
        probe = train_ds[0]
        target_shape = tuple(int(value) for value in probe["heatmap"].shape)
        if target_shape != (1, HEATMAP_RESOLUTION, HEATMAP_RESOLUTION):
            raise RuntimeError(
                f"target heatmap shape {target_shape} != (1, {HEATMAP_RESOLUTION}, {HEATMAP_RESOLUTION})"
            )
        with torch.inference_mode():
            probe_out = model(probe["image"].unsqueeze(0).to(device))
        out_shape = tuple(int(value) for value in probe_out.shape)
        if out_shape[-2:] != (HEATMAP_RESOLUTION, HEATMAP_RESOLUTION):
            raise RuntimeError(f"model output spatial shape {out_shape[-2:]} is not 128x128")
        if tuple(probe_out.shape) != (1, 1, HEATMAP_RESOLUTION, HEATMAP_RESOLUTION):
            raise RuntimeError(
                "prediction/target shape equality violated: "
                f"{tuple(probe_out.shape)} vs {target_shape}"
            )

        # ---------- 5. loss = EXACTLY the R2A L1 objective ----------
        criterion = SoftTargetFocalBCE(gamma=float(config["loss"]["gamma"]))
        if type(criterion).__name__ != "SoftTargetFocalBCE":
            raise RuntimeError("executable criterion is not SoftTargetFocalBCE")

        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=float(config["optimizer"]["learning_rate"]),
            weight_decay=float(config["optimizer"]["weight_decay"]),
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, int(config["scheduler"]["T_max"])
        )
        scaler = torch.amp.GradScaler("cuda")

        batch_size = int(config["training"]["batch_size"])
        accumulation = int(config["training"]["accumulation_steps"])
        if accumulation != 1:
            raise ValueError(
                "clean-v3 accumulation_steps must be 1; "
                f"got {accumulation}"
            )
        max_epochs = int(config["training"]["max_epochs"])
        patience = int(config["training"]["early_stopping_patience"])

        # Deterministic loader generators, persisted across resume.
        train_generator = make_generator(seed)
        val_generator = make_generator(seed)

        train_loader = DataLoader(
            train_ds, batch_size=batch_size, shuffle=True,
            num_workers=0, pin_memory=True,
            generator=train_generator, worker_init_fn=seed_worker,
        )
        val_loader = DataLoader(
            val_ds, batch_size=batch_size, shuffle=False,
            num_workers=0, pin_memory=True,
            generator=val_generator, worker_init_fn=seed_worker,
        )

        history = []
        start_epoch = 1
        best_score = None
        best_epoch = None
        bad_epochs = 0
        global_step = 0
        resume_events = []

        if args.resume:
            state = load_training_checkpoint(
                latest, model, optimizer, scheduler, scaler, True, device
            )
            history = load_history_csv(history_path)
            if not history_contiguity(history):
                raise RuntimeError(
                    "resume history.csv is not contiguous; refusing to resume. STOP."
                )
            final_epoch_matches(state, history)

            stored = state.get("best_validation_score")
            best_score = tuple(stored) if stored else None
            best_epoch = state.get("best_epoch")
            if best_epoch is None:
                best_epoch = (state.get("early_stopping_state") or {}).get("best_epoch")
            bad_epochs = int((state.get("early_stopping_state") or {}).get("bad_epochs", 0))
            global_step = int(state.get("global_step", 0))

            # Restore real loader generator state BEFORE the resumed epoch sequence.
            from src.utils.reproducibility import restore_random_state

            generator_states = state.get("loader_generator_states") or {}

            def _cpu_byte_state(value):
                """``torch.Generator.set_state`` requires a CPU uint8 (Byte) tensor.

                ``load_training_checkpoint(..., map_location=device)`` relocates the
                stored generator state onto CUDA, where it is a CUDA ByteTensor and
                ``set_state`` rejects it ("RNG state must be a torch.ByteTensor").
                Move it back to CPU and pin the dtype.
                """
                if isinstance(value, torch.Tensor):
                    return value.detach().to("cpu", torch.uint8)
                return torch.as_tensor(value, dtype=torch.uint8)

            if "train" in generator_states:
                train_generator.set_state(_cpu_byte_state(generator_states["train"]))
            if "val" in generator_states:
                val_generator.set_state(_cpu_byte_state(generator_states["val"]))
            if state.get("random_state"):
                restore_random_state(state["random_state"])

            start_epoch = int(state["epoch"]) + 1
            resume_events.append(
                {
                    "resumed_at": datetime.datetime.utcnow().isoformat() + "Z",
                    "from_epoch": int(state["epoch"]),
                    "to_epoch": start_epoch,
                }
            )

        # ---------- 6. manifest hashes (authoritative, non-empty) ----------
        # ---------- 6. manifest provenance / membership binding ----------
        # Phase-13 Part-1B amendment NON_SCIENTIFIC_PROVENANCE_BINDING:
        # explicit provenance + membership fields replace the unresolvable
        # image_sha256-derived contract. No scientific parameter changes.
        if not MANIFEST_PROVENANCE_BINDING_PATH.exists():
            raise FileNotFoundError(
                "manifest-provenance amendment missing: "
                f"{MANIFEST_PROVENANCE_BINDING_PATH}. STOP / CHECK_REQUIRED."
            )
        stored_amendment_sha = sha256_file(MANIFEST_PROVENANCE_BINDING_PATH)
        if stored_amendment_sha != MANIFEST_PROVENANCE_BINDING_SHA:
            raise ValueError(
                "manifest-provenance amendment SHA mismatch: expected "
                f"{MANIFEST_PROVENANCE_BINDING_SHA}, got {stored_amendment_sha}. STOP."
            )
        amendment = json.loads(
            MANIFEST_PROVENANCE_BINDING_PATH.read_text(encoding="utf-8")
        )
        if amendment.get("status") != MANIFEST_PROVENANCE_BINDING_STATUS:
            raise ValueError(
                "manifest-provenance amendment status is "
                f"{amendment.get('status')!r}, required "
                f"{MANIFEST_PROVENANCE_BINDING_STATUS!r}"
            )
        if int(amendment.get("scientific_parameters_changed", -1)) != 0:
            raise ValueError("manifest-provenance amendment changed scientific parameters")

        manifest_hashes = compute_manifest_hashes(
            MANIFEST_VERSION, train_frame, val_frame,
            train_sample_table=TRAIN_SAMPLE_TABLE,
            val_sample_table=VAL_SAMPLE_TABLE,
        )
        config_sha = sha256_file(CONFIG_PATH)
        r2a_sha = sha256_file(R2A_LOSS_PATH)
        runner_sha = sha256_file(Path(__file__))
        provenance_amendment_sha = stored_amendment_sha
        # R2C now binds the runner; R2B is retained as provenance only (its
        # post_repair_runner_sha intentionally points at the earlier runner).
        r2b = load_r2b_amendment(runner_sha)
        r2b_amendment_sha = r2b["sha"]
        r2c = load_r2c_amendment(runner_sha)
        r2c_amendment_sha = r2c["sha"]
        # ---- H2-A-B1 PROVENANCE GATE ------------------------------------------
        # The Phase-13 R2C gate binds the PHASE-13 runner file SHA, so it cannot
        # bind this replay runner. It is therefore retained as PROVENANCE ONLY
        # (r2c_amendment_sha is still recorded), and the GOVERNING binding for
        # this run is the frozen H2A protocol artifact. This is a provenance
        # re-pointing with NO gradient or scientific-semantics effect.
        if not H2B_PROTOCOL_PATH.exists():
            raise RuntimeError(f"H2B protocol artifact missing: {H2B_PROTOCOL_PATH}")
        if sha256_file(H2B_PROTOCOL_PATH) != H2B_PROTOCOL_SHA:
            raise RuntimeError(
                "H2A protocol SHA mismatch: expected "
                f"{H2B_PROTOCOL_SHA}, got {sha256_file(H2B_PROTOCOL_PATH)}. STOP."
            )
        h2a_protocol = json.loads(H2B_PROTOCOL_PATH.read_text(encoding="utf-8"))
        if h2a_protocol.get("status") != H2B_PROTOCOL_REQUIRED_STATUS:
            raise RuntimeError(
                f"H2A protocol status is {h2a_protocol.get('status')!r}, required "
                f"{H2B_PROTOCOL_REQUIRED_STATUS!r}. STOP."
            )
        if h2a_protocol.get("experiment_id") != EXPERIMENT_ID:
            raise RuntimeError(
                f"H2A protocol experiment_id {h2a_protocol.get('experiment_id')!r} != "
                f"{EXPERIMENT_ID!r}. STOP."
            )
        if not H2A_SCORE_PATH_AUDIT_PATH.exists():
            raise RuntimeError(f"H2A score-path audit missing: {H2A_SCORE_PATH_AUDIT_PATH}")
        if sha256_file(H2A_SCORE_PATH_AUDIT_PATH) != H2A_SCORE_PATH_AUDIT_SHA:
            raise RuntimeError("H2A score-path audit SHA mismatch. STOP.")
        h2a_score_audit = json.loads(H2A_SCORE_PATH_AUDIT_PATH.read_text(encoding="utf-8"))
        if h2a_score_audit.get("verdict") != H2A_SCORE_PATH_REQUIRED_VERDICT:
            raise RuntimeError(
                f"H2A score-path verdict is {h2a_score_audit.get('verdict')!r}, required "
                f"{H2A_SCORE_PATH_REQUIRED_VERDICT!r}. STOP."
            )
        if not R2B_AMENDMENT_PATH.exists():
            raise RuntimeError("R2B amendment must be preserved as provenance. STOP.")

        if args.resume:
            resume_state = load_training_checkpoint(
                latest, model, optimizer, scheduler, scaler, False, device
            )
            assert_resume_identity(resume_state, config, manifest_hashes, seed)
            r2b_transition = resume_state.get("_r2b_runner_sha_transition")
            if r2b_transition:
                resume_events.append({"r2b_runner_sha_transition": r2b_transition})

        # ---------- 7. training-start audit (BEFORE epoch 1) ----------
        if start_epoch == 1:
            start_payload = {
                "artifact": "POST_PHASE13_H2B_B1_TRAINING_START",
                "experiment_id": EXPERIMENT_ID,
                "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "protocol_identity": H2B_PROTOCOL_IDENTITY,
                "h2b_protocol_sha": H2B_PROTOCOL_SHA,
                "h2b_loss_module_path": str(LOSS_MODULE_PATH.relative_to(ROOT)).replace("\\", "/"),
                "h2b_loss_module_sha": LOSS_MODULE_SHA,
                "objective_change_id": OBJECTIVE_CHANGE_ID,
                "parent_provenance": {
                    "r2_protocol_sha": R2_PROTOCOL_SHA,
                    "r2a_loss_binding_sha": r2a_sha,
                    "role": "PARENT_PROVENANCE_ONLY__NOT_ACTIVE_H2B_OBJECTIVE",
                },
                "provenance_amendment_path": str(MANIFEST_PROVENANCE_BINDING_PATH),
                "provenance_amendment_sha": provenance_amendment_sha,
                "provenance_amendment_type": "NON_SCIENTIFIC_PROVENANCE_BINDING",
                "config_path": str(CONFIG_PATH),
                "config_sha": config_sha,
                "runner_path": str(Path(__file__)),
                "runner_sha": runner_sha,
                "manifest_version": MANIFEST_VERSION,
                "manifest_hashes": manifest_hashes,
                "taxonomy_id": TAXONOMY_ID,
                "heatmap_resolution": HEATMAP_RESOLUTION,
                "input_resolution": INPUT_RESOLUTION,
                "proposal_configuration_count": PROPOSAL_CONFIGURATION_COUNT,
                "proposal_config": {
                    "threshold": PROPOSAL_THRESHOLD,
                    "margin": PROPOSAL_MARGIN,
                    "top_k": PROPOSAL_TOP_K,
                    "nms_iou": PROPOSAL_NMS_IOU,
                },
                "grid_search_enabled": GRID_SEARCH_ENABLED,
                "checkpoint_selection_tuple": [
                    "DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90",
                    "tiny_recall90",
                    "overall_recall90",
                    "PROPOSAL_PIXEL_ANY_HIT_PRECISION",
                    "-mean_roi_area_fraction",
                    "-val_loss",
                ],
                "loss": loss_binding,
                "seed": seed,
                "max_epochs": max_epochs,
                "patience": patience,
                "batch_size": batch_size,
                "accumulation_steps": accumulation,
                "train_cases": len(train_frame),
                "train_components": EXPECTED_TRAIN_COMPONENTS,
                "val_cases": len(val_frame),
                "val_components": EXPECTED_VAL_COMPONENTS,
                "val_strata": EXPECTED_VAL_STRATA,
                "val_component_table": str(VAL_COMPONENT_TABLE),
                "val_component_table_sha": val_component_sha,
                "scientific_parameter_changes": 1,
                "test_reads": 0,
                "scientific_changes": 1,
                "scientific_change_register": {
                    "CHANGE_H2B_001": "loss/objective semantics only",
                },
            }
            write_audit_json_md(
                TRAINING_START_BASENAME, start_payload,
                f"# POST-PHASE-13 H2B-B1 LOCALIZER TRAINING START\n\n"
                f"- experiment_id: `{EXPERIMENT_ID}`\n"
                f"- protocol: {H2B_PROTOCOL_IDENTITY}\n"
                f"- loss: `{LOSS_CLASS}` gamma=2.0 soft-target focal BCE (no Dice)\n"
                f"- config_sha: `{config_sha}`\n"
                f"- population: TRAIN {len(train_frame)} / VAL {len(val_frame)}\n"
                f"- TEST reads: 0\n",
            )

        from tqdm import tqdm

        termination_reason = "MAX_EPOCHS_REACHED"
        nan_inf_events = []
        best_fixed_config_metrics = None
        best_secondary_diagnostics = None
        best_row = None

        for epoch in range(start_epoch, max_epochs + 1):
            # 1. TRAIN epoch
            model.train()
            optimizer.zero_grad(set_to_none=True)
            train_losses = []
            for batch in tqdm(train_loader, desc=f"Epoch {epoch:03d} [Train]"):
                with torch.amp.autocast("cuda"):
                    loss = criterion(
                        model(batch["image"].to(device)),
                        batch["heatmap"].to(device),
                    ) / accumulation
                if not torch.isfinite(loss):
                    nan_inf_events.append({"epoch": epoch, "stage": "train_loss"})
                    raise RuntimeError(f"non-finite TRAIN loss at epoch {epoch}")
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                train_losses.append(float(loss.item()) * accumulation)
                global_step += 1

            # 2. VAL evaluate + 3. ONE fixed proposal configuration
            val_loss, metrics = evaluate_fixed_config_localizer(
                model, val_loader, criterion, device, config,
                val_component_frame=val_components,
                val_sample_frame=val_frame,
            )
            if not np.isfinite(val_loss):
                nan_inf_events.append({"epoch": epoch, "stage": "val_loss"})
                raise RuntimeError(f"non-finite VAL loss at epoch {epoch}")

            # 4. H2-A-B1 6-term deployment-balanced score
            outcome = select_epoch(
                deployment_balance_hmean=metrics["deployment_balance_hmean"],
                tiny_recall90=metrics["tiny_recall90"],
                overall_recall90=metrics["overall_recall90"],
                proposal_pixel_any_hit_precision=metrics["proposal_pixel_any_hit_precision"],
                mean_roi_area_fraction=metrics["mean_roi_area_fraction"],
                val_loss=val_loss,
                best_score=best_score,
                best_epoch=best_epoch,
                bad_epochs=bad_epochs,
                epoch=epoch,
                patience=patience,
                proposal_configuration_count=PROPOSAL_CONFIGURATION_COUNT,
                zero_denominator=bool(metrics.get("zero_denominator", False)),
            )

            # 5. bookkeeping, 6. scheduler, 7. history
            if outcome.is_new_best:
                best_score = outcome.score
                best_epoch = epoch
            bad_epochs = outcome.bad_epochs
            scheduler.step()

            row = {
                "epoch": epoch,
                "train_loss": float(np.mean(train_losses)),
                "val_loss": float(val_loss),
                "learning_rate": optimizer.param_groups[0]["lr"],
                "tiny_recall90": metrics["tiny_recall90"],
                "overall_recall90": metrics["overall_recall90"],
                "mean_roi_area_fraction": metrics["mean_roi_area_fraction"],
                # H2A primary precision term (independently auditable counts).
                "proposal_pixel_hit_count": metrics["proposal_pixel_hit_count"],
                "proposal_total_count": metrics["proposal_total_count"],
                "proposal_pixel_any_hit_precision": metrics["proposal_pixel_any_hit_precision"],
                "proposal_bbox_any_hit_precision": metrics["proposal_bbox_any_hit_precision"],
                "deployment_balance_hmean": metrics["deployment_balance_hmean"],
                "proposal_count_per_image": metrics["proposal_count_per_image"],
                "proposal_score_mean": metrics["proposal_score_mean"],
                "proposal_score_median": metrics["proposal_score_median"],
                "proposal_score_q25": metrics["proposal_score_q25"],
                "proposal_score_q75": metrics["proposal_score_q75"],
                "proposal_score_max": metrics["proposal_score_max"],
                "proposal_score_iqr": metrics["proposal_score_iqr"],
                "fraction_proposals_exactly_at_epoch_max_score": metrics[
                    "fraction_proposals_exactly_at_epoch_max_score"
                ],
                "hit_proposal_score_mean": metrics["hit_proposal_score_mean"],
                "miss_proposal_score_mean": metrics["miss_proposal_score_mean"],
                "proposal_roc_auc_score_to_pixel_any_hit": metrics[
                    "proposal_roc_auc_score_to_pixel_any_hit"
                ],
                "proposal_pr_auc_score_to_pixel_any_hit": metrics[
                    "proposal_pr_auc_score_to_pixel_any_hit"
                ],
                **outcome.as_row_fields(),
            }
            # Secondary diagnostics: RECORDED, never passed to selection.
            for name in DIAGNOSTIC_TERM_NAMES:
                row[name] = metrics.get(name)
            for name in (
                "overall_recall50",
                "any_overlap_recall",
                "mean_coverage",
            ):
                row[name] = metrics.get(name)
            # R2C (§14): every new row states which coverage semantics produced
            # its PRIMARY terms, plus the pixel-mask sensitivity counterparts.
            row["coverage_semantics_primary"] = metrics["coverage_semantics_primary"]
            for name in (
                "pixel_tiny_recall90",
                "pixel_overall_recall90",
                "pixel_mean_roi_area_fraction",
                "hard_tiny_recovered90_pixel",
                "global_empty_images_covered90_pixel",
                "multi_component_recall90_pixel",
            ):
                row[name] = metrics.get(name)
            history.append(row)
            write_history_atomic(history_path, history)

            if outcome.is_new_best:
                best_row = dict(row)
                best_fixed_config_metrics = {
                    "tiny_recall90": metrics["tiny_recall90"],
                    "overall_recall90": metrics["overall_recall90"],
                    "mean_roi_area_fraction": metrics["mean_roi_area_fraction"],
                    "val_loss": float(val_loss),
                }
                best_secondary_diagnostics = {
                    name: metrics.get(name) for name in DIAGNOSTIC_TERM_NAMES
                }

            # 8. latest.pt every epoch, 9. best.pt only on strict improvement
            from src.training.h2a_deployment_balance_selection import SELECTION_TERM_NAMES

            common = dict(
                best_validation_score=best_score if best_score else (),
                configuration=config,
                seed=seed,
                training_history=history,
                manifest_version=MANIFEST_VERSION,
                manifest_hashes=manifest_hashes,
                experiment_id=EXPERIMENT_ID,
                model_name="kub_localizer",
                input_resolution=INPUT_RESOLUTION,
                threshold=PROPOSAL_THRESHOLD,
                taxonomy_id=TAXONOMY_ID,
                early_stopping_state={
                    "best_epoch": best_epoch,
                    "bad_epochs": bad_epochs,
                    "patience": patience,
                },
                loader_generator_states={
                    "train": train_generator.get_state().clone(),
                    "val": val_generator.get_state().clone(),
                },
            )
            # Extended checkpoint metadata (R0-R1 + Part-1B provenance binding).
            # ``save_training_checkpoint`` has a FIXED signature, so extended
            # metadata is persisted inside the ``configuration`` mapping — which
            # the checkpoint format freely accepts — rather than as extra kwargs.
            checkpoint_configuration = dict(config)
            checkpoint_configuration["_phase13_execution_metadata"] = {
                "r2_protocol_sha": R2_PROTOCOL_SHA,
                "r2a_loss_sha": r2a_sha,
                "config_sha": config_sha,
                "runner_sha": runner_sha,
                "provenance_amendment_sha": provenance_amendment_sha,
                "provenance_amendment_type": "NON_SCIENTIFIC_PROVENANCE_BINDING",
                "r2b_amendment": R2B_AMENDMENT_NAME,
                "r2b_amendment_sha": r2b_amendment_sha,
                "metric_semantics": "R2B_PIXEL_MASK_COMPONENT_COVERAGE",
                "r2c_amendment": R2C_AMENDMENT_NAME,
                "r2c_amendment_sha": r2c_amendment_sha,
                "coverage_semantics": PRIMARY_COVERAGE_SEMANTICS,
                "coverage_semantics_secondary": SECONDARY_COVERAGE_SEMANTICS,
                "heatmap_resolution": HEATMAP_RESOLUTION,
                "proposal_config": {
                    "threshold": PROPOSAL_THRESHOLD,
                    "margin": PROPOSAL_MARGIN,
                    "top_k": PROPOSAL_TOP_K,
                    "nms_iou": PROPOSAL_NMS_IOU,
                },
                "proposal_configuration_count": PROPOSAL_CONFIGURATION_COUNT,
                "grid_search_enabled": GRID_SEARCH_ENABLED,
                "selection_term_names": list(SELECTION_TERM_NAMES),
                "best_epoch": best_epoch,
                "loss_class": LOSS_CLASS,
                "loss_label": LOSS_LABEL,
                "loss_gamma": 2.0,
                "loss_modulation_detached": "NO",
                "loss_target_clamping": "NONE",
                "loss_target_binary_conversion": "NONE",
                "loss_dice_weight": "NONE",
                "dice_term": "NONE",
                "auxiliary_loss": "NONE",
                "objective_change_id": OBJECTIVE_CHANGE_ID,
                "h2b_protocol_sha": H2B_PROTOCOL_SHA,
                "h2b_loss_module_sha": LOSS_MODULE_SHA,
                "selection_rule_source": "H2A_DEPLOYMENT_BALANCED_6TERM_CARRY_FORWARD",
                "parent_provenance": {
                    "historical_phase13_parent_provenance": {
                        "r2_protocol_sha": R2_PROTOCOL_SHA,
                        "r2a_loss_binding_sha": r2a_sha,
                        "note": ("Phase-13 parent lineage. NOT the active H2B objective. "
                                 "The Phase-13 parent objective was "
                                 "CenterNetFocalLoss(alpha=2.0, beta=4.0)."),
                    },
                },
            }
            common["configuration"] = checkpoint_configuration
            save_training_checkpoint(
                latest, model, optimizer, scheduler, scaler,
                epoch, global_step, **common,
            )
            if outcome.is_new_best:
                save_training_checkpoint(
                    chk_dir / "best.pt", model, optimizer, scheduler, scaler,
                    epoch, global_step, **common,
                )

            # 10. stop decision
            if outcome.stopped:
                termination_reason = "EARLY_STOPPING_PATIENCE"
                break

        # ---------- 8. training-completion audit ----------
        final_epoch = int(history[-1]["epoch"]) if history else 0
        completion_payload = {
            "artifact": "POST_PHASE13_H2B_B1_TRAINING_COMPLETION",
            "experiment_id": EXPERIMENT_ID,
            "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "protocol_identity": H2B_PROTOCOL_IDENTITY,
            "h2b_protocol_sha": H2B_PROTOCOL_SHA,
            "h2b_loss_module_sha": LOSS_MODULE_SHA,
            "objective_change_id": OBJECTIVE_CHANGE_ID,
            "parent_provenance": {
                "r2_protocol_sha": R2_PROTOCOL_SHA,
                "r2a_loss_binding_sha": r2a_sha,
                "role": "PARENT_PROVENANCE_ONLY__NOT_ACTIVE_H2B_OBJECTIVE",
            },
            "best_epoch": best_epoch,
            "final_epoch": final_epoch,
            "termination_reason": termination_reason,
            "best_selection_tuple": list(best_score) if best_score else None,
            "selection_term_names": None if best_score is None else list(
                __import__("src.training.clean_v3_selection", fromlist=["SELECTION_TERM_NAMES"]).SELECTION_TERM_NAMES
            ),
            "best_fixed_config_metrics": best_fixed_config_metrics,
            "best_secondary_diagnostics": best_secondary_diagnostics,
            "best_epoch_row": best_row,
            "history_path": str(history_path),
            "history_sha": sha256_file(history_path) if history_path.exists() else None,
            "best_checkpoint_path": str(chk_dir / "best.pt"),
            "best_checkpoint_sha": (
                sha256_file(chk_dir / "best.pt") if (chk_dir / "best.pt").exists() else None
            ),
            "latest_checkpoint_path": str(latest),
            "latest_checkpoint_sha": sha256_file(latest) if latest.exists() else None,
            "config_path": str(CONFIG_PATH),
            "config_sha": config_sha,
            "runner_path": str(Path(__file__)),
            "runner_sha": runner_sha,
            "provenance_amendment_path": str(MANIFEST_PROVENANCE_BINDING_PATH),
            "provenance_amendment_sha": provenance_amendment_sha,
            "provenance_amendment_type": "NON_SCIENTIFIC_PROVENANCE_BINDING",
            "r2_protocol_sha": R2_PROTOCOL_SHA,
            "r2a_loss_sha": r2a_sha,
            "manifest_version": MANIFEST_VERSION,
            "manifest_hashes": manifest_hashes,
            "taxonomy_id": TAXONOMY_ID,
            "heatmap_resolution": HEATMAP_RESOLUTION,
            "proposal_configuration_count": PROPOSAL_CONFIGURATION_COUNT,
            "proposal_config": {
                "threshold": PROPOSAL_THRESHOLD,
                "margin": PROPOSAL_MARGIN,
                "top_k": PROPOSAL_TOP_K,
                "nms_iou": PROPOSAL_NMS_IOU,
            },
            "loss": loss_binding,
            "seed": seed,
            "resume_events": resume_events,
            "nan_inf_events": nan_inf_events,
            "grid_configurations_evaluated": 0,
            "test_reads": 0,
            "scientific_changes": 1,
            "scientific_parameter_changes": 1,
            "scientific_change_register": {
                "CHANGE_H2B_001": "loss/objective semantics only",
            },
        }
        write_audit_json_md(
            TRAINING_COMPLETION_BASENAME, completion_payload,
            f"# POST-PHASE-13 H2B-B1 LOCALIZER TRAINING COMPLETION\n\n"
            f"- experiment_id: `{EXPERIMENT_ID}`\n"
            f"- best_epoch: {best_epoch} / final_epoch: {final_epoch}\n"
            f"- termination_reason: {termination_reason}\n"
            f"- best selection tuple: {list(best_score) if best_score else None}\n"
            f"- grid configurations evaluated: 0\n"
            f"- TEST reads: 0\n",
        )
    finally:
        release_lock(exp_dir, force=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
