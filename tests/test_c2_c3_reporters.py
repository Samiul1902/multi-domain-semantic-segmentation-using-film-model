import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(script, out):
    r = subprocess.run([PY, str(ROOT / "scripts" / "analysis" / script), "--out-dir", str(out)], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}


def test_c2_denominators_and_no_pooling(tmp_path):
    run("c2_barr_aggregator.py", tmp_path)
    d = json.loads((tmp_path / "c2_barr_aggregate.json").read_text())
    assert d["inference_rerun"] is False and d["protected_data_accessed"] is False
    assert d["pooling"].startswith("NONE")
    for s in d["val808_by_seed"]:
        f = s["funnel"]
        assert f["n_all"] == 808 and f["n_routed"] == f["n_adopted"] + f["n_rejected"]
        assert f["n_adopted"] == f["adopted_beneficial"] + f["adopted_harmful"] + f["adopted_unchanged"]
    assert d["router_holdout_historical"]["funnel"]["n_all"] == 875
    ext = d["external"]
    assert sum(v["funnel"]["n_all"] for k, v in ext.items()) == 884
    assert ext["Stones_where_are_you"]["stone_free_failure"]["global_foreground_predicted"] == 14
    assert ext["Stones_where_are_you"]["stone_free_failure"]["n_stone_free"] == 14
    a8 = [x for x in d["development_arms"] if x["arm"] == "A8"][0]
    assert (a8["n_routed"], a8["harmful_routed"]) == (1205, 390)
    assert all(c["ok"] for c in d["checks"])


def test_c2_deterministic(tmp_path):
    assert run("c2_barr_aggregator.py", tmp_path / "a") == run("c2_barr_aggregator.py", tmp_path / "b")


def test_c3_no_leaderboard_or_matched(tmp_path):
    run("c3_baseline_reporter.py", tmp_path)
    d = json.loads((tmp_path / "c3_baseline_report.json").read_text())
    assert d["protocol_matched"] == [] and d["leaderboard"] is None and d["controlled_superiority_claim"] is False
    assert d["training_run"] is False
    assert len(d["exploratory_historical"]) == 6
    for r in d["exploratory_historical"]:
        assert r["comparability"] == "PROTOCOL_INCOMPARABLE" and r["seed_count"] == 1 and r["measured_latency_ms"] is None


def test_c3_deterministic(tmp_path):
    assert run("c3_baseline_reporter.py", tmp_path / "a") == run("c3_baseline_reporter.py", tmp_path / "b")
