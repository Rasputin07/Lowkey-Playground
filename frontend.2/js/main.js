/* Settings, theme and start-up. */
async function resetDemo(){try{await API.call('POST','api/reset');toast('Demo data reset.');await render()}catch(x){toast(x.message)}}
function settings(){const u=sess();return head('Settings','Account and display preferences.')+`<div class="card"><p>Signed in as <b>${esc(u.u)}</b> (${u.role}).</p><div class="bar2"><button class="btn sm s" onclick="tg()">Toggle light/dark mode</button>${u.role=='mentor'?'<button class="btn sm s" onclick="resetDemo()">Reset demo data</button>':''}</div><p class="l">Prototype notice: demo authentication (simple hashes, in-memory sessions) is not production security. All data is fictional.</p></div>`}
function tg(){const d=document.documentElement,n=d.dataset.theme=='dark'?'light':'dark';d.dataset.theme=n;ls('lk_th',n)}
document.documentElement.dataset.theme=ls('lk_th')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
boot();
