"""Generate minimal DOCX probes to isolate what Word COM refuses to open."""
import sys
from pathlib import Path
from docx import Document
from docx.shared import Mm
from docx.oxml import OxmlElement

HERE = Path(__file__).resolve().parent
FIG = HERE.parent / "figures" / "V8_F01_accuracy_cost.png"


def save(d, name):
    p = HERE / (".probe_" + name + ".docx")
    d.save(p)
    print(p.name, p.stat().st_size)


# 1 bare
d = Document(); d.add_paragraph("hello"); save(d, "1_bare")

# 2 one image
d = Document(); d.add_paragraph("hello")
d.add_paragraph().add_run().add_picture(str(FIG), width=Mm(150)); save(d, "2_image")

# 3 one table with rules + shading + repeat header
d = Document(); t = d.add_table(rows=2, cols=3)
t.rows[0].cells[0].text = "h"
from v8_report import table_rules, shade, cell_border_bottom, repeat_header
table_rules(t); shade(t.rows[0].cells[0], "EAF0F7")
cell_border_bottom(t.rows[0].cells[0]); repeat_header(t.rows[0]); save(d, "3_table")

# 4 TOC field
from v8_report import field
d = Document(); p = d.add_paragraph(); field(p, ' TOC \\o "1-2" \\h \\z \\u ', "x"); save(d, "4_field")

# 5 header/footer page fields
from v8_report import setup_document
save(setup_document(), "5_setup")

# 6 setup + heading styles with pBdr
d = setup_document(); d.add_heading("1.  Hello", level=1); d.add_paragraph("body"); save(d, "6_heading")

# 7 everything from setup + one of each block
d = setup_document(); d.add_heading("1.  Hello", level=1); d.add_paragraph("body")
t = d.add_table(rows=2, cols=3); table_rules(t); shade(t.rows[0].cells[0], "EAF0F7")
cell_border_bottom(t.rows[0].cells[0]); repeat_header(t.rows[0])
d.add_paragraph().add_run().add_picture(str(FIG), width=Mm(150))
save(d, "7_all")
