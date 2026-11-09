# POST-PHASE-13 REVISION R1 — POLICY FROZEN

- status: **`SUPERVISOR_FROZEN_R1_POLICY_READY_FOR_EXECUTION`**
- hypothesis: **`H1_FIRST_SELECTIVE_ACCEPTANCE`**
- R1 scientific execution authorized: **FALSE**
- created (UTC): `2026-09-22T06:09:00Z`

This artifact defines the **deterministic execution semantics** of the already-frozen 7-config candidate
family. It **does not** change the family.

## Execution semantics

### Acceptance operator

```
proposal is eligible  iff  proposal_score >= score_acceptance_floor
```

- comparator: **`GREATER_THAN_OR_EQUAL`** (not `>`)
- the numeric floors physically stored in the candidate-family CSV **are** the executable constants,
  even though their labels refer to marginal quantiles
- recomputing a slightly different quantile during R1: **FORBIDDEN**
- replacing a stored floor with a higher-precision value after seeing outcomes: **FORBIDDEN**

| config | floor | max accepted |
|---|---|---|
| R1-C0 | 0.100000 | 5 |
| R1-C1 / R1-C2 | 0.119470 | 1 / 5 |
| R1-C3 / R1-C4 | 0.124532 | 1 / 5 |
| R1-C5 / R1-C6 | 0.125065 | 1 / 5 |

### Deterministic within-case order

- start from the already-frozen Part-1C proposals; preserve the frozen `proposal_rank` ordering
- after applying the score floor, select by **`proposal_rank` ASCENDING**
- retain at most `max_accepted_proposals`

**`PROPOSAL_RANK_ROLE = DETERMINISTIC_FROZEN_ORDER_ONLY`** — *not* confidence superiority within ties.

Forbidden re-sorting of tied proposals: GT · proposal area · component coverage · segmentation outcome ·
new random order · sample-specific heuristics · recomputing rank from floating score.

### Zero-acceptance behaviour

If no proposal passes the floor: accepted count **0** · regional intervention **NONE** · final prediction
**GLOBAL exactly**. This is valid and expected. Forcing at least one proposal: **FORBIDDEN**.

### Membership definition

`accepted = score_passes_floor AND selected_by_rank_cap`. The two columns therefore coincide by
construction; both are emitted in the frozen membership table.

## Membership hashes (authoritative R1 policy identities)

SHA-256 over ordered tuples `(sample_id, proposal_rank, accepted)` as UTF-8 lines
`<sample_id>|<proposal_rank>|<1|0>\n`, ordered by `sample_id` lexical ascending then `proposal_rank`
ascending, over all 494 proposals. **R1 inference MUST verify these before CUDA.**

| config | floor | max | accepted | cases with 0 accepted | membership SHA-256 |
|---|---|---|---|---|---|
| **R1-C0** | 0.100000 | 5 | **494** | 0 | `ac5bbc02a12177cf447dab48a99bb5c44a658f653f16e9dab49247591911d327` |
| **R1-C1** | 0.119470 | 1 | 103 | 0 | `844f70d35188815bb1fc42c464ae83ee78726d78777d4c10b24de24dda709354` |
| **R1-C2** | 0.119470 | 5 | 444 | 0 | `ec8c5b9ca97734c08bfcb67985c5706c56a4ab9d39f277bb61dbe10b2a6eb21b` |
| **R1-C3** | 0.124532 | 1 | 103 | 0 | `844f70d35188815bb1fc42c464ae83ee78726d78777d4c10b24de24dda709354` |
| **R1-C4** | 0.124532 | 5 | 372 | 0 | `f58a5a945fa96437c3d4bac68640a7d3f7452b62c11e01bea06151e7b02b17cf` |
| **R1-C5** | 0.125065 | 1 | 102 | **1** | `0c424bb6d0b6b21850e95281daafea51ee17386dfe916e77b66f4d9ca23b0852` |
| **R1-C6** | 0.125065 | 5 | 337 | **1** | `5b40128e981d9114a4c622b378fbd1050d3f073c5b8ae60f0c29b7cb8d3015ad` |

### Per-case accepted distribution

