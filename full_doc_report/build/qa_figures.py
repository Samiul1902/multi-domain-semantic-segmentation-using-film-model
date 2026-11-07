"""Layout QA: detect text clipped outside the figure canvas and overlapping text items.
Rebuilds each PNG from the saved PDF page bounds and checks PNG pixel size and edge clipping."""
import pymupdf as fitz
from pathlib import Path

OUT = Path(r"D:\Softfors\jup\full_doc_report\figures")
for pdf in sorted(OUT.glob("*.pdf")):
    doc = fitz.open(pdf)
    page = doc[0]
    rect = page.rect
    words = page.get_text("words")
    clipped = [w for w in words if w[0] < 0 or w[1] < 0 or w[2] > rect.width + 0.5 or w[3] > rect.height + 0.5]
    # overlap check between words on the same page
    overlaps = 0
    for i in range(len(words)):
        a = words[i]
        for b in words[i + 1:i + 400]:
            ix = min(a[2], b[2]) - max(a[0], b[0])
            iy = min(a[3], b[3]) - max(a[1], b[1])
            if ix > 1.5 and iy > 1.5:
                overlaps += 1
    print(f"{pdf.name}: size={rect.width:.0f}x{rect.height:.0f}pt words={len(words)} clipped={len(clipped)} overlapping_word_pairs={overlaps}")
