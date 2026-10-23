/* Mentor actions: record interventions, update status/outcomes, AI drafts. Mentors review everything; nothing is auto-sent. */
function prefill(sid,t){$('#is').value=sid;$('#it').value=t;$('#in').focus()}
async function addInt(e){e&&e.preventDefault&&e.preventDefault();const sid=$('#is').value,d=$('#id').value,f=$('#if').value;if(!sid)return $('#ie').textContent='Choose a student.';if(!d)return $('#ie').textContent='Choose a due date.';if(f&&f<d)return $('#ie').textContent='Follow-up date must be on or after the due date.';
 try{await API.call('POST','api/interventions',{sid,type:$('#it').value,due:d,fu:f,notes:$('#in').value,vis:$('#iv').checked});toast('Intervention saved.');await render()}catch(x){$('#ie').textContent=x.message}}
async function setSt(id,v){try{await API.call('PATCH','api/interventions/'+id,{status:v});toast('Status updated.');await render()}catch(x){toast(x.message)}}
async function setOut(id,v){try{await API.call('PATCH','api/interventions/'+id,{outcome:v});toast('Outcome saved.');await render()}catch(x){toast(x.message)}}
async function draft(k){const sid=$('#as').value;if(!sid)return;$('#mo').textContent='Generating draft…';try{const r=await API.call('POST','api/ai',{kind:k,sid});$('#mo').textContent=r.text+'\n\n[Mock AI draft – review before use]';$('#rv').checked=false}catch(x){$('#mo').textContent='The AI assistant is temporarily unavailable. Please try again shortly. ('+x.message+')'}}
function sendD(){$('#me').textContent=$('#rv').checked?'Marked ready. (Demo: nothing is actually sent.)':'Review the draft and tick the box first.'}
