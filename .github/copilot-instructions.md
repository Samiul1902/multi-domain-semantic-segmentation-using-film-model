# RA-MedFiLM-BARR — Copilot instructions

**Stage:** Experiment `C1_FILM_ATTRIBUTION_V1` (task-conditioned FiLM vs frozen identity modulation; arms C1-T / C1-C; seeds 42, 123, 3407). Status: **0/6 real runs**; execution authority not selected. Protocol, RC1/RC2/RC3, seeds, splits, checkpoint selection and bootstrap are **frozen**. Populations: TRAIN5832, VAL808. Tasks: ISIC2018, BUSI-WHU, Kvasir-SEG, KUB-StoneX (binary foreground masks; diagnostic classes are metadata).

**Records (read on demand, do not paste):** `docs/MEMORY.md` (state), `docs/c1_execution_authority_decision_v1_0.md`, `docs/c1_execution_handoff_decision_v1_0.md`, `docs/manuscript/`.

**Invariants**
- Never open protected TEST1683 or ROUTER_HOLDOUT; never start C1 training or mint grants/credentials.
- Never fabricate metrics, claims, signatures, institutional approval or ethics statements; don't select DECISION_R/DECISION_I or create RC4.
- Don't modify frozen artifacts, the contaminated trust store (audit evidence), the scientific `.venv`, or the uncommitted `scripts/analysis/run_c1_campaign_launch.py` edit.
- The 884-case external stress test is complete; don't repeat it.

**Retrieval (token economy)**
- Find code with jCodeMunch (`.vscode/mcp.json`; call `menu`/`order`, e.g. `search_symbols`, `get_symbol_source`; index actions need `allow_state_change`) or `rg`; read bounded ranges, not whole files, logs, checkpoints, datasets or images.
- Keep full logs on disk; quote only actionable lines.
- Skills in `.agents/skills/` load on demand, one per simple task: `clean-code` (code), `godkiller` (completion gate), `deepmind-science` (ML rigor), `statistical-analysis`, `scientific-critical-thinking`, `scientific-writing` (manuscripts), `openspec`, `token-saver`. Don't load all.
- Compact replies: finding, action, verification, blockers. No claimed token savings without measurement.

**Workflow:** small verified changes, scoped tests (not the full suite), one focused Git commit; never push without an approved remote.
