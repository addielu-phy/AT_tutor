from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAM = ROOT / "exams" / "ceec-115-physics-g10-g11"

PAPER_URL = "https://www.ceec.edu.tw/files/file_pool/1/0Q194365922929011621/05-115%E5%88%86%E7%A7%91%E6%B8%AC%E9%A9%97%E7%89%A9%E7%90%86%E8%80%83%E7%A7%91%E8%A9%A6%E5%8D%B7.pdf"
ANSWER_URL = "https://www.ceec.edu.tw/files/file_pool/1/0Q196580790644572958/05-115%E5%88%86%E7%A7%91%E6%B8%AC%E9%A9%97%E7%89%A9%E7%90%86%E9%81%B8%E6%93%87%E9%A1%8C%E5%8F%83%E8%80%83%E7%AD%94%E6%A1%88.pdf"
ANNOUNCEMENT_URL = "https://www.ceec.edu.tw/"


def q(no, grade, course, unit, subunit, qtype, answer, points, images, source_page, key_point, explanation, **extra):
    item = {
        "no": no,
        "originalNo": no,
        "grade": grade,
        "course": course,
        "subject": "物理",
        "unit": unit,
        "subunit": subunit,
        "type": qtype,
        "answer": answer,
        "points": points,
        "images": [f"assets/questions/{name}.jpg" for name in images],
        "sourcePage": f"assets/source-pages/{source_page}",
        "keyPoint": key_point,
        "explanationHtml": explanation,
        "difficulty": extra.pop("difficulty", "中等"),
        "verification": extra.pop("verification", "verified"),
        "officialAnswerPublished": extra.pop("officialAnswerPublished", qtype in {"single", "multi"}),
    }
    item.update(extra)
    return item


