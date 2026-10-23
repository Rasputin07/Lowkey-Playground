/* API client. Uses the LOWKEY server (/api/*) when reachable; otherwise falls back to an offline demo store
   (same router, data kept in this browser). The UI shows which mode is active. */
const API=(()=>{let mode=null,tok=null,mem=null;const clone=o=>JSON.parse(JSON.stringify(o));Core.seed=SEED;
const load=()=>{if(mem)return mem;try{mem=JSON.parse(localStorage.getItem('lk_db'))}catch(e){}if(!mem)mem=clone(SEED);mem.sess=mem.sess||{};return mem};
const persist=()=>{try{localStorage.setItem('lk_db',JSON.stringify(mem))}catch(e){}};
async function call(method,url,body){
 if(mode!=='offline'){let r,d;try{r=await fetch(url,{method,headers:{'Content-Type':'application/json',...(tok?{Authorization:'Bearer '+tok}:{})},body:body?JSON.stringify(body):undefined});if(!(r.headers.get('content-type')||'').includes('json'))throw 0;d=await r.json()}
  catch(e){if(mode==='server')throw new Error('Cannot reach the LOWKEY server. Check that it is running, then try again.');mode='offline'}
  if(mode!=='offline'){mode='server';if(!r.ok)throw Object.assign(new Error(d.error||'Request failed'),{status:r.status});return d}}
 const x=Core.route(load(),persist,method,url,body,tok);if(x.status>=400)throw Object.assign(new Error(x.data.error),{status:x.status});return x.data}
return{call,setToken:t=>{tok=t},get mode(){return mode}}})();
