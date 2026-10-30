---
name: clean-code
description: Enforces test-driven development (TDD), static analysis cleanliness, robust error taxonomy, and vulnerability-free coding practices.
---

# Clean Code & Vulnerability Scanner Directives

## Implementation Rules
1. **Defensive Coding & Type Safety:**
   - Use explicit type annotations on public module APIs, dataclasses, and functions.
   - Validate input contracts at the boundaries; fail early and fail informatively with specific exception hierarchies.
2. **Deterministic Test-Driven Development (TDD):**
   - Accompany architectural changes or new modules with synthetic, self-contained unit tests.
   - Cover edge cases: empty inputs, out-of-distribution shapes, NaN/Inf tensor handling, and permission failures.
3. **Security & Cryptographic Hygiene:**
   - Never embed secret keys, credentials, or private keys inside codebase repositories.
   - Use secure temporary files and verify file permissions when interacting with OS trust stores or local services.
   - Prevent command injection or unsanitized shell evaluation when spawning external processes.

