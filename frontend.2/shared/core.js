/* LOWKEY core – risk rules, calculations, mock AI and the API router.
   Used by server.js (Node) and, when no server is reachable, by the browser's offline demo store. */
(function(root){
const hash=s=>{let h=5381;for(const c of s)h=((h<<5)+h+c.charCodeAt(0))>>>0;return h};
const last=a=>a[a.length-1],avg=a=>a.length?Math.round(a.reduce((x,y)=>x+y,0)/a.length):0;
function risk(s){const f=[],a=s.att;if(a[0]-last(a)>=15)f.push(`Attendance moved from ${a[0]}% to ${last(a)}% over 8 weeks`);const mi=s.m.slice(-4).filter(x=>!x).length;if(mi>=3)f.push(`${mi} of the last 4 assignments were not submitted`);if(s.q[0]-last(s.q)>=15)f.push(`Quiz scores moved from ${s.q[0]} to ${last(s.q)}`);if(s.lms[0]-last(s.lms)>=30)f.push(`LMS engagement index moved from ${s.lms[0]} to ${last(s.lms)}`);return{f,lvl:f.length>=3?'High':f.length==2?'Medium':f.length==1?'Watch':'On track'}}
const gp=m=>m>=90?10:m>=80?9:m>=70?8:m>=60?7:m>=50?6:5;
function plan(s){const R=s.sub.reduce((a,x)=>a+x[2],0),C=(s.s-1)*20,req=(s.t*(C+R)-s.cg*C)/R;return{R,C,req,ok:req<=10,sgpa:s.sub.reduce((a,x)=>a+gp(x[1])*x[2],0)/R}}
function summary(L,I){const n=L.length,lv=L.map(s=>risk(s).lvl),col=k=>n?L[0][k].map((_,i)=>avg(L.map(s=>s[k][i]))):[];
return{total:n,review:lv.filter(x=>x!='On track').length,high:lv.filter(x=>x=='High').length,att:avg(L.map(s=>last(s.att))),asg:avg(L.map(s=>s.m.reduce((a,b)=>a+b,0)/s.m.length*100)),
pending:I.filter(i=>i.status!='Completed').length,fu:I.filter(i=>i.fu&&i.status!='Completed').length,ints:I.length,done:I.filter(i=>i.status=='Completed').length,
dist:{High:lv.filter(x=>x=='High').length,Medium:lv.filter(x=>x=='Medium').length,Watch:lv.filter(x=>x=='Watch').length,'On track':lv.filter(x=>x=='On track').length},
w:{att:col('att'),lms:col('lms'),q:col('q'),asg:n?L[0].m.map((_,i)=>avg(L.map(s=>s.m[i]*100))):[]}}}
// Mock AI: templates only. All numbers come from verified records via risk()/plan().
function ai(k,s,q){const w=s.sub.slice().sort((a,b)=>a[1]-b[1]),r=risk(s),p=plan(s),t=w.reduce((a,x)=>a+100-x[1],0)||1;
const O={
plan:()=>'Weekly study plan (mock AI, 14 hours)\n'+w.map(x=>`• ${x[0]}: ${(14*(100-x[1])/t).toFixed(1)} h (current marks ${x[1]}%)`).join('\n')+'\n\nSuggested rhythm: weekdays 1.5 h after class; weekend 3.5 h revision; one practice quiz on Sunday.',
quiz:()=>`Practice quiz – ${w[0][0]} (mock AI)\n1. Define the key terms from your last lecture.\n2. Solve one worked example without notes.\n3. Explain one concept to a friend in 3 sentences.\n(Add approved course material for subject-specific questions.)`,
notes:()=>`Revision notes outline – ${w[0][0]} (mock AI)\n• Core definitions\n• 3 formulas/algorithms to memorise\n• Common mistakes\n• 5 self-test questions`,
cgpa:()=>p.ok?`Target ${s.t}: calculated need is ${p.req.toFixed(2)} semester GPA across ${p.R} credits. Priority subjects: ${w.slice(0,2).map(x=>x[0]).join(', ')}. No outcome is guaranteed.`:`Target ${s.t} needs ${p.req.toFixed(2)} in one semester, which is above the scale. Try a multi-semester goal.`,
chat:()=>`Mock AI: Let's break "${q}" into a definition, a simple example, and a practice question. Based on your records, ${w[0][0]} (${w[0][1]}%) may be worth extra time.`,
sum:()=>`Case summary – ${s.n} (draft, mock AI)\nObserved: CGPA ${s.cg} (target ${s.t}); attendance ${last(s.att)}%; ${s.m.filter(x=>!x).length} of 8 assignments missed.\nIndicators: ${r.f.join('; ')||'none'}.\nThese are prompts for a conversation, not predictions.`,
msg:()=>`Hi ${s.n.split(' ')[0]}, I noticed a few things in your recent coursework and wanted to check in – no pressure. Would you like to find a time to talk about how things are going and what would help?`,
brief:()=>`Meeting brief – ${s.n}\n1. Ask how the semester feels so far.\n2. Discuss: ${r.f.join('; ')||'steady progress'}.\n3. Explore obstacles and support options.\n4. Agree one small step and a follow-up date.`};
return O[k]?O[k]():null}
// ---- Chatbot: grounded intent engine (no AI key needed) + facts for the optional live LLM ----
const CRISIS=/suicid|kill myself|end my life|self[- ]?harm|hurt myself|want to die|don'?t want to live/i;
function facts(s){const r=risk(s),p=plan(s);return{semester:s.s,department:s.d,current_cgpa:s.cg,target_cgpa:s.t,attendance_weekly_pct:s.att,lms_engagement_index_weekly:s.lms,assignments_submitted_last_8_weeks_1yes_0no:s.m,quiz_scores:s.q,subjects:s.sub.map(x=>({subject:x[0],marks_pct:x[1],credits:x[2]})),upcoming_deadlines:(s.dl||[]).map(x=>({title:x[0],due:x[1]})),risk_indicators:r.f,indicator_level:r.lvl,target_cgpa_calculation:{required_semester_gpa:+p.req.toFixed(2),reachable_this_semester:p.ok,credits_this_semester:p.R,note:'Grade scale and prior credits are placeholders'}}}
const MENU=(M)=>M?'I can summarise this student, explain the indicators, draft a supportive message, prepare a meeting brief, or show subjects needing attention.':'I can explain your indicators, check attendance and deadlines, calculate what your target CGPA needs, and make a study plan, quiz or revision outline.';
function chatMock(me,s,q){const m=q.toLowerCase(),M=me.role=='mentor',w=s.sub.slice().sort((a,b)=>a[1]-b[1]),r=risk(s),has=x=>x.test(m),f=s.n.split(' ')[0],who=M?f+"'s":'your';
if(CRISIS.test(q))return{crisis:1,reply:"I'm really sorry you're feeling this way, and I'm glad you said it. I can't give you the support a person can, so please talk to someone you trust today or contact your campus counselling service. In India you can call Tele-MANAS on 14416. If you might act on these thoughts or are in danger, call your local emergency number. You don't have to carry this alone."};
let t;
if(has(/\b(summar|overview of)/)&&M)t=ai('sum',s);
else if(has(/message|draft|email|text them/)&&M)t=ai('msg',s)+'\n\n(Draft only. Review before sending.)';
else if(has(/brief|meeting prep|prepare.*meeting/)&&M)t=ai('brief',s);
else if(has(/fail|drop ?out|guarantee|predict|will i (pass|fail)|chances/))t=`I can't predict outcomes, and an indicator is not a verdict. What the records show for ${who} account: ${r.f.length?r.f.join('; ')+'.':'no concerning patterns.'} The useful question is what support would help next.`;
else if(has(/attendance|classes|absent/))t=`${M?f+"'s":'Your'} weekly attendance moved from ${s.att[0]}% to ${s.att[s.att.length-1]}% over 8 weeks. I don't have your institution's attendance rule, so please check it for the exact minimum.`;
else if(has(/assign|deadline|due|submit|homework/)){const mi=s.m.filter(x=>!x).length;t=`${mi} of the last ${s.m.length} assignments were not submitted. `+((s.dl||[]).length?'Upcoming: '+s.dl.map(x=>`${x[0]} (${x[1]})`).join('; ')+'.':'No upcoming deadlines are recorded.')}
else if(has(/cgpa|gpa|target|grade needed/))t=ai('cgpa',s);
else if(has(/plan|schedule|timetable|study/))t=ai('plan',s);
else if(has(/quiz|practice|test me/))t=ai('quiz',s);
else if(has(/notes|revis/))t=ai('notes',s);
else if(has(/weak|subject|focus|improve|struggl/))t=`Lowest current marks: ${w.slice(0,2).map(x=>`${x[0]} (${x[1]}%)`).join(' and ')}. Giving these extra time first is a reasonable start.`;
else if(has(/why|flag|risk|indicator|concern|worr|check-?in/))t=r.f.length?`Indicators for ${who} record (level: ${r.lvl}):\n`+r.f.map(x=>'• '+x).join('\n')+'\nThese suggest a supportive conversation could help. They are not predictions.':'Nothing is flagged right now. The recorded patterns look steady.';
else if(!M&&has(/mentor|talk to|speak to|help me|support/))t='You can send a meeting request to your mentor from My Support. I can also help you prepare what to say.';
else t=(has(/^(hi|hello|hey)\b/)?'Hi! ':"I'm not sure I can answer that from your records. ")+MENU(M);
return{reply:t}}
const TYPES=['Mentor meeting','Remedial class','Study support','Follow-up discussion'],STAT=['Pending','In Progress','Completed'];
/* API router: route(db, save, method, url, body, token) -> {status,data}. Role checks are enforced here, server-side. */
function route(db,save,method,url,body,tok){
const[,p,id]=url.split('?')[0].split('/').filter(Boolean),b=body||{},R=(s,d)=>({status:s,data:d}),E=(s,m)=>R(s,{error:m});
if(p=='health')return R(200,{ok:true});
if(method=='POST'&&p=='login'){let e=String(b.email||'').trim().toLowerCase();const pw=String(b.password||'').trim();if(!e||!pw)return E(400,'Enter your email/username and password.');if(!e.includes('@'))e+='@lowkey.demo';const a=db.users[e];if(!a||a.role!==b.role||a.h!==hash(pw))return E(401,'Those details do not match a '+b.role+' demo account.');const t=Math.random().toString(36).slice(2)+Date.now().toString(36);db.sess[t]={u:e,role:a.role,sid:a.sid,mid:a.mid};save();return R(200,{token:t,user:db.sess[t]})}
const me=db.sess[tok];if(!me)return E(401,'Please sign in again.');
if(p=='logout'){delete db.sess[tok];save();return R(200,{ok:true})}
const M=me.role=='mentor',mine=db.students.filter(s=>M?s.mid==me.mid:s.id==me.sid),ids=mine.map(s=>s.id),myI=db.ints.filter(i=>ids.includes(i.sid));
if(p=='me')return R(200,me);
if(p=='students'){if(id){const s=mine.find(x=>x.id==id);return s?R(200,s):E(403,'You do not have access to that student.')}return R(200,mine)}
if(p=='summary')return M?R(200,summary(mine,myI)):E(403,'Mentors only.');
if(p=='interventions'){
 if(method=='GET')return R(200,M?myI:myI.filter(i=>i.vis).map(({notes,outcome,...r})=>r));
 if(!M)return E(403,'Mentors only.');
 if(method=='POST'){if(!ids.includes(b.sid))return E(400,'Choose one of your assigned students.');if(!TYPES.includes(b.type))return E(400,'Choose an intervention type.');if(!/^\d{4}-\d{2}-\d{2}$/.test(b.due||''))return E(400,'Choose a due date.');if(b.fu&&b.fu<b.due)return E(400,'Follow-up date must be on or after the due date.');
  const s=mine.find(x=>x.id==b.sid),i={id:Date.now(),sid:b.sid,type:b.type,due:b.due,fu:b.fu||'',notes:String(b.notes||'').trim().slice(0,500)||'(no notes)',status:'Pending',base:last(s.att),vis:b.vis?1:0};db.ints.push(i);save();return R(201,i)}
 if(method=='PATCH'){const i=myI.find(x=>x.id==id);if(!i)return E(404,'Intervention not found.');if(b.status!==undefined){if(!STAT.includes(b.status))return E(400,'Invalid status.');i.status=b.status;if(b.status=='Completed')i.after=last(mine.find(x=>x.id==i.sid).att)}if(b.outcome!==undefined)i.outcome=String(b.outcome).slice(0,500);save();return R(200,i)}}
if(p=='requests'){
 if(method=='GET')return R(200,db.reqs.filter(r=>ids.includes(r.sid)));
 if(M)return E(403,'Only students can send requests.');const t=String(b.t||'').trim().slice(0,500);if(!t)return E(400,'Please describe what you need.');const r={id:Date.now(),sid:me.sid,t,at:new Date().toISOString().slice(0,10)};db.reqs.push(r);save();return R(201,r)}
if(p=='ai'&&method=='POST'){const s=mine.find(x=>x.id==b.sid);if(!s)return E(403,'You do not have access to that student.');if(!M&&['sum','msg','brief'].includes(b.kind))return E(403,'Mentors only.');if(b.kind=='chat'&&!String(b.q||'').trim())return E(400,'Type a question first.');const t=ai(b.kind,s,String(b.q||'').slice(0,300));return t?R(200,{mock:true,text:t}):E(400,'Unknown request type.')}
if(p=='chat'&&method=='POST'){const ms=b.messages;if(!Array.isArray(ms)||ms.length<1||ms.length>20)return E(400,'Send between 1 and 20 messages.');for(const x of ms)if(!x||!['user','assistant'].includes(x.role)||typeof x.content!='string'||!x.content.trim()||x.content.length>2000)return E(400,'Each message needs a role and 1-2000 characters.');if(ms[0].role!='user'||last(ms).role!='user')return E(400,'The conversation must start and end with a user message.');
 const s=mine.find(x=>x.id==(M?b.sid:me.sid));if(!s)return E(403,'You do not have access to that student.');const c=chatMock(me,s,last(ms).content);return R(200,{reply:c.reply,mode:'mock',_facts:facts(s),_role:me.role,_crisis:!!c.crisis})}
if(p=='reset'&&method=='POST'){if(!M)return E(403,'Mentors only.');db.ints=JSON.parse(JSON.stringify(C.seed.ints));db.reqs=[];save();return R(200,{ok:true})}
return E(404,'Not found.')}
const C={hash,risk,gp,plan,summary,ai,facts,route,seed:null};
if(typeof module!=='undefined')module.exports=C;else root.Core=C;
})(typeof window!=='undefined'?window:globalThis);
