from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXAM = ROOT / "exams" / "ceec-115-physics-g10-g11"
DATA = EXAM / "data.js"
OFFICIAL = ROOT / "source" / "ceec-115-physics" / "ceec-115-physics-official-answers.pdf"
EXPECTED = [1,2,3,4,5,10,12,13,14,18,19,20,23]
OFFICIAL_SELECTED = {1:"B",2:"C",3:"A",4:"E",5:"B",10:"D",12:"BE",13:"ACD",14:"AD",19:"C"}


def load_quiz() -> dict:
    text=DATA.read_text(encoding="utf-8").strip();prefix="window.QUIZ = "
    if not text.startswith(prefix) or not text.endswith(";"):raise AssertionError("data wrapper")
    return json.loads(text[len(prefix):-1])


def score_question(q, ans):
    if q["type"]=="single":return q["points"] if ans==q["answer"] else 0
    if q["type"]=="multi":
        chosen=set(str(ans or "")); correct=set(q["answer"])
        if not chosen:return 0
        k=sum((x in chosen)!=(x in correct) for x in "ABCDE")
        return round(max(0,q["points"]*(5-2*k)/5),2)
    total=0
    for p in q.get("parts",[]):
        val=(ans or {}).get(p["id"],"")
        if p["kind"]=="number":
            try: ok=str(val).strip()!="" and abs(float(val)-float(p["answer"]))<=float(p.get("tolerance",0))
            except: ok=False
        else:ok=str(val)==str(p["answer"])
        if ok: total+=p["points"]
    return round(total,2)


def correct_answer(q):
    if q["type"] in {"single","multi"}:return q["answer"]
    return {p["id"]:p["answer"] for p in q["parts"]}


def wrong_answer(q):
    if q["type"]=="single":return next(x for x in "ABCDE" if x!=q["answer"])
    if q["type"]=="multi":return "".join(x for x in "ABCDE" if x not in q["answer"])
    return {p["id"]:"-999999" for p in q["parts"]}


def local_checks() -> dict:
    quiz=load_quiz();qs=quiz["questions"]
    assert quiz["questionCount"]==13==len(qs)
    assert [q["no"] for q in qs]==EXPECTED
    assert len({q["no"] for q in qs})==13
    assert quiz["totalScore"]==sum(q["points"] for q in qs)==50
    assert sum(q["grade"]=="高一" for q in qs)==4
    assert sum(q["grade"]=="高二" for q in qs)==9
    assert {t:sum(q["type"]==t for q in qs) for t in ("single","multi","composite")}=={"single":7,"multi":3,"composite":3}
    for q in qs:
        assert q["unit"] and q["course"] and q["keyPoint"] and len(q["explanationHtml"])>120
        assert "待補" not in q["explanationHtml"] and "```" not in q["explanationHtml"]
        for rel in q["images"]+[q["sourcePage"]]:
            p=EXAM/rel;assert p.exists(),p
            with Image.open(p) as im: assert im.width>=500 and im.height>=50,(p,im.size)
    by_no={q["no"]:q for q in qs}
    for no,answer in OFFICIAL_SELECTED.items():assert by_no[no]["answer"]==answer,(no,by_no[no]["answer"],answer)
    official_text="\n".join(p.get_text() for p in fitz.open(OFFICIAL))
    assert re.search(r"\b1\s+B\b",official_text) and re.search(r"\b21\s+C\b",official_text) and re.search(r"\b13\s+ACD\b",official_text)
    total_correct=sum(score_question(q,correct_answer(q)) for q in qs)
    total_wrong=sum(score_question(q,wrong_answer(q)) for q in qs)
    assert total_correct==50,total_correct
    assert total_wrong==0,total_wrong
    assert score_question(by_no[12],"BE")==5
    assert score_question(by_no[12],"B")==3
    assert score_question(by_no[12],"AB")==1
    assert score_question(by_no[18],{"a":"917"})==4
    assert score_question(by_no[20],{"eqM":"Mg-f=Ma甲","eqm":"mg-f=ma乙","g":"1007"})==6
    assert score_question(by_no[23],{"meanR":"300","uA":"5.8"})==4
    docs={}
    for name,expected_pages in (("ceec_115_physics_g10_g11_exam.pdf",6),("ceec_115_physics_g10_g11_answers.pdf",4)):
        p=EXAM/"downloads"/name;assert p.exists() and p.stat().st_size>100000,p
        doc=fitz.open(p);assert doc.page_count==expected_pages,(p,doc.page_count)
        assert all(len(pg.get_text().strip())>20 for pg in doc)
        docs[name]={"pages":doc.page_count,"bytes":p.stat().st_size}
    return {"questions":13,"points":50,"grade1":4,"grade2":9,"types":{"single":7,"multi":3,"composite":3},"official_answers_checked":len(OFFICIAL_SELECTED),"all_correct":total_correct,"all_wrong":total_wrong,"documents":docs}


def http_checks(base: str) -> dict:
    paths=["","teacher.html","shared/style.css","shared/teacher.js","exams/ceec-115-physics-g10-g11/","exams/ceec-115-physics-g10-g11/teacher.html","exams/ceec-115-physics-g10-g11/data.js","exams/ceec-115-physics-g10-g11/app.js","exams/ceec-115-physics-g10-g11/exam.css","exams/ceec-115-physics-g10-g11/assets/questions/q01.jpg","exams/ceec-115-physics-g10-g11/assets/questions/q23.jpg","exams/ceec-115-physics-g10-g11/downloads/ceec_115_physics_g10_g11_exam.pdf","exams/ceec-115-physics-g10-g11/downloads/ceec_115_physics_g10_g11_answers.pdf"]
    checked=[]
    for path in paths:
        url=base.rstrip("/")+"/"+path
        with urllib.request.urlopen(url,timeout=25) as r:
            body=r.read();assert r.status==200 and body,(url,r.status,len(body));checked.append({"path":path or "/","status":r.status,"bytes":len(body)})
    return {"base":base,"resources":checked}


def main():
    result={"local":local_checks()}
    if len(sys.argv)>1:result["http"]=http_checks(sys.argv[1])
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
