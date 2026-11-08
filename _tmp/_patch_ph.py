import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_phase_inventory.py")
s = p.read_text(encoding="utf-8")

old = '''            # obsolete absolute paths pointing at an older layout
            if re.search(r"[A-Z]:\\\\\\\\?(?!Softfors)", src):
                stale += 1'''
new = '''            # obsolete: absolute paths that no longer resolve
            abs_paths = set(re.findall(r"[A-Za-z]:\\\\\\\\[^\\s'\\"\\),\\]]+", src))
            missing_paths = [q for q in abs_paths if not Path(q).exists()]
            if abs_paths and len(missing_paths) / len(abs_paths) > 0.5:
                stale += 1'''
assert old in s, "stale block not found"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("PATCHED")
