from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXAM = ROOT / "exams" / "kmu-115-physchem"
DATA = EXAM / "data.js"


def load_quiz() -> dict:
    text = DATA.read_text(encoding="utf-8").strip()
    prefix = "window.QUIZ = "
    if not text.startswith(prefix) or not text.endswith(";"):
        raise RuntimeError("data.js 包裝格式錯誤")
    return json.loads(text[len(prefix) : -1])


def official_score(questions: list[dict], answers: dict[int, str]) -> float:
    small = advanced = 0.0
    for q in questions:
        chosen = answers.get(q["no"])
        if not chosen:
            continue
        delta = q["points"] if chosen == q["answer"] else -q["penalty"]
        if q["points"] == 1:
            small += delta
        else:
            advanced += delta
    return round(max(0, small) + max(0, advanced), 2)


def local_checks() -> dict:
    quiz = load_quiz()
    qs = quiz["questions"]
    assert len(qs) == 90
    assert [q["no"] for q in qs] == list(range(1, 91))
    assert len({q["no"] for q in qs}) == 90
    assert sum(q["subject"] == "物理" for q in qs) == 45
    assert sum(q["subject"] == "化學" for q in qs) == 45
    assert sum(q["points"] for q in qs) == 150
    assert all(q["answer"] in "ABCDE" for q in qs)
    assert all(q["unit"] and q["explanationHtml"] and q["keyPoint"] for q in qs)
    assert all(len(q["explanationHtml"]) >= 100 for q in qs)
    assert all(q["verification"] in {"verified", "official-answer-questionable"} for q in qs)
    assert all("正式詳解產生中" not in q["explanationHtml"] and "```" not in q["explanationHtml"] for q in qs)
    dims = []
    for q in qs:
        for rel in q["images"]:
            path = EXAM / rel
            assert path.exists(), path
            with Image.open(path) as image:
                dims.append(image.size)
                assert image.width >= 1400 and image.height >= 120
    all_correct = {q["no"]: q["answer"] for q in qs}
    all_wrong = {q["no"]: next(letter for letter in "ABCDE" if letter != q["answer"]) for q in qs}
    assert official_score(qs, all_correct) == 150
    assert official_score(qs, all_wrong) == 0
    return {
        "questions": len(qs),
        "physics": 45,
        "chemistry": 45,
        "points": 150,
        "images": len(dims),
        "all_correct_official_score": 150,
        "all_wrong_official_score": 0,
    }


def http_checks(base: str) -> dict:
    paths = [
        "",
        "teacher.html",
        "shared/style.css",
        "shared/quiz-app.js",
        "shared/teacher.js",
        "exams/kmu-115-physchem/",
        "exams/kmu-115-physchem/teacher.html",
        "exams/kmu-115-physchem/data.js",
        "exams/kmu-115-physchem/assets/questions/q01.jpg",
        "exams/kmu-115-physchem/assets/questions/q90.jpg",
    ]
    checked = []
    for path in paths:
        url = base.rstrip("/") + "/" + path
        with urllib.request.urlopen(url, timeout=20) as response:
            body = response.read()
            if response.status != 200 or not body:
                raise RuntimeError(f"HTTP check failed: {url}")
            checked.append({"path": path or "/", "status": response.status, "bytes": len(body)})
    return {"base": base, "resources": checked}


def main() -> None:
    result = {"local": local_checks()}
    if len(sys.argv) > 1:
        result["http"] = http_checks(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
