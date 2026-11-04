import json

import pytest

from src.research import operator


def test_c1_cli_delegates_only_to_rc4(tmp_path, monkeypatch):
    from src.research.c1_film_launch_rc4 import launch_driver_rc4
    seen = {}
    def launch(arm, seed, **kwargs):
        seen.update(arm=arm, seed=seed, **kwargs)
        return {"status": "SYNTHETIC_TEST_ONLY"}
    monkeypatch.setattr(launch_driver_rc4, "launch", launch)
    args = ["c1-launch", "--arm", "C1-T", "--seed", "42", "--release-digest", "a" * 64,
            "--output-root", str(tmp_path / "out"), "--resume"]
    for field in ("approval", "instruction", "time-status", "budget", "run-plan", "recovery"):
        path = tmp_path / f"{field}.json"
        path.write_text(json.dumps({"synthetic_field": field}))
        args.extend([f"--{field}", str(path)])
    assert operator.main(args) == 0
    assert seen["arm"] == "C1-T" and seen["seed"] == 42 and seen["resume"]
    assert seen["time_status"] == {"synthetic_field": "time-status"}


def test_c1_missing_authority_paths_refused_by_parser():
    with pytest.raises(SystemExit):
        operator.build_parser().parse_args(["c1-launch", "--arm", "C1-T", "--seed", "42"])


def test_baseline_cli_preserves_existing_grant_surface(monkeypatch):
    from src.research.stage6 import baseline_real
    token = object()
    monkeypatch.setattr(baseline_real, "load_grant", lambda spec: token)
    def run(model, seed, *, grant, resume):
        assert grant is token and model == "UNET" and seed == 42 and resume
        return {"status": "SYNTHETIC_TEST_ONLY"}
    monkeypatch.setattr(baseline_real, "run_real_baseline", run)
    assert operator.main(["baseline-run", "--model", "UNET", "--seed", "42",
                          "--grant-provider", "synthetic:fixture", "--resume"]) == 0
