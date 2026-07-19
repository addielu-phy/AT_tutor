"use strict";

const QUIZ = window.QUIZ;
const LETTERS = ["A", "B", "C", "D", "E"];
const app = document.getElementById("app");
const lightbox = document.getElementById("lightbox");
const lbImg = document.getElementById("lbimg");
const STORE = `at_tutor_${QUIZ.id}`;
const QMAP = Object.fromEntries(QUIZ.questions.map(q => [Number(q.no), q]));
let session = null;

function esc(s){return String(s ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
function now(){return Date.now();}
function round2(n){return Math.round((Number(n)+Number.EPSILON)*100)/100;}
function pct(n,d){return d?Math.round(n/d*100):0;}
function fmtDate(ts){const d=new Date(ts),p=n=>String(n).padStart(2,"0");return `${d.getFullYear()}/${p(d.getMonth()+1)}/${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;}
function fmtDur(sec){const m=Math.floor(sec/60),s=sec%60;return m?`${m}分${s}秒`:`${s}秒`;}
function modeLabel(m){return ({grade1:"高一必修範圍",grade2:"高二選修I、II",all:"完整13題精選卷",wrong:"錯題重練"})[m]||"自學練習";}
function loadDB(){try{return JSON.parse(localStorage.getItem(STORE))||{profiles:{},last:""};}catch(e){return {profiles:{},last:""};}}
function saveDB(db){try{localStorage.setItem(STORE,JSON.stringify(db));}catch(e){console.warn("local save failed",e);}}
function getProfile(name){const db=loadDB();if(!db.profiles[name])db.profiles[name]={created:now(),attempts:[]};saveDB(db);return db.profiles[name];}
function updateProfile(name,fn){const db=loadDB();if(!db.profiles[name])db.profiles[name]={created:now(),attempts:[]};fn(db.profiles[name],db);db.last=name;saveDB(db);return db.profiles[name];}
function questionTotal(ids){return ids.reduce((s,no)=>s+(QMAP[no]?.points||0),0);}

function cloudOn(){return !!(window.CLOUD&&CLOUD.enabled&&window.firebase&&CLOUD.config&&CLOUD.config.projectId);}
function cloudInit(){if(cloudOn()&&!firebase.apps.length)firebase.initializeApp(CLOUD.config);}
function pendingKey(){return `${STORE}_pending_cloud`;}
function getPending(){try{return JSON.parse(localStorage.getItem(pendingKey()))||[];}catch(e){return [];}}
function setPending(list){try{localStorage.setItem(pendingKey(),JSON.stringify(list));}catch(e){}}
function cloudStatus(txt,cls){const el=document.getElementById("cloudStatus");if(el){el.textContent=txt;el.className=`chip ${cls||""}`.trim();}}
function cloudPayload(att,name){return {name,mode:att.mode,attemptNo:att.attemptNo||null,quiz:QUIZ.id,quizId:QUIZ.id,quizTitle:QUIZ.title,subject:QUIZ.subject,score:att.score,officialScore:att.officialScore,possibleScore:att.possibleScore,correct:att.correct,total:att.total,ids:att.ids||[],answers:att.answers||{},wrongIds:att.wrongIds||[],earnedByQuestion:att.earnedByQuestion||{},durationSec:att.durationSec||0,clientTime:att.date||Date.now(),date:att.date||Date.now(),source:"AT_tutor-pages"};}
async function cloudSendOne(payload){cloudInit();await firebase.firestore().collection("results").add({...payload,ts:firebase.firestore.FieldValue.serverTimestamp()});}
async function flushPendingCloud(){if(!cloudOn())return;const list=getPending();if(!list.length)return;const remain=[];for(const p of list){try{await cloudSendOne(p);}catch(e){remain.push(p);}}setPending(remain);if(!remain.length)cloudStatus("✓ 已補傳暫存紀錄","good");}
async function cloudPush(att,name){if(!cloudOn())return;const payload=cloudPayload(att,name);cloudStatus("雲端上傳中…","");try{await flushPendingCloud();await cloudSendOne(payload);cloudStatus("✓ 已同步教師端","good");}catch(e){console.warn("cloud push failed",e);const list=getPending();list.push(payload);setPending(list);cloudStatus("雲端暫時失敗，已存在本機待補傳","warn");}}

function installTheme(){const saved=localStorage.getItem("at_tutor_theme")||"dark";document.documentElement.dataset.theme=saved;const btn=document.getElementById("themeToggle");if(btn){btn.textContent=saved==="light"?"🌙":"☀️";btn.onclick=()=>{const cur=document.documentElement.dataset.theme==="light"?"dark":"light";document.documentElement.dataset.theme=cur;localStorage.setItem("at_tutor_theme",cur);btn.textContent=cur==="light"?"🌙":"☀️";};}}
window.zoom=src=>{lbImg.src=src;lightbox.classList.add("on");};
lightbox.onclick=()=>lightbox.classList.remove("on");
function typeset(){if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise().catch(()=>{});}
function sourceHTML(q){return (q.images||[]).map((src,i)=>`<img class="source-img" src="${esc(src)}" alt="原題第${q.originalNo||q.no}題${q.images.length>1?`圖${i+1}`:""}" loading="eager" onclick="zoom('${esc(src)}')">`).join("")+`<div class="source-note">點圖可放大；保留大考中心原題版面${q.sourcePage?` · <a href="${esc(q.sourcePage)}" target="_blank" rel="noopener">查看原卷整頁</a>`:""}</div>`;}

function emptyAnswer(q){return q.type==="composite"?{}:"";}
function answerFor(no){if(session.answers[no]===undefined)session.answers[no]=emptyAnswer(QMAP[no]);return session.answers[no];}
function isAnswered(q,ans){if(q.type==="composite")return (q.parts||[]).every(p=>String(ans?.[p.id]??"").trim()!=="");return String(ans??"").trim()!=="";}
function questionScore(q,ans){
  if(q.type==="single")return ans===q.answer?q.points:0;
  if(q.type==="multi"){
    const chosen=new Set(String(ans||"").split("").filter(x=>LETTERS.includes(x)));
    if(!chosen.size)return 0;
    const correct=new Set(String(q.answer||"").split(""));
    let k=0;for(const L of LETTERS)if(chosen.has(L)!==correct.has(L))k++;
    return round2(Math.max(0,q.points*(LETTERS.length-2*k)/LETTERS.length));
  }
  if(q.type==="composite"){
    let earned=0;
    for(const p of q.parts||[]){const raw=ans?.[p.id];if(p.kind==="number"){const n=Number(raw);if(String(raw??"").trim()!==""&&Number.isFinite(n)&&Math.abs(n-Number(p.answer))<=Number(p.tolerance||0))earned+=Number(p.points||0);}else if(String(raw??"")===String(p.answer))earned+=Number(p.points||0);}
    return round2(earned);
  }
  return 0;
}
function fullCredit(q,ans){return questionScore(q,ans)>=q.points-0.001;}
function userAnswerText(q,ans){
  if(q.type==="single")return ans||"未作答";
  if(q.type==="multi")return ans?String(ans).split("").join("、"):"未作答";
  return (q.parts||[]).map(p=>`${p.label}：${String(ans?.[p.id]??"").trim()||"未作答"}${p.kind==="number"&&String(ans?.[p.id]??"").trim()?` ${p.unit||""}`:""}`).join("；");
}
function expectedHTML(q){if(q.type!=="composite")return `<b>正解：${esc(q.answerText||q.answer)}</b>`;return `<b>參考答案</b><ul>${(q.parts||[]).map(p=>`<li>${esc(p.label)}：${esc(p.answerDisplay||p.answer)}${p.kind==="number"&&p.unit?` ${esc(p.unit)}`:""}</li>`).join("")}</ul>`;}

function singleControls(q,ans,reveal){return `<div class="grid col-12 answer-options">${LETTERS.map(L=>{let cls="btn option";if(ans===L)cls+=" selected";if(reveal&&L===q.answer)cls+=" correct";if(reveal&&ans===L&&L!==q.answer)cls+=" wrong";return `<button class="${cls}" onclick="chooseSingle('${L}')"><span class="key">${L}</span><span>選項 ${L}</span></button>`;}).join("")}</div>`;}
function multiControls(q,ans,reveal){const chosen=new Set(String(ans||"").split(""));return `<p class="muted small">多選題：可複選；未全對時依原卷五選項獨立判定方式部分給分。</p><div class="grid col-12 answer-options">${LETTERS.map(L=>{let cls="btn option";if(chosen.has(L))cls+=" selected";if(reveal&&String(q.answer).includes(L))cls+=" correct";if(reveal&&chosen.has(L)&&!String(q.answer).includes(L))cls+=" wrong";return `<button class="${cls}" onclick="toggleMulti('${L}')"><span class="key">${L}</span><span>選項 ${L}</span></button>`;}).join("")}</div>`;}
function compositeControls(q,ans,reveal){return `<div class="input-grid">${(q.parts||[]).map(p=>{const val=ans?.[p.id]??"";let status="";if(reveal){const got=p.kind==="number"?String(val).trim()!==""&&Number.isFinite(Number(val))&&Math.abs(Number(val)-Number(p.answer))<=Number(p.tolerance||0):String(val)===String(p.answer);status=`<span class="chip ${got?'good':'bad'}">${got?'正確':'需修正'}｜${p.points}分</span>`;}if(p.kind==="select")return `<label class="answer-field"><span>${esc(p.label)} ${status}</span><select onchange="setPart('${p.id}',this.value)">${(p.options||[]).map(([v,t])=>`<option value="${esc(v)}" ${String(v)===String(val)?'selected':''}>${esc(t)}</option>`).join("")}</select></label>`;return `<label class="answer-field"><span>${esc(p.label)} ${status}</span><div class="input-unit"><input inputmode="decimal" type="number" step="any" value="${esc(val)}" onchange="setPart('${p.id}',this.value)" oninput="setPart('${p.id}',this.value,false)" placeholder="輸入數值"><b>${esc(p.unit||'')}</b></div></label>`;}).join("")}</div>`;}
function answerControls(q,ans,reveal){if(q.type==="single")return singleControls(q,ans,reveal);if(q.type==="multi")return multiControls(q,ans,reveal);return compositeControls(q,ans,reveal);}

function latestWrongIds(prof){const last=[...(prof.attempts||[])].reverse().find(a=>a.quizId===QUIZ.id&&Array.isArray(a.wrongIds));return last?last.wrongIds.map(Number):[];}
function unitStats(att){const map={};(att.ids||[]).forEach(no=>{const q=QMAP[no];if(!q)return;if(!map[q.unit])map[q.unit]={earned:0,total:0};map[q.unit].total+=q.points;map[q.unit].earned+=Number(att.earnedByQuestion?.[no]||0);});return map;}

function viewLogin(){const db=loadDB(),names=Object.keys(db.profiles||{});app.innerHTML=`
<div class="brand"><div class="logo">115</div><div><h1>${esc(QUIZ.siteTitle)}</h1><div class="sub">${esc(QUIZ.title)}</div></div></div>
<div class="card"><span class="chip unit">大考中心官方題源｜13題50分</span><h2>先輸入練習名稱</h2><p class="muted small">請使用暱稱，勿輸入敏感個資。紀錄先存在此裝置，Firebase可用時交卷後同步授權教師端。</p><label class="lbl" for="nm">名字／暱稱</label><input id="nm" maxlength="24" placeholder="例如：PHY-01" onkeydown="if(event.key==='Enter')startLogin()"><div style="height:12px"></div><button class="btn primary block" onclick="startLogin()">進入練習室 →</button>${names.length?`<hr class="sep"><div class="row">${names.map(n=>`<button class="btn sm" onclick="enter('${encodeURIComponent(n)}')">👤 ${esc(n)} <span class="muted">${db.profiles[n].attempts.length}次</span></button>`).join("")}</div>`:""}</div>
<div class="grid"><div class="card col-8"><h3>篩題規則</h3><p>${esc(QUIZ.selectionNote)}</p><div class="row"><span class="chip">高一4題</span><span class="chip">高二9題</span><span class="chip">原題截圖</span><span class="chip">自動批改</span><span class="chip">錯題重練</span></div></div><div class="card col-4 center"><div class="score">50</div><div class="muted">精選卷滿分</div><a class="btn sm ghost" href="../../index.html">← AT_tutor首頁</a></div></div>
<div class="foot">來源：${esc(QUIZ.sourceLabel)}<br><a href="${esc(QUIZ.sourceUrl)}" target="_blank" rel="noopener">官方完整試卷PDF</a> · <a href="${esc(QUIZ.answerUrl)}" target="_blank" rel="noopener">官方選擇題答案</a> · <a href="teacher.html">教師版</a></div>`;const inp=document.getElementById("nm");if(db.last)inp.value=db.last;inp.focus();}
window.startLogin=function(){const name=document.getElementById("nm").value.trim();if(!name){alert("請先輸入名字或暱稱");return;}updateProfile(name,()=>{});viewDashboard(name);};
window.enter=enc=>viewDashboard(decodeURIComponent(enc));
function viewDashboard(name){const prof=getProfile(name),atts=(prof.attempts||[]).filter(a=>a.quizId===QUIZ.id),wrong=latestWrongIds(prof);const hist=atts.length?atts.slice().reverse().map((a,ri)=>`<div class="att"><div class="badge">${a.score}%</div><div class="grow"><b>第${atts.length-ri}次</b> <span class="chip">${modeLabel(a.mode)}</span><div class="muted small">${a.officialScore}/${a.possibleScore}分・${fmtDur(a.durationSec)}・${fmtDate(a.date)}</div></div><button class="btn sm" onclick="viewSavedResult('${encodeURIComponent(name)}',${atts.length-1-ri})">解析</button></div>`).join(""):`<p class="muted">還沒有紀錄，開始第一次練習吧。</p>`;app.innerHTML=`<div class="spread"><div class="brand"><div class="logo">自</div><div><h1>${esc(name)}的練習室</h1><div class="sub">115分科物理｜高一高二精選</div></div></div><button class="btn sm ghost" onclick="viewLogin()">切換</button></div><div class="card"><h2>選擇練習方式</h2><div class="modegrid"><button class="modecard" onclick="startMode('${encodeURIComponent(name)}','grade1')"><div class="mi">🌱</div><div class="mt">高一必修</div><div class="md">4題・13分</div></button><button class="modecard" onclick="startMode('${encodeURIComponent(name)}','grade2')"><div class="mi">⚙️</div><div class="mt">高二選修I、II</div><div class="md">9題・37分</div></button><button class="modecard" onclick="startMode('${encodeURIComponent(name)}','all')"><div class="mi">📝</div><div class="mt">完整精選卷</div><div class="md">13題・50分・答案最後顯示</div></button><button class="modecard" ${wrong.length?`onclick="startMode('${encodeURIComponent(name)}','wrong')"`:"disabled"}><div class="mi">🎯</div><div class="mt">錯題重練</div><div class="md">${wrong.length?`${wrong.length}題待加強`:"完成練習後啟用"}</div></button></div><div style="height:12px"></div><span id="cloudStatus" class="chip ${cloudOn()?"good":"warn"}">${cloudOn()?"雲端同步已啟用":"本機保存模式"}</span></div><div class="card"><h3>練習紀錄 <span class="muted small">${atts.length}次</span></h3>${hist}</div><div class="foot"><a href="teacher.html">教師版</a> · <a href="../../index.html">AT_tutor首頁</a></div>`;}
window.startMode=function(enc,mode){const name=decodeURIComponent(enc),prof=getProfile(name);let ids=QUIZ.questions.filter(q=>mode==="grade1"?q.grade==="高一":mode==="grade2"?q.grade==="高二":true).map(q=>q.no);if(mode==="wrong"){ids=latestWrongIds(prof);if(!ids.length){alert("目前沒有錯題可練。");return;}}session={name,mode,ids,i:0,answers:{},revealed:{},start:now(),saved:false};renderQuestion();};
function progressHTML(){const done=session.ids.filter(no=>isAnswered(QMAP[no],session.answers[no])).length;return `<div class="pbar" title="${done}/${session.ids.length}"><span style="width:${pct(done,session.ids.length)}%"></span></div>`;}
function renderQuestion(){const no=session.ids[session.i],q=QMAP[no],ans=answerFor(no),reveal=!!session.revealed[no];app.innerHTML=`<div class="spread"><div><h2>${modeLabel(session.mode)} <span class="muted small">${session.i+1}/${session.ids.length}</span></h2><div class="sub">原題第${q.originalNo}題｜${esc(q.grade)}｜${esc(q.course)}｜${q.points}分</div></div><button class="btn sm ghost" onclick="leaveSession()">離開</button></div><div class="card tight">${progressHTML()}</div><div class="grid"><div class="card col-8"><div class="spread"><div class="row"><span class="chip unit">原題第${q.originalNo}題</span><span class="chip">${esc(q.type==='single'?'單選':q.type==='multi'?'多選':'非選')}</span></div><div class="row"><span class="chip unit">${esc(q.unit)}</span><span class="chip">${esc(q.subunit)}</span></div></div>${sourceHTML(q)}${answerControls(q,ans,reveal)}${session.mode!=="all"&&!reveal?`<div style="height:12px"></div><button class="btn ghost block" onclick="revealCurrent()">核對本題並顯示詳解</button>`:""}${reveal?`<div class="explain"><div class="spread">${expectedHTML(q)}<span class="chip ${fullCredit(q,ans)?'good':questionScore(q,ans)>0?'warn':'bad'}">本題${questionScore(q,ans)}/${q.points}分</span></div><p><b>解題關鍵：</b>${esc(q.keyPoint)}</p>${q.explanationHtml}</div>`:""}</div><div class="card col-4"><h3>題號</h3><div class="qnav">${session.ids.map((id,idx)=>{const qq=QMAP[id],aa=session.answers[id];let cls=idx===session.i?"cur":"";if(isAnswered(qq,aa))cls+=" done";if(session.revealed[id])cls+=fullCredit(qq,aa)?" right":" wrong";return `<button class="${cls}" onclick="jump(${idx})">${id}</button>`;}).join("")}</div><p class="muted small">「完整精選卷」交卷後才顯示答案；分年級與錯題模式可逐題核對。</p></div></div><div class="stickybar"><div class="spread"><button class="btn" onclick="prevQ()" ${session.i===0?"disabled":""}>←上一題</button><div class="row"><button class="btn" onclick="nextQ()" ${session.i===session.ids.length-1?"disabled":""}>下一題→</button><button class="btn primary" onclick="finishSession()">交卷／結算</button></div></div></div>`;typeset();}
window.chooseSingle=L=>{session.answers[session.ids[session.i]]=L;renderQuestion();};
window.toggleMulti=L=>{const no=session.ids[session.i],set=new Set(String(answerFor(no)||"").split("").filter(Boolean));set.has(L)?set.delete(L):set.add(L);session.answers[no]=LETTERS.filter(x=>set.has(x)).join("");renderQuestion();};
window.setPart=function(id,value,rerender=true){const no=session.ids[session.i],ans=answerFor(no);ans[id]=value;session.answers[no]=ans;if(rerender)renderQuestion();};
window.revealCurrent=()=>{session.revealed[session.ids[session.i]]=true;renderQuestion();};
window.jump=i=>{session.i=i;renderQuestion();};window.prevQ=()=>{if(session.i>0){session.i--;renderQuestion();}};window.nextQ=()=>{if(session.i<session.ids.length-1){session.i++;renderQuestion();}};
window.leaveSession=function(){if(Object.keys(session.answers).length&&!confirm("尚未結算，確定離開嗎？"))return;viewDashboard(session.name);};
function scoreSession(s){let earned=0,correct=0;const wrongIds=[],unanswered=[],earnedByQuestion={};for(const no of s.ids){const q=QMAP[no],ans=s.answers[no],got=questionScore(q,ans);earnedByQuestion[no]=got;earned+=got;if(fullCredit(q,ans))correct++;else wrongIds.push(no);if(!isAnswered(q,ans))unanswered.push(no);}const possibleScore=questionTotal(s.ids),officialScore=round2(earned);return {correct,wrongIds,unanswered,earnedByQuestion,officialScore,possibleScore,score:pct(officialScore,possibleScore)};}
window.finishSession=function(){const missing=session.ids.filter(no=>!isAnswered(QMAP[no],session.answers[no])).length;if(session.mode==="all"&&missing&&!confirm(`還有${missing}題未完整作答，確定交卷嗎？`))return;const result=scoreSession(session),att={quizId:QUIZ.id,quizTitle:QUIZ.title,subject:QUIZ.subject,mode:session.mode,ids:session.ids.slice(),answers:JSON.parse(JSON.stringify(session.answers)),...result,total:session.ids.length,date:now(),durationSec:Math.max(1,Math.round((now()-session.start)/1000))};saveAttempt(att);viewResult(att,true);};
function saveAttempt(att){if(session.saved)return;session.saved=true;const count=updateProfile(session.name,p=>p.attempts.push(att)).attempts.length;att.attemptNo=count;cloudPush(att,session.name);}
function viewResult(att,fresh){const byUnit=Object.entries(unitStats(att)).sort((a,b)=>a[0].localeCompare(b[0],"zh-Hant"));const diag=byUnit.map(([u,v])=>`<tr><td><span class="chip unit">${esc(u)}</span></td><td class="right">${round2(v.earned)}/${v.total}</td><td><div class="minibar"><span style="width:${pct(v.earned,v.total)}%;background:${v.earned/v.total>=.7?'var(--good)':v.earned/v.total>=.4?'var(--warn)':'var(--bad)'}"></span></div></td><td class="right">${pct(v.earned,v.total)}%</td></tr>`).join("");const review=att.ids.map(no=>{const q=QMAP[no],ans=att.answers[no],got=Number(att.earnedByQuestion?.[no]||0);return `<div class="card tight"><div class="spread"><div><span class="chip ${got>=q.points-0.001?'good':got>0?'warn':'bad'}">原題${no}｜${got}/${q.points}分</span> <span class="chip unit">${esc(q.grade)}｜${esc(q.unit)}</span></div></div>${sourceHTML(q)}<p><b>你的答案：</b>${esc(userAnswerText(q,ans))}</p><div class="explain">${expectedHTML(q)}<p><b>解題關鍵：</b>${esc(q.keyPoint)}</p>${q.explanationHtml}</div></div>`;}).join("");app.innerHTML=`<div class="spread"><div class="brand"><div class="logo">${att.score}%</div><div><h1>練習結果</h1><div class="sub">${modeLabel(att.mode)}・${fmtDur(att.durationSec)}</div></div></div><button class="btn sm ghost" onclick="viewDashboard('${esc(session?.name||loadDB().last||'')}')">回練習室</button></div><div class="card center"><div class="score">${att.officialScore}/${att.possibleScore}</div><h3>完全答對${att.correct}/${att.total}題</h3><p id="cloudStatus" class="chip ${cloudOn()?"":"warn"}">${fresh&&cloudOn()?"雲端上傳中…":"已保存在本機"}</p></div><div class="card"><h3>單元診斷</h3><table><tr><th>單元</th><th class="right">得分</th><th>比例</th><th class="right">%</th></tr>${diag}</table></div><div class="spread"><h3>逐題解析</h3><button class="btn sm" onclick="window.print()">列印</button></div>${review}`;typeset();}
window.viewSavedResult=function(enc,i){const name=decodeURIComponent(enc),att=(getProfile(name).attempts||[]).filter(a=>a.quizId===QUIZ.id)[i];session={name};viewResult(att,false);};

installTheme();viewLogin();if(cloudOn())flushPendingCloud();
