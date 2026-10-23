/* LOWKEY chatbot widget. Floating panel that lives outside #root so it survives re-renders.
   History is kept in memory only: private to this browser tab, never shown to mentors. */
const LKChat=(()=>{
let el=null,hist=[],busy=false,sid=null,seen='';
const CH={student:['Why was I flagged?','What do I need for my target CGPA?','Make me a study plan',"What's due soon?"],
 mentor:['Summarise this student','Draft a supportive message','Prepare a meeting brief','Which subjects need attention?']};
const MODE={ai:'AI-powered answers','mock':'Demo mode: answers from your records (no AI key)','mock-fallback':'AI unavailable: basic answers from your records'};
const fmt=t=>esc(t).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>');
const isM=()=>{const u=sess();return u&&u.role=='mentor'};
function add(role,text){const d=document.createElement('div');d.className='cm cm-'+role;if(role=='user')d.textContent=text;else d.innerHTML=fmt(text);const l=$('#clog');l.append(d);l.scrollTop=l.scrollHeight;return d}
function welcome(){$('#clog').innerHTML='';add('bot',isM()?"Hi! Pick a student above and ask me anything about their record. Drafts are for your review before anything is sent.":"Hi! I'm your LOWKEY assistant. I answer from your own recorded data, and I'll say so when something isn't available.");
 $('#cchips').innerHTML=CH[isM()?'mentor':'student'].map(c=>`<button type="button">${esc(c)}</button>`).join('')}
function students(){const a=$('#csel'),m=isM();if(!m){a.innerHTML='';sid=null;return}
 const key=S.map(x=>x.id).join();if(key===seen&&sid)return;seen=key;
 if(!sid||!S.some(x=>x.id==sid))sid=(typeof st!='undefined'&&st.sel&&S.some(x=>x.id==st.sel)?st.sel:(S[0]||{}).id)||null;
 a.innerHTML=`<label for="cst">Student</label><select id="cst">${S.map(x=>`<option value="${esc(x.id)}" ${x.id==sid?'selected':''}>${esc(x.n)}</option>`).join('')}</select>`;
 $('#cst').onchange=e=>{sid=e.target.value;hist=[];welcome()}}
function win(){const a=hist.slice(-19);while(a.length&&a[0].role!='user')a.shift();return a}
async function send(t){t=t.trim();if(!t||busy)return;if(isM()&&!sid)return add('bot','No assigned student is available yet.');
 busy=true;$('#cchips').innerHTML='';hist.push({role:'user',content:t});add('user',t);$('#cin').value='';
 const w=add('bot','Thinking…');w.classList.add('typing');
 try{const r=await API.call('POST','api/chat',{messages:win(),sid:isM()?sid:undefined});hist.push({role:'assistant',content:r.reply});w.classList.remove('typing');w.innerHTML=fmt(r.reply);$('#cmode').textContent=MODE[r.mode]||''}
 catch(e){if(e.status==401){return logout('Your session expired. Please sign in again.')}hist.pop();w.classList.remove('typing');w.classList.add('cerr');w.textContent=(e.message||'Something went wrong')+' Your message was not lost: press Send to try again.';$('#cin').value=t}
 busy=false;$('#cin').focus()}
function open(o){$('#cpanel').hidden=!o;$('#cfab').hidden=o;$('#cfab').setAttribute('aria-expanded',o);if(o){if(!hist.length&&!$('#clog').children.length)welcome();students();$('#cin').focus()}else $('#cfab').focus()}
function build(){el=document.createElement('div');el.id='lkc';
 el.innerHTML=`<button class="cfab" id="cfab" type="button" aria-expanded="false" aria-controls="cpanel">💬 Ask LOWKEY</button>
 <section class="cpanel" id="cpanel" role="dialog" aria-label="LOWKEY assistant" hidden>
 <header><div><b>LOWKEY Assistant</b><span class="cmode" id="cmode"></span></div><div><button type="button" id="cclr" aria-label="Clear conversation" title="Clear conversation">↺</button><button type="button" id="cx" aria-label="Close assistant">✕</button></div></header>
 <div class="csel" id="csel"></div><div id="clog" role="log" aria-live="polite"></div><div id="cchips"></div>
 <form id="cform"><input id="cin" maxlength="2000" autocomplete="off" placeholder="Type your question…" aria-label="Message"><button class="btn sm" id="csend">Send</button></form>
 <p class="cnote">AI can make mistakes. Numbers come from the records. Chats stay in this browser and aren't shared with mentors.</p></section>`;
 document.body.append(el);
 $('#cfab').onclick=()=>open(true);$('#cx').onclick=()=>open(false);
 $('#cclr').onclick=()=>{hist=[];$('#cmode').textContent='';welcome()};
 $('#cform').onsubmit=e=>{e.preventDefault();send($('#cin').value)};
 $('#cchips').onclick=e=>{const b=e.target.closest('button');if(b)send(b.textContent)};
 el.addEventListener('keydown',e=>{if(e.key=='Escape'&&!$('#cpanel').hidden)open(false)})}
return{sync(){if(!sess()){this.reset();return}if(!el)build();students()},reset(){if(el){el.remove();el=null}hist=[];sid=null;seen='';busy=false}}})();
/* Hook into the app shell without editing it: re-sync after every render, wipe on logout. */
(()=>{const p=paint,l=logout;paint=function(x){p(x);LKChat.sync()};logout=function(m){LKChat.reset();l(m)}})();
