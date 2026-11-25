'use strict';
// UI texts (Italian / English). Server messages (logs, history, state) are translated server-side.
const I18N = {
 it: {
  // navigation
  crumb_ws: 'Workspace', nav_overview: 'Panoramica', nav_versions: 'Versioni precedenti', nav_activity: 'Attività', nav_console: 'Console',
  mnav_versions: 'Versioni', mnav_aria: 'Sezioni', lang_aria: 'Lingua', logout_title: 'Esci',
  side_auto: 'AUTOMAZIONE', side_title: 'La tua TV, sempre aggiornata.', side_text: 'Gestione Nuvio da un server Linux o da un PC Windows.',
  support_a: 'Progetto gratuito. Ti è utile?', support_b: 'Offrimi un caffè', footer_local: 'Un progetto locale per LG webOS', footer_source: 'Fonte', footer_support: 'Ti è utile? Offrimi un caffè',
  // header + hero
  h1_a: 'Il tuo Nuvio, ', h1_b: 'sotto controllo.', subtitle: 'Gestisci gli aggiornamenti di Nuvio TV senza aprire webOS Dev Manager.',
  badge_init: 'Inizializzazione', kicker_device: 'DISPOSITIVO COLLEGATO', tv_unknown: 'Stato sconosciuto',
  btn_check: 'Verifica aggiornamenti', btn_update: 'Installa aggiornamento',
  progress_default: 'Operazione in corso', step_check: 'Verifica', step_download: 'Download', step_verify: 'Controllo IPK', step_install: 'Installazione', step_confirm: 'Conferma',
  pt_check: 'Verifica in corso', pt_update: 'Aggiornamento in corso', pt_force: 'Reinstallazione in corso', pt_downgrade: 'Ripristino versione in corso', pt_auto: 'Controllo programmato in corso',
  // stats
  stat_tv: 'VERSIONE SULLA TV', stat_latest: 'ULTIMA RELEASE', stat_status: 'STATO AGGIORNAMENTO',
  installed_none: 'Non ancora rilevata', installed_app: 'Applicazione installata', installed_unknown: 'Versione non identificata', installed_missing: 'Nuvio non rilevato', installed_waiting: 'In attesa di verifica',
  latest_from: 'Da GitHub ufficiale', latest_published: 'Release ufficiale pubblicata', latest_waiting: 'In attesa di GitHub',
  last_check: 'Ultima verifica: {date}', last_check_never: 'Ultima verifica: mai',
  tv_reachable: 'Developer Mode raggiungibile', tv_offline: 'Offline / non raggiungibile', tv_tocheck: 'Stato da verificare',
  lbl_running: 'In corso…', badge_running: 'Operazione in corso', lbl_error: 'Errore verifica', badge_error: 'Attenzione richiesta',
  lbl_offline: 'TV offline', badge_offline: 'TV non raggiungibile', lbl_available: 'Disponibile', badge_available: 'Nuova versione',
  lbl_updated: 'Aggiornata', badge_updated: 'Tutto aggiornato', lbl_tocheck: 'Da verificare', badge_tocheck: 'Verifica richiesta',
  // automation + notes
  auto_over: 'CONTROLLO AUTOMATICO', auto_h2: 'Il pilota automatico', auto_p: 'Il dispositivo host verifica ogni giorno la presenza di nuove versioni. Quando abilitato, installa solo aggiornamenti sicuri e verificati.',
  auto_label: 'Installazione automatica', auto_sched: 'Controllo quotidiano · ore 19:30', auto_aria: 'Attiva aggiornamenti automatici',
  auto_note: "Se la TV è spenta o la versione non è leggibile, l'installazione viene saltata.",
  notes_h2: "Cosa c'è di nuovo", notes_by: 'NuvioMedia · Release ufficiale', notes_empty: 'Le novità della release compariranno dopo la prima verifica.',
  // previous versions
  dg_h2: 'Versioni precedenti', dg_chip: 'SOLO MANUALE',
  dg_intro: 'Se una nuova release di Nuvio presenta problemi, puoi provare a installare un IPK precedente dal repository ufficiale. Nessun downgrade viene avviato automaticamente. Un ripristino disattiva anche i successivi aggiornamenti automatici.',
  dg_label: 'VERSIONE DA RIPRISTINARE', dg_load: '↻ Carica release', dg_select_placeholder: 'Carica le release da GitHub',
  dg_hint: 'Sono mostrate solo le release ufficiali che includono un singolo pacchetto IPK.', dg_select_detail: 'Seleziona una versione per visualizzarne i dettagli.',
  dg_action_title: 'Ripristino controllato', dg_action_p: "La TV deve essere raggiungibile e la versione attuale deve essere riconosciuta. Il pacchetto viene verificato prima dell'installazione.",
  dg_btn: 'Installa versione precedente →', dg_warning: '⚠ Le versioni più vecchie potrebbero non leggere alcune impostazioni create dalle versioni nuove. Non viene eseguita una disinstallazione automatica.',
  versions_loading: 'Caricamento release ufficiali da GitHub…', versions_select: 'Seleziona una versione…', versions_none: 'Nessuna release IPK disponibile',
  versions_official: 'release ufficiale', versions_found: '{n} release ufficiali con IPK trovate · sono installabili solo le versioni precedenti a quella presente sulla TV.',
  versions_error: 'Impossibile caricare le release: {error}', date_unknown: 'data non indicata', notes_none: 'Nessuna nota disponibile per questa release.',
  // activity + console
  act_over: 'EVENTI RECENTI', act_h2: 'Cronologia attività', act_chip: 'ULTIMI 30', act_empty: 'Nessuna operazione eseguita.',
  act_check: 'Verifica aggiornamenti', act_auto: 'Verifica programmata', act_update: 'Installazione aggiornamento', act_force: 'Reinstallazione forzata', act_downgrade: 'Ripristino versione precedente',
  con_over: 'DIAGNOSTICA', con_h2: 'Console e comandi', force_title: 'Reinstallazione manuale',
  force_p: "Reinstalla l'IPK ufficiale più recente anche se la versione installata è già aggiornata. Non disinstalla l'app.",
  force_btn: 'Forza installazione ↗', con_waiting: 'In attesa di eventi…',
  // dialogs
  cancel: 'Annulla', fd_kicker: 'AZIONE MANUALE', fd_h2: 'Forzare la reinstallazione?',
  fd_p: "Scaricherò nuovamente l'ultimo IPK ufficiale di Nuvio e tenterò di installarlo sulla TV. Evita di avviare l'operazione mentre stai guardando qualcosa.", fd_confirm: 'Sì, reinstalla',
  dd_kicker: 'RIPRISTINO MANUALE', dd_h2: 'Confermi il downgrade?', dd_from: 'Stai per passare da', dd_to: 'a',
  dd_risk: "L'operazione potrebbe interrompere Nuvio e modificare la compatibilità delle impostazioni salvate. Nessuna disinstallazione verrà eseguita automaticamente.",
  dd_auto: 'Gli aggiornamenti automatici saranno disattivati', dd_until: 'finché non li riattivi.', dd_ack: 'Ho capito i rischi e desidero procedere.', dd_confirm: 'Conferma downgrade',
  // toasts + errors
  op_started: 'Operazione avviata.', op_finished: 'Operazione terminata', session_expired: 'Sessione scaduta.', req_error: 'Errore durante la richiesta.',
  dg_started: 'Downgrade verso v{version} avviato. Controlla i log.', auto_on: 'Installazione automatica attivata.', auto_off: 'Installazione automatica disattivata.',
  // login
  login_doc_title: 'Accedi — Nuvio Control Center', login_h1a: 'La tua TV.', login_h1b: 'Il tuo controllo.',
  login_p: 'Accedi alla dashboard per gestire gli aggiornamenti Nuvio della tua LG webOS.', login_label: 'PASSWORD DASHBOARD', login_ph: 'Inserisci la password',
  login_btn: 'Accedi al Control Center', login_busy: 'Accesso in corso…', login_failed: 'Accesso non riuscito.', login_wrong: 'Password errata.',
  login_too_many: 'Troppi tentativi. Riprova tra qualche minuto.', login_footer: 'Protetto da sessione locale'
 },
 en: {
  crumb_ws: 'Workspace', nav_overview: 'Overview', nav_versions: 'Previous versions', nav_activity: 'Activity', nav_console: 'Console',
  mnav_versions: 'Versions', mnav_aria: 'Sections', lang_aria: 'Language', logout_title: 'Sign out',
  side_auto: 'AUTOMATION', side_title: 'Your TV, always up to date.', side_text: 'Manage Nuvio from a Linux server or a Windows PC.',
  support_a: 'Free project. Find it useful?', support_b: 'Buy me a coffee', footer_local: 'A local project for LG webOS', footer_source: 'Source', footer_support: 'Find it useful? Buy me a coffee',
  h1_a: 'Your Nuvio, ', h1_b: 'under control.', subtitle: 'Manage Nuvio TV updates without opening webOS Dev Manager.',
  badge_init: 'Starting', kicker_device: 'CONNECTED DEVICE', tv_unknown: 'Unknown status',
  btn_check: 'Check for updates', btn_update: 'Install update',
  progress_default: 'Operation in progress', step_check: 'Check', step_download: 'Download', step_verify: 'IPK check', step_install: 'Install', step_confirm: 'Confirm',
  pt_check: 'Checking', pt_update: 'Updating', pt_force: 'Reinstalling', pt_downgrade: 'Restoring version', pt_auto: 'Scheduled check running',
  stat_tv: 'VERSION ON TV', stat_latest: 'LATEST RELEASE', stat_status: 'UPDATE STATUS',
  installed_none: 'Not detected yet', installed_app: 'App installed', installed_unknown: 'Version not identified', installed_missing: 'Nuvio not detected', installed_waiting: 'Waiting for a check',
  latest_from: 'From official GitHub', latest_published: 'Official release published', latest_waiting: 'Waiting for GitHub',
  last_check: 'Last check: {date}', last_check_never: 'Last check: never',
  tv_reachable: 'Developer Mode reachable', tv_offline: 'Offline / not reachable', tv_tocheck: 'Status to be checked',
  lbl_running: 'Running…', badge_running: 'Operation in progress', lbl_error: 'Check error', badge_error: 'Attention needed',
  lbl_offline: 'TV offline', badge_offline: 'TV not reachable', lbl_available: 'Available', badge_available: 'New version',
  lbl_updated: 'Up to date', badge_updated: 'All up to date', lbl_tocheck: 'To be checked', badge_tocheck: 'Check needed',
  auto_over: 'AUTOMATIC CHECK', auto_h2: 'Autopilot', auto_p: 'The host checks for new versions every day. When enabled, it installs only safe, verified updates.',
  auto_label: 'Automatic installation', auto_sched: 'Daily check · 19:30', auto_aria: 'Turn on automatic updates',
  auto_note: 'If the TV is off or its version cannot be read, the installation is skipped.',
  notes_h2: "What's new", notes_by: 'NuvioMedia · Official release', notes_empty: 'Release notes will appear after the first check.',
  dg_h2: 'Previous versions', dg_chip: 'MANUAL ONLY',
  dg_intro: 'If a new Nuvio release has problems, you can try installing an older IPK from the official repository. No downgrade ever starts automatically. A restore also turns off later automatic updates.',
  dg_label: 'VERSION TO RESTORE', dg_load: '↻ Load releases', dg_select_placeholder: 'Load releases from GitHub',
  dg_hint: 'Only official releases with a single IPK package are shown.', dg_select_detail: 'Select a version to see its details.',
  dg_action_title: 'Controlled restore', dg_action_p: 'The TV must be reachable and its current version must be recognised. The package is verified before installing.',
  dg_btn: 'Install previous version →', dg_warning: '⚠ Older versions may not read some settings created by newer ones. Nothing is uninstalled automatically.',
  versions_loading: 'Loading official releases from GitHub…', versions_select: 'Select a version…', versions_none: 'No IPK release available',
  versions_official: 'official release', versions_found: '{n} official releases with an IPK found · only versions older than the one on the TV can be installed.',
  versions_error: 'Could not load releases: {error}', date_unknown: 'date not given', notes_none: 'No notes available for this release.',
  act_over: 'RECENT EVENTS', act_h2: 'Activity history', act_chip: 'LAST 30', act_empty: 'No operations yet.',
  act_check: 'Update check', act_auto: 'Scheduled check', act_update: 'Update install', act_force: 'Forced reinstall', act_downgrade: 'Previous version restore',
  con_over: 'DIAGNOSTICS', con_h2: 'Console and commands', force_title: 'Manual reinstall',
  force_p: 'Reinstalls the latest official IPK even if the installed version is already up to date. It does not uninstall the app.',
  force_btn: 'Force install ↗', con_waiting: 'Waiting for events…',
  cancel: 'Cancel', fd_kicker: 'MANUAL ACTION', fd_h2: 'Force a reinstall?',
  fd_p: "I'll download the latest official Nuvio IPK again and try to install it on the TV. Avoid starting it while you are watching something.", fd_confirm: 'Yes, reinstall',
  dd_kicker: 'MANUAL RESTORE', dd_h2: 'Confirm the downgrade?', dd_from: 'You are about to go from', dd_to: 'to',
  dd_risk: 'This may interrupt Nuvio and affect the compatibility of saved settings. Nothing will be uninstalled automatically.',
  dd_auto: 'Automatic updates will be turned off', dd_until: 'until you turn them back on.', dd_ack: 'I understand the risks and want to proceed.', dd_confirm: 'Confirm downgrade',
  op_started: 'Operation started.', op_finished: 'Operation finished', session_expired: 'Session expired.', req_error: 'Request failed.',
  dg_started: 'Downgrade to v{version} started. Check the logs.', auto_on: 'Automatic installation turned on.', auto_off: 'Automatic installation turned off.',
  login_doc_title: 'Sign in — Nuvio Control Center', login_h1a: 'Your TV.', login_h1b: 'Your control.',
  login_p: 'Sign in to the dashboard to manage Nuvio updates on your LG webOS TV.', login_label: 'DASHBOARD PASSWORD', login_ph: 'Enter the password',
  login_btn: 'Sign in to Control Center', login_busy: 'Signing in…', login_failed: 'Sign-in failed.', login_wrong: 'Wrong password.',
  login_too_many: 'Too many attempts. Try again in a few minutes.', login_footer: 'Protected by a local session'
 }
};
let LANG = 'it';
function t(key, params) {
 let s = (I18N[LANG] && I18N[LANG][key]) || I18N.it[key] || key;
 if (params) for (const k of Object.keys(params)) s = s.split('{' + k + '}').join(String(params[k]));
 return s;
}
function uiLocale() { return LANG === 'en' ? 'en-GB' : 'it-IT'; }
function storedLang() { try { return localStorage.getItem('nuvio_lang'); } catch (e) { return null; } }
function browserLang() { return /^it\b/i.test(navigator.language || '') ? 'it' : 'en'; }
// Static texts: data-i18n (text), data-i18n-title / -placeholder / -aria (attributes).
function applyI18n(root) {
 const r = root || document;
 r.querySelectorAll('[data-i18n]').forEach(n => { n.textContent = t(n.dataset.i18n); });
 r.querySelectorAll('[data-i18n-title]').forEach(n => { n.title = t(n.dataset.i18nTitle); });
 r.querySelectorAll('[data-i18n-placeholder]').forEach(n => { n.placeholder = t(n.dataset.i18nPlaceholder); });
 r.querySelectorAll('[data-i18n-aria]').forEach(n => { n.setAttribute('aria-label', t(n.dataset.i18nAria)); });
 if (document.body && document.body.dataset.i18nDocTitle) document.title = t(document.body.dataset.i18nDocTitle);
 document.documentElement.lang = LANG;
 document.querySelectorAll('[data-lang]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lang === LANG)));
}
// persist=false for automatic choices (browser language, server default): only a click is remembered.
function setLang(lang, persist) {
 LANG = I18N[lang] ? lang : 'it';
 if (persist !== false) { try { localStorage.setItem('nuvio_lang', LANG); } catch (e) { /* storage unavailable */ } }
 applyI18n();
}
// A language picked on the sign-in page is applied to the server setting right after login.
function pendingLang(value) {
 try {
  if (value === undefined) return sessionStorage.getItem('nuvio_lang_pending');
  if (value) sessionStorage.setItem('nuvio_lang_pending', value); else sessionStorage.removeItem('nuvio_lang_pending');
 } catch (e) { return null; }
 return null;
}
