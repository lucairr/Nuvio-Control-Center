"""Tiny authenticated web application, no third-party Python dependencies."""
import argparse
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import urlparse

try:
    from . import core
    from .locking import available
except ImportError:
    import core
    from locking import available

WEB = Path(__file__).resolve().parent.parent / 'web'
AUTH_FILE = core.STATE_DIR / 'auth.json'
SESSIONS = {}
LOGIN_ATTEMPTS = {}
MUTEX = threading.Lock()
ACTIVE_JOB = None
SESSION_SECONDS = 12 * 3600


def hash_pw(password):
    if len(password) < 12:
        raise ValueError('Usa una password di almeno 12 caratteri.')
    salt = os.urandom(18)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000)
    return {'salt': salt.hex(), 'hash': digest.hex(), 'iterations': 310000}


def check_pw(password):
    d = core.read_json(AUTH_FILE, {})
    try:
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(d['salt']), int(d['iterations']))
        return hmac.compare_digest(digest, bytes.fromhex(d['hash']))
    except (ValueError, KeyError, TypeError):
        return False


def clear_stale_busy():
    """Return True when no operation is really running (and reset the flag)."""
    try:
        if available(core.LOCK_FILE):
            core.update_state(busy=False, job=None,
                              message='Operazione precedente interrotta; stato ripristinato.')
            return True
    except OSError:
        pass
    return False


def redirect_output_if_windowless():
    """pythonw.exe (Windows Task Scheduler) has no console: keep a small log file."""
    if os.sys.stdout is not None and os.sys.stderr is not None:
        return
    log_path = core.STATE_DIR / 'dashboard.log'
    try:
        if log_path.exists() and log_path.stat().st_size > 1024 * 1024:
            os.replace(log_path, core.STATE_DIR / 'dashboard.log.1')
        stream = open(log_path, 'a', encoding='utf-8', buffering=1)
    except OSError:
        return
    os.sys.stdout = stream
    os.sys.stderr = stream


def run_background(action, target_tag=None):
    global ACTIVE_JOB
    def task():
        try:
            core.perform(action, target_tag)
        except Exception:
            pass  # Core persists a detailed error in the event log.
        finally:
            with MUTEX:
                ACTIVE_JOB = None
    with MUTEX:
        if ACTIVE_JOB and ACTIVE_JOB.is_alive():
            return False
        if core.state().get('busy'):
            # A scheduled check killed mid-run (PC shutdown, Task Scheduler time
            # limit, OOM) leaves busy=True forever. If nobody holds the lock,
            # the flag is stale: clear it instead of blocking every button.
            if not clear_stale_busy():
                return False
        ACTIVE_JOB = threading.Thread(target=task, daemon=True, name='nuvio-' + action)
        ACTIVE_JOB.start()
        return True


