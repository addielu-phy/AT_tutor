from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "work" / "questions_raw.json"
PARTS = [
    ROOT / "work" / "explanations_1_30.json",
    ROOT / "work" / "explanations_31_60.json",
    ROOT / "work" / "explanations_61_90.json",
]
OUT = ROOT / "exams" / "kmu-115-physchem" / "data.js"
EXAM_DIR = OUT.parent

PHYSICS_UNITS = {
    "力學": {2, 3, 4, 31, 32, 33},
    "流體力學": {1, 6, 34, 35},
    "波動與聲學": {7, 8, 37, 38, 39},
    "熱學與熱力學": {36, 40, 41, 42, 43, 44},
    "電磁學": {5, 9, 10, 12, 45, 46, 47, 48, 49, 50, 51, 52, 53, 56},
    "光學": {11, 13, 54, 55, 57},
    "近代與核物理": {14, 15, 58, 59, 60},
}

CHEMISTRY_UNITS = {
    "原子結構與週期律": {18, 20, 21, 27, 29},
    "化學鍵結與分子結構": {19, 30, 77, 80},
    "固態與材料化學": {22, 61, 67},
    "溶液、酸鹼與平衡": {16, 26, 28, 65, 69, 70, 71, 84},
    "氧化還原與電化學": {23, 24, 90},
    "化學熱力學": {25, 89},
    "有機結構與立體化學": {17, 62, 66, 72, 74, 82, 83, 85},
    "有機反應與機構": {63, 64, 68, 73, 75, 76, 79, 81, 86},
    "無機與配位化學": {78, 87, 88},
}


def teaching_unit(number: int, subject: str) -> str:
    groups = PHYSICS_UNITS if subject == "物理" else CHEMISTRY_UNITS
    for name, numbers in groups.items():
        if number in numbers:
            return name
    raise RuntimeError(f"第 {number} 題找不到教學大單元")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    raw = read_json(RAW_PATH)
    explanations = []
    for path in PARTS:
        if not path.exists():
            raise FileNotFoundError(path)
        data = read_json(path)
        if not isinstance(data, list):
            raise TypeError(f"{path.name} 不是 JSON array")
        explanations.extend(data)

    raw_by_no = {int(item["number"]): item for item in raw}
    exp_by_no = {int(item["number"]): item for item in explanations}
    expected = set(range(1, 91))
    if set(raw_by_no) != expected:
        raise RuntimeError(f"原題缺號：{sorted(expected-set(raw_by_no))}")
    if len(explanations) != len(exp_by_no):
        raise RuntimeError("詳解有重複題號")
    if set(exp_by_no) != expected:
        raise RuntimeError(f"詳解缺號：{sorted(expected-set(exp_by_no))}")

    questions = []
    flagged = []
    for no in range(1, 91):
        src = raw_by_no[no]
        exp = exp_by_no[no]
        if str(exp.get("answer", "")).upper() != src["answer"]:
            raise RuntimeError(f"第 {no} 題詳解答案 {exp.get('answer')} 與官方 {src['answer']} 不一致")
        image_path = EXAM_DIR / src["image"]
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        verification = exp.get("verification", "verified")
        if verification != "verified":
            flagged.append(no)
        explanation_html = exp.get("explanationHtml") or ""
        unit = exp.get("unit") or ""
        key_point = exp.get("keyPoint") or ""
        if len(explanation_html) < 100:
            raise RuntimeError(f"第 {no} 題詳解過短：{len(explanation_html)} chars")
        if "```" in explanation_html or "正式詳解產生中" in explanation_html or "待補" in explanation_html:
            raise RuntimeError(f"第 {no} 題詳解含占位或 Markdown code fence")
        if not unit or not key_point:
            raise RuntimeError(f"第 {no} 題缺 unit/keyPoint")
        questions.append(
            {
                "no": no,
                "subject": src["subject"],
                "unit": teaching_unit(no, src["subject"]),
                "subunit": unit,
                "conceptTags": exp.get("conceptTags") or [],
                "answer": src["answer"],
                "answerText": exp.get("answerText") or f"選項 {src['answer']}",
                "keyPoint": key_point,
                "explanationHtml": explanation_html,
                "difficulty": exp.get("difficulty") or "中等",
                "verification": verification,
                "note": exp.get("note") or "",
                "points": src["points"],
                "penalty": 0.25 if src["points"] == 1 else 0.5,
                "images": [src["image"]],
                "sourcePage": src["sourcePage"],
            }
        )

    quiz = {
        "id": "at-tutor-kmu-115-physchem",
        "siteTitle": "AT_tutor｜後醫考古題自學平台",
        "title": "高醫 115 學年度學士後醫學系｜物理及化學",
        "subject": "物理及化學",
        "description": "原題截圖、五選一自動批改、物理／化學分科、正式模擬、繁中逐題詳解、錯題重練與教師端統計。",
        "sourceLabel": "使用者提供之 Google Drive：115高醫試題.pdf、115高醫解答.pdf",
        "sourceUrl": "https://drive.google.com/drive/folders/1EG8uFQPnpE54WF2F9YGyZuThZXZ-NfF5?usp=drive_link",
        "school": "高雄醫學大學",
        "examYear": "115學年度",
        "questionCount": 90,
        "totalScore": 150,
        "timeMinutes": 100,
        "updatedAt": date.today().isoformat(),
        "questions": questions,
    }
    body = json.dumps(quiz, ensure_ascii=False, indent=2).replace("</script", "<\\/script")
    OUT.write_text("window.QUIZ = " + body + ";\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT),
        "questions": len(questions),
        "physics": sum(q["subject"] == "物理" for q in questions),
        "chemistry": sum(q["subject"] == "化學" for q in questions),
        "flagged": flagged,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
