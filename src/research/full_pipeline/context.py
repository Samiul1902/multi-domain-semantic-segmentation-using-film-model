"""Run context: everything a stage needs, resolved once.

A stage never reaches for a global path.  It receives a :class:`RunContext` that
already knows the seed family, the operational bounds, the population, the fold
tables and the per-family artifact root, so the same stage code runs unchanged
for seed 42, 123 or 3407 and for a synthetic population.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from . import recipe as R
from .population import (FoldTable, PopulationSpec, load_canonical_population,
                          resolve_folds)
from .provenance import atomic_write_json, read_json, relpath_str, sha256_file, utc_now
from .seeds import SeedFamily

__all__ = ["RunContext", "StageRecord"]


@dataclass
class RunContext:
    """Per-(family) execution context."""

    family: SeedFamily
    root: Path
    bounds: R.OperationalBounds
    population: PopulationSpec
    recipe: R.Recipe = field(default_factory=R.Recipe)
    allow_derived_folds: bool = False
    synthetic: bool = False
    _folds: Dict[str, FoldTable] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------ #
    @property
    def seed(self) -> int:
        return self.family.seed

    @property
    def tag(self) -> str:
        return self.family.tag

    @property
    def family_name(self) -> str:
        """Model-family discriminator stamped into every checkpoint and manifest.

        ``FULL`` for this context.  A Lite context overrides it, which is what
        keeps a Lite checkpoint from ever being read as a FULL component.
        """
        return "FULL"

    @property
    def run_root(self) -> Path:
        return self.root / self.tag

    @property
    def device(self) -> str:
        return self.bounds.device

    # ---- artifact paths --------------------------------------------- #
    def p(self, *parts: str) -> Path:
        return self.run_root.joinpath(*parts)

    @property
    def g_dir(self) -> Path:
        return self.p("G")

    @property
    def cache_dir(self) -> Path:
        return self.p("cache")

    @property
    def r_dir(self) -> Path:
        return self.p("R")

    @property
    def l_dir(self) -> Path:
        return self.p("L")

    @property
    def b_dir(self) -> Path:
        return self.p("B")

    @property
    def s_dir(self) -> Path:
        return self.p("S")

    @property
    def inference_dir(self) -> Path:
        return self.p("inference")

    # ---- folds -------------------------------------------------------- #
    def folds(self, kind: str) -> FoldTable:
        if kind not in self._folds:
            self._folds[kind] = resolve_folds(
                self.population, kind=kind, seed=self.seed,
                allow_derived=self.allow_derived_folds or self.synthetic)
        return self._folds[kind]

    # ---- provenance ---------------------------------------------------- #
    def base_manifest(self) -> dict:
        return {
            "artifact": f"{self.family_name.lower()}_barr_family_manifest",
            "method": "RA-MedFiLM-BARR",
            "family": self.family_name,
            "seed": self.seed,
            "tag": self.tag,
            "synthetic": bool(self.synthetic),
            "protocol_faithful": bool(self.bounds.is_protocol_faithful),
            "operational_override": self.bounds.overrides(),
            "population": self.population.summary(),
            "recipe": self.recipe.as_dict(),
            "device": self.bounds.device,
            "host_clock_trust": "NOT_ESTABLISHED",
            "determinism": __import__("src.research.full_pipeline.seeds",
                                      fromlist=["determinism_report"]).determinism_report(),
            "created_utc": utc_now(),
            "test_reads": 0,
            "router_holdout_reads": 0,
        }

    def write_family_manifest(self, extra: Optional[dict] = None) -> Path:
        m = self.base_manifest()
        if extra:
            m.update(extra)
        path = self.run_root / "manifest.json"
        atomic_write_json(m, path)
        return path

    # ---- G identity ---------------------------------------------------- #
    def g_checkpoint(self) -> Path:
        return self.g_dir / "best.pt"

    def g_sha(self) -> str:
        p = self.g_checkpoint()
        if not p.exists():
            raise FileNotFoundError(f"G checkpoint for family {self.tag} is missing: {p}")
        return sha256_file(p)

    def upstream_for(self, component: str) -> Dict[str, Dict[str, str]]:
        """The upstream SHA chain a component checkpoint must record."""
        out: Dict[str, Dict[str, str]] = {}
        if component in ("R", "B", "S"):
            out["G"] = {"path": relpath_str(self.g_checkpoint()), "sha256": self.g_sha()}
        if component in ("B", "S"):
            final_r = self.r_dir / "final" / "final.pt"
            if not final_r.exists():
                raise FileNotFoundError(f"R_psi final checkpoint missing: {final_r}")
            out["R"] = {"path": relpath_str(final_r), "sha256": sha256_file(final_r)}
        return out

    # ---- stage state ---------------------------------------------------- #
    def stage_state_path(self, stage: str) -> Path:
        return self.run_root / "_state" / f"{stage}.json"

    def stage_state(self, stage: str) -> dict:
        return read_json(self.stage_state_path(stage), default={})

    def set_stage_state(self, stage: str, record: dict) -> None:
        atomic_write_json(record, self.stage_state_path(stage))

    def stage_done(self, stage: str) -> bool:
        st = self.stage_state(stage)
        return bool(st.get("status") == "COMPLETE")


@dataclass
class StageRecord:
    """Uniform return value of a stage."""

    stage: str
    status: str
    artifacts: Dict[str, str] = field(default_factory=dict)
    detail: Dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"stage": self.stage, "status": self.status,
                "artifacts": self.artifacts, "detail": self.detail,
                "completed_utc": utc_now()}
