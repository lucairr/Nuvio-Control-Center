'use strict';
const $ = id=>document.getElementById(id); let csrf='', working=false, toastTimeout, releaseOptions=[], installedNow=null;
function niceDate(date){try{return new Intl.DateTimeFormat(uiLocale(),{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}).format(new Date(date));}catch{return '—'}}
function toast(msg, err=false){let el=$('toast'); el.textContent=msg;el.className='toast show'+(err?' error':'');clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>el.className='toast',5500)}
function text(id,v){$(id).textContent=v==null?'—':String(v)}
function el(tag,cls,txt){const n=document.createElement(tag); if(cls)n.className=cls;if(txt!=null)n.textContent=String(txt);return n}
async function api(url, method='GET',data){const opts={method,credentials:'same-origin',headers:{}};if(method!=='GET'){opts.headers['Content-Type']='application/json';opts.headers['X-CSRF-Token']=csrf;opts.body=JSON.stringify(data||{});}let res=await fetch(url,opts);let payload=await res.json();if(res.status===401){location.href='/';throw Error(t('session_expired'))}if(!res.ok)throw Error(payload.error||t('req_error'));return payload}
async function start(action){try{working=true;buttons(true);await api('/api/actions/'+action,'POST');toast(t('op_started'));poll(350);}catch(e){working=false;buttons(false);toast(e.message,true)}}
function buttons(disabled){['check-btn','update-btn','force-btn'].forEach(id=>$(id).disabled=disabled); updateDowngradeButton();}
function vparts(v){if(typeof v!=='string'||!/^v?\d+(?:\.\d+){1,3}$/.test(v))return null;let p=v.replace(/^v/,'').split('.').map(Number);while(p.length<4)p.push(0);return p}
function isOlder(target,current){const a=vparts(target), b=vparts(current);if(!a||!b)return false;for(let i=0;i<a.length;i++){if(a[i]<b[i])return true;if(a[i]>b[i])return false}return false}
function selectedRelease(){return releaseOptions.find(r=>r.tag===$('downgrade-select').value)}
function updateDowngradeButton(){const choice=selectedRelease();const ok=!!choice&&isOlder(choice.version,installedNow);$('downgrade-btn').disabled=!!working||!ok||!!currentBusy;}
let currentBusy=false;

