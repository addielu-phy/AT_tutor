from __future__ import annotations

import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "ceec-115-physics" / "ceec-115-physics-paper.pdf"
EXAM = ROOT / "exams" / "ceec-115-physics-g10-g11"
QUESTIONS = EXAM / "assets" / "questions"
SOURCE_PAGES = EXAM / "assets" / "source-pages"
WORK = ROOT / "work" / "ceec-115-physics"
SCALE = 3.0

# PDF page numbers are zero-based. Coordinates are PDF points.
CROPS = {
    "q01": (1, (45, 142, 550, 209)),
    "g02-03-stem": (1, (45, 207, 550, 246)),
    "g02-03-table": (1, (338, 274, 535, 350)),
    "q02": (1, (45, 240, 330, 362)),
    "q03": (1, (45, 355, 550, 482)),
    "q04": (1, (45, 481, 550, 575)),
    "q05": (1, (45, 569, 550, 657)),
    "q10": (2, (45, 679, 550, 790)),
    "q12": (3, (45, 267, 550, 427)),
    "q13": (3, (45, 420, 550, 647)),
    "q14": (3, (45, 646, 550, 790)),
    "g18-20-stem": (5, (45, 188, 550, 455)),
    "q18": (5, (45, 454, 550, 475)),
    "q19": (5, (45, 477, 550, 511)),
    "q20": (5, (45, 514, 550, 618)),
    "g21-23-stem": (5, (45, 620, 550, 706)),
    "q21": (6, (45, 82, 550, 453)),
    "q22": (6, (45, 446, 550, 674)),
    "q23": (6, (45, 669, 550, 780)),
    "g24-26-stem": (7, (45, 82, 550, 320)),
    "q24": (7, (45, 313, 550, 460)),
    "q25": (7, (45, 452, 550, 515)),
    "q26": (7, (45, 505, 550, 805)),
}

SELECTED_ASSET_ORDER = [
    "q01", "g02-03-stem", "g02-03-table", "q02", "q03", "q04", "q05", "q10",
    "q12", "q13", "q14", "g18-20-stem", "q18", "q19", "q20",
    "q23",
]
PUBLISHED_SOURCE_PAGE_INDEXES = [1, 2, 3, 5, 6]


def render_clip(page: fitz.Page, clip: tuple[float, float, float, float], output: Path) -> None:
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=fitz.Rect(*clip), alpha=False)
    tmp = output.with_suffix(".png")
    pix.save(tmp)
    with Image.open(tmp) as im:
        rgb = im.convert("RGB")
        rgb.save(output, quality=95, optimize=True, progressive=True)
    tmp.unlink()


def build_contact_sheet(paths: list[Path], output: Path) -> None:
    cards: list[tuple[str, Image.Image]] = []
    thumb_w = 700
    for path in paths:
        with Image.open(path) as im:
            rgb = im.convert("RGB")
            h = round(rgb.height * thumb_w / rgb.width)
            cards.append((path.stem, rgb.resize((thumb_w, h))))
    gap, label_h, cols = 24, 42, 2
    rows = (len(cards) + cols - 1) // cols
    row_heights = []
    for row in range(rows):
        row_cards = cards[row * cols : (row + 1) * cols]
        row_heights.append(max(im.height for _, im in row_cards) + label_h)
    sheet_w = gap + cols * (thumb_w + gap)
    sheet_h = gap + sum(h + gap for h in row_heights)
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    y = gap
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx >= len(cards):
                break
            name, im = cards[idx]
            x = gap + col * (thumb_w + gap)
            draw.text((x, y), name, fill="black")
            sheet.paste(im, (x, y + label_h))
        y += row_heights[row] + gap
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    QUESTIONS.mkdir(parents=True, exist_ok=True)
    SOURCE_PAGES.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    for old in QUESTIONS.glob("*.jpg"):
        old.unlink()
    for old in SOURCE_PAGES.glob("*.jpg"):
        old.unlink()
    doc = fitz.open(SOURCE)
    generated: list[Path] = []
    for name in SELECTED_ASSET_ORDER:
        page_index, rect = CROPS[name]
        output = QUESTIONS / f"{name}.jpg"
        render_clip(doc[page_index], rect, output)
        generated.append(output)
    for page_index in PUBLISHED_SOURCE_PAGE_INDEXES:
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.4, 2.4), alpha=False)
        tmp = SOURCE_PAGES / f"page-{page_index:02d}.png"
        out = SOURCE_PAGES / f"page-{page_index:02d}.jpg"
        pix.save(tmp)
        with Image.open(tmp) as im:
            im.convert("RGB").save(out, quality=92, optimize=True, progressive=True)
        tmp.unlink()
    selected = [QUESTIONS / f"{name}.jpg" for name in SELECTED_ASSET_ORDER]
    build_contact_sheet(selected, WORK / "selected-crops-contact-sheet.jpg")
    manifest = {
        "source": str(SOURCE),
        "scale": SCALE,
        "crops": {name: {"pdfPage": CROPS[name][0] + 1, "rect": list(CROPS[name][1]), "file": f"assets/questions/{name}.jpg"} for name in SELECTED_ASSET_ORDER},
        "generated": len(generated),
        "sourcePages": len(PUBLISHED_SOURCE_PAGE_INDEXES),
    }
    (WORK / "crop-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"question_assets": len(generated), "source_pages": len(PUBLISHED_SOURCE_PAGE_INDEXES), "contact_sheet": str(WORK / "selected-crops-contact-sheet.jpg")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
