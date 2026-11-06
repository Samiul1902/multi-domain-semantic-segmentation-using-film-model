import pymupdf, pathlib
pdf = r"D:/Softfors/jup/reports/atlas/RA_MEDFILM_BARR_Research_Results_Atlas.pdf"
out = pathlib.Path(r"D:/Softfors/jup/_tmp/atlas_build/pdf_pages"); out.mkdir(parents=True, exist_ok=True)
doc = pymupdf.open(pdf)
print("pages", doc.page_count)
for i in range(doc.page_count):
    pix = doc[i].get_pixmap(dpi=110)
    pix.save(out / f"p{i+1:02d}.png")
print("rendered", doc.page_count, "pages to", out)
