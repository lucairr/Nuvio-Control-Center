"""Server-side messages (state, logs, history, API errors, CLI) in Italian and English.

The language comes from config.json ("language": "it" | "en"). Messages are stored
already translated, so log lines keep the language they were written in.
"""

LANGUAGES = ('it', 'en')
DEFAULT_LANGUAGE = 'it'  # existing installations predate the setting and are Italian

MESSAGES = {
    # --- generic / state
    'waiting_first_check': ('In attesa della prima verifica', 'Waiting for the first check'),
    'error_prefix': ('Errore: ', 'Error: '),
    'unknown_error': ('errore sconosciuto', 'unknown error'),
    'stale_cleared': ('Operazione precedente interrotta; stato ripristinato.', 'Previous operation was interrupted; state restored.'),
    # --- LG CLI
    'cli_missing': ('Comando {name} assente. Installa @webos-tools/cli e verifica il PATH del servizio.',
                    'Command {name} not found. Install @webos-tools/cli and check the service PATH.'),
    'cli_timeout': ('{name}: timeout dopo {timeout} secondi', '{name}: timed out after {timeout} seconds'),
    # --- GitHub releases
    'gh_endpoint': ('Endpoint GitHub non autorizzato.', 'GitHub endpoint not allowed.'),
    'gh_too_big': ('Risposta GitHub troppo grande.', 'GitHub response too large.'),
    'gh_bad_format': ('Formato release GitHub non valido.', 'Invalid GitHub release format.'),
    'gh_unstable': ('Release non stabile o tag non riconosciuto.', 'Release is not stable or the tag is not recognised.'),
    'gh_one_ipk': ('Atteso un solo IPK ufficiale; trovati: {count}.', 'Expected exactly one official IPK; found: {count}.'),
    'gh_bad_url': ('URL IPK ufficiale non riconosciuto.', 'Official IPK URL not recognised.'),
    'gh_tag_mismatch': ('IPK non corrispondente al tag della release.', 'IPK does not match the release tag.'),
    'gh_size': ('Dimensione IPK inattesa (limite 250 MB).', 'Unexpected IPK size (limit 250 MB).'),
    'gh_bad_list': ('Elenco release GitHub non valido.', 'Invalid GitHub release list.'),
    'bad_selected_version': ('Versione selezionata non valida.', 'Invalid selected version.'),
    'release_mismatch': ('La release ricevuta non corrisponde alla versione richiesta.', 'The release received does not match the requested version.'),
    # --- IPK checks
    'ipk_no_ar': ('IPK non valido: intestazione AR assente.', 'Invalid IPK: missing AR header.'),
    'ipk_bad_header': ('IPK non valido: intestazione archivio corrotta.', 'Invalid IPK: corrupted archive header.'),
    'ipk_bad_size': ('IPK non valido: dimensione archivio.', 'Invalid IPK: archive size.'),
    'ipk_member_big': ('IPK non valido: componente troppo grande.', 'Invalid IPK: component too large.'),
    'ipk_appinfo_big': ('appinfo.json troppo grande.', 'appinfo.json too large.'),
    'ipk_unreadable': ('Contenuto IPK non leggibile: {error}', 'IPK content not readable: {error}'),
    'ipk_no_appinfo': ('Il file IPK non contiene appinfo.json per {app}.', 'The IPK file has no appinfo.json for {app}.'),
    'ipk_version': ('Versione IPK {actual} diversa dalla release {expected}.', 'IPK version {actual} differs from release {expected}.'),
    # --- download
    'dl_redirect': ('Redirect download su host inatteso.', 'Download redirected to an unexpected host.'),
    'dl_too_big': ('Download IPK oltre 250 MB.', 'IPK download over 250 MB.'),
    'dl_size': ('Dimensione download non corretta: {got} != {expected}.', 'Wrong download size: {got} != {expected}.'),
    'dl_sha_format': ('Formato SHA-256 ufficiale non riconosciuto.', 'Official SHA-256 format not recognised.'),
    'dl_sha_mismatch': ('Hash SHA-256 dell’IPK diverso da GitHub.', 'IPK SHA-256 hash differs from GitHub.'),
    # --- operation flow
    'unknown_action': ('Azione sconosciuta', 'Unknown action'),
    'already_running': ('Operazione già in esecuzione (dashboard o timer).', 'An operation is already running (dashboard or timer).'),
    'bad_downgrade_tag': ('Tag del downgrade non valido.', 'Invalid downgrade tag.'),
    'checking': ('Controllo in corso…', 'Checking…'),
    'started_check': ('Avviato: verifica manuale', 'Started: manual check'),
    'started_update': ('Avviato: aggiornamento', 'Started: update'),
    'started_force': ('Avviato: installazione forzata', 'Started: forced installation'),
    'started_auto': ('Avviato: verifica programmata', 'Started: scheduled check'),
    'started_downgrade': ('Avviato: ripristino versione {tag}', 'Started: restoring version {tag}'),
    'release_found': ('Release trovata: {version}', 'Release found: {version}'),
    'github_version': ('GitHub: versione {version}', 'GitHub: version {version}'),
    'tv_unreachable': ('TV non raggiungibile sulla porta Developer Mode 9922.', 'TV not reachable on Developer Mode port 9922.'),
    'tv_unreachable_detail': ('TV spenta, Developer Mode assente o rete non raggiungibile.', 'TV off, Developer Mode disabled or network unreachable.'),
    'tv_unreachable_log': ('TV non raggiungibile, nessuna installazione.', 'TV not reachable, nothing installed.'),
    'not_installed': ('Nuvio non risulta installato: interrotto per sicurezza. Usa l’installer ufficiale per il primo avvio.',
                      'Nuvio does not appear to be installed: stopped for safety. Use the official installer for the first installation.'),
    'dg_unknown_installed': ('Downgrade bloccato: versione installata non identificabile.', 'Downgrade blocked: installed version cannot be identified.'),
    'dg_not_older': ('Downgrade bloccato: seleziona una versione strettamente precedente a quella sulla TV.',
                     'Downgrade blocked: select a version strictly older than the one on the TV.'),
    'dg_auto_off': ('Aggiornamenti automatici disattivati per mantenere la versione ripristinata.',
                    'Automatic updates turned off to keep the restored version.'),
    'dg_requested': ('Downgrade manuale richiesto: {current} → {target}.', 'Manual downgrade requested: {current} → {target}.'),
    'update_available': ('Aggiornamento disponibile: {version}', 'Update available: {version}'),
    'up_to_date': ('Già aggiornato.', 'Already up to date.'),
    'version_unreadable': ('App rilevata, versione non leggibile: installazione automatica bloccata.',
                           'App detected but its version is not readable: automatic installation blocked.'),
    'check_done_auto_off': ('Controllo completato. Installazione automatica disattivata.', 'Check completed. Automatic installation is off.'),
    'nothing_to_install': ('Nessun aggiornamento da installare.', 'No update to install.'),
    'cannot_verify_installed': ('Impossibile verificare la versione installata: installazione bloccata. Usa “Forza” solo dopo verifica.',
                                'Cannot verify the installed version: installation blocked. Use “Force” only after checking.'),
    'tv_newer': ('La TV ha una versione più nuova di GitHub: downgrade bloccato.', 'The TV has a newer version than GitHub: downgrade blocked.'),
    'downloading': ('Download IPK ufficiale {version}…', 'Downloading official IPK {version}…'),
    'downloaded': ('IPK scaricato ({mb} MB), SHA-256 {sha}…', 'IPK downloaded ({mb} MB), SHA-256 {sha}…'),
    'verifying': ('Verifica del pacchetto scaricato…', 'Checking the downloaded package…'),
    'verified': ('Pacchetto verificato: {app} v{version}', 'Package verified: {app} v{version}'),
    'installing': ('Installazione sulla TV in corso (non spegnerla)…', 'Installing on the TV (do not turn it off)…'),
    'lg_installer': ('Installer LG: {output}', 'LG installer: {output}'),
    'confirming': ('Controllo della versione installata…', 'Checking the installed version…'),
    'unverified': ('Installazione eseguita, ma verifica versione non conclusiva: controlla Nuvio sulla TV.',
                   'Installation done, but the version check was inconclusive: check Nuvio on the TV.'),
    'dg_done': ('Downgrade completato alla versione {version}.', 'Downgrade completed to version {version}.'),
    'updated': ('Nuvio aggiornato correttamente alla versione {version}.', 'Nuvio successfully updated to version {version}.'),
    # --- web API
    'file_not_found': ('File non trovato', 'File not found'),
    'session_expired': ('Sessione scaduta, effettua l’accesso.', 'Session expired, please sign in.'),
    'bad_csrf': ('Token di sicurezza non valido.', 'Invalid security token.'),
    'bad_origin': ('Origine della richiesta non valida.', 'Invalid request origin.'),
    'github_unavailable': ('GitHub non disponibile: {error}', 'GitHub not available: {error}'),
    'page_not_found': ('Pagina inesistente', 'Page not found'),
    'too_many_attempts': ('Troppi tentativi. Riprova tra qualche minuto.', 'Too many attempts. Try again in a few minutes.'),
    'wrong_password': ('Password errata.', 'Wrong password.'),
    'busy': ('È già in corso una verifica o installazione.', 'A check or installation is already running.'),
    'op_started': ('Operazione avviata: {action}', 'Operation started: {action}'),
    'bad_confirm': ('Conferma o versione di destinazione non valida.', 'Invalid confirmation or target version.'),
    'dg_started': ('Downgrade avviato verso {tag}', 'Downgrade started to {tag}'),
    'bad_value': ('Valore non valido.', 'Invalid value.'),
    'auto_on': ('Aggiornamenti automatici attivati', 'Automatic updates turned on'),
    'auto_off': ('Aggiornamenti automatici disattivati', 'Automatic updates turned off'),
    'language_set': ('Lingua impostata: italiano', 'Language set: English'),
    # --- command line
    'cli_doctor_help': ('Diagnostica locale (nessuna modifica alla TV)', 'Local diagnostics (nothing is changed on the TV)'),
    'pw_prompt': ('Password dashboard (min. 12 caratteri): ', 'Dashboard password (min. 12 characters): '),
    'pw_repeat': ('Ripeti password: ', 'Repeat password: '),
    'pw_mismatch': ('Le password non coincidono.', 'Passwords do not match.'),
    'pw_set': ('Password impostata.', 'Password set.'),
    'pw_missing': ('Password dashboard non configurata: esegui set-password.', 'Dashboard password not configured: run set-password.'),
    'listening': ('Dashboard in ascolto su {host}:{port}', 'Dashboard listening on {host}:{port}'),
    # --- doctor
    'dr_title': ('diagnostica', 'diagnostics'),
    'dr_system': ('Sistema', 'System'),
    'dr_data_dir': ('Cartella dati', 'Data folder'),
    'dr_config': ('Configurazione', 'Configuration'),
    'dr_present': ('presente', 'present'),
    'dr_missing': ('MANCANTE', 'MISSING'),
    'dr_password': ('Password dashboard', 'Dashboard password'),
    'dr_pw_set': ('impostata', 'set'),
    'dr_pw_missing': ('MANCANTE (set-password)', 'MISSING (set-password)'),
    'dr_not_in_path': ('NON TROVATO nel PATH', 'NOT FOUND in PATH'),
    'dr_reachable': ('raggiungibile', 'reachable'),
    'dr_unreachable': ('non raggiungibile (TV spenta / Dev Mode off / IP errato)', 'not reachable (TV off / Dev Mode off / wrong IP)'),
    'dr_port': ('Dashboard porta {port}', 'Dashboard port {port}'),
    'dr_listening': ('in ascolto', 'listening'),
    'dr_not_listening': ('non in ascolto (servizio/attivita non avviati?)', 'not listening (service/task not running?)'),
    'dr_nuvio': ('Nuvio sulla TV', 'Nuvio on the TV'),
    'dr_version_unreadable': ('presente, versione non leggibile', 'present, version not readable'),
    'dr_not_installed': ('non installato', 'not installed'),
    'dr_pairing': ('Associazione TV ({device})', 'TV pairing ({device})'),
    'dr_language': ('Lingua', 'Language'),
    'dr_result_ok': ('Risultato: tutto OK', 'Result: all OK'),
    'dr_result_ko': ('Risultato: ci sono punti da sistemare (vedi righe !!)', 'Result: some items need attention (see !! lines)'),
}


def normalize(lang):
    lang = str(lang or '').lower()[:2]
    return lang if lang in LANGUAGES else DEFAULT_LANGUAGE


def t(key, lang=None, **params):
    pair = MESSAGES[key]
    text = pair[LANGUAGES.index(normalize(lang))]
    return text.format(**params) if params else text