| config | 0 | 1 | 2 | 3 | 4 | 5 | mean | median |
|---|---|---|---|---|---|---|---|---|
| R1-C0 | 0 | 0 | 1 | 6 | 6 | 90 | 4.796117 | 5.0 |
| R1-C1 | 0 | 103 | 0 | 0 | 0 | 0 | 1.000000 | 1.0 |
| R1-C2 | 0 | 2 | 9 | 11 | 14 | 67 | 4.310680 | 5.0 |
| R1-C3 | 0 | 103 | 0 | 0 | 0 | 0 | 1.000000 | 1.0 |
| R1-C4 | 0 | 6 | 22 | 16 | 21 | 38 | 3.611650 | 4.0 |
| R1-C5 | **1** | 102 | 0 | 0 | 0 | 0 | 0.990291 | 1.0 |
| R1-C6 | **1** | 11 | 24 | 19 | 19 | 29 | 3.271845 | 3.0 |

## Control identity gate

**R1-C0** accepts **494 / 494** and its per-case accepted counts are **identical** to the frozen Part-1C
proposal counts. **PASS.**

## Relationship checks — all PASS

- **floor monotonicity (same cap):** raising the floor **adds 0** accepted proposals.
  C0 ⊇ C2 ⊇ C4 ⊇ C6 (max 5) and C1 ⊇ C3 ⊇ C5 (max 1).
- **cap subset (same floor):** C1 ⊆ C2, C3 ⊆ C4, C5 ⊆ C6.

No membership inconsistency. Performance is **not** interpreted here.

## Score-tie audit

| item | value |
|---|---|
| proposal count | 494 |
| marginal max score (exact) | `0.1250653713941574` |
| count exactly at max | **337** |
| fraction exactly at max | **0.682186** |
| rank-1 saturated | **102 / 103** |
| rank-2 saturated | 91 / 103 |
| proposals strictly between stored floor 0.125065 and exact max | **0** |
| proposals passing the 0.125065 floor | 337 |

Because many proposals are tied at the marginal maximum, `proposal_rank` is used **only** as the
already-frozen deterministic ordering. **R1 must not claim that rank 1 is necessarily more confident than
rank 2 within an exact score tie.**

## Disclosed family redundancy (family NOT changed)

**R1-C1 and R1-C3 produce IDENTICAL membership** (`844f70d3…`). With `max_accepted_proposals = 1` the
selection is the lowest-rank floor-passing proposal; every rank-1 proposal has score **>= 0.124852**,
which is above both the 0.119470 and 0.124532 floors, so rank-1 always passes and the two floors never
differ in effect.

- distinct memberships: **6** across **7** configurations
- configurations added or removed: **NONE**
- family changed: **NO** — disclosed only; the family remains frozen as supervisor-authored

R1 will therefore effectively test **6 distinct policies**.

## Frozen / unchanged

training **0** · localizer checkpoint **UNCHANGED** · proposal geometry **UNCHANGED** · margin **0.20** ·
NMS IoU **0.30** · segmentation checkpoints **UNCHANGED** · regional crop/restore **UNCHANGED** ·
fusion **UNCHANGED** · segmentation threshold **0.5** · score weighting **NONE** · new fusion **NONE**

## Label blindness

GT used for membership: **NO** · segmentation outcome used for membership: **NO** · component labels used:
**NO** · proposal hit/miss labels used: **NO**

Membership columns: `config_id` · `sample_id` · `proposal_rank` · `proposal_score` ·
`score_acceptance_floor` · `score_passes_floor` · `max_accepted_proposals` · `selected_by_rank_cap` ·
`accepted` · `accepted_order_within_case`

## Pass gate — all conditions satisfied

family rows 7 · proposal rows 494 · control accepts exactly 494 · memberships deterministic ·
subset/monotonicity checks pass · tie handling explicitly frozen · 7 membership hashes recorded ·
no GT for membership · no segmentation outcome for membership · no model inference · TEST untouched

## Continuity

Phase 13 **COMPLETE / FROZEN** · regional gate **REVISE_LOCALIZER / FROZEN** · Revision R0
**COMPLETE / PASS / FROZEN** · Revision R1 policy definition **COMPLETE / PASS** · Revision R1
scientific execution **ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION — AUTHORIZED: FALSE** · Phase 14
**NOT_STARTED** · TEST **UNTOUCHED**

## Zero-execution counters

training **0** · optimizer **0** · model constructions **0** · CUDA requests **0** · localizer forwards
**0** · segmentation forwards **0** · regional crop forwards **0** · proposal generation **0** ·
checkpoint writes **0** · TEST reads **0** · external-test reads **0**

**next_action: `WAIT_FOR_SUPERVISOR_REVISION_R1_EXECUTION_AUTHORIZATION`**
