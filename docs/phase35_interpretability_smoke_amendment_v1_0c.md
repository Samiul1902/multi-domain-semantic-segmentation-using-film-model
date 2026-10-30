# Phase 35 - Synthetic Smoke-Mode Implementation Amendment (v1.0c)

**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0c`
**Classification:** `PRE_EXECUTION_SYNTHETIC_SMOKE_ENTRYPOINT_IMPLEMENTATION_AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE`
**Phase ID (immutable):** `phase_35_interpretability`
**Method:** RA-MedFiLM-BARR

## 1. Chronology (disclosed in full)
| stage | content | outcome |
|---|---|---|
| v1.0 | scientific specification + execution source | specification **VALID**; execution source skeleton |
| v1.0a | gallery-SHA reconciliation + frozen-source static preflight | **CORRECTLY BLOCKED PREMODEL** (25/54) |
| v1.0b | additive executable implementation repair | source **COMPLETE**; synthetic smoke **BLOCKED** |
| **v1.0c** | **real synthetic smoke entry point + source freeze** | **this amendment** |

**No scientific output has occurred.** Model constructions 0 - checkpoint deserializations 0 -
forwards 0 - autograd calls 0 - Grad-CAM 0 - router attribution 0 - raw VAL reads 0 - GT reads 0 -
ROUTER_HOLDOUT reads 0 - TEST reads 0 - training 0. No gate environment variable was set and no
`--mode` was invoked in this work order.

## 2. What v1.0c changes (and what it deliberately does not)
`phase35_interpretability_execution_v1_0c.py` supersedes
`phase35_interpretability_execution_v1_0b.py` **for the smoke entry point only**. It imports the
frozen v1.0b execution module as `V0B` and binds the four scientific modes to the *very same
function objects*:

```
MODE_DISPATCH = OrderedDict([
    ("smoke",   mode_smoke),        # v1.0c-local, real implementation
    ("film",    V0B.mode_film),     # frozen v1.0b, reused verbatim
    ("gradcam", V0B.mode_gradcam),  # frozen v1.0b, reused verbatim
    ("router",  V0B.mode_router),   # frozen v1.0b, reused verbatim
    ("science", V0B.mode_science),  # frozen v1.0b, reused verbatim
])
```

No scientific function is re-defined or re-implemented in v1.0c. The frozen v1.0b module and the
frozen v1.0b shared contracts are **byte-identical** to their v1.0b freeze
(`581926840d77...`, `9963215e1431...`).

## 3. The real smoke entry point
`mode_smoke()` is no longer a stub. It performs a pre-scientific synthetic interface validation:

1. verifies the authority gate SHA-256 set;
2. checks environment compatibility (RTX 3060 Ti, torch 2.6.0+cu124, CUDA available);
3. verifies the G and B_phi checkpoint **file SHA-256 before any deserialization**;
4. constructs, strict-loads and parameter-verifies **G (3,523,001)** and **B_phi (36,801)**;
5. validates the FiLM accessor over all 4 tasks x 5 sites (channel counts, finiteness);
6. validates the task-embedding shapes (G `[4,32]`, B_phi `[4,16]`);
7. runs **ONE** synthetic gradient-enabled G forward through the canonical
   `bridge` / `decoder1` Grad-CAM path (autocast fp16, no `no_grad` / `inference_mode`);
8. runs **ONE** synthetic B_phi forward plus **ONE** numeric-input gradient and Gradient x Input
   on the **raw** `delta_hat` (no sigmoid);
9. unit-tests the zero-denominator aggregation policy (NULL share plus
   `ZERO_ROUTER_GRAD_ATTRIBUTION`, no epsilon, no renormalization);
10. proves parameter immutability via `state_dict` identity before vs after.

**Gates are separated by design.** Smoke mode requires `PHASE35_SMOKE_EXECUTE=1`; scientific modes
require `PHASE35_EXECUTE=1`. Neither authorizes the other.

**R_psi and S_omega are never constructed, never loaded and never forwarded.** The smoke reads no
real data of any kind: only deterministic synthetic tensors (seed 42, `[1,3,512,512]`).

## 4. Disclosed defect (not repaired here)
`PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY` - the frozen `gradcam_target_scalar` indexes `logits[mask]`; the canonical
G logits tensor is `[1,1,512,512]` while the canonical scientific mask producer
`build_target_mask(p_global)` returns a rank-2 `[512,512]` array, so the scientific Grad-CAM target
scalar raises `IndexError`. Evidence: a model-free tensor-semantics probe under torch 2.6.0+cu124,
and a metadata-only header inspection of all 808 VAL npz (`prob` = `(512,512)` `<f2`). The frozen
v1.0b module is **not** modified; the smoke uses a rank-compatible synthetic mask and records the
incompatibility in `mask_rank_contract`. **Scientific Grad-CAM execution stays BLOCKED pending a
v1.0d rank-safety repair.**

## 5. Static preflight (zero execution)
`scripts/analysis/phase35_execution_preflight_v1_0c.py` re-runs the 54 original v1.0a load-bearing checks against the effective v1.0c
source set and adds 40 v1.0c amendment checks:
**94 checks, 0 failed**, with
22 predecessors verified byte-identical. No model was constructed, no checkpoint
deserialized, no forward or backward executed, no raw VAL / GT / ROUTER_HOLDOUT / TEST read.

## 6. Locks
Phase35 scientific execution `NOT_STARTED`; Phase36 `NOT_STARTED`; TEST `LOCKED_UNTIL_PHASE39`;
ROUTER_HOLDOUT `OPENED_AND_FROZEN`. The v1.0c amendment changes **no** scientific protocol.
