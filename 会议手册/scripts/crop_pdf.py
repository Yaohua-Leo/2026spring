from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def crop_bottom(src: Path, dst: Path, trim_points: float) -> None:
    reader = PdfReader(str(src))
    writer = PdfWriter()

    for page in reader.pages:
        page.mediabox.lower_left = (page.mediabox.left, page.mediabox.bottom + trim_points)
        page.cropbox.lower_left = (page.cropbox.left, page.cropbox.bottom + trim_points)
        writer.add_page(page)

    with dst.open("wb") as fh:
        writer.write(fh)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop a fixed amount from the bottom of each PDF page.")
    parser.add_argument("src", type=Path)
    parser.add_argument("dst", type=Path)
    parser.add_argument("--trim-points", type=float, default=92.0)
    args = parser.parse_args()

    crop_bottom(args.src, args.dst, args.trim_points)
    print(f"Wrote {args.dst}")


if __name__ == "__main__":
    main()
