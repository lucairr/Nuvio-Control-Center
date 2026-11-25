document.getElementById('login-form').addEventListener('submit', async e => {
 e.preventDefault(); const b=e.target.querySelector('button'), err=document.getElementById('login-error');
 b.disabled=true; b.textContent='Accesso in corso…'; err.textContent='';
 try { const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:document.getElementById('password').value})}); const d=await r.json(); if(!r.ok) throw new Error(d.error||'Accesso non riuscito.'); window.location.href='/'; }
 catch(e){err.textContent=e.message; b.disabled=false; b.innerHTML='Accedi al Control Center <span>↗</span>'}
});
