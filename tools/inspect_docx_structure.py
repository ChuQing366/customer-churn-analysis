from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
}


def q(name: str) -> str:
    prefix, local = name.split(":")
    return f"{{{NS[prefix]}}}{local}"


def paragraph_text(p: ET.Element) -> str:
    parts = []
    for node in p.iter():
        if node.tag == q("w:t"):
            parts.append(node.text or "")
        elif node.tag == q("w:tab"):
            parts.append("\t")
        elif node.tag == q("w:br"):
            parts.append("\n")
    return "".join(parts)


def para_style(p: ET.Element) -> str:
    ppr = p.find("w:pPr", NS)
    if ppr is None:
        return ""
    style = ppr.find("w:pStyle", NS)
    return style.attrib.get(q("w:val"), "") if style is not None else ""


def has_drawing(p: ET.Element) -> bool:
    return p.find(".//w:drawing", NS) is not None or p.find(".//w:pict", NS) is not None


def outline(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    body = root.find("w:body", NS)
    items = []
    for i, child in enumerate(list(body)):
        if child.tag != q("w:p"):
            if child.tag == q("w:tbl"):
                items.append({"idx": i, "type": "tbl", "style": "", "text": "[TABLE]"})
            continue
        text = paragraph_text(child).strip()
        style = para_style(child)
        drawing = has_drawing(child)
        if text or drawing or style:
            items.append(
                {
                    "idx": i,
                    "type": "p",
                    "style": style,
                    "drawing": drawing,
                    "text": text[:260],
                }
            )
    return items


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: inspect_docx_structure.py <docx> [out.json]")
    path = Path(sys.argv[1])
    data = outline(path)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        for item in data:
            print(f"{item['idx']:04d} {item['style']:<18} img={item.get('drawing', False)!s:<5} {item['text']}")


if __name__ == "__main__":
    main()
