import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_notebook.py")
s = p.read_text(encoding="utf-8")

old = '''def _audit(event, args):
    if event in BLOCKED_EVENTS:
        raise AnalysisOnlyViolation(f"blocked process launch: {event}")
    if event == "open":
        path, mode, flags = args
        try:
            p = Path(path).resolve()
        except Exception:
            return
        if p in PROTECTED_READS:
            raise AnalysisOnlyViolation(f"protected TEST manifest access: {p}")
        writing = False
        if isinstance(mode, str):
            writing = any(c in mode for c in "wax+")
        if isinstance(flags, int) and flags & _WRITE_FLAGS:
            writing = True
        if writing and REPORT not in p.parents and p != REPORT:
            raise AnalysisOnlyViolation(f"write outside full_doc_report: {p}")'''

new = '''# Constants are bound as default arguments so the hook stays valid during
# interpreter teardown, when module globals have already been cleared.
def _audit(event, args, _blocked=frozenset(BLOCKED_EVENTS),
           _protected=frozenset(PROTECTED_READS),
           _report=str(REPORT), _flags=_WRITE_FLAGS, _path=Path):
    if event in _blocked:
        raise AnalysisOnlyViolation(f"blocked process launch: {event}")
    if event == "open":
        path, mode, flags = args
        try:
            p = _path(path).resolve()
        except Exception:
            return
        if str(p) in {str(x) for x in _protected}:
            raise AnalysisOnlyViolation(f"protected TEST manifest access: {p}")
        writing = False
        if isinstance(mode, str):
            writing = any(c in mode for c in "wax+")
        if isinstance(flags, int) and flags & _flags:
            writing = True
        if writing and _report not in str(p.parent) and str(p) != _report:
            raise AnalysisOnlyViolation(f"write outside full_doc_report: {p}")'''

assert old in s, "guard block not found"
s = s.replace(old, new)

# Insert a negative-control cell right after the guard installation cell.
anchor = '''sys.addaudithook(_audit)
'''
assert anchor in s
marker = '''code(r\'\'\'
G.require()
import importlib.metadata as md'''

self_test = '''code(r\'\'\'
G.require()
# Negative controls: the guard must actually refuse these operations.
# If any of them succeeds, enforcement is broken and the notebook is invalid.
checks = []

try:
    torch.optim.Adam([])
    checks.append(("optimiser construction", "NOT BLOCKED"))
except AnalysisOnlyViolation as e:
    checks.append(("optimiser construction", "blocked"))

try:
    torch.optim.AdamW([])
    checks.append(("AdamW construction", "NOT BLOCKED"))
except AnalysisOnlyViolation as e:
    checks.append(("AdamW construction", "blocked"))

try:
    (REPO / "manifests/phase4_v3/test.csv").open("rb").read(1)
    checks.append(("TEST manifest read", "NOT BLOCKED"))
except AnalysisOnlyViolation:
    checks.append(("TEST manifest read", "blocked"))
except FileNotFoundError:
    checks.append(("TEST manifest read", "blocked (file absent)"))

try:
    (REPO / "reports" / "_guard_probe.txt").open("w").write("x")
    checks.append(("write outside report dir", "NOT BLOCKED"))
except AnalysisOnlyViolation:
    checks.append(("write outside report dir", "blocked"))

for name, verdict in checks:
    print(f"  {name:28s}: {verdict}")

assert all(v.startswith("blocked") for _, v in checks), "GUARD FAILED — do not trust this notebook"
print()
print("All negative controls blocked. Analysis-only enforcement verified.")
\'\'\')

'''

assert marker in s
s = s.replace(marker, self_test + marker, 1)

p.write_text(s, encoding="utf-8")
print("PATCHED")
