from __future__ import annotations

import sys
from pathlib import Path

from docx import Document


def main() -> None:
    path = Path(sys.argv[1])
    doc = Document(path)
    for index, table in enumerate(doc.tables):
        print(f"--- TABLE {index} ---")
        print(table.cell(0, 0).text[:3000])


if __name__ == "__main__":
    main()
