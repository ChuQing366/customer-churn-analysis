from __future__ import annotations

import sys
from pathlib import Path

import win32com.client


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: export_docx_pdf_word.py <input.docx> <output.pdf>")

    input_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(input_path), ReadOnly=True)
        try:
            doc.ExportAsFixedFormat(str(output_path), 17)
        finally:
            doc.Close(False)
    finally:
        word.Quit()
    print(output_path)


if __name__ == "__main__":
    main()
