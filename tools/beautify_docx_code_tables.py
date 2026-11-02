from __future__ import annotations

import shutil
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


CODE_TABLE_INDEXES = {1, 2, 3, 4}


def set_cell_shading(cell, fill: str = "F6F8FA") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = tc_pr.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        tc_pr.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_margins(cell, margin_dxa: int = 160) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for side in ("top", "left", "bottom", "right"):
        element = tc_mar.find(qn(f"w:{side}"))
        if element is None:
            element = OxmlElement(f"w:{side}")
            tc_mar.append(element)
        element.set(qn("w:w"), str(margin_dxa))
        element.set(qn("w:type"), "dxa")


def set_table_borders(table, color: str = "D0D7DE", size: str = "8") -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_no_proof(run) -> None:
    r_pr = run._r.get_or_add_rPr()
    if r_pr.find(qn("w:noProof")) is None:
        r_pr.append(OxmlElement("w:noProof"))


def format_code_table(table) -> None:
    table.autofit = False
    table.allow_autofit = False
    table.width = Inches(6.1)
    set_table_borders(table)

    for row in table.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            set_cell_shading(cell)
            set_cell_margins(cell)
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                paragraph.paragraph_format.left_indent = Pt(0)
                paragraph.paragraph_format.right_indent = Pt(0)
                paragraph.paragraph_format.first_line_indent = Pt(0)
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.05
                for run in paragraph.runs:
                    run.font.name = "Consolas"
                    run.font.size = Pt(8.5)
                    run.font.bold = False
                    run.font.italic = False
                    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
                    set_no_proof(run)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: beautify_docx_code_tables.py <input.docx> <output.docx>")

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    shutil.copy2(input_path, output_path)
    doc = Document(output_path)
    for index, table in enumerate(doc.tables):
        if index in CODE_TABLE_INDEXES:
            format_code_table(table)
    doc.save(output_path)
    print(output_path)


if __name__ == "__main__":
    main()
