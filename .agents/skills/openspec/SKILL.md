---
name: openspec
description: Spec-first software architecture guidelines, ensuring comprehensive design definitions, contracts, and interfaces are mapped out prior to deep implementation.
---

# OpenSpec: Spec-First Software Architecture

## Core Workflow
1. **Define the Specification First:**
   - Before executing non-trivial code modifications or deep architectural changes, declare the exact functional requirements, invariants, and failure modes.
   - Specify component inputs, outputs, types, and mathematical pre/post-conditions.
2. **Interface Boundaries & Modularity:**
   - Decouple data preparation, model architectures, loss formulations, metric calculators, and experiment orchestrators.
   - Avoid hidden global state; pass configuration explicitly through typed dataclasses or strict dictionaries.
3. **Migration & Deprecation Safety:**
   - Preserve historical baselines and backward compatibility.
   - Add new features additively (e.g., versioned packages or release candidates) without mutating frozen historical evidence or breaking reproducibility.

