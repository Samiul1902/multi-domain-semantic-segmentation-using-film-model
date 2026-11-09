# EXT-03 Study Identifier Namespace Reconciliation — v1.2

**Classification:** `EXT03_STUDY_IDENTIFIER_NAMESPACE_RECONCILIATION`
**Version:** 1.2 (additive; supersedes a *label*, not any bytes)
**Generated local:** 2026-10-26T22:29 (+06:00) — provenance `AUTHOR_ENTERED_AT_WRITE`; the computed, timezone-aware value is in the companion `.json` `generated_local`
**Mode:** read-only. No frozen configuration modified, no study reserved, no study started.

**Companion:** `ext03_study_identifier_namespace_reconciliation_v1_2.json`

---

## 1. The collision

The v1.1 supervisor memorandum introduced a prospective study and labelled it **EXT-04**:

> *"Option B — Prospective protocol-faithful baseline study (EXT-04)"*
> — `ext03_supervisor_decision_memorandum_v1_1.md`, §3

**EXT-04 is already taken.** It is not a free slot. It is a frozen study-programme identifier with an assigned, pre-registered study set that predates this work by weeks. Reusing the label for a baseline benchmark would silently redirect a frozen roadmap slot to a different purpose.

The collision is confined to two artifacts — the v1.1 memorandum `.md` and `.json`. Nothing else in the repository uses EXT-04 for a baseline study.

---

## 2. The frozen EXT-04 meaning

**Authority:** `reports/planning/advanced_study_registry.json`, revision
`RA_MEDFILM_BARR_EXT02_1A_ADVANCED_STUDY_PROGRAM_V1_0` (32 studies, all `NOT_STARTED`), and
`docs/ADVANCED_STUDY_REGISTRY.md` §"Execution roadmap".

| Study | Tier | Name | Why it belongs to EXT-04 |
|---|---|---|---|
| AS-01 | TIER 1 | Four-Domain Dataset Progression | P1→P2→P3→P4 domain **progression** |
| AS-02 | TIER 2 | Fixed-N Domain-Diversity Progression | diversity-vs-volume **progression** at fixed N |
| AS-03 | TIER 1 | Training Data-Volume / Learning-Curve Study | data-volume **scaling** |
| AS-04 | TIER 1 | Single-Domain vs Shared Multi-Domain | training-regime **progression** |
| AS-05 | TIER 1 | Negative Transfer / Domain Retention | progression **consequence** |
| AS-07 | TIER 3 | Domain-Order Sensitivity | progression **ordering** (optional) |

Every one of these is a **progression, scaling, or transfer** study. That is the semantic identity of EXT-04: *how the model behaves as the training regime is progressively expanded.*

A protocol-faithful baseline benchmark is none of those things. It is a **re-execution of AS-08** ("Same-Protocol Model Benchmark") under a corrected recipe. AS-08 was assigned to **EXT-03**, not EXT-04.

**The frozen roadmap is explicit:**

```
EXT-03: AS-08, AS-27 (baseline reproducibility)
EXT-04: AS-01, AS-02, AS-03, AS-04, AS-05, AS-07 (optional)
```

---

## 3. Why the collision matters

1. **Roadmap integrity.** The manuscript's study programme will be cited as EXT-03 → EXT-04 → EXT-05 → … If EXT-04 is silently redefined as "the baseline redo", a reader tracing the roadmap finds a progression study slot occupied by a benchmark study.
2. **Authorization laundering.** A new study inherits credibility from an already-frozen identifier. A supervisor approving "EXT-04" may reasonably believe they are approving the progression study that EXT-04 has always meant. Naming is not neutral when names are load-bearing.
3. **Pre-registration semantics.** AS-01..AS-05 and AS-07 are pre-registered. Reusing their container identifier for an unregistered study blurs the line between preregistered and post-hoc work — the exact distinction EXT-03 already failed to maintain.
4. **Provenance.** A future audit asking "what was EXT-04?" would find two incompatible answers in the same repository.

---

## 4. Recommendation

**Adopt `EXT-03B` as the provisional identifier for the prospective protocol-faithful baseline study.**

Rationale:

- **Correct parent.** The study repairs AS-08, which is an EXT-03 assignment. Its parent is EXT-03, not EXT-04.
- **Established convention.** The programme already uses sub-letter identifiers for sibling studies: `EXT-05B`, `EXT-05C`, `EXT-09B`. `EXT-03B` is the idiomatic form, not an invention.
- **No roadmap slot consumed.** EXT-04 through EXT-11 remain untouched and in their frozen order.
- **Self-documenting.** "EXT-03B" reads as *the second study in the EXT-03 baseline family*, which is exactly what it is: the protocol-faithful re-execution of the divergent EXT-03 matrix.
- **Reversible.** A provisional label can be ratified or replaced by the supervisor without touching any frozen artifact.

**Status of the recommendation: `PROVISIONAL__SUBJECT_TO_SUPERVISOR_AUTHORIZATION`.** This document does not reserve `EXT-03B`, does not register a study, does not create a roadmap entry, and does not authorise any execution. It records a naming defect and proposes a correction.

---

## 5. Alternatives considered

| Candidate | Verdict | Reason |
|---|---|---|
| **`EXT-03B`** | **Recommended** | Correct parent; matches existing sub-letter convention; consumes no slot |
| `EXT-03R` | Viable fallback | "R" for repair is explicit, but breaks the programme's letter-sequence convention (B, C are siblings, not repairs) |
| `EXT-04B` | Rejected | Anchors the study to the wrong parent and still implies an EXT-04 relationship that does not exist |
| `EXT-12` | Rejected | Appends after EXT-11 (manuscript V2, the terminal slot); implies a programme stage that has not been reached |
| Rename to "EXT-04 baseline sub-study" | Rejected | A sub-label still occupies the EXT-04 namespace and still misleads a roadmap reader |

---

## 6. Option C needs no EXT identifier at all

The FiLM-off control recommended in the v1.1 memorandum is **not an EXT study**. It is a one-factor ablation of the Phase-21 architecture, and the programme already has a container for exactly that: `phase28_one_factor_control_contract.json` (the 13-arm one-factor ablation family).

**Recommendation:** register the FiLM-off control under the **Phase-28 ablation family**, not the EXT namespace. It has no EXT number, needs none, and giving it one would repeat the same class of error this document exists to correct.

If a supervisor nevertheless requires an EXT label, the only defensible provisional choice is `EXT-03C` — a third sibling in the baseline/control family — and never EXT-04 or any higher number.

---

## 7. Correction mechanism

The defective label lives in `ext03_supervisor_decision_memorandum_v1_1.md` and `.json`. Both are v1.1 artifacts and are **retained byte-for-byte**, per the standing rule that superseded artifacts are superseded in *authority*, never rewritten in *bytes*.

This document is the additive supersession record:

- **Superseded:** the string "EXT-04" wherever it names the prospective protocol-faithful baseline study in the v1.1 memorandum.
- **Retained:** every other statement in that memorandum, including the A/B/C analysis, the recommendation of Option C, and the explicit non-authorisation.
- **Not superseded:** the frozen EXT-04 progression/scaling study set, which is unaffected and remains `NOT_STARTED`.

---

## 8. Uncertainty and scope

- This reconciliation asserts only that **the label collides**. It does not assert that any study was registered, approved, or started under either meaning.
- No roadmap file, study registry, or planning artifact was modified.
- The recommendation is a naming proposal. It confers no scientific authority and no execution right.

---

*End of reconciliation. No frozen configuration modified, no study reserved, no training, no inference.*
