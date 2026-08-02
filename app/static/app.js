const sessionId = crypto.randomUUID();
const chat = document.querySelector('#chat');
const form = document.querySelector('#form');
const message = document.querySelector('#message');

async function loadStats(){
  const s = await fetch('/api/stats').then(r=>r.json());
  const fields=[['Events',s.events],['Failed',s.failed_events],['High risk',s.high_risk_events],['Playbooks',s.playbooks],['ML model',s.model_ready?'Ready':'On demand']];
  document.querySelector('#stats').innerHTML=fields.map(([k,v])=>`<div class="stat"><b>${v}</b><span>${k}</span></div>`).join('');
}
function add(role,text,traces=[]){
  const el=document.createElement('article'); el.className=`message ${role}`;
  el.innerHTML=role==='assistant'?`<div class="avatar">S</div><div><strong>SentinelOps</strong><p>${text}</p>${traces.map(t=>`<details class="trace"><summary>${t.tool}: ${t.summary}</summary><pre>${JSON.stringify(t.evidence,null,2)}</pre></details>`).join('')}</div>`:`<div><p>${text}</p></div>`;
  chat.appendChild(el); chat.scrollTop=chat.scrollHeight;
}
async function ask(text){
  add('user',text); message.value='';
  const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,message:text})});
  const data=await res.json(); add('assistant',data.answer,data.traces||[]); loadStats();
}
form.addEventListener('submit',e=>{e.preventDefault(); if(message.value.trim()) ask(message.value.trim());});
document.querySelectorAll('[data-prompt]').forEach(b=>b.addEventListener('click',()=>ask(b.dataset.prompt)));
document.querySelector('#upload').addEventListener('click',async()=>{const f=document.querySelector('#file').files[0];if(!f)return;const fd=new FormData();fd.append('file',f);const r=await fetch('/api/playbooks',{method:'POST',body:fd});const d=await r.json();document.querySelector('#uploadStatus').textContent=r.ok?`${d.filename} indexed`:d.detail;loadStats();});
loadStats();
