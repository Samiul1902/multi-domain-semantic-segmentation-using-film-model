# PHASE-13 PART-1B — BINDING CSV R2A SHA ERRATUM

**Type:** `PROVENANCE_METADATA_CORRECTION_ONLY` · **Status:** `PASS`

## Defect

Ten R2A-linked rows in the binding CSV carried a **malformed** R2A SHA that did not correspond to the physical on-disk amendment.

- wrong SHA: `f3aececfbe683fa7c60ea75820d2ef3de3ab0d4fc29c9a3e02d2ce5bd4a1f4d1`
- occurrences before: 10 → after: **0**

## Correction

1. Physically SHA-256 hashed the on-disk R2A JSON:
   `f3aececfbe683fa7c60ea758b7b7d6446e3cc6584e86e8faa2c7eb4f14029667`
2. Verified it equals the canonical value `f3aececfbe683fa7c60ea758b7b7d6446e3cc6584e86e8faa2c7eb4f14029667` — **MATCH**.
3. Rebuilt the CSV deterministically with a real CSV writer so every R2A-sourced row cites the exact physical SHA.

## Non-changes

- **scientific values edited: NO**
- all 10 `SUPERSEDED_PRIOR_CHECK_REQUIRED_AUDIT` rows preserved
- `pandas.read_csv` passes with no special options; shape 130 × 6

## Hashes

- CSV before: `1dfbe95bd85a3ad6b6991ef30987f70f08f9cefcef45fbc1779abb65f75a4862`
- CSV after : `1dfbe95bd85a3ad6b6991ef30987f70f08f9cefcef45fbc1779abb65f75a4862`
