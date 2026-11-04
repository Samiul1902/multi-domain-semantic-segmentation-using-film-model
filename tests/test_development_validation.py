import numpy as np
from PIL import Image
import pytest

from src.data.development_validation import DevelopmentValidationError, validate_rows


def row(tmp_path, sample="s1", split="TRAIN", value=10):
    image = tmp_path / f"{sample}.png"
    mask = tmp_path / f"{sample}-mask.png"
    Image.fromarray(np.full((8, 12), value, dtype=np.uint8)).save(image)
    Image.fromarray(np.ones((8, 12), dtype=np.uint8)).save(mask)
    return dict(sample_id=sample, split=split, dataset="KUB", task_id=3,
                image_path=str(image), mask_path=str(mask), category="Kidney_Stone")


def test_protected_row_refused_before_any_pixel(tmp_path, monkeypatch):
    valid = row(tmp_path)
    protected = dict(valid, sample_id="protected", split="TEST")
    monkeypatch.setattr(Image, "open", lambda *a, **k: pytest.fail("pixels opened"))
    with pytest.raises(PermissionError):
        validate_rows([valid, protected])


def test_duplicates_and_group_leakage(tmp_path):
    a, b = row(tmp_path), row(tmp_path, "s2", "VAL")
    a["patient_id"] = b["patient_id"] = "synthetic-patient"
    result = validate_rows([a, b])
    assert result["status"] == "LEAKAGE_DETECTED"
    assert len(result["cross_split_image_groups"]) == len(result["cross_split_patient_groups"]) == 1


def test_geometry_identity_and_domain_checks(tmp_path):
    a = row(tmp_path)
    assert validate_rows([a])["status"] == "VALIDATED_DEVELOPMENT_ONLY"
    with pytest.raises(DevelopmentValidationError):
        validate_rows([a, a])
    with pytest.raises(DevelopmentValidationError):
        validate_rows([dict(a, task_id=0)])
    Image.fromarray(np.zeros((2, 2), dtype=np.uint8)).save(a["mask_path"])
    with pytest.raises(DevelopmentValidationError, match="geometry"):
        validate_rows([a])


def test_metadata_not_used_for_pixel_processing(tmp_path):
    a = row(tmp_path)
    assert validate_rows([a]) == validate_rows([dict(a, category="Ureteric_Stone")])
