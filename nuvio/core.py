"""Nuvio Control Center core - standard library only.
Runs only known commands from the official LG CLI. No remote shell from the web.
"""
import contextlib
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import subprocess
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request
from . import i18n
from .locking import exclusive

APP_ID = 'space.nuvio.webos'
REPO = 'NuvioMedia/NuvioTVSmart'
API_URL = 'https://api.github.com/repos/' + REPO + '/releases/latest'
RELEASES_URL = 'https://api.github.com/repos/' + REPO + '/releases?per_page=100'
TAG_RELEASE_URL = 'https://api.github.com/repos/' + REPO + '/releases/tags/'
STATE_DIR = Path(os.environ.get('NUVIO_HOME') or (str(Path.home() / '.nuvio-control-center') if os.name == 'nt' else '/var/lib/nuvio-updater'))
CONFIG_FILE = STATE_DIR / 'config.json'
STATE_FILE = STATE_DIR / 'state.json'
LOCK_FILE = STATE_DIR / 'operation.lock'
MAX_IPK = 250 * 1024 * 1024
VERSION = '1.2.0-beta'
UA = 'Nuvio-Control-Center/' + VERSION + ' (community updater; LG webOS)'
VER = re.compile(r'^v?(\d+(?:\.\d+){1,3})(?:[-+][A-Za-z0-9.]+)?$')
STABLE_TAG = re.compile(r'^v?\d+(?:\.\d+){1,3}$')


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


def version_key(v):
    m = VER.fullmatch(str(v or '').strip())
    if not m:
        return None
    nums = tuple(int(n) for n in m.group(1).split('.'))
    return nums + (0,) * (4 - len(nums))


def is_windows():
    return os.name == 'nt'


# On Windows a file that another process (dashboard, scheduled check,
# antivirus, backup agent) has open briefly cannot be replaced/read and raises
# PermissionError. Retry for ~2 s instead of failing in the middle of an install.
_RETRIES = 40
_RETRY_DELAY = 0.05


def read_json(path, default):
    for attempt in range(_RETRIES):
        try:
            return json.loads(Path(path).read_text(encoding='utf-8'))
        except PermissionError:
            if attempt == _RETRIES - 1:
                return default
            time.sleep(_RETRY_DELAY)
        except (FileNotFoundError, ValueError, OSError):
            return default
    return default