QUESTIONS = [
    q(1, "高二", "選修物理I", "力與運動", "等加速度直線運動", "single", "B", 3, ["q01"], "page-01.jpg",
      "用不含時間的運動公式 v²=v₀²+2aΔx。",
      "<p>取前進方向為正，初速為30 m/s，經50 m後降到25 m/s。</p><ol><li>25²=30²+2a(50)。</li><li>a=(625−900)/100=−2.75 m/s²。</li><li>題目問減速度量值，約為2.8 m/s²。</li></ol><p>所以選B。</p>", answerText="2.8 m/s²", difficulty="基礎"),
    q(2, "高二", "選修物理I／II", "萬有引力與振動", "行星表面重力與單擺", "single", "C", 3,
      ["g02-03-stem", "g02-03-table", "q02"], "page-01.jpg",
      "均勻球體表面重力 g∝ρR，而單擺週期 T∝1/√g。",
      "<p>均勻行星的質量M=(4/3)πR³ρ，所以表面重力g=GM/R²=(4/3)πGρR。</p><ol><li>g<sub>地</sub>/g<sub>火</sub>=(5.5×6400)/(3.9×3400)。</li><li>同一單擺T=2π√(L/g)，故T<sub>火</sub>/T<sub>地</sub>=√(g<sub>地</sub>/g<sub>火</sub>)。</li></ol><p>因此T<sub>火</sub>=√[(6400×5.5)/(3400×3.9)]T，選C。</p>", answerText="√[(6400×5.5)/(3400×3.9)]T"),
    q(3, "高二", "選修物理I", "萬有引力", "脫離速率", "single", "A", 3,
      ["g02-03-stem", "g02-03-table", "q03"], "page-01.jpg",
      "脫離速率vₑ=√(2GM/R)，對均勻球體可化為vₑ∝R√ρ。",
      "<p>將M=(4/3)πR³ρ代入vₑ=√(2GM/R)，可得vₑ=R√[(8/3)πGρ]。</p><ol><li>因此v<sub>火</sub>/v<sub>地</sub>=(3400/6400)√(3.9/5.5)。</li><li>合併到根號內即√[(3.9×3400²)/(5.5×6400²)]。</li></ol><p>所以選A。</p>", answerText="√[(3.9×3400²)/(5.5×6400²)]v"),
    q(4, "高一", "必修物理", "能量與宇宙", "質能互換", "single", "E", 3, ["q04"], "page-01.jpg",
      "恆星總輻射功率為球面積乘單位面積功率，再用E=mc²。",
      "<p>距恆星R處每單位面積接收功率P，故恆星向各方向發出的總功率為L=4πR²P。</p><ol><li>單位時間放出的能量為L。</li><li>由E=mc²，單位時間損失質量為L/c²。</li><li>所以dm/dt=4πR²P/c²。</li></ol><p>選E。</p>", answerText="4πR²P/c²", difficulty="基礎"),
    q(5, "高一", "必修物理", "波動", "電磁波頻率與波長", "single", "B", 3, ["q05"], "page-01.jpg",
      "天線長度為四分之一波長，再用c=fλ。",
      "<p>天線長4 cm且等於λ/4，因此λ≈16 cm=0.16 m。</p><ol><li>f=c/λ=(3.0×10⁸)/0.16≈1.88×10⁹ Hz。</li><li>1.88 GHz落在500 MHz～5 GHz。</li></ol><p>所以選B。</p>", answerText="500 MHz～5 GHz", difficulty="基礎"),
    q(10, "高一", "必修物理", "近代物理", "核衰變守恆", "single", "D", 3, ["q10"], "page-02.jpg",
      "α衰變使A減4、Z減2；β⁻衰變使A不變、Z加1。",
      "<p>由²³²₉₀Th變成²²⁸₉₀Th，質量數先減4，因此必有一次α衰變。</p><ol><li>一次α後成為A=228、Z=88。</li><li>要回到Z=90，需兩次β⁻衰變，每次使Z增加1。</li></ol><p>總計一次α與兩次β衰變，選D。</p>", answerText="一次α衰變、兩次β衰變", difficulty="基礎"),
    q(12, "高二", "選修物理II", "熱學", "熱力學與氣體", "multi", "BE", 5, ["q12"], "page-03.jpg",
      "絕熱噴氣時剩餘氣體降溫、降壓並對外作正功，分子數會減少。",
      "<p>氣罐絕熱良好，持續噴氣時氣體離開且剩餘氣體膨脹作功。</p><ul><li>A錯：罐內壓力下降。</li><li>B對：剩餘氣體內能降低，溫度下降。</li><li>C錯：剩餘氣體內能不會增加。</li><li>D錯：氣體噴出使罐內分子數減少。</li><li>E對：題幹已指出罐內氣體對外界作功，且為正功。</li></ul><p>答案為B、E。</p>", answerText="B、E"),
    q(13, "高二", "選修物理I／II", "力學", "剛體姿態與角動量", "multi", "ACD", 5, ["q13"], "page-03.jpg",
      "總推力決定平移；成對反向旋翼抵銷反作用力矩；推力不均造成傾斜與水平分量。",
      "<ul><li>A對：總推力大於重力時向上加速。</li><li>B錯：反向旋轉不是讓向上的推升力互相抵銷。</li><li>C對：反向旋翼可抵銷角動量與反作用力矩，避免偏航。</li><li>D對：左高右低時總推力方向帶有向右分量，機身向右運動。</li><li>E錯：前高後低對應的水平分量不是向前；要向前通常需讓機身前低後高。</li></ul><p>答案為A、C、D。</p>", answerText="A、C、D"),
    q(14, "高二", "選修物理II", "力學", "彈簧、能量與動量", "multi", "AD", 5, ["q14"], "page-03.jpg",
      "相同彈簧壓縮相同距離，作功與末動能相同；週期、加速度與動量仍受質量影響。",
      "<ul><li>A對：彈簧作功皆為(1/2)kd²。</li><li>B錯：離開時間為四分之一週期，T∝√m，質量不同所以時間不同。</li><li>C錯：初始彈力相同，a∝1/m；質量比1:4使加速度比4:1。</li><li>D對：末動能相同，p=√(2mK)，故p甲:p乙=√1:√4=1:2。</li><li>E錯：兩者末動能都等於(1/2)kd²，比例為1:1。</li></ul><p>答案為A、D。</p>", answerText="A、D"),
    q(18, "高二", "選修物理I", "力與運動", "打點紙帶求加速度", "composite", None, 4,
      ["g18-20-stem", "q18"], "page-05.jpg",
      "以兩段平均速度對應各自中點時刻，再求速度變化率。",
      "<p>打點頻率50 Hz，相鄰點時間0.020 s。</p><ol><li>第6到第8點：Δx=9.8−5.5=4.3 cm，Δt=0.040 s，中點速度v₇=107.5 cm/s。</li><li>第8到第11點：Δx=19.0−9.8=9.2 cm，Δt=0.060 s，中點速度v₉.₅≈153.33 cm/s。</li><li>兩個中點時刻相差(9.5−7)×0.020=0.050 s。</li><li>a=(153.33−107.5)/0.050≈916.7 cm/s²。</li></ol><p>答案約為917 cm/s²（9.17 m/s²）。</p>",
      answerText="約917 cm/s²", parts=[{"id":"a","label":"加速度量值","kind":"number","answer":916.7,"tolerance":5.0,"unit":"cm/s²","points":4,"answerDisplay":"約917 cm/s²"}], officialAnswerPublished=False),
    q(19, "高二", "選修物理I", "力與運動", "等加速度位置回推", "single", "C", 3,
      ["g18-20-stem", "q19"], "page-05.jpg",
      "由第6、8、11點資料先求加速度，再代回位置式求第一點刻度。",
      "<p>承第18題，a=916.7 cm/s²。令第一點為t=0、位置x₀。</p><ol><li>第6、8點分別在t=0.10、0.14 s。</li><li>由兩位置式相減可得初速v₀=−2.5 cm/s。</li><li>x₀=5.5−v₀(0.10)−(1/2)a(0.10)²≈1.17 cm。</li></ol><p>最接近1.0 cm，選C。</p>", answerText="1.0 cm", difficulty="中等"),
    q(20, "高二", "選修物理I", "力與運動", "牛頓第二定律與阻力", "composite", None, 6,
      ["g18-20-stem", "q20"], "page-05.jpg",
      "取向下為正，兩次實驗皆滿足mg−f=ma，再聯立消去固定阻力f。",
      "<p>取向下為正，甲、乙兩金屬塊分別滿足M g−f=M a甲與m g−f=m a乙。</p><ol><li>兩式相減：(M−m)g=M a甲−m a乙。</li><li>代入M=170 g、m=50 g、a甲=916.7 cm/s²、a乙=700 cm/s²。</li><li>g=[170(916.7)−50(700)]/(170−50)≈1006.9 cm/s²。</li></ol><p>所以g≈1.01×10³ cm/s²（10.1 m/s²）。相應固定阻力量值約0.153 N。</p>",
      answerText="Mg−f=Ma甲；mg−f=ma乙；g≈1.01×10³ cm/s²", parts=[
          {"id":"eqM","label":"甲實驗（質量M）","kind":"select","answer":"Mg-f=Ma甲","points":1,"answerDisplay":"Mg−f=Ma甲","options":[["","請選擇"],["Mg-f=Ma甲","Mg−f=Ma甲"],["Mg+f=Ma甲","Mg+f=Ma甲"],["Mg=Ma甲","Mg=Ma甲"]]},
          {"id":"eqm","label":"乙實驗（質量m）","kind":"select","answer":"mg-f=ma乙","points":1,"answerDisplay":"mg−f=ma乙","options":[["","請選擇"],["mg-f=ma乙","mg−f=ma乙"],["mg+f=ma乙","mg+f=ma乙"],["mg=ma乙","mg=ma乙"]]},
          {"id":"g","label":"重力加速度量值","kind":"number","answer":1006.9,"tolerance":5.0,"unit":"cm/s²","points":4,"answerDisplay":"約1.01×10³ cm/s²"}
      ], officialAnswerPublished=False),
    q(23, "高一", "必修物理", "科學測量", "平均值與A類不確定度", "composite", None, 4,
      ["q23"], "page-06.jpg",
      "逐筆以R=V/I求電阻，平均後用u_A=√[Σ(Rᵢ−R̄)²/(n(n−1))]。",
      "<p>三筆電阻分別為0.62/0.002=310 Ω、1.80/0.006=300 Ω、2.90/0.010=290 Ω。</p><ol><li>平均電阻R̄=(310+300+290)/3=300 Ω。</li><li>A類標準不確定度u_A=√{[(310−300)²+(300−300)²+(290−300)²]/[3(3−1)]}。</li><li>u_A=√(200/6)≈5.77 Ω，適當表示為5.8 Ω。</li></ol><p>結果可寫成R=(300.0±5.8) Ω（若依不確定度位數調整，也可寫300±6 Ω）。</p>",
      answerText="平均300 Ω；A類不確定度約5.8 Ω", parts=[
          {"id":"meanR","label":"平均電阻","kind":"number","answer":300.0,"tolerance":1.0,"unit":"Ω","points":2,"answerDisplay":"300 Ω"},
          {"id":"uA","label":"A類不確定度","kind":"number","answer":5.77,"tolerance":0.3,"unit":"Ω","points":2,"answerDisplay":"約5.8 Ω"}
      ], officialAnswerPublished=False),
]


