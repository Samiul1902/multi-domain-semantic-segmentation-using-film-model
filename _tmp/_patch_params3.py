import pathlib

# ------------------------------------------- ReMedFiLM notebook 01 only -----
q = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_remedfilm_notebooks.py")
t = q.read_text(encoding="utf-8")

old01 = '''        code(r\'\'\'
inv = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
inv[["symbol", "model_class", "role", "conditional", "parameters"]].to_string(index=False)
\'\'\'),
        code(r\'\'\'
print("FULL resident parameters:", int(inv[inv.symbol == "FULL"].parameters.iloc[0]))
parts = inv[inv.symbol != "FULL"].set_index("symbol").parameters.astype(int)
print("component sum           :", int(parts.sum()))
assert int(parts.sum()) == int(inv[inv.symbol == "FULL"].parameters.iloc[0])
print()
for k, v in parts.items():
    print(f"  {k:8s} {v:>10,}  ({v / parts.sum():6.2%})")
\'\'\'),'''

new01 = '''        code(r\'\'\'
parts = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
parts[["symbol", "model_class", "role", "conditional", "parameters"]].to_string(index=False)
\'\'\'),
        code(r\'\'\'
comp = parts[parts.symbol != "FULL"].set_index("symbol").parameters.astype(int)
total = int(parts[parts.symbol == "FULL"].parameters.iloc[0])
print("FULL resident parameters:", total)
print("component sum           :", int(comp.sum()))
assert int(comp.sum()) == total
print()
for k, v in comp.items():
    print(f"  {k:8s} {v:>10,}  ({v / total:6.2%})")
print()
raw = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
print("NOTE — phase26_component_inventory.csv has a units defect: it stores")
print(f"  G.parameters = {int(raw[raw.symbol == 'G'].parameters.iloc[0]):,} (that is MACs)")
print("The corrected derived table is used here. See DEFECT-01.")
\'\'\'),'''
assert old01 in t, "nb01 block not found"
t = t.replace(old01, new01)
q.write_text(t, encoding="utf-8")
print("remedfilm nb01 patched")

# ------------------------------------------------ phase notebooks 24/25/26 --
r = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_phase_notebooks.py")
u = r.read_text(encoding="utf-8")
n = 0
pairs = [
    ('''real = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
real[["symbol", "model_class", "parameters", "role"]]''',
     '''real = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
real[["symbol", "model_class", "role", "parameters"]]'''),
    ('''inv = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
print("component inventory")
inv[["symbol", "model_class", "parameters", "conditional", "role"]].to_string(index=False)
print()
print("sum of components:", int(inv[inv.symbol != "FULL"].parameters.sum()))''',
     '''inv = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
print("component inventory (corrected parameter column)")
inv[["symbol", "model_class", "parameters", "conditional", "role"]].to_string(index=False)
print()
print("sum of components:", int(inv[inv.symbol != "FULL"].parameters.sum()))'''),
    ('''inv = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
inv[["symbol", "model_class", "checkpoint", "role", "conditional", "parameters"]].to_string(index=False)''',
     '''inv = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
inv[["symbol", "model_class", "checkpoint", "role", "conditional", "parameters"]].to_string(index=False)'''),
]
for old, new in pairs:
    if old in u:
        u = u.replace(old, new)
        n += 1
    else:
        print("  not found:", old.splitlines()[0][:60])
r.write_text(u, encoding="utf-8")
print(f"phase notebooks patched: {n}/3")
