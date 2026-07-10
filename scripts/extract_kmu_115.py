from __future__ import annotations

import json
import re
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
EXAM_PDF = SOURCE / "115高醫試題.pdf"
ANSWER_PDF = SOURCE / "115高醫解答.pdf"
EXAM_DIR = ROOT / "exams" / "kmu-115-physchem"
ASSET_DIR = EXAM_DIR / "assets"
QUESTION_DIR = ASSET_DIR / "questions"
SOURCE_PAGE_DIR = ASSET_DIR / "source-pages"
RAW_PATH = ROOT / "work" / "questions_raw.json"
CONTACT_SHEET = ROOT / "work" / "kmu_115_contact_sheet.jpg"


def parse_answers() -> dict[int, str]:
    doc = fitz.open(ANSWER_PDF)
    text = "\n".join(page.get_text("text") for page in doc)
    marker = "後醫-物理及化學"
    end_marker = "後醫-普通生物及生化概論"
    if marker not in text or end_marker not in text:
        raise RuntimeError("找不到高醫物理及化學答案區段")
    section = text.split(marker, 1)[1].split(end_marker, 1)[0]
    answers: dict[int, str] = {}
    for chunk in section.split("題號")[1:]:
        if "答案" not in chunk:
            continue
        nums_text, ans_text = chunk.split("答案", 1)
        nums = [int(x) for x in re.findall(r"(?m)^\s*(\d{1,2})\s*$", nums_text)]
        letters = re.findall(r"(?m)^\s*([A-E])\s*$", ans_text)
        if len(nums) != len(letters):
            raise RuntimeError(f"答案解析數量不符：{nums[:3]}... nums={len(nums)} letters={len(letters)}")
        answers.update(zip(nums, letters))
    expected = set(range(1, 91))
    if set(answers) != expected:
        raise RuntimeError(f"答案題號不完整：missing={sorted(expected-set(answers))}, extra={sorted(set(answers)-expected)}")
    return answers


def question_starts(page: fitz.Page) -> list[tuple[int, float]]:
    hits: list[tuple[int, float]] = []
    for word in page.get_text("words"):
        match = re.fullmatch(r"(\d{1,2})\.", str(word[4]))
        if match:
            hits.append((int(match.group(1)), float(word[1])))
    hits.sort(key=lambda pair: pair[1])
    return hits


def render_clip(page: fitz.Page, clip: fitz.Rect, scale: float = 3.0) -> Image.Image:
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def extract_text(page: fitz.Page, clip: fitz.Rect) -> str:
    text = page.get_text("text", clip=clip)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    filtered: list[str] = []
    for line in lines:
        if line.startswith("115 學年度學士後醫學系招生考試"):
            continue
        if line.startswith("本試題（含封面）"):
            continue
        if line == "物理及化學試題":
            continue
        filtered.append(line)
    return "\n".join(filtered)


def save_jpeg(image: Image.Image, path: Path, quality: int = 94) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = ImageOps.autocontrast(image)
    image.save(path, "JPEG", quality=quality, optimize=True, progressive=True)


def make_contact_sheet(records: list[dict]) -> None:
    thumb_w = 500
    label_h = 38
    gap = 18
    thumbs: list[tuple[Image.Image, str]] = []
    for rec in records:
        image = Image.open(EXAM_DIR / rec["image"]).convert("RGB")
        ratio = thumb_w / image.width
        height = max(80, int(image.height * ratio))
        thumb = image.resize((thumb_w, height), Image.Resampling.LANCZOS)
        thumbs.append((thumb, f"Q{rec['number']:02d} · p.{rec['page']} · {rec['subject']} · 答案 {rec['answer']}"))
    sheet_w = thumb_w * 3 + gap * 4
    row_heights = []
    for row in range((len(thumbs) + 2) // 3):
        row_items = thumbs[row * 3 : row * 3 + 3]
        row_heights.append(max(img.height for img, _ in row_items) + label_h + gap)
    sheet_h = gap + sum(row_heights)
    sheet = Image.new("RGB", (sheet_w, sheet_h), "#eef3f8")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    y = gap
    for row, row_h in enumerate(row_heights):
        for col, (img, label) in enumerate(thumbs[row * 3 : row * 3 + 3]):
            x = gap + col * (thumb_w + gap)
            sheet.paste(img, (x, y + label_h))
            draw.text((x, y + 5), label, fill="#162033", font=font)
        y += row_h
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET, "JPEG", quality=88, optimize=True)


def main() -> None:
    QUESTION_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_PAGE_DIR.mkdir(parents=True, exist_ok=True)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    answers = parse_answers()
    doc = fitz.open(EXAM_PDF)
    records: list[dict] = []

    for page_index in range(1, doc.page_count):
        page = doc[page_index]
        starts = question_starts(page)
        if not starts:
            continue

        full_clip = fitz.Rect(24, 72, page.rect.width - 14, page.rect.height - 28)
        full_page = render_clip(page, full_clip, 2.1)
        save_jpeg(full_page, SOURCE_PAGE_DIR / f"page-{page_index+1:02d}.jpg", 92)

        for idx, (number, start_y) in enumerate(starts):
            end_y = starts[idx + 1][1] - 5 if idx + 1 < len(starts) else page.rect.height - 34
            clip = fitz.Rect(24, max(76, start_y - 6), page.rect.width - 14, min(page.rect.height - 30, end_y))
            image = render_clip(page, clip, 3.2)
            image_path = QUESTION_DIR / f"q{number:02d}.jpg"
            save_jpeg(image, image_path, 95)
            subject = "物理" if number <= 15 or 31 <= number <= 60 else "化學"
            points = 1 if number <= 30 else 2
            records.append(
                {
                    "id": f"q{number:02d}",
                    "number": number,
                    "page": page_index + 1,
                    "subject": subject,
                    "points": points,
                    "answer": answers[number],
                    "image": f"assets/questions/q{number:02d}.jpg",
                    "sourcePage": f"assets/source-pages/page-{page_index+1:02d}.jpg",
                    "text": extract_text(page, clip),
                }
            )

    records.sort(key=lambda item: item["number"])
    if [item["number"] for item in records] != list(range(1, 91)):
        raise RuntimeError("逐題裁切題號不完整")
    RAW_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    make_contact_sheet(records)
    print(json.dumps({
        "questions": len(records),
        "physics": sum(1 for r in records if r["subject"] == "物理"),
        "chemistry": sum(1 for r in records if r["subject"] == "化學"),
        "question_assets": len(list(QUESTION_DIR.glob("q*.jpg"))),
        "source_pages": len(list(SOURCE_PAGE_DIR.glob("page-*.jpg"))),
        "raw_json": str(RAW_PATH),
        "contact_sheet": str(CONTACT_SHEET),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
