from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt


SONGTI = "\u5b8b\u4f53"
TIMES = "Times New Roman"
DOC_PATH = max(
    [p for p in (Path.cwd() / "reports").glob("*.docx") if "模板结构重写版" in p.name],
    key=lambda p: p.stat().st_mtime,
)


def looks_like_code(text: str) -> bool:
    return any(
        marker in text
        for marker in [
            "import ",
            "def ",
            "print(",
            "pd.",
            "GridSearchCV",
            "return ",
            "cleaned[",
            "metrics.append",
        ]
    )


def ensure_rfonts(run):
    if run._element.rPr is None:
        run._element.get_or_add_rPr()
    if run._element.rPr.rFonts is None:
        run._element.rPr.get_or_add_rFonts()
    return run._element.rPr.rFonts


def set_run_font(run, font_name: str, size: Pt, bold=None):
    run.font.name = font_name
    rfonts = ensure_rfonts(run)
    for attr in ["w:eastAsia", "w:ascii", "w:hAnsi", "w:cs"]:
        rfonts.set(qn(attr), font_name)
    run.font.size = size
    if bold is not None:
        run.bold = bold


def normalize_paragraph(paragraph, in_table=False):
    text = paragraph.text.strip()
    style_name = paragraph.style.name if paragraph.style else ""

    if looks_like_code(text):
        font_name = TIMES
        size = Pt(12)
        bold = None
        after = Pt(0)
    elif in_table:
        font_name = SONGTI
        size = Pt(10.5)
        bold = None
        after = Pt(0)
    elif style_name.startswith("Heading 1"):
        font_name = SONGTI
        size = Pt(16)
        bold = True
        after = Pt(6)
    elif style_name.startswith("Heading 2"):
        font_name = SONGTI
        size = Pt(14)
        bold = True
        after = Pt(4)
    elif style_name.startswith("Heading 3"):
        font_name = SONGTI
        size = Pt(12)
        bold = True
        after = Pt(3)
    else:
        font_name = SONGTI
        size = Pt(12)
        bold = None
        after = Pt(6)

    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = after
    for run in paragraph.runs:
        set_run_font(run, font_name, size, bold)


def normalize_doc():
    doc = Document(DOC_PATH)

    for style_name in ["Normal", "List Paragraph", "List Bullet", "List Number"]:
        if style_name in doc.styles:
            style = doc.styles[style_name]
            style.font.name = SONGTI
            style._element.rPr.rFonts.set(qn("w:eastAsia"), SONGTI)
            style._element.rPr.rFonts.set(qn("w:ascii"), SONGTI)
            style._element.rPr.rFonts.set(qn("w:hAnsi"), SONGTI)
            style._element.rPr.rFonts.set(qn("w:cs"), SONGTI)
            style.font.size = Pt(12)
            style.paragraph_format.line_spacing = 1.5

    for paragraph in doc.paragraphs:
        normalize_paragraph(paragraph)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    normalize_paragraph(paragraph, in_table=True)

    doc.save(DOC_PATH)
    print(DOC_PATH)


if __name__ == "__main__":
    normalize_doc()
