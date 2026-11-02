from __future__ import annotations

import sys
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    pdf_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    page_paths = []
    for i in range(len(pdf)):
        page = pdf[i]
        bitmap = page.render(scale=1.3)
        img = bitmap.to_pil().convert("RGB")
        out = out_dir / f"page-{i+1:02d}.png"
        img.save(out)
        page_paths.append(out)

    thumbs = []
    for out in page_paths:
        im = Image.open(out).convert("RGB")
        im.thumbnail((220, 310))
        canvas = Image.new("RGB", (240, 350), "white")
        canvas.paste(im, ((240 - im.width) // 2, 10))
        thumbs.append(canvas)
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 240, rows * 350), "#f3f4f6")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    for i, thumb in enumerate(thumbs):
        x = (i % cols) * 240
        y = (i // cols) * 350
        sheet.paste(thumb, (x, y))
        draw.text((x + 12, y + 320), f"Page {i+1}", fill="#111827", font=font)
    sheet.save(out_dir / "contact_sheet.png")
    print(out_dir / "contact_sheet.png")


if __name__ == "__main__":
    main()
