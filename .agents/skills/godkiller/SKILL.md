---
name: godkiller
description: Hard verification gate preventing premature task completion. Demands verifiable CLI/test execution evidence before declaring any task done.
---

# Godkiller / Hard Verification Gates

## Non-Negotiable Directives
1. **No Unverified Declarations:**
   - Never claim a task, bugfix, or refactor is complete (`claim_done` / status: PASS) without concrete execution evidence.
   - Theoretical correctness or absence of visible syntax errors is NOT proof of working software.
2. **Mandatory Execution Verification:**
   - Run the relevant test suite (e.g., `pytest`, unit testing harnesses, type checkers) in the execution environment.
   - Verify exit code `0` and explicitly inspect that tests were collected and executed (not skipped or silently bypassed).
3. **Artifact & Hash Integrity:**
   - If a build, release, or manifest is generated, independently compute and verify its physical file size and cryptographic digest (SHA-256).
   - Ensure clean working tree state or intentional scoped staging before finalizing work.

