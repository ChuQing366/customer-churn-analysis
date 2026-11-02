from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt


DOC = Path.cwd() / "reports" / "第五组-企业客户流失与预警分析系统-保留模板结构版.docx"
SONGTI = "\u5b8b\u4f53"
TIMES = "Times New Roman"


def looks_like_code(text):
    return any(x in text for x in ["import ", "def ", "pd.", "GridSearchCV", "return ", "metrics.append"])


def set_font(run, name, size):
    run.font.name = name
    if run._element.rPr is None:
        run._element.get_or_add_rPr()
    if run._element.rPr.rFonts is None:
        run._element.rPr.get_or_add_rFonts()
    for attr in ["w:eastAsia", "w:ascii", "w:hAnsi", "w:cs"]:
        run._element.rPr.rFonts.set(qn(attr), name)
    run.font.size = Pt(size)


def apply():
    doc = Document(DOC)
    for idx, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if not text:
            continue
        # Preserve cover page's original visual size by only setting font family
        # on the first template page. Body starts after paragraph 38 in this file.
        if idx <= 38:
            for r in p.runs:
                if r.text.strip():
                    set_font(r, SONGTI, r.font.size.pt if r.font.size else 12)
            continue
        size = 12
        name = TIMES if looks_like_code(text) else SONGTI
        p.paragraph_format.line_spacing = 1.5
        for r in p.runs:
            set_font(r, name, size)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    text = p.text.strip()
                    name = TIMES if looks_like_code(text) else SONGTI
                    size = 12 if looks_like_code(text) else 10.5
                    p.paragraph_format.line_spacing = 1.5
                    for r in p.runs:
                        set_font(r, name, size)

    doc.save(DOC)
    print(DOC)


if __name__ == "__main__":
    apply()
