"""Tests for the paper-asset pipeline: validators, C1 aggregator honesty, manifest."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from src.research.paper_assets import validation as V  # noqa: E402
import c1_results_aggregator as AGG  # noqa: E402


def good_prov():
    return dict(source_artifact="a.csv", population="VAL808", n=808, metric_unit="Dice proportion",
                evaluation_version="v1", provenance_run="run", evidence_class="descriptive")


class TestValidators:
    def test_duplicate_and_missing_ids(self):
        with pytest.raises(V.AssetValidationError):
            V.require_unique_ids(["a", "b", "a"])
        with pytest.raises(V.AssetValidationError):
            V.require_unique_ids(["a", ""])

    def test_nonfinite_rejected(self):
        for bad in (float("nan"), float("inf"), None):
            with pytest.raises(V.AssetValidationError):
                V.require_finite([0.5, bad])

    def test_dataset_labels(self):
        with pytest.raises(V.AssetValidationError):
            V.require_dataset_labels(["ISIC", "HAM10000"], ("ISIC", "BUSI"))

    def test_denominators(self):
        V.require_funnel(100, 20, 15, 5, 10, 5)
        with pytest.raises(V.AssetValidationError):
            V.require_funnel(100, 20, 15, 4)
        with pytest.raises(V.AssetValidationError):
            V.require_funnel(100, 20, 15, 5, 10, 6)

    def test_reversed_paired_sign(self):
        V.require_paired_sign([0.8], [0.7], [0.1])
        with pytest.raises(V.AssetValidationError):
            V.require_paired_sign([0.8], [0.7], [-0.1])

    def test_percentage_point_label(self):
        V.require_pp_label(0.01, 1.0)
        with pytest.raises(V.AssetValidationError):
            V.require_pp_label(0.01, 0.01)

    def test_provenance_required(self):
        V.require_provenance(good_prov())
        for k in list(good_prov()):
            p = good_prov(); p.pop(k)
            with pytest.raises(V.AssetValidationError):
                V.require_provenance(p)
        p = good_prov(); p["evidence_class"] = "confirmed"
        with pytest.raises(V.AssetValidationError):
            V.require_provenance(p)

    def test_protocol_incomparable_is_a_valid_evidence_classification(self):
        record = good_prov()
        record["evidence_class"] = "PROTOCOL_INCOMPARABLE"
        V.require_provenance(record)

    def test_synthetic_never_real(self):
        with pytest.raises(V.AssetValidationError):
            V.require_authentic("SYNTHETIC_TEST_ONLY")
        V.require_authentic("CONFIRMED_EXECUTED_RESULT")


class TestAggregator:
    def test_absent_runs_not_established_no_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = AGG.aggregate(Path(tmp))
            assert r["status"] == "NOT_ESTABLISHED" and r["complete"] is False
            assert r["runs_completed"] == 0 and len(r["missing_runs"]) == 6
            assert not any(k in r for k in ("estimate", "ci", "per_seed"))
            AGG.write_outputs(r, Path(tmp) / "out")
            assert not (Path(tmp) / "out" / "c1_seed_level.csv").exists()

    def test_frozen_method_metadata(self):
        m = AGG.METHOD
        assert (m["bootstrap_draws"], m["rng_seed"], m["confidence"]) == (10000, 20261027, 0.95)

    def test_synthetic_runs_labelled_and_rejected_in_production(self):
        from src.research.c1_film.integration_contract import make_contract
        from src.research.c1_film.training_engine import Trainer
        from src.research.c1_film.synthetic_fixture import fixture_loaders
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for s in AGG.P.EXPECTED_SEEDS:
                for a in AGG.P.EXPECTED_ARMS:
                    Trainer(make_contract(a, s, synthetic=True, device="cpu")).run(root / f"seed{s}" / a, fixture_loaders)
            with pytest.raises(ValueError):
                AGG.aggregate(root)
            r = AGG.aggregate(root, allow_synthetic=True, n_boot=50)
            assert r["synthetic"] is True and r["complete"] is False
            assert r["status"] == "SYNTHETIC_TEST_ONLY"
            with pytest.raises(V.AssetValidationError):
                V.require_authentic(r["status"])


class TestBuild:
    @pytest.fixture(scope="class")
    def built(self):
        import build_paper_assets as B
        return B, B.main(["--strict"]), B.main([])

    def test_strict_fails_partial_succeeds(self, built):
        _, strict_rc, partial_rc = built
        assert strict_rc == 2 and partial_rc == 0

    def test_manifest_statuses(self, built):
        m = json.loads((ROOT / "paper_asset_manifest.json").read_text(encoding="utf-8"))
        assert m["protected_data_accessed"] is False
        assert m["c1_status"] == "NOT_ESTABLISHED"
        assert m["figures"]["fig03"]["status"].startswith("PENDING")
        assert m["figures"]["fig04"]["status"].startswith("PENDING")
        assert not m["figures"]["fig03"]["files"]
        for k in ("fig01", "fig02", "fig05", "fig06", "fig07", "fig08", "fig09", "fig10"):
            assert m["figures"][k]["status"] == "READY"
            assert any(f.endswith(".pdf") for f in m["figures"][k]["files"])
            assert any(f.endswith(".svg") for f in m["figures"][k]["files"])
            assert any(f.endswith(".png") for f in m["figures"][k]["files"])

    def test_no_c1_figure_files_exist(self, built):
        assert not list((ROOT / "paper_doc" / "figures").glob("fig03*"))
        assert not list((ROOT / "paper_doc" / "figures").glob("fig04*"))

    def test_funnel_denominators_match_sources(self, built):
        B = built[0]
        dev, ext = B.funnel_data()
        assert (dev["total"], dev["attempted"], dev["adopted"], dev["rejected"]) == (4957, 1239, 1205, 34)
        assert (ext["total"], ext["attempted"], ext["adopted"], ext["rejected"]) == (884, 184, 139, 45)
        assert (ext["improved"], ext["worsened"], ext["unchanged"]) == (96, 34, 9)

    def test_tables_have_provenance_and_c1_pending(self, built):
        import csv
        for f in (ROOT / "paper_doc" / "tables").glob("*.csv"):
            rows = list(csv.DictReader(open(f, encoding="utf-8")))
            assert rows
            for r in rows:
                V.require_provenance(r)
        t3 = list(csv.DictReader(open(ROOT / "paper_doc" / "tables" / "table3_c1_paired.csv", encoding="utf-8")))
        assert t3[0]["estimate"] == "NOT_ESTABLISHED"