class Handler(BaseHTTPRequestHandler):
    server_version = 'NuvioControlCenter/' + core.VERSION

    def log_message(self, format, *args):
        # No credential / cookie values in logs.
        if os.sys.stdout is not None:
            print('[http] ' + (format % args), flush=True)

    def headers_common(self, type='application/json; charset=utf-8', length=None):
        self.send_header('Content-Type', type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        if length is not None:
            self.send_header('Content-Length', str(length))

    def reply(self, status, data, cookie=None):
        content = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.headers_common(length=len(content))
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(content)

    def serve_file(self, filename, content_type):
        path = WEB / filename
        try: data = path.read_bytes()
        except OSError:
            return self.reply(404, {'error': 'File non trovato'})
        self.send_response(200)
        self.headers_common(content_type, len(data))
        self.end_headers()
        self.wfile.write(data)

    def sid(self):
        cookie = SimpleCookie()
        try: cookie.load(self.headers.get('Cookie', ''))
        except Exception: return None
        return cookie.get('nuvio_sid').value if 'nuvio_sid' in cookie else None

    def session(self):
        sid = self.sid()
        if not sid: return None
        with MUTEX:
            s = SESSIONS.get(sid)
            if s and s['expires'] > time.time():
                return s
            SESSIONS.pop(sid, None)
        return None

    def require_auth(self, csrf=False):
        s = self.session()
        if not s:
            self.reply(401, {'error': 'Sessione scaduta, effettua l’accesso.'})
            return False
        if csrf:
            token = self.headers.get('X-CSRF-Token', '')
            if not hmac.compare_digest(token, s['csrf']):
                self.reply(403, {'error': 'Token di sicurezza non valido.'})
                return False
            origin = self.headers.get('Origin')
            host = self.headers.get('Host', '')
            if origin and urlparse(origin).netloc != host:
                self.reply(403, {'error': 'Origine della richiesta non valida.'})
                return False
        return True

    def body(self):
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 0 or size > 4096:
                raise ValueError('Corpo richiesta troppo grande.')
            return json.loads(self.rfile.read(size)) if size else {}
        except (ValueError, json.JSONDecodeError):
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/':
            self.serve_file('dashboard.html' if self.session() else 'login.html', 'text/html; charset=utf-8')
        elif path in ('/static/style.css', '/static/app.js', '/static/login.js'):
            filename = path.rsplit('/', 1)[1]
            self.serve_file(filename, 'text/css; charset=utf-8' if filename.endswith('.css') else 'application/javascript; charset=utf-8')
        elif path == '/api/session':
            s = self.session()
            self.reply(200, {'authenticated': bool(s), 'csrf': s['csrf'] if s else None})
        elif path == '/api/status':
            if not self.require_auth(): return
            self.reply(200, core.status_public())
        elif path == '/api/releases':
            if not self.require_auth(): return
            try:
                self.reply(200, {'releases': core.get_previous_releases()})
            except Exception as exc:
                self.reply(502, {'error': 'GitHub non disponibile: ' + str(exc)[:170]})
        else:
            self.reply(404, {'error': 'Pagina inesistente'})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/api/login':
            origin = self.headers.get('Origin')
            if origin and urlparse(origin).netloc != self.headers.get('Host', ''):
                self.reply(403, {'error': 'Origine della richiesta non valida.'})
                return
            data = self.body()
            ip = self.client_address[0]
            with MUTEX:
                attempts = [t for t in LOGIN_ATTEMPTS.get(ip, []) if time.time() - t < 300]
                LOGIN_ATTEMPTS[ip] = attempts
                blocked = len(attempts) >= 7
            if blocked:
                self.reply(429, {'error': 'Troppi tentativi. Riprova tra qualche minuto.'})
                return
            pw = str(data.get('password', ''))[:512]
            if not check_pw(pw):
                with MUTEX: LOGIN_ATTEMPTS.setdefault(ip, []).append(time.time())
                self.reply(401, {'error': 'Password errata.'})
                return
            sid = secrets.token_urlsafe(40)
            csrf = secrets.token_urlsafe(40)
            with MUTEX:
                LOGIN_ATTEMPTS.pop(ip, None)
                SESSIONS[sid] = {'csrf': csrf, 'expires': time.time() + SESSION_SECONDS}
            cookie = f'nuvio_sid={sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_SECONDS}'
            self.reply(200, {'ok': True, 'csrf': csrf}, cookie)
            return
        if not self.require_auth(csrf=True): return
        if path == '/api/logout':
            sid = self.sid()
            with MUTEX: SESSIONS.pop(sid, None)
            self.reply(200, {'ok': True}, 'nuvio_sid=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
            return
        if path in ('/api/actions/check', '/api/actions/update', '/api/actions/force'):
            action = path.rsplit('/', 1)[1]
            if not run_background(action):
                self.reply(409, {'error': 'È già in corso una verifica o installazione.'})
                return
            self.reply(202, {'ok': True, 'message': 'Operazione avviata: ' + action})
            return
        if path == '/api/actions/downgrade':
            payload = self.body()
            tag = payload.get('tag')
            if payload.get('confirm') != 'DOWNGRADE' or not isinstance(tag, str) or not core.STABLE_TAG.fullmatch(tag):
                self.reply(400, {'error': 'Conferma o versione di destinazione non valida.'})
                return
            if not run_background('downgrade', tag):
                self.reply(409, {'error': 'È già in corso una verifica o installazione.'})
                return
            self.reply(202, {'ok': True, 'message': 'Downgrade avviato verso ' + tag})
            return
        if path == '/api/settings/auto':
            enabled = self.body().get('enabled')
            if type(enabled) is not bool:
                self.reply(400, {'error': 'Valore non valido.'})
                return
            cfg = core.read_json(core.CONFIG_FILE, {})
            cfg['auto_update'] = enabled
            core.write_json(core.CONFIG_FILE, cfg)
            core.log('Aggiornamenti automatici ' + ('attivati' if enabled else 'disattivati'))
            self.reply(200, {'ok': True, 'auto_update': enabled})
            return
        self.reply(404, {'error': 'Azione sconosciuta'})


def doctor():
    """Read-only environment report, safe to paste (sanitized) into an issue."""
    import platform
    import socket
    ok = True
    def line(label, value, good=True):
        nonlocal ok
        ok = ok and good
        print(f"[{'OK' if good else '!!'}] {label}: {value}")
    print('Nuvio Control Center ' + core.VERSION + ' - diagnostica')
    line('Sistema', f'{platform.system()} {platform.release()} ({platform.machine()})')
    line('Python', platform.python_version(), tuple(map(int, platform.python_version_tuple()[:2])) >= (3, 9))
    line('Cartella dati', str(core.STATE_DIR), core.STATE_DIR.is_dir())
    line('Configurazione', 'presente' if core.CONFIG_FILE.is_file() else 'MANCANTE', core.CONFIG_FILE.is_file())
    line('Password dashboard', 'impostata' if AUTH_FILE.is_file() else 'MANCANTE (set-password)', AUTH_FILE.is_file())
    for name in ('node', 'ares-install', 'ares-novacom', 'ares-setup-device'):
        path = core.find_cli(name)
        line(name, path or 'NON TROVATO nel PATH', bool(path))
    cfg = core.config()
    online = core.tv_tcp_online(cfg['tv_ip'])
    line('TV ' + cfg['tv_ip'] + ':9922', 'raggiungibile' if online else 'non raggiungibile (TV spenta / Dev Mode off / IP errato)', online)
    try:
        with socket.create_connection(('127.0.0.1' if cfg['web_bind'] == '0.0.0.0' else cfg['web_bind'], cfg['web_port']), timeout=1.5):
            line('Dashboard porta ' + str(cfg['web_port']), 'in ascolto')
    except OSError:
        line('Dashboard porta ' + str(cfg['web_port']), 'non in ascolto (servizio/attivita non avviati?)', False)
    if online and core.find_cli('ares-install'):
        try:
            info = core.get_installed(cfg['tv_device'])
            line('Nuvio sulla TV', info.get('version') or ('presente, versione non leggibile' if info.get('present') else 'non installato'), bool(info.get('present')))
        except RuntimeError as exc:
            line('Associazione TV (' + cfg['tv_device'] + ')', str(exc)[:200], False)
    print('Risultato: ' + ('tutto OK' if ok else 'ci sono punti da sistemare (vedi righe !!)'))
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description='Nuvio Control Center (Linux / Windows)')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('serve')
    sub.add_parser('set-password')
    sub.add_parser('doctor', help='Diagnostica locale (nessuna modifica alla TV)')
    job = sub.add_parser('run')
    job.add_argument('action', choices=('auto', 'check', 'update', 'force'))
    args = parser.parse_args()
    for stream in (os.sys.stdout, os.sys.stderr):
        try:
            stream.reconfigure(errors='replace')
        except (AttributeError, ValueError):
            pass
    core.STATE_DIR.mkdir(parents=True, exist_ok=True)
    if args.command in ('serve', 'run'):
        redirect_output_if_windowless()
    if args.command == 'set-password':
        import getpass
        pw = getpass.getpass('Password dashboard (min. 12 caratteri): ')
        if pw != getpass.getpass('Ripeti password: '):
            parser.error('Le password non coincidono.')
        core.write_json(AUTH_FILE, hash_pw(pw))
        print('Password impostata.')
    elif args.command == 'doctor':
        raise SystemExit(doctor())
    elif args.command == 'run':
        try: core.perform(args.action)
        except Exception as exc: parser.error(str(exc))
    elif args.command == 'serve':
        # Recover from a hard restart during installation; do not clear an
        # active job running in the independent systemd timer process.
        if core.state().get('busy'):
            clear_stale_busy()
        if not AUTH_FILE.is_file():
            parser.error('Password dashboard non configurata: esegui set-password.')
        cfg = core.config()
        # Clear stale flags only if there is no active external operation.
        address = (cfg['web_bind'], cfg['web_port'])
        if os.sys.stdout is not None:
            print(f'Dashboard in ascolto su {address[0]}:{address[1]}', flush=True)
        ThreadingHTTPServer(address, Handler).serve_forever(poll_interval=0.5)


if __name__ == '__main__':
    main()