// --- Minimal, safe Markdown -> DOM (headings, lists, bold, code, https links). Never uses innerHTML.
function mdInline(parent,txt){
 const re=/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https:\/\/[^)\s]+\)|https:\/\/[^\s)]+)/g;let last=0,m;
 while((m=re.exec(txt))){if(m.index>last)parent.append(txt.slice(last,m.index));const t=m[0];
  if(t.startsWith('**'))parent.append(el('strong','',t.slice(2,-2)));
  else if(t.startsWith('`'))parent.append(el('code','',t.slice(1,-1)));
  else{const lm=/^\[([^\]]+)\]\((.+)\)$/.exec(t);const a=el('a','md-link',lm?lm[1]:t.replace(/^https:\/\//,''));a.href=lm?lm[2]:t;a.target='_blank';a.rel='noopener noreferrer';parent.append(a)}
  last=m.index+t.length}
 if(last<txt.length)parent.append(txt.slice(last));
}
function renderMarkdown(container,md,maxChars){
 container.replaceChildren();let src=String(md||'').replace(/\r\n/g,'\n');if(maxChars&&src.length>maxChars)src=src.slice(0,maxChars).replace(/\n[^\n]*$/,'')+'\n…';
 let list=null,para=null;
 for(const raw of src.split('\n')){const line=raw.trim();
  if(!line){list=null;para=null;continue}
  const h=/^#{1,6}\s+(.*)$/.exec(line), li=/^[-*•]\s+(.*)$/.exec(line);
  if(h){list=null;para=null;const n=el('div','md-h');mdInline(n,h[1].replace(/[*_]/g,''));container.append(n)}
  else if(li){para=null;if(!list){list=el('ul','md-ul');container.append(list)}const n=el('li');mdInline(n,li[1]);list.append(n)}
  else{list=null;if(!para){para=el('p','md-p');container.append(para)}else para.append(' ');mdInline(para,line)}
 }
 if(!container.childNodes.length)container.append(el('span','',''));
}
// --- Progress of the running operation
const STEPS=['check','download','verify','install','confirm'];
function renderProgress(state){
 const box=$('progress-box');if(!state.busy){box.hidden=true;return}
 box.hidden=false;const job=state.job||'',step=state.step||'check';
 const installing=['update','force','downgrade'].includes(job)||(job==='auto'&&step!=='check');
 text('progress-title',['check','update','force','downgrade','auto'].includes(job)?t('pt_'+job):t('progress_default'));text('progress-msg',state.message||'');
 const idx=Math.max(0,STEPS.indexOf(step));const steps=$('progress-steps');steps.hidden=!installing;
 steps.querySelectorAll('li').forEach((li,i)=>{li.className=i<idx?'done':i===idx?'current':''});
 const pct=installing?Math.round((idx+0.5)/STEPS.length*100):null;
 $('progress-fill').style.width=pct==null?'':pct+'%';$('progress-fill').classList.toggle('indeterminate',pct==null);
 text('progress-pct',pct==null?'':pct+'%');
}
// --- Highlight the section in view (sidebar + mobile bar)
function setActive(id){document.querySelectorAll('[data-section]').forEach(a=>a.classList.toggle('selected',a.dataset.section===id));
 const keys={overview:'nav_overview',versions:'nav_versions',activity:'nav_activity',console:'nav_console'};const b=document.querySelector('.crumb b');if(b&&keys[id]){b.dataset.i18n=keys[id];b.textContent=t(keys[id])}}
let scrollTick=false;
function updateActiveFromScroll(){scrollTick=false;let cur='overview';const line=window.innerHeight*0.4;
 ['versions','activity','console'].forEach(id=>{const n=$(id);if(n&&n.getBoundingClientRect().top<line)cur=id});
 if(window.innerHeight+window.scrollY>=document.documentElement.scrollHeight-4)cur='console';setActive(cur)}
window.addEventListener('scroll',()=>{if(!scrollTick){scrollTick=true;requestAnimationFrame(updateActiveFromScroll)}},{passive:true});
document.querySelectorAll('[data-section]').forEach(a=>a.addEventListener('click',()=>setActive(a.dataset.section)));
function render(state){
 lastState=state;
 const c=state.config||{}, ins=state.installed||{}, latest=state.latest||{};
 text('tv-name',c.tv_name||'LG webOS');text('tv-ip',c.tv_ip||'—');
 text('tv-connection', state.tv_online===true?t('tv_reachable'):state.tv_online===false?t('tv_offline'):t('tv_tocheck'));
 installedNow=ins.version||null;currentBusy=!!state.busy; updateDowngradeButton();
 text('installed-version',ins.version?'v'+ins.version:'—');
 text('installed-caption',ins.version?t('installed_app'):ins.present?t('installed_unknown'):ins.present===false?t('installed_missing'):t('installed_waiting'));
 text('latest-version',latest.version?'v'+latest.version:'—');text('release-tag',latest.version?'v'+latest.version:'—');
 text('latest-caption',latest.version?t('latest_published'):t('latest_waiting'));
 text('check-caption',state.last_check?t('last_check',{date:niceDate(state.last_check)}):t('last_check_never'));
 const badge=$('overall-badge'), lbl=$('update-label');
 const isError=state.error===true||/^(Errore|Error):/.test(String(state.message||''));
 const st=state.busy?['running','busy']:isError?['error','error']:state.tv_online===false?['offline','warning']:state.update_available===true?['available','warning']:state.update_available===false?['updated','success']:['tocheck',''];
 lbl.dataset.i18n='lbl_'+st[0];lbl.textContent=t('lbl_'+st[0]);
 const bt=$('overall-text');bt.dataset.i18n='badge_'+st[0];bt.textContent=t('badge_'+st[0]);badge.className='header-pill'+(st[1]?' '+st[1]:'');
 if(document.activeElement!==$('auto-toggle'))$('auto-toggle').checked=!!c.auto_update;
 $('github-release').href=(typeof latest.release_url==='string'&&latest.release_url.startsWith('https://github.com/NuvioMedia/NuvioTVSmart/'))?latest.release_url:'https://github.com/NuvioMedia/NuvioTVSmart/releases';
 if(latest.notes!==window.__lastNotes){window.__lastNotes=latest.notes;if(latest.notes)renderMarkdown($('release-notes'),latest.notes,2400);else text('release-notes',t('notes_empty'))}
 renderProgress(state);
 const activities=$('activity-list');activities.replaceChildren();
 const a=(state.history||[]).slice().reverse().slice(0,7);
 if(!a.length)activities.append(el('div','empty',t('act_empty')));
 a.forEach(item=>{const row=el('div','activity-row'), icon=el('div','activity-icon '+(item.outcome==='success'?'success':item.outcome==='error'?'error':'neutral'),item.outcome==='success'?'✓':item.outcome==='error'?'!':'↻');let mid=el('div','activity-center');mid.append(el('strong','',['check','auto','update','force','downgrade'].includes(item.action)?t('act_'+item.action):item.action));mid.append(el('span','',item.details||item.outcome));row.append(icon,mid,el('time','',niceDate(item.time)));activities.append(row)});
 const logs=$('console-log'); logs.replaceChildren();const l=(state.logs||[]).slice().reverse().slice(0,35);
 if(!l.length)logs.append(el('div','empty',t('con_waiting')));
 l.forEach(item=>{const row=el('div','log-line '+(item.kind||'info'));row.append(el('span','log-time',niceDate(item.time)),el('span','log-message',item.message));logs.append(row)});
 if(!state.busy&&working){working=false;toast(state.message||t('op_finished'),isError);}
 buttons(!!state.busy||working);
 $('update-btn').disabled=!!state.busy||working||state.update_available!==true;updateDowngradeButton();
}
async function loadPreviousVersions(){
 const btn=$('versions-load');btn.disabled=true;text('versions-hint',t('versions_loading'));
 try{
  const result=await api('/api/releases');releaseOptions=Array.isArray(result.releases)?result.releases:[];
  versionsLoaded=true;renderVersionOptions();
 }catch(e){text('versions-hint',t('versions_error',{error:e.message}));toast(e.message,true)}
 finally{btn.disabled=false}
}
let versionsLoaded=false;
function renderVersionOptions(){
 const select=$('downgrade-select');const existing=select.value;select.replaceChildren();
 select.append(el('option','',releaseOptions.length?t('versions_select'):t('versions_none')));select.options[0].value='';
 releaseOptions.forEach(r=>{const opt=el('option','',`v${r.version} · ${r.published_at?niceDate(r.published_at):t('versions_official')}`);opt.value=r.tag;select.append(opt)});
 select.disabled=!releaseOptions.length;
 if(existing&&releaseOptions.some(r=>r.tag===existing))select.value=existing;
 text('versions-hint',t('versions_found',{n:releaseOptions.length}));
 renderSelectedRelease();updateDowngradeButton();
}
function renderSelectedRelease(){
 const r=selectedRelease(),info=$('previous-version-info');info.replaceChildren();
 if(!r){info.append(el('span','prev-icon','⌁'),el('span','',t('dg_select_detail')));return}
 const details=el('div','previous-version-details');details.append(el('strong','',`Nuvio TV v${r.version}`));
 details.append(el('span','',`${(r.size/1048576).toFixed(1)} MB · ${r.published_at?niceDate(r.published_at):t('date_unknown')}`));
 const notes=el('div','previous-notes');if(r.notes)renderMarkdown(notes,r.notes,900);else notes.textContent=t('notes_none');details.append(notes);
 info.append(el('span','prev-icon','⇣'),details);updateDowngradeButton();
}
// Poll faster while an operation runs so each step is visible, slower when idle.
let pollTimer=null;
function poll(delay){clearTimeout(pollTimer);pollTimer=setTimeout(async()=>{await refresh();poll()},delay!=null?delay:((currentBusy||working)?1500:5000))}
async function refresh(){try{const d=await api('/api/status');render(d)}catch(e){console.error('status:',e.message)}}
// --- Language: the server setting (shared by logs, history and scheduled checks) wins in the dashboard.
let lastState=null;
function relocalize(){applyI18n();if(lastState)render(lastState);if(versionsLoaded)renderVersionOptions();else renderSelectedRelease();updateClock()}
document.querySelectorAll('[data-lang]').forEach(b=>b.addEventListener('click',async()=>{const lang=b.dataset.lang;if(lang===LANG)return;setLang(lang);relocalize();
 try{await api('/api/settings/language','POST',{language:lang});await refresh()}catch(e){toast(e.message,true)}}));
setLang(storedLang()||browserLang(),false);
(async()=>{try{const s=await api('/api/session');if(!s.authenticated){location.href='/';return}csrf=s.csrf;const picked=pendingLang();pendingLang(null);
 if(picked&&picked!==s.language){setLang(picked);relocalize();try{await api('/api/settings/language','POST',{language:picked})}catch(e){}}
 else if(s.language){setLang(s.language);relocalize()}
 await refresh();poll()}catch(e){location.href='/'}})();
$('check-btn').addEventListener('click',()=>start('check'));
$('update-btn').addEventListener('click',()=>start('update'));
$('force-btn').addEventListener('click',()=>$('force-dialog').showModal());
$('versions-load').addEventListener('click',loadPreviousVersions);
$('downgrade-select').addEventListener('change',renderSelectedRelease);
$('downgrade-btn').addEventListener('click',()=>{
 const r=selectedRelease();if(!r||!isOlder(r.version,installedNow)||currentBusy||working)return;
 text('downgrade-from','v'+installedNow);text('downgrade-to','v'+r.version);
 $('downgrade-ack').checked=false;$('confirm-downgrade').disabled=true;$('downgrade-dialog').showModal();
});
$('downgrade-ack').addEventListener('change',()=>{$('confirm-downgrade').disabled=!$('downgrade-ack').checked});
$('cancel-downgrade').addEventListener('click',()=>$('downgrade-dialog').close());
$('confirm-downgrade').addEventListener('click',async()=>{
 const r=selectedRelease();if(!r||!$('downgrade-ack').checked||!isOlder(r.version,installedNow))return;
 $('downgrade-dialog').close();working=true;buttons(true);
 try{await api('/api/actions/downgrade','POST',{tag:r.tag,confirm:'DOWNGRADE'});toast(t('dg_started',{version:r.version}));poll(350)}
 catch(e){working=false;buttons(false);toast(e.message,true)}
});
$('cancel-force').addEventListener('click',()=>$('force-dialog').close());
$('confirm-force').addEventListener('click',()=>{$('force-dialog').close();start('force')});
$('auto-toggle').addEventListener('change',async e=>{let wanted=e.target.checked;try{await api('/api/settings/auto','POST',{enabled:wanted});toast(wanted?t('auto_on'):t('auto_off'))}catch(err){e.target.checked=!wanted;toast(err.message,true)}});
$('logout').addEventListener('click',async()=>{try{await api('/api/logout','POST')}catch(e){}location.href='/'});
function updateClock(){text('clock',new Intl.DateTimeFormat(uiLocale(),{weekday:'short',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}).format(new Date()))}
setInterval(updateClock,30000);updateClock();
