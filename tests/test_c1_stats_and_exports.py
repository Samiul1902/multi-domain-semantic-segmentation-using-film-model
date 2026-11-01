"""C1 statistics review tests and run-artifact validation/export tests."""
from __future__ import annotations

import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from src.research.evaluation_r1.statistics import paired_bootstrap  # noqa: E402
from src.research.paper_assets import c1_run_export as X  # noqa: E402

SEEDS, DOMS = (42, 123, 3407), ("KUB", "ISIC", "BUSI", "KVASIR")


def rows(delta=0.1, n=6, patients=3):
    out = []
    for d in DOMS:
        for i in range(n):
            for s in SEEDS:
                out.append({"domain": d, "sample_id": f"{d}-{i}", "seed": s, "treatment": 0.6 + delta, "control": 0.6,
                            "patient_id": f"p{i % patients}" if d == "KUB" else None})
    return out


def boot(r, **kw):
    return paired_bootstrap(r, seeds=SEEDS, domains=DOMS, n_boot=kw.pop("n_boot", 200), **kw)


class TestBootstrapProtocol:
    def test_sign_and_equal_domain_estimate(self):
        r = boot(rows(0.1))
        assert r["estimate"] == pytest.approx(0.1) and r["ci"][0] == pytest.approx(0.1)
        assert set(r["per_seed"]) == {"42", "123", "3407"}
        flipped = [{**x, "treatment": x["control"], "control": x["treatment"]} for x in rows(0.1)]
        assert boot(flipped)["estimate"] == pytest.approx(-0.1)

    def test_equal_domain_weighting_not_case_weighting(self):
        r = rows(0.0)
        for x in r:
            if x["domain"] == "KUB":
                x["treatment"] += 0.4
        for x in r:
            if x["domain"] == "ISIC":
                x["sample_id"] += "x"
        r += [{**x, "sample_id": x["sample_id"] + f"_{k}"} for x in r if x["domain"] == "ISIC" for k in range(20)]
        assert boot(r)["estimate"] == pytest.approx(0.4 / 4)

    def test_frozen_parameters_and_determinism(self):
        a, b = boot(rows(0.05), n_boot=50), boot(rows(0.05), n_boot=50)
        assert a == b and a["rng"] == "PCG64" and a["rng_seed"] == 20261027 and a["confidence"] == 0.95
        assert boot(rows(0.05), n_boot=10000)["resamples"] == 10000

    def test_missing_pair_duplicate_and_unexpected(self):
        r = rows()
        with pytest.raises(ValueError):
            boot(r[:-1])
        with pytest.raises(ValueError):
            boot(r + [r[0]])
        with pytest.raises(ValueError):
            boot(r + [{**r[0], "seed": 7}])

    def test_invalid_metrics_rejected(self):
        for bad in (float("nan"), float("inf")):
            r = rows(); r[3]["treatment"] = bad
            with pytest.raises(ValueError):
                boot(r)

    def test_kub_patient_required_and_consistent(self):
        r = rows(); r[0]["patient_id"] = None
        with pytest.raises(ValueError):
            boot(r)
        r = rows(); r[0]["patient_id"] = "NOT_AVAILABLE"
        with pytest.raises(ValueError):
            boot(r)
        r = rows(); r[0]["patient_id"] = "other"
        with pytest.raises(ValueError):
            boot(r)

    def test_clustering_only_for_kub_no_invented_clusters(self):
        r = rows(patients=3)
        for x in r:
            if x["domain"] == "ISIC":
                x["patient_id"] = "shared"
        res = boot(r)
        assert res["cluster_counts"]["KUB"] == 3
        assert res["cluster_counts"]["ISIC"] == 6 and res["cluster_counts"]["BUSI"] == 6
        assert res["other_domains_unit"] == "image"

    def test_ci_reports_descriptive_no_pvalue(self):
        res = boot(rows())
        assert not any("p_value" in k or k == "p" for k in res)
        assert "no seed inference" in res["uncertainty"]
        assert res["ci_method"] == "domain_stratified_paired_cluster_percentile"

    def test_real_roster_has_kub_patients_only(self):
        from src.research.evaluation_r3.c1_artifact_pipeline import load_val808_patient_roster
        ros = load_val808_patient_roster()
        assert len(ros) == 808
        assert len({p for p in ros.values() if p}) == 111


@pytest.fixture(scope="module")
def run_dir():
    from src.research.c1_film.integration_contract import make_contract
    from src.research.c1_film.synthetic_fixture import fixture_loaders
    from src.research.c1_film.training_engine import Trainer
    tmp = Path(tempfile.mkdtemp(prefix="c1x_"))
    Trainer(make_contract("C1-T", 42, synthetic=True, device="cpu")).run(tmp / "seed42" / "C1-T", fixture_loaders)
    yield tmp / "seed42" / "C1-T"
    shutil.rmtree(tmp, ignore_errors=True)