def make_quiz():
    return {
        "id": "at-tutor-ceec-115-physics-g10-g11",
        "siteTitle": "AT_tutor｜高中物理自學平台",
        "title": "115分科測驗物理｜高一高二範圍精選卷",
        "subject": "物理",
        "description": "從115學年度分科測驗物理科逐題依108課綱篩出高一必修與高二選修物理I、II範圍，保留原題截圖、官方配分、自動批改、非選題結構化作答、逐題詳解與錯題重練。",
        "selectionNote": "納入高一必修物理與高二選修物理I、II；依解題所需最高先備課程排除高三選修物理III、IV。",
        "scoringNote": "共13題、50分。單選答對得全分；多選依原卷五個選項獨立判定方式部分給分；非選題依網站結構化欄位計分。",
        "sourceLabel": "大考中心｜115學年度分科測驗物理考科試題與選擇題參考答案",
        "sourceUrl": PAPER_URL,
        "answerUrl": ANSWER_URL,
        "announcementUrl": ANNOUNCEMENT_URL,
        "school": "大學入學考試中心",
        "examYear": "115學年度",
        "questionCount": len(QUESTIONS),
        "totalScore": sum(item["points"] for item in QUESTIONS),
        "updatedAt": "2026-07-19",
        "questions": QUESTIONS,
    }


def main():
    EXAM.mkdir(parents=True, exist_ok=True)
    quiz = make_quiz()
    assert quiz["questionCount"] == 13
    assert quiz["totalScore"] == 50
    assert [item["no"] for item in QUESTIONS] == [1,2,3,4,5,10,12,13,14,18,19,20,23]
    data = "window.QUIZ = " + json.dumps(quiz, ensure_ascii=False, indent=2) + ";\n"
    (EXAM / "data.js").write_text(data, encoding="utf-8")
    source_cfg = ROOT / "exams" / "kmu-115-physics" / "firebase-config.js"
    if source_cfg.exists():
        shutil.copy2(source_cfg, EXAM / "firebase-config.js")
    print(json.dumps({"exam": str(EXAM), "questions": quiz["questionCount"], "points": quiz["totalScore"], "data_bytes": len(data.encode('utf-8'))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
