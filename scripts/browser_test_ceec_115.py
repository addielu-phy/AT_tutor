from __future__ import annotations

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE="http://127.0.0.1:8769"
OUT=ROOT/"work"/"ceec-115-physics"/"browser-qa";OUT.mkdir(parents=True,exist_ok=True)


def main():
    result={}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="msedge",headless=True)
        ctx=browser.new_context(viewport={"width":1440,"height":1000},device_scale_factor=1)
        ctx.route("**/firebase-config.js",lambda route:route.fulfill(status=200,content_type="application/javascript",body="window.CLOUD={enabled:false};"))
        page=ctx.new_page();errors=[]
        page.on("console",lambda m:errors.append(f"console:{m.type}:{m.text}") if m.type=="error" else None)
        page.on("pageerror",lambda e:errors.append(f"pageerror:{e}"))
        page.goto(BASE+"/",wait_until="networkidle")
        assert "物理自學評量平台" in page.title()
        assert page.get_by_text("物理科高一高二範圍精選卷").count()==1
        page.goto(BASE+"/exams/ceec-115-physics-g10-g11/",wait_until="networkidle")
        assert "13題50分" in page.locator("body").inner_text().replace(" ","")
        page.locator("#nm").fill("LOCAL-QA")
        page.get_by_role("button",name="進入練習室 →").click()
        page.get_by_role("button",name="完整精選卷").click()
        qcount=page.evaluate("QUIZ.questions.length")
        partial=page.evaluate("questionScore(QMAP[12],'B')")
        onepoint=page.evaluate("questionScore(QMAP[12],'AB')")
        image_check=page.evaluate("""async()=>{const srcs=[...new Set(QUIZ.questions.flatMap(q=>q.images))];const out=[];for(const src of srcs){const im=new Image();im.src=src;await im.decode();out.push([src,im.naturalWidth,im.naturalHeight]);}return out;}""")
        page.evaluate("""()=>{for(const q of QUIZ.questions){if(q.type==='single'||q.type==='multi')session.answers[q.no]=q.answer;else session.answers[q.no]=Object.fromEntries(q.parts.map(p=>[p.id,p.answer]));}finishSession();}""")
        page.wait_for_selector("text=50/50",timeout=10000)
        result_text=page.locator("body").inner_text()
        assert "完全答對13/13題" in result_text.replace(" ","")
        assert partial==3 and onepoint==1
        assert qcount==13 and len(image_check)>=13 and all(w>=500 and h>=50 for _,w,h in image_check)
        page.screenshot(path=str(OUT/"desktop-full-score.png"),full_page=True)
        result["desktop"]={"questions":qcount,"score":"50/50","partial_BE_B":partial,"partial_BE_AB":onepoint,"images":len(image_check),"errors":errors}
        assert not errors,errors
        ctx.close()

        mobile=browser.new_context(viewport={"width":390,"height":844},device_scale_factor=1,is_mobile=True)
        mobile.route("**/firebase-config.js",lambda route:route.fulfill(status=200,content_type="application/javascript",body="window.CLOUD={enabled:false};"))
        mp=mobile.new_page();merrors=[]
        mp.on("console",lambda m:merrors.append(f"console:{m.type}:{m.text}") if m.type=="error" else None);mp.on("pageerror",lambda e:merrors.append(f"pageerror:{e}"))
        mp.goto(BASE+"/exams/ceec-115-physics-g10-g11/",wait_until="networkidle")
        overflow_login=mp.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
        mp.locator("#nm").fill("MOBILE-QA");mp.get_by_role("button",name="進入練習室 →").click();mp.get_by_role("button",name="高二選修I、II").click()
        mp.evaluate("""()=>{const idx=session.ids.indexOf(13);session.i=idx;renderQuestion();}""")
        mp.wait_for_selector("text=原題第13題")
        overflow_question=mp.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
        mp.screenshot(path=str(OUT/"mobile-q13.png"),full_page=True)
        assert overflow_login<=1 and overflow_question<=1,(overflow_login,overflow_question)
        assert not merrors,merrors
        result["mobile"]={"viewport":"390x844","overflow_login":overflow_login,"overflow_question":overflow_question,"errors":merrors}
        mobile.close()

        teacher=browser.new_context(viewport={"width":1280,"height":900})
        teacher.route("**/firebase-config.js",lambda route:route.fulfill(status=200,content_type="application/javascript",body="window.CLOUD={enabled:false};"))
        tp=teacher.new_page();terrors=[]
        tp.on("console",lambda m:terrors.append(f"console:{m.type}:{m.text}") if m.type=="error" else None);tp.on("pageerror",lambda e:terrors.append(f"pageerror:{e}"))
        tp.goto(BASE+"/exams/ceec-115-physics-g10-g11/teacher.html",wait_until="networkidle")
        assert "教師版" in tp.locator("body").inner_text() and "全班最常錯題" in tp.locator("body").inner_text()
        tp.screenshot(path=str(OUT/"teacher-local-fallback.png"),full_page=True)
        assert not terrors,terrors
        result["teacher"]={"mode":"local-fallback","errors":terrors}
        teacher.close();browser.close()
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
