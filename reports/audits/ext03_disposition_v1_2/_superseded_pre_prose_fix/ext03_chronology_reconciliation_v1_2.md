# EXT-03 Chronology Reconciliation — v1.2

**Classification:** `EXT03_CHRONOLOGY_RECONCILIATION`  
**Generated local:** 2026-10-26T22:26:25+06:00  
**Mode:** read-only measurement. No timestamp rewritten, no artifact modified, no creation order asserted beyond the evidence.

---

## 1. The question

Why does the v1.1 manifest carry 21:43:08 while documents it hashes claim 21:45-22:00?

## 2. Answer

5 documents carry an embedded timestamp LATER than the moment the file was actually written, using 4 distinct round values (21:45:00, 21:50:00, 21:55:00, 22:00:00). Every one lands on an exact five-minute boundary. A measured clock does not produce consecutive exact boundaries, so these are hand-authored literals, not measurements. All eight v1.1 documents were created between 21:37:18 and 21:43:08 by filesystem evidence, and the manifest is the LAST of them — the correct dependency order for a manifest that hashes its inputs. No chronology violation occurred. The apparent inversion is an artefact of fabricated embedded timestamps.

| Check | Result |
|---|---|
| Manifest correctly ordered relative to its inputs | **True** |
| Dependency order violated | **False** |
| Embedded timestamps unreliable | **True** |
| Literal (non-measured) timestamps | **7** |
| Apparent inversions | **5** |

## 3. Measured creation order

Ordered strictly by filesystem modification time. This is the only ordering evidence that does not depend on a document's own claim. Embedded values are converted to local time before comparison; a document stamped in UTC is compared on the instant, not the digits.

| # | Artifact | mtime | embedded claim | class |
|---|---|---|---|---|
| 1 | `ext03_matrix_completion_summary_v1_1.py` | 21:37:18 | — | NO_EMBEDDED_TIMESTAMP |
| 2 | `test_ext03_completion_summary_v1_1.py` | 21:37:34 | — | NO_EMBEDDED_TIMESTAMP |
| 3 | `ext03_matrix_completion_summary_v1_1.json` | 21:37:58 | 21:37:58 | COMPUTED_AT_WRITE |
| 4 | `ext03_matrix_final_family_summary_v1_1.csv` | 21:37:58 | — | NO_EMBEDDED_TIMESTAMP |
| 5 | `ext03_evidence_provenance_reconciliation_v1_1.json` | 21:38:28 | 21:45:00 | LITERAL_ROUND_FIVE_MINUTE |
| 6 | `ext03_scientific_adjudication_addendum_v1_1.md` | 21:39:05 | 21:50:00 | LITERAL_ROUND_FIVE_MINUTE |
| 7 | `ext03_scientific_adjudication_addendum_v1_1.json` | 21:39:23 | 21:50:00 | LITERAL_ROUND_FIVE_MINUTE |
| 8 | `ext03_false_certification_supersession_register_v1_1.json` | 21:39:50 | 21:55:00 | LITERAL_ROUND_FIVE_MINUTE |
| 9 | `ext03_missing_evidence_disposition_v1_1.json` | 21:40:21 | 22:00:00 | LITERAL_ROUND_FIVE_MINUTE |
| 10 | `ext03_supervisor_decision_memorandum_v1_1.md` | 21:42:36 | 21:42:00 | LITERAL_ROUNDED_DOWN |
| 11 | `ext03_supervisor_decision_memorandum_v1_1.json` | 21:42:50 | 21:42:00 | LITERAL_ROUNDED_DOWN |
| 12 | `ext03_sha256_manifest_v1_1.json` | 21:43:08 | 21:43:08 | COMPUTED_AT_WRITE |

## 4. Apparent inversions, itemised

Each row is a document whose embedded timestamp is *later* than the moment the file was actually written.

| Artifact | claims | actually written | overstatement |
|---|---|---|---|
| `ext03_evidence_provenance_reconciliation_v1_1.json` | 21:45:00 | 21:38:28 | +391 s |
| `ext03_scientific_adjudication_addendum_v1_1.md` | 21:50:00 | 21:39:05 | +655 s |
| `ext03_scientific_adjudication_addendum_v1_1.json` | 21:50:00 | 21:39:23 | +636 s |
| `ext03_false_certification_supersession_register_v1_1.json` | 21:55:00 | 21:39:50 | +910 s |
| `ext03_missing_evidence_disposition_v1_1.json` | 22:00:00 | 21:40:21 | +1179 s |

These 5 documents carry 4 distinct claimed values (21:45:00, 21:50:00, 21:55:00, 22:00:00), and every one lands on an exact five-minute boundary. A measured clock does not produce consecutive exact boundaries. These are literals.

## 5. Clock evidence

**Measured now:** `w32tm /query /status`

```
Leap Indicator: 3(not synchronized)
Stratum: 0 (unspecified)
Precision: -23 (119.209ns per tick)
Root Delay: 0.0000000s
Root Dispersion: 0.0000000s
ReferenceId: 0x00000000 (unspecified)
Last Successful Sync Time: unspecified
Source: Local CMOS Clock
Poll Interval: 10 (1024s)
```

**Synchronized:** `False` · **Source:** `Local CMOS Clock`

**Recorded history** (`.workbuddy-ai/memory/2026-10-25.md`, quoted not re-measured):

- Time-Service event ID **52**, offset **448320 s** (5.19 days)
- System time stepped from `2026-10-20T10:36:33` to `2026-10-25T15:08:33`

**Uncertainty label:** `HOST_CLOCK_NOT_SYNCHRONIZED__ABSOLUTE_UTC_CORRESPONDENCE_UNVERIFIED`

w32tm reports the clock is NOT synchronized and is sourced from the Local CMOS Clock, the same hardware previously measured 5.19 days behind at boot. Absolute wall-clock values therefore carry an unquantified offset. Relative ordering within this session remains valid because the measured modification times are strictly monotonic and no clock step occurred between them; a step would appear as a non-monotonic sequence or as an implausible gap.

## 6. What this does and does not establish

**Established.** The eight v1.1 documents were created in a strictly increasing sequence from 21:37:18 to 21:43:08. The manifest is last. Its inputs all existed when it ran. The dependency order is sound.

**Established.** 7 of the 9 documents that carry an embedded timestamp carry a hand-authored literal; 2 carries a genuinely computed value (the manifest). The literals are not measurements and must not be cited as creation times.

**Not established.** The absolute UTC time of any event on this host. The clock is unsynchronised and previously measured 5.19 days off.

**Not attempted.** No timestamp was rewritten, back-dated, or corrected. The defective embedded values remain in the v1.1 artifacts byte-for-byte, and this reconciliation is the additive record that they are defective.

## 7. Uncertainty labels

- `FILESYSTEM_TIMES_MEASURED_NOW__ABSOLUTE_VALUE_INHERITS_HOST_CLOCK_DEFECT`
- `EMBEDDED_TIMESTAMPS_ARE_NOT_MEASUREMENTS_UNLESS_CLASS_IS_COMPUTED_AT_WRITE`
- `EXACT_CREATION_ORDER_BEFORE_2026-10-26_UNRECOVERABLE_FROM_THIS_EVIDENCE`
- `NO_TIMESTAMP_WAS_REWRITTEN_TO_RESOLVE_THE_APPARENT_INVERSION`

*End of reconciliation. No artifact modified, no timestamp rewritten, no training, no inference.*
