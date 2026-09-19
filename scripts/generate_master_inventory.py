import os, sys, hashlib, json, csv
from pathlib import Path
from collections import Counter

targets = ['notebooks', 'reports', 'checkpoints', 'configs', 'scripts', 'src', 'manifests', 'docs']
inventory = []

for t in targets:
    p = Path(t)
    if not p.exists():
        continue
    for f in p.rglob('*'):
        if f.is_file():
            size = f.stat().st_size
            if size < 50 * 1024 * 1024:
                try:
                    h = hashlib.sha256(f.read_bytes()).hexdigest()
                except Exception:
                    h = 'ERROR_READING'
            else:
                h = 'EXCEEDS_50MB'
            
            ext = f.suffix.lower()
            rel = str(f).replace('\\', '/')
            inventory.append({
                'path': rel,
                'size_bytes': size,
                'sha256': h,
                'extension': ext,
                'parent_dir': str(f.parent).replace('\\', '/')
            })

print(f"Total scanned files: {len(inventory)}")

out_json = Path('reports/audits/master_project_file_inventory.json')
out_json.parent.mkdir(parents=True, exist_ok=True)
with open(out_json, 'w', encoding='utf-8') as jf:
    json.dump(inventory, jf, indent=2)

out_csv = Path('reports/audits/master_project_file_inventory.csv')
with open(out_csv, 'w', encoding='utf-8', newline='') as cf:
    writer = csv.DictWriter(cf, fieldnames=['path', 'size_bytes', 'sha256', 'extension', 'parent_dir'])
    writer.writeheader()
    writer.writerows(inventory)

out_md = Path('reports/audits/master_project_file_inventory.md')
lines = [
    "# Master Project File Inventory",
    "",
    f"- **Total Cataloged Files:** {len(inventory)}",
    "- **Generated At:** 2026-09-19",
    "- **Scope:** `notebooks/`, `reports/`, `checkpoints/`, `configs/`, `scripts/`, `src/`, `manifests/`, `docs/`",
    "",
    "## File Type Breakdown",
    ""
]

counts = Counter([item['extension'] for item in inventory])
for ext, count in counts.most_common():
    label = ext if ext else "[no_ext]"
    lines.append(f"- `{label}`: {count}")

lines.extend([
    "",
    "## Target Preservation Integrity",
    "- Canonical Frozen Notebook SHA-256 (`notebooks/13_phase14_regional_refiner_diagnostic.ipynb`):"
])

canon_found = False
for item in inventory:
    if item['path'] == 'notebooks/13_phase14_regional_refiner_diagnostic.ipynb':
        canon_found = True
        lines.append(f"  - Actual: `{item['sha256']}`")
        lines.append(f"  - Expected: `b5b329d1d100138db640e4a3e91069a4008a434d998945646bc7a4522c040948`")
        assert item['sha256'] == 'b5b329d1d100138db640e4a3e91069a4008a434d998945646bc7a4522c040948', f"Hash mismatch: {item['sha256']}"

assert canon_found, "Canonical notebook not found in inventory!"

out_md.write_text("\n".join(lines), encoding='utf-8')
print("Inventory generated and verified successfully!")

