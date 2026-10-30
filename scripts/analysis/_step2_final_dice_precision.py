"""STEP 2.1 — final_dice TEXTUAL precision census (no float coercion for precision)."""
import csv
import os
from collections import Counter

ROOT = r"D:\Softfors\jup"
p = os.path.join(ROOT, "reports", "tables", "phase27_val808_per_sample_scores.csv")

raws = []
with open(p, "r", encoding="utf-8", newline="") as fh:
    rd = csv.DictReader(fh)
    for r in rd:
        raws.append(r["final_dice"])

digits = []
for s in raws:
    s = s.strip()
    if "." in s:
        frac = s.split(".", 1)[1]
        digits.append(len(frac))
    else:
        digits.append(0)

c = Counter(digits)
print("n rows:", len(raws))
print("min decimal digits:", min(digits))
print("max decimal digits:", max(digits))
print("digit-count distribution:", dict(sorted(c.items())))
print("first 5 raw:", raws[:5])
print("last 5 raw:", raws[-5:])
# distinct raw string count
distinct = len(set(raws))
print("distinct raw strings:", distinct)

# Check for scientific notation / trailing zeros / rounding evidence
sci = [s for s in raws if ("e" in s.lower())]
print("scientific-notation values:", len(sci), sci[:5])
trailing0 = [s for s in raws if s.endswith("0") and "." in s]
print("values ending in '0' (possible rounding artifact):", len(trailing0), trailing0[:8])

# full-repr float check: Python repr(float(x)) round-trips
import json
roundtrip_ok = 0
for s in raws:
    if repr(float(s)) == s:
        roundtrip_ok += 1
print("values equal to Python repr(float(x)) (full-repr persisted):", roundtrip_ok, "/", len(raws))
