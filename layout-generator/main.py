#!/usr/bin/env python3
"""Render the visible body of a local HTML page as a PNG, without a browser."""

import argparse
from pathlib import Path
import struct
import sys

import pymupdf
from weasyprint import CSS, HTML


def find_body_box(box):
    """Find the rendered body box in WeasyPrint's laid-out box tree."""
    element = getattr(box, "element", None)
    if element is not None and element.tag.lower() == "body":
        return box
    for child in getattr(box, "children", ()):
        found = find_body_box(child)
        if found is not None:
            return found
    return None


def body_bounds(box):
    """Return the body's border-box bounds in CSS pixels."""
    return (
        box.border_box_x(),
        box.border_box_y(),
        box.border_width(),
        box.border_height(),
    )


def save_bmp(pixmap, output: Path):
    """Write an RGB PyMuPDF pixmap as a 24-bit, bottom-up BMP file."""
    width, height = pixmap.width, pixmap.height
    row_size = (width * 3 + 3) & ~3
    image_size = row_size * height
    with output.open("wb") as bmp:
        bmp.write(struct.pack("<2sIHHI", b"BM", 54 + image_size, 0, 0, 54))
        bmp.write(struct.pack(
            "<IiiHHIIiiII", 40, width, height, 1, 24, 0, image_size,
            2835, 2835, 0, 0,
        ))
        samples = pixmap.samples
        source_stride = pixmap.stride
        padding = b"\0" * (row_size - width * 3)
        for y in range(height - 1, -1, -1):
            start = y * source_stride
            row = samples[start:start + width * 3]
            bgr = bytearray(width * 3)
            bgr[0::3] = row[2::3]
            bgr[1::3] = row[1::3]
            bgr[2::3] = row[0::3]
            bmp.write(bgr)
            bmp.write(padding)


def render(html_path: Path, output: Path, viewport_width: int, viewport_height: int):
    page_css = CSS(string=(
        f"@page {{ size: {viewport_width}px {viewport_height}px; margin: 0 }}"
    ))
    document = HTML(filename=str(html_path)).render(stylesheets=[page_css])
    body = next(
        (found for page in document.pages
         if (found := find_body_box(page._page_box)) is not None),
        None,
    )
    if body is None:
        raise ValueError("aucune balise <body> n'a été trouvée dans la page")

    x, y, width, height = body_bounds(body)
    if width <= 0 or height <= 0:
        raise ValueError("la balise <body> n'a pas de dimensions visibles")

    pdf_bytes = document.write_pdf()
    pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    page = pdf[0]
    # WeasyPrint uses CSS pixels; PDF uses points (72 points per 96 CSS pixels).
    scale = 72 / 96
    crop = pymupdf.Rect(x * scale, y * scale, (x + width) * scale, (y + height) * scale)
    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(96 / 72, 96 / 72), clip=crop,
        colorspace=pymupdf.csRGB, alpha=False,
    )
    save_bmp(pixmap, output)


def main() -> int:
    default_output = Path(__file__).resolve().parent.parent / "screen-controlleur" / "pic"
    parser = argparse.ArgumentParser(
    description="Convertit la balise <body> d'un fichier HTML local en BMP."
    )
    parser.add_argument("html", type=Path, help="fichier HTML à convertir")
    parser.add_argument(
        "-o", "--out", type=Path, default=default_output,
        help=f"dossier de sortie (défaut : {default_output})",
    )
    parser.add_argument("--width", type=int, default=1920, help="largeur du viewport CSS")
    parser.add_argument("--height", type=int, default=1080, help="hauteur du viewport CSS")
    args = parser.parse_args()

    if args.width <= 0 or args.height <= 0:
        parser.error("la largeur et la hauteur doivent être supérieures à zéro")

    html_path = args.html.expanduser().resolve()
    if not html_path.is_file():
        parser.error(f"le fichier HTML n'existe pas : {html_path}")

    output_dir = args.out.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{html_path.stem}.bmp"

    try:
        render(html_path, output, args.width, args.height)
    except Exception as exc:
        print(f"Erreur pendant le rendu HTML : {exc}", file=sys.stderr)
        return 1

    print(f"Image enregistrée : {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
