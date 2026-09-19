import json
from pathlib import Path
import hashlib

nb_path = Path("notebooks/13_phase14_regional_refiner_diagnostic.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

total_cells = len(nb["cells"])
print(f"Total cells: {total_cells}")
code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
print(f"Total code cells: {len(code_cells)}")

errors = []
for idx, c in enumerate(code_cells):
    ec = c.get("execution_count")
    outputs = c.get("outputs", [])
    errs = [o for o in outputs if o.get("output_type") == "error"]
    if errs:
        errors.append((idx, errs))
    has_display = any(o.get("output_type") == "display_data" for o in outputs)
    first_line = c["source"][0].strip() if c["source"] else ""
    print(f"Code cell {idx} (exec={ec}, outputs={len(outputs)}, has_display={has_display}): {first_line[:60]}...")

print(f"\nTotal errors across all code cells: {len(errors)}")
assert len(errors) == 0, f"Found {len(errors)} errors in notebook execution!"

# Cell 46 checks
c46 = code_cells[-1]
c46_outputs = c46.get("outputs", [])
c46_png = False
for o in c46_outputs:
    if o.get("output_type") == "display_data":
        data = o.get("data", {})
        if "image/png" in data:
            c46_png = True
            b64_len = len(data["image/png"])
            print(f"Cell 46 image/png size: {b64_len} characters (base64)")

print(f"Cell 46 embedded image/png present: {c46_png}")
assert c46_png, "Cell 46 did not embed image/png!"

# Print Cell 46 stdout
for o in c46_outputs:
    if o.get("output_type") == "stream" and o.get("name") == "stdout":
        print("\n--- Cell 46 Output ---")
        print("".join(o.get("text", [])))

# SHA-256
h = hashlib.sha256()
with open(nb_path, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):
        h.update(chunk)
final_sha = h.hexdigest()
print(f"Final Notebook SHA-256: {final_sha}")

