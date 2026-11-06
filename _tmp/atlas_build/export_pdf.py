import os
import win32com.client as win32

SRC = r"D:/Softfors/jup/reports/atlas/RA_MEDFILM_BARR_Research_Results_Atlas.docx"
DST = r"D:/Softfors/jup/reports/atlas/RA_MEDFILM_BARR_Research_Results_Atlas.pdf"

if os.path.exists(DST):
    os.remove(DST)
    print("removed stale pdf")

word = None
try:
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = word.Documents.Open(SRC)
    doc.ExportAsFixedFormat(DST, 17)
    pages = doc.ComputeStatistics(2)
    doc.Close(0)
    print("PDF_EXPORT_OK", DST, "pages", pages, "bytes", os.path.getsize(DST))
finally:
    if word is not None:
        try:
            word.Quit()
        except Exception:
            pass
