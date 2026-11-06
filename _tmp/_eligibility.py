"""C1 eligibility verification — read-only. No training, no TEST access, no authority minting."""
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, r"D:\Softfors\jup")
ROOT = Path(r"D:\Softfors\jup")
R = []


def check(name, fn):
    try:
        R.append((name, "PASS", str(fn())))
    except Exception as e:  # noqa: BLE001
        R.append((name, "FAIL", f"{type(e).__name__}: {e}"))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# 1. interpreter
check("interpreter.executable", lambda: sys.executable)
check("interpreter.prefix_is_venv", lambda: sys.prefix == r"D:\Softfors\jup\.venv")
check("interpreter.version", lambda: sys.version.split()[0])

# 2. CUDA / GPU
def gpu():
    import torch
    assert torch.cuda.is_available(), "CUDA unavailable"
    name = torch.cuda.get_device_name(0)
    cap = torch.cuda.get_device_capability(0)
    total = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
    a = torch.randn(256, 256, device="cuda"); b = torch.randn(256, 256, device="cuda")
    c = a @ b; torch.cuda.synchronize()
    assert torch.isfinite(c).all()
    return f"{name} cc={cap} {total:.2f} GiB torch={torch.__version__} cuda={torch.version.cuda}"
check("gpu.cuda_and_tensor_op", gpu)

# 3. frozen protocol
PROTO = ROOT / "reports/planning/c1_film_attribution_v1/protocol.json"
EXPECTED_PROTO = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"
check("protocol.file_exists", lambda: PROTO.is_file())
check("protocol.sha256_matches_frozen",
      lambda: (_ for _ in ()).throw(AssertionError(f"{sha(PROTO)} != {EXPECTED_PROTO}"))
      if sha(PROTO) != EXPECTED_PROTO else sha(PROTO))

# 4. manifests
TRAIN = ROOT / "manifests/phase4_v3/train.csv"
VAL = ROOT / "manifests/phase4_v3/val.csv"
EXP_TRAIN = "28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6"
EXP_VAL = "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315"
check("manifest.train.sha256", lambda: sha(TRAIN) if sha(TRAIN) == EXP_TRAIN else (_ for _ in ()).throw(AssertionError(sha(TRAIN))))
check("manifest.val.sha256", lambda: sha(VAL) if sha(VAL) == EXP_VAL else (_ for _ in ()).throw(AssertionError(sha(VAL))))


def rows(p):
    with p.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


check("manifest.train.rows", lambda: len(rows(TRAIN)))
check("manifest.val.rows", lambda: len(rows(VAL)))


def splits():
    tr, va = rows(TRAIN), rows(VAL)
    assert len(tr) == 5832 and len(va) == 808, (len(tr), len(va))
    assert {r["split"] for r in tr} == {"TRAIN"}, {r["split"] for r in tr}
    assert {r["split"] for r in va} == {"VAL"}, {r["split"] for r in va}
    overlap = {r["sample_id"] for r in tr} & {r["sample_id"] for r in va}
    assert not overlap, f"overlap={len(overlap)}"
    return f"train=5832 val=808 split_ok overlap=0 cols={list(tr[0])[:4]}..."
check("manifest.split_and_overlap", splits)


def files():
    tr, va = rows(TRAIN), rows(VAL)
    miss = 0
    for r in tr + va:
        for k in ("image_path", "mask_path"):
            if not Path(r[k]).is_file():
                miss += 1
    assert miss == 0, f"missing={miss}"
    return f"checked {len(tr)+len(va)} rows x 2 paths; missing=0"
check("manifest.files_present", files)

# 5. TEST lock (hashes the frozen manifest only; no images/masks/predictions)
def testlock():
    from src.utils.test_lock import verify_test_lock
    lock = verify_test_lock(str(ROOT))
    return f"manifest_version={lock['manifest_version']} n={lock['test_sample_count']} locked"
check("test.lock_verifies", testlock)
check("test.v3_manifest_not_opened_by_this_check", lambda: "manifests/phase4_v3/test.csv NOT read")

# 6. matched arms
def arms():
    import torch
    from src.research.c1_film.control import build_matched_arms, parameter_accounting
    from src.research.c1_film.training_engine import initial_digest
    t, c = build_matched_arms(42)
    st, sc = t.state_dict(), c.state_dict()
    assert set(st) == set(sc)
    identical = all(torch.equal(st[k], sc[k]) for k in st)
    dt, dc = initial_digest(t), initial_digest(c)
    assert identical and dt == dc
    assert dt == "77b74cf12446a28b36eb4813f7ed628e0e9da753bcf0c41b679d67cffc94fe11", dt
    return (f"identical_initial=True digest={dt[:16]} "
            f"T={parameter_accounting(t)['trainable']} C={parameter_accounting(c)['trainable']} "
            f"total={parameter_accounting(t)['total']}")
check("c1.matched_initial_weights", arms)

# 7. authorization surfaces
from src.research.c1_film_launch_rc4 import trust_rc4
check("auth.rc4_trust_root_exists", lambda: trust_rc4.PRODUCTION_ROOT.is_dir())
check("auth.rc4_trust_root_path", lambda: str(trust_rc4.PRODUCTION_ROOT))
check("auth.legacy_root_present_but_contaminated", lambda: trust_rc4.LEGACY_ROOT.is_dir())


def rc4_identity():
    from src.research.c1_film_launch_rc4 import release_identity_rc4 as rid
    return rid.verify_release_rc4()["release_digest"]
check("auth.rc4_release_identity", rc4_identity)


def approval_status():
    d = json.loads((ROOT / "configs/c1_operator/approval.json").read_text(encoding="utf-8"))
    return f"authorized_by={d.get('authorized_by')!r} (AGENT-GENERATED CONTAMINATION — not authority)"
check("auth.approval_json_is_contaminated", approval_status)

# 8. existing real runs
def runs():
    base = ROOT / "experiments/c1_film_attribution_v1"
    if not base.exists():
        return "no experiments/c1_film_attribution_v1 directory (0 runs)"
    return f"entries={[p.name for p in base.iterdir()][:10]}"
check("c1.existing_real_runs", runs)

# 9. licence / ethics record
def licence():
    candidates = [
        ROOT / "docs/dataset_licences.md", ROOT / "docs/ethics_approval.md",
        ROOT / "docs/IRB.md", ROOT / "LICENSES.md", ROOT / "data/LICENSE",
        ROOT / "docs/licence_and_ethics_attestation.md",
    ]
    found = [str(p.relative_to(ROOT)) for p in candidates if p.exists()]
    return f"records_found={found}" if found else "NONE (no licence/ethics record in repository)"
check("permissions.licence_ethics_record", licence)

print("=" * 78)
for name, status, detail in R:
    print(f"{status:<5} {name:<48} {detail}")
print("=" * 78)
print("FAILS:", sum(1 for _, s, _ in R if s == "FAIL"))
