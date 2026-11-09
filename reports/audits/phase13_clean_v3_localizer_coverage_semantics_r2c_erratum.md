# PHASE-13 PART-1B — R2C RUNNER-SHA REPORTING ERRATUM

- **classification:** `R2C_MARKDOWN_RUNNER_SHA_REPORTING_ERRATUM_ONLY`
- **status:** **PASS**
- **scientific result changed:** **NO**
- **model state changed:** NO
- **selection changed:** NO

## The discrepancy

| source | post-repair runner SHA | correct? |
|---|---|---|
| R2C **JSON** (`post_repair_runner_sha`) | `00ff82447f1f83935c042ea4fa19ad4f05956c48a80c474eaa98fc643bf79913` | **YES** |
| R2C JSON (`runner_sha_transition.post_repair_runner_sha`) | `00ff82447f1f83935c042ea4fa19ad4f05956c48a80c474eaa98fc643bf79913` | **YES** |
| R2C **markdown** (human-readable table) | `0d5a199d223296346f7d998551ec842f77298f0ec6e0328a1c6f007e8e751737` | **NO — stale** |
| **executing runner (physical SHA-256)** | `00ff82447f1f83935c042ea4fa19ad4f05956c48a80c474eaa98fc643bf79913` | — |

## Canonical authority

The authoritative value is `00ff82447f1f83935c042ea4fa19ad4f05956c48a80c474eaa98fc643bf79913`,
established by three independent sources:

1. R2C JSON `post_repair_runner_sha`
2. checkpoint metadata `runner_sha` in `_phase13_execution_metadata`
3. the executing runner's physical SHA-256

**Authorization identity is consistent.** The R2C JSON is the artifact the runner
physically reads and verifies at runtime (`post_repair_runner_sha` must equal the
executing runner SHA). It contains the correct value. The stale value appears only
in the human-readable markdown summary, which carries no authorization weight.

## Root cause

The R2C JSON was updated to the final executing runner SHA after the last runner
patch, but the companion markdown table was not re-synchronised and retained an
intermediate value captured before the final two runner edits.

## Remediation

| action | done |
|---|---|
| R2C JSON modified | **NO** (preserved as frozen) |
| R2C markdown annotated with erratum | YES |
| original markdown value retained visibly | **YES** |
| silent rewrite performed | **NO** |

## Disclosure

The original markdown discrepancy is **not hidden**. The markdown table row now
shows the stale value alongside the corrected value with an explicit pointer to
this erratum.

No training. No inference. No proposal generation. TEST reads: **0**.
