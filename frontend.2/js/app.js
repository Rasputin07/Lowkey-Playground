/* LOWKEY app shell: session, login, navigation and rendering. */
const $=s=>document.querySelector(s),esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const M={};const ls=(k,v)=>{try{if(v===undefined)return JSON.parse(localStorage.getItem(k));M[k]=v;localStorage.setItem(k,JSON.stringify(v))}catch(e){if(v===undefined)return M[k]??null}};
const sGet=()=>{let v=null;try{v=sessionStorage.getItem('lk_s')||localStorage.getItem('lk_s')}catch(e){}return v||window._m||null};
const sSet=(v,rem)=>{window._m=v;try{sessionStorage.removeItem('lk_s');localStorage.removeItem('lk_s');if(v)(rem?localStorage:sessionStorage).setItem('lk_s',v)}catch(e){}};
const sess=()=>JSON.parse(sGet()||'null');
const {risk,gp,plan}=Core;
let S=[],DB={ints:[],reqs:[],sum:null,loaded:false};
let st={view:'ov',sel:null,role:'student',chat:[],err:null,note:'',f:{q:'',d:'',s:'',r:''}};
const sById=id=>S.find(x=>x.id===id),last=a=>a[a.length-1];
const tag=l=>`<span class="tag ${l.split(' ')[0]}">${l}</span>`;
const ints=()=>DB.ints,reqs=()=>DB.reqs,ST=['Pending','In Progress','Completed'];
const P='#6c4cf5',B='#0ea5e9',O='#d97706';
const NAV={student:[['ov','Overview'],['ac','My Academics'],['co','AI Study Copilot'],['pr','My Progress'],['su','My Support'],['se','Settings']],
mentor:[['ov','Overview'],['dir','Student Directory'],['rk','Risk Analysis'],['in','Interventions'],['as','AI Mentor Assistant'],['fa','Fairness & Insights'],['tl','Signal Timeline'],['se','Settings']]};
const toast=m=>{let t=$('#ts');if(!t){t=document.createElement('div');t.id='ts';t.setAttribute('role','status');document.body.appendChild(t)}t.textContent=m;t.className='show';setTimeout(()=>t.className='',3500)};
// ---------- Login ----------
function loginView(){$('#root').innerHTML=`<div class="login"><div class="lc" id="lf"><div class="logo"><i>🎓</i>LOWKEY</div><button type="button" class="tgl" onclick="tg()" aria-label="Toggle light and dark mode">🌓</button><h1>Welcome back</h1><p>Understand your progress. Shape your future.</p>
<div class="roles" role="group" aria-label="Choose role"><button type="button" class="role" data-r="student" aria-pressed="${st.role=='student'}">🎓 Student</button><button type="button" class="role" data-r="mentor" aria-pressed="${st.role=='mentor'}">🧑‍🏫 Mentor</button></div>
<label for="u">Email or username</label><input id="u" autocomplete="username" required><label for="p">Password</label><div class="pw"><input id="p" type="password" autocomplete="current-password" required><button type="button" id="sp" aria-label="Show or hide password">Show</button></div>
<div class="row"><label style="margin:0;font-weight:400"><input type="checkbox" id="rm">Remember me</label><a id="fg">Forgot password?</a></div><div class="err" id="er" role="alert"></div>
<button class="btn full" type="button" id="sb">Sign in</button><div class="hint" id="hn"></div></div></div>`;
const hint=()=>$('#hn').innerHTML=st.role=='student'?'Demo student: <b>student@lowkey.demo</b> / <b>student123</b><br>Demo only – fictional data, not production security.':'Demo mentor: <b>mentor@lowkey.demo</b> / <b>mentor123</b><br>Demo only – fictional data, not production security.';hint();
document.querySelectorAll('.role').forEach(b=>b.onclick=()=>{st.role=b.dataset.r;document.querySelectorAll('.role').forEach(x=>x.setAttribute('aria-pressed',x==b));hint()});
$('#sp').onclick=()=>{const p=$('#p');p.type=p.type=='password'?'text':'password';$('#sp').textContent=p.type=='password'?'Show':'Hide'};
$('#fg').onclick=()=>$('#er').textContent='Demo placeholder: password reset is not available in this prototype.';
const doLogin=async e=>{e&&e.preventDefault&&e.preventDefault();const em=$('#u').value.trim(),p=$('#p').value.trim();if(!em||!p)return $('#er').textContent='Enter your email/username and password.';const b=$('#sb');b.disabled=true;b.textContent='Signing in…';
try{const r=await API.call('POST','api/login',{email:em,password:p,role:st.role});sSet(JSON.stringify({...r.user,token:r.token}),$('#rm').checked);st.view='ov';DB.loaded=false;st.chat=[];render()}catch(x){$('#er').textContent=x.message;b.disabled=false;b.textContent='Sign in'}};
$('#er').textContent=st.note||'';st.note='';
$('#sb').onclick=doLogin;['#u','#p'].forEach(i=>$(i).onkeydown=e=>{if(e.key=='Enter')doLogin(e)})}
function logout(m){try{API.call('POST','api/logout').catch(()=>{})}catch(e){}sSet(null);API.setToken(null);S=[];DB={ints:[],reqs:[],sum:null,loaded:false};st={...st,view:'ov',sel:null,chat:[],err:null,note:typeof m=='string'?m:''};loginView()}
// ---------- Shell ----------
async function load(){const u=sess();if(!u)return true;const c=API.call;
 try{const[a,i,r]=await Promise.all([c('GET','api/students'),c('GET','api/interventions'),c('GET','api/requests')]);S=a;DB.ints=i;DB.reqs=r;DB.sum=u.role=='mentor'?await c('GET','api/summary'):null;DB.loaded=true;st.err=null}
 catch(e){if(e.status==401){logout('Your session expired. Please sign in again.');return false}st.err=e.message}return true}
async function render(){const u=sess();if(!u)return loginView();API.setToken(u.token);if(!DB.loaded){st.err=null;paint(true)}if(await load())paint()}
function paint(loading){const u=sess();if(!u)return loginView();const V=u.role=='student'?SV:MV;if(!NAV[u.role].some(n=>n[0]===st.view))st.view='ov';let h;
 if(loading)h='<div class="card" role="status" aria-live="polite"><h3>Loading your data…</h3><p class="l">Fetching from the LOWKEY API.</p></div>';
 else if(st.err)h=`<div class="card" role="alert"><h3>We couldn't load your data</h3><p>${esc(st.err)}</p><button class="btn sm" onclick="render()">Try again</button></div>`;
 else try{h=V[st.view](u)}catch(e){h=`<div class="card" role="alert"><h3>Something went wrong</h3><p>${esc(e.message)}. Try another page or sign out and back in.</p></div>`}
 $('#root').innerHTML=`<div class="app"><aside><div class="logo"><i>🎓</i>LOWKEY</div><small>${u.role=='student'?'Student space':'Mentor workspace'}</small>${NAV[u.role].map(n=>`<button class="${n[0]==st.view?'on':''}" onclick="go('${n[0]}')">${n[1]}</button>`).join('')}<button onclick="tg()">🌓 Light / dark mode</button><button onclick="logout()" style="margin-top:auto">Logout</button><small class="mode">${API.mode=='server'?'● Live API':'● Offline demo store'}</small></aside><main>${h}</main></div>`}
function go(v){if(!NAV[st.role].some(n=>n[0]===v))return;st.view=v;st.sel=null;render()}
function boot(){const u=sess();if(!u)return loginView();st.role=u.role;render()}
