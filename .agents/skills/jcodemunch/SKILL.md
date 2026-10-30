---
name: jcodemunch
description: Minimizes context consumption by building compressed structural code maps, symbol outlines, and compact multi-file indexes before loading entire source trees.
---

# jCodeMunch / Context Minimization

## Strategy
1. **Index Before Ingestion:**
   - When inspecting large modules, packages, or directories, never load thousands of lines blindly.
   - First obtain structural summaries: class hierarchies, function signatures, docstrings, exports (`__all__`), and module shapes.
2. **Dense Symbol Extraction:**
   - Use targeted regex/AST scans or specific line slicing to extract interface contracts and type annotations.
   - Keep file inspection windows tightly bound to the exact lines participating in the bug, refactor, or optimization.
3. **Data & Artifact Compacting:**
   - Summarize tabular data (CSV/JSON/Parquet) with shapes, column headers, non-null counts, and head/tail samples rather than dumping full tables.
   - For image/tensor batches, report tensor shapes, dtypes, value ranges ($\min, \max, \mu, \sigma$), and device residency.

