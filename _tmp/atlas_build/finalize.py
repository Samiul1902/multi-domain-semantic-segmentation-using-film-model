import json, shutil
from pathlib import Path
from docx import Document

SRC = Path(r"D:/Softfors/jup/_tmp/atlas_build")
OUT = Path(r"D:/Softfors/jup/reports/atlas")
OUT.mkdir(parents=True, exist_ok=True)

# machine-readable index
idx = json.loads((SRC / "atlas_index.json").read_text(encoding="utf-8"))
(OUT / "atlas_table_figure_index.json").write_text(json.dumps(idx, indent=2), encoding="utf-8")
shutil.copyfile(SRC / "atlas_table_index.csv", OUT / "atlas_table_index.csv")
shutil.copyfile(SRC / "atlas_figure_index.csv", OUT / "atlas_figure_index.csv")
shutil.copyfile(SRC / "atlas_data.json", OUT / "atlas_data.json")

# structural verification
missing_fig = [f["id"] for f in idx["figures"] if not Path(f["path"]).exists()]
missing_src = []
for t in idx["tables"]:
    for s in t["sources"]:
        p = Path(s) if Path(s).is_absolute() else Path(r"D:/Softfors/jup") / s
        if not p.exists() and "multiple" not in s:
            missing_src.append((t["id"], s))

doc = Document(str(OUT / "RA_MEDFILM_BARR_Research_Results_Atlas.docx"))
print("DOCX tables:", len(doc.tables), "inline_shapes:", len(doc.inline_shapes),
      "paragraphs:", len(doc.paragraphs))
print("index tables:", len(idx["tables"]), "index figures:", len(idx["figures"]),
      "missing_sources:", len(idx["missing_sources"]))
print("missing figure files:", missing_fig)
print("missing table sources:", missing_src[:10])
print("files:", sorted(p.name for p in OUT.iterdir()))
