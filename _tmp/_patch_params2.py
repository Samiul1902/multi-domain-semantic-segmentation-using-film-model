import pathlib

# ------------------------------------------------------------ remedfilm -----
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

old25 = '''        code(r\'\'\'
inv = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
print("component inventory")
inv[["symbol", "model_class", "parameters", "conditional", "role"]].to_string(index=False)
print()
print("sum of components:", int(inv[inv.symbol != "FULL"].parameters.sum()))
\'\'\'),'''
new25 = '''        code(r\'\'\'
inv = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
print("component inventory (corrected parameter column)")
inv[["symbol", "model_class", "parameters", "conditional", "role"]].to_string(index=False)
print()
comp = inv[inv.symbol != "FULL"]
print("sum of components:", int(comp.parameters.sum()))
\'\'\'),'''
assert old25 in t, "nb25 block not found"
t = t.replace(old25, new25)

old26 = '''        code(r\'\'\'
inv = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
inv[["symbol", "model_class", "checkpoint", "role", "conditional", "parameters"]].to_string(index=False)
\'\'\'),'''
new26 = '''        code(r\'\'\'
inv = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
inv[["symbol", "model_class", "checkpoint", "role", "conditional", "parameters"]].to_string(index=False)
\'\'\'),'''
assert old26 in t, "nb26 block not found"
t = t.replace(old26, new26)
q.write_text(t, encoding="utf-8")
print("remedfilm notebooks patched")

# ------------------------------------------------------- phase notebooks ----
r = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_phase_notebooks.py")
u = r.read_text(encoding="utf-8")
old24 = '''        code(r\'\'\'
# Cross-check: the realised parameter counts against the Phase 24 targets.
real = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
real[["symbol", "model_class", "parameters", "role"]]
\'\'\'),'''
new24 = '''        code(r\'\'\'
# Cross-check: realised parameter counts against the Phase 24 targets.
real = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
real[["symbol", "model_class", "role", "parameters"]]
\'\'\'),'''
assert old24 in u, "nb24 block not found"
u = u.replace(old24, new24)

# phase 25/26 notebooks also read the frozen inventory
u = u.replace(
    '''inv = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
print("component inventory")
inv[["symbol", "model_class", "parameters", "conditional", "role"]].to_string(index=False)''',
    '''inv = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
print("component inventory (corrected parameter column)")
inv[["symbol", "model_class", "parameters", "conditional", "role"]].to_string(index=False)''')
u = u.replace(
    '''inv = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
inv[["symbol", "model_class", "checkpoint", "role", "conditional", "parameters"]].to_string(index=False)''',
    '''inv = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
inv[["symbol", "model_class", "checkpoint", "role", "conditional", "parameters"]].to_string(index=False)''')
r.write_text(u, encoding="utf-8")
print("phase notebooks patched")
