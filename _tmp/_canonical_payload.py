"""Runs INSIDE D:\\Softfors\\jup\\.venv\\Scripts\\python.exe — read-only verification."""
import pathlib
import sys
import tempfile

sys.path.insert(0, r"D:\Softfors\jup")

print("EXECUTABLE", sys.executable)
print("PREFIX", sys.prefix)
print("BASE_PREFIX", sys.base_prefix)
print("VERSION", sys.version.split()[0])
print("IS_VENV", sys.prefix != sys.base_prefix)

import numpy as np
print("NUMPY", np.__version__)

import torch
print("TORCH", torch.__version__)
print("CUDA_AVAILABLE", torch.cuda.is_available())
print("CUDA_BUILD", torch.version.cuda)
if torch.cuda.is_available():
    print("DEVICE_COUNT", torch.cuda.device_count())
    print("DEVICE_NAME", torch.cuda.get_device_name(0))
    print("CAPABILITY", torch.cuda.get_device_capability(0))
    torch.manual_seed(42)
    a = torch.randn(512, 512, device="cuda")
    b = torch.randn(512, 512, device="cuda")
    c = a @ b
    torch.cuda.synchronize()
    d = a.cpu() @ b.cpu()
    print("GPU_MATMUL_SHAPE", tuple(c.shape))
    print("GPU_MATMUL_FINITE", bool(torch.isfinite(c).all()))
    print("GPU_CPU_MAXABS", float((c.cpu() - d).abs().max()))
    print("PEAK_ALLOC_MIB", round(torch.cuda.max_memory_allocated(0) / 1024 ** 2, 2))

# Focused research integration: Phase 22 primitives + Phase 41/42 package round-trip.
from src.analysis import phase22_common as C
from src.research.deployment import artifacts as A
from src.research.deployment.validation import assert_exact

print("PHASE22_THRESHOLD", C.THRESHOLD)
print("PHASE22_SIZES", list(C.SUPPORTED_SIZES))
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    files = {}
    for n in "GRBS":
        p = td / f"{n}.bin"
        p.write_bytes(f"SYNTHETIC_{n}".encode())
        files[n] = p
    shas = {k: A.digest(v) for k, v in files.items()}
    cfg = dict(family="FULL", seed=42, protocol_sha256="a" * 64, source_sha256="b" * 64,
               preprocessing=dict(channels=3, resolution=512,
                                  implementation_sha256="c" * 64,
                                  contract_id="synthetic_verify"),
               roi_threshold=.3, segmentation_threshold=.5, safety_threshold=.5,
               router_numeric_dim=202, task_embedding_dim=16, router_total_dim=218,
               evidence_class="SYNTHETIC_TEST_ONLY")
    root = td / "pkg"
    sha = A.package(root, files, shas, cfg)
    A.verify(root, sha)
    print("PACKAGING_ROUNDTRIP_OK", sha[:16])
assert_exact({"p": torch.ones(2, 2)}, {"p": torch.ones(2, 2)})
print("PARITY_HELPER_OK")

import scripts.analysis.phase39_final_test_common_v1_2 as P39
print("PHASE39_CONSTANTS_OK", P39.TEST_N, P39.SEGMENTATION_THRESHOLD)

print("CANONICAL_VERIFICATION_OK")