def _replace_with_retry(src, dst):
    for attempt in range(_RETRIES):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt == _RETRIES - 1:
                raise
            time.sleep(_RETRY_DELAY)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.nuvio-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.chmod(temp, 0o600)
        _replace_with_retry(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def config():
    data = read_json(CONFIG_FILE, {})
    return {'tv_ip': data.get('tv_ip', '127.0.0.1'),
            'tv_device': data.get('tv_device', 'nuvio-lg'),
            'tv_name': data.get('tv_name', 'LG webOS TV'),
            'auto_update': bool(data.get('auto_update', False)),
            'web_port': int(data.get('web_port', 8765)),
            'web_bind': data.get('web_bind', '127.0.0.1'),
            'language': i18n.normalize(data.get('language'))}


def tr(key, **params):
    """Translate a server message into the configured language."""
    return i18n.t(key, i18n.normalize(read_json(CONFIG_FILE, {}).get('language')), **params)


def state():
    d = read_json(STATE_FILE, {})
    return {'latest': d.get('latest'), 'installed': d.get('installed'),
            'last_check': d.get('last_check'), 'last_success': d.get('last_success'),
            'busy': bool(d.get('busy')), 'job': d.get('job'), 'step': d.get('step'),
            'message': d.get('message') or tr('waiting_first_check'), 'error': bool(d.get('error')),
            'history': d.get('history', [])[-30:], 'logs': d.get('logs', [])[-120:],
            'tv_online': d.get('tv_online'), 'update_available': d.get('update_available'),
            'download_size': d.get('download_size')}


def update_state(**kwargs):
    d = state()
    d.update(kwargs)
    write_json(STATE_FILE, d)


def log(message, kind='info'):
    d = state()
    d['logs'].append({'time': now(), 'kind': kind, 'message': str(message)[:600]})
    d['logs'] = d['logs'][-120:]
    write_json(STATE_FILE, d)
    if sys.stdout is not None:
        line = f'[{now()}] [{kind.upper()}] {message}'
        try:
            print(line, flush=True)
        except UnicodeEncodeError:
            # Windows consoles (cp1252/cp850) cannot print arrows, curly quotes, etc.
            # A log line must never abort an install.
            enc = getattr(sys.stdout, 'encoding', None) or 'ascii'
            print(line.encode(enc, 'replace').decode(enc, 'replace'), flush=True)


def history(action, outcome, version='', details=''):
    d = state()
    d['history'].append({'time': now(), 'action': action, 'outcome': outcome,
                         'version': version, 'details': str(details)[:300]})
    d['history'] = d['history'][-30:]
    write_json(STATE_FILE, d)


def find_cli(name):
    """Locate an LG CLI command. On Windows also look in the per-user npm
    global folder, which Task Scheduler / pythonw may not have in PATH."""
    binary = shutil.which(name)
    if binary or not is_windows():
        return binary
    folders = []
    configured = read_json(CONFIG_FILE, {}).get('cli_dir')
    if isinstance(configured, str) and configured:
        folders.append(Path(configured))
    if os.environ.get('NUVIO_NPM_PREFIX'):
        folders.append(Path(os.environ['NUVIO_NPM_PREFIX']))
    if os.environ.get('APPDATA'):
        folders.append(Path(os.environ['APPDATA']) / 'npm')
    for folder in folders:
        for ext in ('.cmd', '.exe'):
            candidate = folder / (name + ext)
            if candidate.is_file():
                return str(candidate)
    return None


def cli(name, args, timeout=45):
    binary = find_cli(name)
    if not binary:
        raise RuntimeError(tr('cli_missing', name=name))
    env = os.environ.copy()
    # Linux systemd: the LG CLI profile and SSH key live under the private service home.
    # Windows: the pairing belongs to the interactive user's profile.
    if not is_windows():
        env['HOME'] = str(STATE_DIR)
    extra = {}
    if is_windows():
        # Dashboard runs under pythonw.exe: without this flag every LG CLI call
        # would flash a black console window on the user's desktop.
        extra['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
    try:
        p = subprocess.run([binary, *args], stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, errors='replace', timeout=timeout, env=env, **extra)
    except subprocess.TimeoutExpired:
        raise RuntimeError(tr('cli_timeout', name=name, timeout=timeout))
    out = ((p.stdout or '') + '\n' + (p.stderr or '')).strip()
    if p.returncode:
        raise RuntimeError(f'{name}: ' + (out[-700:] or tr('unknown_error')))
    return out


def tv_tcp_online(ip):
    try:
        with socket.create_connection((ip, 9922), timeout=2.5):
            return True
    except (OSError, ValueError):
        return False


def parse_installed(output):
    """Conservative: recognizes version only when tied to the exact app ID.
    Other apps' versions can never be confused with Nuvio's.
    """
    for candidate in [output.strip(), output[output.find('['):] if '[' in output else '']:
        try:
            payload = json.loads(candidate)
            objects = payload if isinstance(payload, list) else [payload]
            def walk(x):
                if isinstance(x, dict):
                    if x.get('id') == APP_ID or x.get('appId') == APP_ID:
                        v = x.get('version') or x.get('appVersion')
                        return True, str(v) if version_key(v) else None
                    for nested in x.values():
                        r = walk(nested)
                        if r[0]: return r
                if isinstance(x, list):
                    for item in x:
                        r = walk(item)
                        if r[0]: return r
                return False, None
            for obj in objects:
                r = walk(obj)
                if r[0]: return r
        except (ValueError, TypeError):
            pass
    # Common CLI output: package id and adjacent version or ID on its own line.
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if APP_ID not in line:
            continue
        if not re.search(r'(?<![\w.-])' + re.escape(APP_ID) + r'(?![\w.-])', line):
            continue
        fragment = ' '.join(lines[max(0, i - 1): i + 3])
        # Explicit version: <version>, version=, version : (case-insensitive)
        m = re.search(r'\bversion\s*[:=]\s*["\']?(v?\d+\.\d+(?:\.\d+){0,2})', fragment, re.I)
        if m and version_key(m.group(1)):
            return True, m.group(1)
        # table output: "space.nuvio.webos  1.2.3" only on the same line
        m = re.search(re.escape(APP_ID) + r'\s+([vV]?\d+\.\d+(?:\.\d+){0,2})\b', line)
        if m and version_key(m.group(1)):
            return True, m.group(1)
        return True, None
    return False, None


def get_installed(device):
    output = cli('ares-install', ['--device', device, '--listfull'], timeout=40)
    present, version = parse_installed(output)
    if present and version:
        return {'present': True, 'version': version, 'source': 'listfull'}
    # If listfull did not expose a version, read the app's own metadata in
    # Developer Mode (read-only, exact known path; no arbitrary web commands).
    if present or APP_ID in output:
        remote_path = '/media/developer/apps/usr/palm/applications/' + APP_ID + '/appinfo.json'
        try:
            raw = cli('ares-novacom', ['--device', device, '--run', 'cat ' + remote_path], timeout=30)
            match = re.search(r'\{[^{}]*\"id\"\s*:\s*\"' + re.escape(APP_ID) + r'\"[^{}]*\}', raw, re.S)
            if match:
                obj = json.loads(match.group(0))
                v = obj.get('version')
                if version_key(v):
                    return {'present': True, 'version': v, 'source': 'appinfo'}
        except (RuntimeError, ValueError):
            pass
    # If listfull did not contain an ID, check short list (presence only).
    short = cli('ares-install', ['--device', device, '--list'], timeout=40)
    present = present or APP_ID in short
    return {'present': present, 'version': version, 'source': 'listfull' if version else 'presence-only'}


def github_json(url):
    """Read release metadata from GitHub's fixed API endpoints only."""
    if not url.startswith('https://api.github.com/repos/' + REPO + '/releases'):
        raise RuntimeError(tr('gh_endpoint'))
    req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json',
                           'User-Agent': UA, 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(req, timeout=20) as response:
        raw = response.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise RuntimeError(tr('gh_too_big'))
    return json.loads(raw)


def parse_release(data):
    if not isinstance(data, dict):
        raise RuntimeError(tr('gh_bad_format'))
    tag = str(data.get('tag_name', ''))
    if not STABLE_TAG.fullmatch(tag) or data.get('draft') or data.get('prerelease'):
        raise RuntimeError(tr('gh_unstable'))
    assets = [a for a in data.get('assets', [])
              if isinstance(a, dict) and str(a.get('name', '')).lower().endswith('.ipk')]
    if len(assets) != 1:
        raise RuntimeError(tr('gh_one_ipk', count=len(assets)))
    asset = assets[0]
    url = str(asset.get('browser_download_url', ''))
    prefix = 'https://github.com/' + REPO + '/releases/download/'
    if not url.startswith(prefix) or not url.lower().endswith('.ipk'):
        raise RuntimeError(tr('gh_bad_url'))
    # Tag/path must be consistent: prevents accidentally installing an IPK from another release.
    url_parts = urllib.parse.urlsplit(url)
    relative = url_parts.path[len('/' + REPO + '/releases/download/'):]
    download_tag = urllib.parse.unquote(relative.split('/', 1)[0])
    if download_tag != tag or url_parts.query or url_parts.fragment:
        raise RuntimeError(tr('gh_tag_mismatch'))
    size = int(asset.get('size', 0))
    if size < 100 or size > MAX_IPK:
        raise RuntimeError(tr('gh_size'))
    return {'version': tag.lstrip('v'), 'tag': tag, 'name': asset['name'],
            'size': size, 'url': url, 'sha256': str(asset.get('digest') or ''),
            'notes': str(data.get('body') or '')[:8000],
            'published_at': str(data.get('published_at') or ''),
            'release_url': 'https://github.com/' + REPO + '/releases/tag/' + urllib.parse.quote(tag, safe='')}


def get_release():
    return parse_release(github_json(API_URL))


def get_previous_releases():
    """List up to 100 stable GitHub releases offering exactly one official webOS IPK.
    Listing is read-only, without connection to or changes on the TV.
    """
    rows = github_json(RELEASES_URL)
    if not isinstance(rows, list):
        raise RuntimeError(tr('gh_bad_list'))
    out, seen = [], set()
    for data in rows[:100]:
        try:
            item = parse_release(data)
        except (RuntimeError, TypeError, ValueError, KeyError):
            continue
        if item['version'] in seen:
            continue
        seen.add(item['version'])
        out.append({k: item[k] for k in ('tag', 'version', 'name', 'size',
                                        'published_at', 'release_url', 'notes')})
    out.sort(key=lambda x: version_key(x['version']), reverse=True)
    return out


def get_release_by_tag(tag):
    """Always resolve the selected version server-side; never accept arbitrary download URLs."""
    if not isinstance(tag, str) or len(tag) > 48 or not STABLE_TAG.fullmatch(tag):
        raise ValueError(tr('bad_selected_version'))
    data = github_json(TAG_RELEASE_URL + urllib.parse.quote(tag, safe=''))
    release = parse_release(data)
    if release['tag'] != tag:
        raise RuntimeError(tr('release_mismatch'))
    return release


def verify_ipk(path, expected_version):
    """Inspect AR -> data.tar.* -> appinfo.json, without extracting any file."""
    with open(path, 'rb') as f:
        if f.read(8) != b'!<arch>\n':
            raise RuntimeError(tr('ipk_no_ar'))
        count = 0
        found = None
        while True:
            header = f.read(60)
            if not header: break
            if len(header) != 60 or header[58:60] != b'`\n':
                raise RuntimeError(tr('ipk_bad_header'))
            name = header[:16].decode('ascii', 'replace').strip().rstrip('/')
            try: size = int(header[48:58].decode('ascii').strip())
            except ValueError: raise RuntimeError(tr('ipk_bad_size'))
            if size < 0 or size > MAX_IPK:
                raise RuntimeError(tr('ipk_member_big'))
            count += 1
            if name.startswith('data.tar'):
                segment = f.read(size)
                try:
                    with tarfile.open(fileobj=io.BytesIO(segment), mode='r:*') as tar:
                        for member in tar:
                            if member.name.rstrip('/').endswith('/appinfo.json') and member.isfile():
                                if member.size > 1024 * 1024:
                                    raise RuntimeError(tr('ipk_appinfo_big'))
                                with tar.extractfile(member) as app_file:
                                    obj = json.load(app_file)
                                if obj.get('id') == APP_ID:
                                    found = obj
                                    break
                except (tarfile.TarError, ValueError, KeyError) as exc:
                    raise RuntimeError(tr('ipk_unreadable', error=str(exc)))
            else:
                f.seek(size, 1)
            if size % 2:
                f.seek(1, 1)
        if count < 2 or found is None:
            raise RuntimeError(tr('ipk_no_appinfo', app=APP_ID))
        actual = str(found.get('version', ''))
        if version_key(actual) != version_key(expected_version):
            raise RuntimeError(tr('ipk_version', actual=actual, expected=expected_version))
        return {'id': found['id'], 'version': actual}


def download_release(release, dest):
    req = urllib.request.Request(release['url'], headers={'User-Agent': UA, 'Accept': 'application/octet-stream'})
    h = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(req, timeout=55) as response, open(dest, 'wb') as f:
        final_host = urllib.parse.urlparse(response.geturl()).hostname or ''
        if final_host not in ('github.com', 'release-assets.githubusercontent.com') and not final_host.endswith('.githubusercontent.com'):
            raise RuntimeError(tr('dl_redirect'))
        while True:
            chunk = response.read(512 * 1024)
            if not chunk: break
            total += len(chunk)
            if total > MAX_IPK:
                raise RuntimeError(tr('dl_too_big'))
            h.update(chunk)
            f.write(chunk)
    if total != release['size']:
        raise RuntimeError(tr('dl_size', got=total, expected=release['size']))
    digest = release.get('sha256') or ''
    if digest:
        if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest):
            raise RuntimeError(tr('dl_sha_format'))
        if h.hexdigest().lower() != digest.split(':', 1)[1].lower():
            raise RuntimeError(tr('dl_sha_mismatch'))
    return h.hexdigest()


def status_public():
    c = config()
    d = state()
    return {**d, 'config': {'tv_ip': c['tv_ip'], 'tv_name': c['tv_name'],
                            'tv_device': c['tv_device'], 'auto_update': c['auto_update'],
                            'language': c['language']},
            'app_id': APP_ID, 'repo': REPO}


def perform(action, target_tag=None):
    if action not in ('check', 'update', 'force', 'auto', 'downgrade'):
        raise ValueError(tr('unknown_action'))
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        guard = exclusive(LOCK_FILE)
        guard.__enter__()
    except BlockingIOError:
        raise RuntimeError(tr('already_running'))
    try:
        if action == 'downgrade' and (not isinstance(target_tag, str) or not STABLE_TAG.fullmatch(target_tag)):
            raise ValueError(tr('bad_downgrade_tag'))
        c = config()
        update_state(busy=True, error=False, job=action, step='check', message=tr('checking'))
        try:
            log(tr('started_' + action, tag=str(target_tag)) if action == 'downgrade' else tr('started_' + action))
            release = get_release()
            update_state(latest={k: release[k] for k in ('version', 'name', 'size', 'notes', 'release_url')},
                         download_size=release['size'], last_check=now(),
                         message=tr('release_found', version=release['version']))
            log(tr('github_version', version=release['version']))
            is_online = tv_tcp_online(c['tv_ip'])
            update_state(tv_online=is_online)
            if not is_online:
                update_state(installed={'present': None, 'version': None, 'source': 'offline'}, update_available=None,
                             message=tr('tv_unreachable'))
                history(action, 'offline', release['version'], tr('tv_unreachable_detail'))
                log(tr('tv_unreachable_log'), 'warn')
                return
            installed = get_installed(c['tv_device'])
            update_state(installed=installed)
            installed_version = installed['version']
            latest_version = release['version']
            cmp_local, cmp_remote = version_key(installed_version), version_key(latest_version)
            has_update = (cmp_local < cmp_remote) if cmp_local and cmp_remote else None
            update_state(update_available=has_update)
            if not installed['present']:
                raise RuntimeError(tr('not_installed'))
            install_release = release
            if action == 'downgrade':
                if not installed['present'] or not cmp_local:
                    raise RuntimeError(tr('dg_unknown_installed'))
                install_release = get_release_by_tag(target_tag)
                target_version = install_release['version']
                if not version_key(target_version) < cmp_local:
                    raise RuntimeError(tr('dg_not_older'))
                # Keep the manually selected older version: daily auto-update must
                # not overwrite it on the next scheduled run.
                cfg_raw = read_json(CONFIG_FILE, {})
                if cfg_raw.get('auto_update'):
                    cfg_raw['auto_update'] = False
                    write_json(CONFIG_FILE, cfg_raw)
                    log(tr('dg_auto_off'), 'warn')
                log(tr('dg_requested', current=installed_version, target=target_version))
            if action == 'check':
                msg = (tr('update_available', version=latest_version) if has_update else
                       tr('up_to_date') if has_update is False else
                       tr('version_unreadable'))
                update_state(message=msg)
                history(action, 'ok', latest_version, msg)
                log(msg)
                return
            if action == 'auto' and not c['auto_update']:
                msg = tr('check_done_auto_off')
                update_state(message=msg)
                history(action, 'ok', latest_version, msg)
                log(msg)
                return
            if action in ('auto', 'update') and has_update is not True:
                msg = (tr('nothing_to_install') if has_update is False else
                       tr('cannot_verify_installed'))
                update_state(message=msg)
                history(action, 'skipped', latest_version, msg)
                log(msg, 'warn' if has_update is None else 'info')
                return
            if action != 'downgrade' and cmp_local and cmp_remote and cmp_local > cmp_remote:
                raise RuntimeError(tr('tv_newer'))
            update_state(step='download', message=tr('downloading', version=install_release['version']))
            with tempfile.TemporaryDirectory(prefix='nuvio-ipk-', dir=str(STATE_DIR)) as td:
                path = Path(td) / 'nuvio.ipk'
                checksum = download_release(install_release, path)
                log(tr('downloaded', mb=round(path.stat().st_size / 1048576, 1), sha=checksum[:16]))
                update_state(step='verify', message=tr('verifying'))
                metadata = verify_ipk(path, install_release['version'])
                log(tr('verified', app=metadata['id'], version=metadata['version']))
                update_state(step='install', message=tr('installing'))
                out = cli('ares-install', ['--device', c['tv_device'], str(path)], timeout=300)
                log(tr('lg_installer', output=out[-300:].replace('\n', ' ')))
            update_state(step='confirm', message=tr('confirming'))
            post = get_installed(c['tv_device'])
            update_state(installed=post, update_available=(version_key(post['version']) < cmp_remote) if version_key(post['version']) and cmp_remote else None)
            if version_key(post['version']) != version_key(install_release['version']):
                msg = tr('unverified')
                history(action, 'unverified', install_release['version'], msg)
                update_state(message=msg)
                log(msg, 'warn')
            else:
                msg = tr('dg_done' if action == 'downgrade' else 'updated', version=install_release['version'])
                update_state(last_success=now(), message=msg)
                history(action, 'success', install_release['version'], msg)
                log(msg, 'success')
        except Exception as exc:
            msg = str(exc)
            update_state(error=True, message=tr('error_prefix') + msg[:240])
            history(action, 'error', str(target_tag) if action == 'downgrade' else '', msg)
            log(msg, 'error')
            raise
        finally:
            update_state(busy=False, job=None, step=None)
    finally:
        guard.__exit__(None, None, None)
