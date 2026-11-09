# BARR-M1 — Approval Packet Index (v1.0c)

**Revision:** `RA_MEDFILM_BARR_BARR_M1_V1_0C__FINAL_APPROVAL_PACKAGE`
**Terminal:** `BARR_M1_APPROVAL_PACKAGE_READY__SCIENTIFIC_EXECUTION_NOT_AUTHORIZED`
**Approval status:** **NOT APPROVED**

---

## What this packet is

A self-contained, versioned, integrity-manifested release of everything a supervisor needs to
decide on BARR-M1 — and nothing that could be mistaken for execution.

## Reading order

| # | Document | Purpose |
|---|---|---|
| 1 | `barr_m1_v1_0c_supervisor_authorization_request.md` | **Start here.** The decision document. |
| 2 | `barr_m1_v1_0c_reporting_precision.md` | Six precision clarifications (Task 1). |
| 3 | `../barr_m1_v1_0b/barr_m1_v1_0b_addendum.md` | The numerical/contrast reconciliation. |
| 4 | `../barr_m1_v1_0a/barr_m1_work_order_revision_v1_0a.md` | The corrected study design. |
| 5 | `../barr_m1_v1_0a/barr_m1_supervisor_memorandum_v1_0a.md` | The short memo. |

## Machine-readable evidence

| Artifact | Content |
|---|---|
| `reports/audits/barr_m1_v1_0c_scope_freeze.json` | Frozen execution scope |
| `reports/audits/barr_m1_v1_0c_precision_audit.json` | Precision numbers |
| `reports/audits/barr_m1_v1_0c_gate_validation.json` | R1–R10 gate validation |
| `reports/audits/barr_m1_v1_0c_release_manifest.json` | SHA-256 integrity manifest |
| `reports/audits/barr_m1_v1_0c_final_check.json` | Release checks |
| `reports/audits/barr_m1_v1_0c_terminal.json` | Terminal state |

## Gate

`scripts/analysis/barr_m1_reanalysis_gate_v1_0c.py` — harness SHA `e82ecdb781a56355a9a0a1ebabd948932fee0e15e71d90770bbd0b8459e96c32`.

- `--validate` runs the gate **without** producing scientific output.
- `--execute` is **refused** in this build.
- The gate reproduces the frozen A0/A1/A7/A8 aggregates exactly and runs 8 synthetic negative
  controls; it computes **no** new paired contrast.

## State

```
BARR_M1_APPROVAL_PACKAGE_READY__SCIENTIFIC_EXECUTION_NOT_AUTHORIZED
```

No training · no inference · no new contrast · no TEST · no ROUTER_HOLDOUT · no frozen-artifact
modification.
