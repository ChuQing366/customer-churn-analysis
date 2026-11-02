from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from PIL import Image


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: inspect_docx_report.py <docx>")

    path = Path(sys.argv[1])
    doc = Document(path)
    print(f"path={path}")
    print(f"paragraphs={len(doc.paragraphs)}")
    print(f"tables={len(doc.tables)}")
    print(f"sections={len(doc.sections)}")
    print(f"inline_shapes={len(doc.inline_shapes)}")
    print("\nPARAGRAPHS")
    for index, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            print(f"{index:04d}\t{para.style.name}\t{text[:180]}")
    print("\nTABLES")
    for index, table in enumerate(doc.tables):
        rows = len(table.rows)
        cols = len(table.columns)
        preview = []
        for row in table.rows[:2]:
            preview.append(" | ".join(cell.text.strip().replace("\n", " / ")[:50] for cell in row.cells[:4]))
        print(f"{index:03d}\t{rows}x{cols}\t{' || '.join(preview)}")
    print("\nINLINE SHAPES")
    for index, shape in enumerate(doc.inline_shapes, start=1):
        print(f"{index:03d}\t{shape.width / 914400:.2f}in x {shape.height / 914400:.2f}in")
    print("\nEMBEDDED IMAGES")
    with ZipFile(path) as archive:
        image_names = [name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        for index, name in enumerate(image_names, start=1):
            try:
                with archive.open(name) as handle:
                    image = Image.open(handle)
                    print(f"{index:03d}\t{name}\t{image.size[0]}x{image.size[1]}\t{image.mode}")
            except Exception as exc:
                print(f"{index:03d}\t{name}\tunreadable\t{exc}")


if __name__ == "__main__":
    main()
