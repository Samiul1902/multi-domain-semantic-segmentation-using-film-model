"""Additive R1 evaluation utilities; no authorization or data loading."""

VERSION = "evaluation_r1_v1"
DOMAINS = ("ISIC", "BUSI", "KVASIR", "KUB")
SCHEMA_VERSION = "harmonized_binary_v1"


def code_identity():
    """SHA-256 over sorted package source names and their raw byte hashes."""
    import hashlib
    import json
    from pathlib import Path
    root = Path(__file__).parent
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(root.iterdir()) if p.suffix in {".py", ".json"}}
    return hashlib.sha256(json.dumps(sources, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
