'use strict';
// Language on the sign-in page: this browser's choice, else the server setting, else the browser language.
const savedLang = storedLang();
setLang(savedLang || browserLang(), false);
fetch('/api/session', {credentials: 'same-origin'}).then(r => r.json()).then(s => {
 if (!savedLang && s && s.language) setLang(s.language, false);
}).catch(() => {});
document.querySelectorAll('[data-lang]').forEach(b => b.addEventListener('click', () => { setLang(b.dataset.lang); pendingLang(b.dataset.lang); }));

document.getElementById('login-form').addEventListener('submit', async e => {
 e.preventDefault();
 const b = e.target.querySelector('button'), label = document.getElementById('login-btn-text'), err = document.getElementById('login-error');
 b.disabled = true; label.textContent = t('login_busy'); err.textContent = '';
 try {
  const r = await fetch('/api/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({password: document.getElementById('password').value})});
  const d = await r.json();
  if (!r.ok) throw new Error(r.status === 401 ? t('login_wrong') : r.status === 429 ? t('login_too_many') : (d.error || t('login_failed')));
  window.location.href = '/';
 } catch (ex) {
  err.textContent = ex.message; b.disabled = false; label.textContent = t('login_btn');
 }
});
