---
name: deepmind-science
description: Structured scientific workflows for AI/ML/DL research, mathematical formulation verification, reproducible training checkpoints, and empirical metric logging.
---

# DeepMind Science & ML Research Directives

## Scientific Rigor & Protocol Integrity
1. **Mathematical Grounding:**
   - Always reconcile mathematical specifications against concrete PyTorch/JAX model implementations (e.g., verify activation bounding, zero-initialization, exact loss coefficients).
   - Formulate loss functions, scaling rules, and modular pipelines with explicit equations before coding.
2. **Deterministic Reproducibility:**
   - Control all random generators: Python `random`, NumPy `np.random`, PyTorch `torch.manual_seed`, `torch.cuda.manual_seed_all`, and worker process seeds.
   - Set deterministic backends (`torch.backends.cudnn.deterministic = True`, `benchmark = False`) when exact replicability is mandated by protocol.
3. **Model & Checkpoint Governance:**
   - Ensure all checkpoint saves are atomic (write to temp file, flush/sync, rename).
   - Enforce cryptographic fingerprinting (SHA-256) of datasets, manifests, configs, and model weights to detect data drift or split contamination.
4. **Data Isolation & Leakage Prevention:**
   - Maintain strict separation across Train, Validation, and Test splits.
   - Never inspect, decode, visualize, or compute metrics on held-out or test splits during training or hyperparameter search.
   - Check for duplicate or near-duplicate leakage across patient/donor/source groupings.

