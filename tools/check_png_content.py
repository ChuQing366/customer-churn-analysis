from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    for path in sorted(Path("outputs").rglob("*.png")):
        image = Image.open(path).convert("RGB").resize((160, 120))
        pixels = np.asarray(image)
        nonwhite = float(np.mean(np.any(pixels < 245, axis=2)))
        std = float(pixels.std())
        print(f"{path}\tnonwhite={nonwhite:.3f}\tstd={std:.1f}\tsize={path.stat().st_size}")


if __name__ == "__main__":
    main()