def clone(src: Path):
    dst = Path(tempfile.mkdtemp(prefix="c1y_")) / "run"
    shutil.copytree(src, dst)
    return dst


class TestRunArtifacts:
    def test_synthetic_rejected_by_default(self, run_dir):
        with pytest.raises(X.RunArtifactError, match="SYNTHETIC_RUN_REJECTED"):
            X.validate_run(run_dir)

    def test_valid_synthetic_with_flag_and_provenance(self, run_dir):
        rep = X.validate_run(run_dir, allow_synthetic=True, expected_arm="C1-T", expected_seed=42)
        assert rep["synthetic"] and rep["epochs_completed"] == 3 and len(rep["checkpoint_sha256"]) == 64
        assert rep["resume_continuity"]["history_prefix_consistent"] is True
        assert rep["parameter_counts"]["frozen"] == 0

    def test_wrong_arm_or_seed(self, run_dir):
        with pytest.raises(X.RunArtifactError):
            X.validate_run(run_dir, allow_synthetic=True, expected_arm="C1-C")
        with pytest.raises(X.RunArtifactError):
            X.validate_run(run_dir, allow_synthetic=True, expected_seed=123)

    def test_export_files_and_stamp(self, run_dir, tmp_path):
        rep = X.export_run(run_dir, tmp_path, allow_synthetic=True)
        assert rep["data_authenticity"] == "SYNTHETIC"
        lc = list(csv.DictReader(open(tmp_path / "seed42_C1-T_learning_curve.csv")))
        assert [r["epoch"] for r in lc] == ["1", "2", "3"]
        pi = list(csv.DictReader(open(tmp_path / "seed42_C1-T_per_image.csv")))
        assert len({r["sample_id"] for r in pi}) == len(pi) == 8
        prov = json.loads((tmp_path / "seed42_C1-T_provenance.json").read_text())
        assert prov["producer_gaps"] and "events.jsonl" in prov["minimum_compatible_future_amendment"]

    def test_export_is_deterministic(self, run_dir, tmp_path):
        X.export_run(run_dir, tmp_path / "a", allow_synthetic=True)
        X.export_run(run_dir, tmp_path / "b", allow_synthetic=True)
        for f in (tmp_path / "a").iterdir():
            assert f.read_bytes() == (tmp_path / "b" / f.name).read_bytes()

    def test_corrupted_checkpoint_rejected(self, run_dir):
        d = clone(run_dir)
        ptr = json.loads((d / "latest.json").read_text())
        p = d / ptr["file"]; b = bytearray(p.read_bytes()); b[len(b) // 2] ^= 0xFF; p.write_bytes(bytes(b))
        with pytest.raises(X.RunArtifactError, match="CHECKPOINT"):
            X.validate_run(d, allow_synthetic=True)

    def test_incomplete_lifecycle_rejected(self, run_dir):
        d = clone(run_dir)
        life = json.loads((d / "lifecycle.json").read_text()); life["state"] = "PAUSED"
        (d / "lifecycle.json").write_text(json.dumps(life))
        with pytest.raises(X.RunArtifactError, match="RUN_NOT_COMPLETE"):
            X.validate_run(d, allow_synthetic=True)

    def test_missing_pointer_and_missing_epoch_file(self, run_dir):
        d = clone(run_dir); (d / "latest.json").unlink()
        with pytest.raises(X.RunArtifactError):
            X.validate_run(d, allow_synthetic=True)
        d = clone(run_dir)
        first = sorted(d.glob("epoch-0001-*.pt"))[0]; first.unlink()
        with pytest.raises(X.RunArtifactError, match="EPOCH_CHECKPOINT_SEQUENCE_INCOMPLETE"):
            X.validate_run(d, allow_synthetic=True)

    def test_identity_mismatch_rejected(self, run_dir):
        d = clone(run_dir)
        ptr = json.loads((d / "latest.json").read_text()); ptr["identity"] = "0" * 64
        (d / "latest.json").write_text(json.dumps(ptr))
        with pytest.raises(X.RunArtifactError, match="IDENTITY_MISMATCH"):
            X.validate_run(d, allow_synthetic=True)

    def test_cli_reports_missing_without_fabrication(self, tmp_path, capsys):
        import c1_run_artifacts as C
        rc = C.main(["validate", "--experiment-root", str(tmp_path)])
        out = json.loads(capsys.readouterr().out)
        assert rc == 3 and out["runs_valid"] == 0 and set(out["status"].values()) == {"MISSING"}
