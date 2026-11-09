"""Create truncated copies of the V8 DOCX body to locate the construct Word rejects."""
import copy
import sys
from pathlib import Path
from docx import Document

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "ReMedFiLM_Complete_Scientific_Report_V8.docx"

d = Document(SRC)
body = d.element.body
children = [c for c in body.iterchildren() if c.tag.endswith("}sectPr") is False]
sect = [c for c in body.iterchildren() if c.tag.endswith("}sectPr")]
print("body children:", len(children), "sectPr:", len(sect))

fractions = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
for fr in fractions:
    n = max(1, int(len(children) * fr))
    doc = Document(SRC)
    b = doc.element.body
    keep = [c for c in b.iterchildren() if not c.tag.endswith("}sectPr")][:n]
    for c in list(b.iterchildren()):
        if c.tag.endswith("}sectPr"):
            continue
        b.remove(c)
    # re-append kept elements before sectPr
    sp = [c for c in b.iterchildren() if c.tag.endswith("}sectPr")]
    for c in keep:
        if sp:
            sp[0].addprevious(c)
        else:
            b.append(c)
    out = HERE / f".bisect_{int(fr*100):03d}.docx"
    doc.save(out)
    print(out.name, n, out.stat().st_size)
