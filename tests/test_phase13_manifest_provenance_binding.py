"""Production-shape manifest-provenance binding tests for PHASE-13 PART-1B.

These tests exercise the REAL production schema, not a synthetic stand-in.

The previous Gate-N test fabricated an ``image_sha256`` column and therefore
passed while production failed. That is exactly the defect this suite exists to
prevent, so this suite:

  * loads the REAL phase4_v3 manifests and the REAL sample tables
  * runs the REAL join/filter the runner performs
  * calls the REAL ``compute_manifest_hashes`` implementation

It may read manifest CSVs and sample-table CSVs. It must NOT:

  * read image pixels
  * read mask pixels
  * construct a model
  * request CUDA
  * iterate a DataLoader
  * touch TEST

Amendment identity
------------------
``reports/audits/phase13_clean_v3_localizer_manifest_provenance_binding.json``
status ``PROVENANCE_BINDING_APPROVED_FOR_PART1B``,
type ``NON_SCIENTIFIC_PROVENANCE_BINDING``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
AMENDMENT_PATH = (
    ROOT / "reports" / "audits"
    / "phase13_clean_v3_localizer_manifest_provenance_binding.json"
)
AMENDMENT_SHA = "436831dbaf3305e632e6b4a34adb0eb1b4b1edf962e74354d337ec1328bfdd5a"

MANIFEST_VERSION = "phase4_v3"
EXPECTED_TRAIN = 770
EXPECTED_VAL = 103

OBSOLETE_FIELDS = ("train_table_sha256", "val_table_sha256")

REQUIRED_SHA_FIELDS = (
    "train_manifest_file_sha256",
    "val_manifest_file_sha256",
    "train_sample_table_file_sha256",
    "val_sample_table_file_sha256",
    "train_filtered_sample_ids_sha256",
    "val_filtered_sample_ids_sha256",
)

REQUIRED_COUNT_FIELDS = (
    "train_filtered_sample_count",
    "val_filtered_sample_count",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def runner():
    spec = importlib.util.spec_from_file_location(
        "phase13_clean_v3_runner", RUNNER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def manifest_paths():
    from src.utils.manifest_guard import get_manifest_path

    return {
        "train": Path(get_manifest_path(MANIFEST_VERSION, "train")),
        "val": Path(get_manifest_path(MANIFEST_VERSION, "val")),
    }


@pytest.fixture(scope="module")
def frames(runner):
    """The REAL filtered FULL_FIELD frames, exactly as the runner builds them."""
    from src.utils.manifest_guard import get_manifest_path

    manifest_train = pd.read_csv(get_manifest_path(MANIFEST_VERSION, "train"))
    manifest_val = pd.read_csv(get_manifest_path(MANIFEST_VERSION, "val"))
    train_ids = set(manifest_train["sample_id"].astype(str))
    val_ids = set(manifest_val["sample_id"].astype(str))

    train_table = pd.read_csv(runner.TRAIN_SAMPLE_TABLE)
    val_table = pd.read_csv(runner.VAL_SAMPLE_TABLE)

    train_frame = train_table[
        train_table["view_type"].eq("FULL_FIELD")
        & train_table["sample_id"].astype(str).isin(train_ids)
    ].reset_index(drop=True)
    val_frame = val_table[
        val_table["view_type"].eq("FULL_FIELD")
        & val_table["sample_id"].astype(str).isin(val_ids)
    ].reset_index(drop=True)
    return train_frame, val_frame


@pytest.fixture(scope="module")
def provenance(runner, frames):
    train_frame, val_frame = frames
    return runner.compute_manifest_hashes(
        MANIFEST_VERSION,
        train_frame,
        val_frame,
        train_sample_table=runner.TRAIN_SAMPLE_TABLE,
        val_sample_table=runner.VAL_SAMPLE_TABLE,
    )


def _physical_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


# ===========================================================================
# A. Real source tables require no image_sha256 column
# ===========================================================================
def test_A_real_tables_do_not_require_image_sha256(runner):
    """The production input schema has no image_sha256 column, and the
    provenance binding must not demand one."""
    train_table = pd.read_csv(runner.TRAIN_SAMPLE_TABLE)
    val_table = pd.read_csv(runner.VAL_SAMPLE_TABLE)

    assert "image_sha256" not in train_table.columns
    assert "image_sha256" not in val_table.columns

    # the implementation must not reference the column at all
    source = RUNNER_PATH.read_text(encoding="utf-8")
    assert 'frame, "image_sha256"' not in source
    assert "'image_sha256'" not in source


# ===========================================================================
# B. phase4_v3 + FULL_FIELD filtering reproduces the frozen population
# ===========================================================================
def test_B_filtering_reproduces_frozen_population(frames):
    train_frame, val_frame = frames
    assert len(train_frame) == EXPECTED_TRAIN
    assert len(val_frame) == EXPECTED_VAL


# ===========================================================================
# C. Filtered sample IDs are unique
# ===========================================================================
def test_C_filtered_sample_ids_unique(frames):
    train_frame, val_frame = frames
    for label, frame in (("TRAIN", train_frame), ("VAL", val_frame)):
        ids = [str(value) for value in frame["sample_id"].tolist()]
        assert len(set(ids)) == len(ids), f"{label} sample_ids not unique"


# ===========================================================================
# D. All eight explicit fields resolve
# ===========================================================================
def test_D_all_required_fields_resolve(provenance):
    for key in REQUIRED_SHA_FIELDS:
        assert isinstance(provenance[key], str), f"{key} is not a string"
        assert len(provenance[key]) == 64, f"{key} is not a 64-hex digest"
        int(provenance[key], 16)  # must be valid hex

    for key in REQUIRED_COUNT_FIELDS:
        assert isinstance(provenance[key], int), f"{key} is not an int"
        assert provenance[key] > 0, f"{key} resolved empty"

    assert provenance["train_filtered_sample_count"] == EXPECTED_TRAIN
    assert provenance["val_filtered_sample_count"] == EXPECTED_VAL


# ===========================================================================
# E. Shuffled row order produces an identical membership digest
# ===========================================================================
def test_E_shuffle_invariance(runner, frames):
    train_frame, val_frame = frames

    train_shuffled = train_frame.sample(frac=1.0, random_state=1234).reset_index(drop=True)
    val_shuffled = val_frame.sample(frac=1.0, random_state=4321).reset_index(drop=True)

    assert runner.filtered_sample_ids_digest(train_shuffled) == \
        runner.filtered_sample_ids_digest(train_frame)
    assert runner.filtered_sample_ids_digest(val_shuffled) == \
        runner.filtered_sample_ids_digest(val_frame)

    shuffled_prov = runner.compute_manifest_hashes(
        MANIFEST_VERSION, train_shuffled, val_shuffled,
        train_sample_table=runner.TRAIN_SAMPLE_TABLE,
        val_sample_table=runner.VAL_SAMPLE_TABLE,
    )
    base_prov = runner.compute_manifest_hashes(
        MANIFEST_VERSION, train_frame, val_frame,
        train_sample_table=runner.TRAIN_SAMPLE_TABLE,
        val_sample_table=runner.VAL_SAMPLE_TABLE,
    )
    for key in REQUIRED_SHA_FIELDS:
        assert shuffled_prov[key] == base_prov[key], f"{key} changed under shuffle"


# ===========================================================================
# F. Adding/removing one sample ID changes the membership digest
# ===========================================================================
def test_F_membership_change_alters_digest(runner, frames):
    train_frame, _val_frame = frames

    base = runner.filtered_sample_ids_digest(train_frame)

    # remove one member
    removed = train_frame.iloc[:-1].reset_index(drop=True)
    assert runner.filtered_sample_ids_digest(removed) != base

    # add one member (clone the first row under a fresh id)
    added = train_frame.copy()
    extra = added.iloc[[0]].copy()
    extra["sample_id"] = "__SYNTHETIC_MEMBERSHIP_PROBE__"
    added = pd.concat([added, extra], ignore_index=True)
    assert runner.filtered_sample_ids_digest(added) != base


# ===========================================================================
# G. File SHA fields equal the direct physical SHA-256 of their sources
# ===========================================================================
def test_G_file_shas_match_physical_bytes(provenance, manifest_paths, runner):
    assert provenance["train_manifest_file_sha256"] == _physical_sha(manifest_paths["train"])
    assert provenance["val_manifest_file_sha256"] == _physical_sha(manifest_paths["val"])
    assert provenance["train_sample_table_file_sha256"] == _physical_sha(runner.TRAIN_SAMPLE_TABLE)
    assert provenance["val_sample_table_file_sha256"] == _physical_sha(runner.VAL_SAMPLE_TABLE)


# ===========================================================================
# H. No TEST file is opened
# ===========================================================================
def test_H_no_test_file_opened(runner, frames, monkeypatch):
    """Any attempt to open a TEST-split file during provenance must fail."""
    opened = []
    real_open = open

    def guarded_open(file, *args, **kwargs):
        path = str(file).replace("\\", "/").lower()
        opened.append(path)
        if "test" in Path(path).name and path.endswith(".csv"):
            raise AssertionError(f"TEST file opened during provenance: {file}")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)
    train_frame, val_frame = frames
    runner.compute_manifest_hashes(
        MANIFEST_VERSION, train_frame, val_frame,
        train_sample_table=runner.TRAIN_SAMPLE_TABLE,
        val_sample_table=runner.VAL_SAMPLE_TABLE,
    )
    monkeypatch.undo()

    assert not any("manifests/phase4_v3/test" in p for p in opened)
    assert not any("manifests/test.csv" in p for p in opened)


# ===========================================================================
# I. Superseded field names absent from executable provenance
# ===========================================================================
def test_I_obsolete_fields_absent_from_provenance(provenance):
    for field in OBSOLETE_FIELDS:
        assert field not in provenance, (
            f"superseded field {field} present in executable provenance"
        )


# ===========================================================================
# J. Amendment identity
# ===========================================================================
def test_J_amendment_identity_and_status(runner):
    assert AMENDMENT_PATH.exists()
    assert _physical_sha(AMENDMENT_PATH) == AMENDMENT_SHA
    assert runner.MANIFEST_PROVENANCE_BINDING_SHA == AMENDMENT_SHA

    payload = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))
    assert payload["status"] == "PROVENANCE_BINDING_APPROVED_FOR_PART1B"
    assert payload["amendment_type"] == "NON_SCIENTIFIC_PROVENANCE_BINDING"
    assert payload["old_contract_status"] == "SUPERSEDED_UNRESOLVABLE_FIELD_SEMANTICS"
    assert payload["scientific_parameters_changed"] == 0
    assert payload["population_changed"] is False
    assert payload["manifest_changed"] is False
    assert payload["training_data_changed"] is False
    assert payload["image_sha256_fabricated"] is False
    assert payload["image_content_hash_claim_made"] is False
    assert payload["test_reads"] == 0


# ===========================================================================
# K. Loud failure modes
# ===========================================================================
def test_K_missing_sample_table_fails_loudly(runner, frames):
    train_frame, val_frame = frames
    with pytest.raises(FileNotFoundError):
        runner.compute_manifest_hashes(
            MANIFEST_VERSION, train_frame, val_frame,
            train_sample_table=ROOT / "does" / "not" / "exist.csv",
            val_sample_table=runner.VAL_SAMPLE_TABLE,
        )


def test_K_wrong_membership_count_fails_loudly(runner, frames):
    train_frame, val_frame = frames
    with pytest.raises(ValueError, match="membership count"):
        runner.compute_manifest_hashes(
            MANIFEST_VERSION, train_frame.iloc[:-1].reset_index(drop=True), val_frame,
            train_sample_table=runner.TRAIN_SAMPLE_TABLE,
            val_sample_table=runner.VAL_SAMPLE_TABLE,
        )


def test_K_duplicate_sample_ids_fail_loudly(runner, frames):
    train_frame, val_frame = frames
    train_frame = train_frame.copy()
    train_frame.loc[1, "sample_id"] = train_frame.loc[0, "sample_id"]
    with pytest.raises(ValueError, match="not unique"):
        runner.filtered_sample_ids_digest(train_frame)


def test_K_missing_sample_id_column_fails_loudly(runner):
    with pytest.raises(ValueError, match="no 'sample_id' column"):
        runner.filtered_sample_ids_digest(pd.DataFrame({"other": [1, 2]}))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "--no-header"]))
