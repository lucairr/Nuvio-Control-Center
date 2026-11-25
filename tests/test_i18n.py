"""Translation completeness (server + web UI) and language switching."""
import json
import re
import shutil
import string
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from nuvio import core, i18n, server
from tests.test_http import HttpTests

WEB = Path(__file__).resolve().parent.parent / 'web'


def placeholders(text):
    return sorted(name for _, name, _, _ in string.Formatter().parse(text) if name)


class ServerMessagesTests(unittest.TestCase):
    def test_every_message_has_both_languages_with_same_placeholders(self):
        for key, pair in i18n.MESSAGES.items():
            self.assertEqual(len(pair), len(i18n.LANGUAGES), key)
            it, en = pair
            self.assertTrue(it.strip() and en.strip(), key)
            self.assertEqual(placeholders(it), placeholders(en), key)

    def test_normalize_and_fallback(self):
        self.assertEqual(i18n.normalize('EN-us'), 'en')
        self.assertEqual(i18n.normalize('fr'), i18n.DEFAULT_LANGUAGE)
        self.assertEqual(i18n.normalize(None), i18n.DEFAULT_LANGUAGE)
        self.assertEqual(i18n.t('updated', 'en', version='1.2.10'), 'Nuvio successfully updated to version 1.2.10.')
        self.assertEqual(i18n.t('updated', 'it', version='1.2.10'), 'Nuvio aggiornato correttamente alla versione 1.2.10.')

    def test_every_tr_key_used_in_code_exists(self):
        root = Path(__file__).resolve().parent.parent / 'nuvio'
        used = set()
        for f in root.glob('*.py'):
            used |= set(re.findall(r"\btr\('([a-z0-9_]+)'", f.read_text(encoding='utf-8')))
            used |= set(re.findall(r"\bT\('([a-z0-9_]+)'", f.read_text(encoding='utf-8')))
        missing = sorted(k for k in used if k not in i18n.MESSAGES and not k.endswith('_'))
        self.assertEqual(missing, [])
        for action in ('check', 'update', 'force', 'auto', 'downgrade'):
            self.assertIn('started_' + action, i18n.MESSAGES)


@unittest.skipUnless(shutil.which('node'), 'node not available')
class WebDictionaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = "const fs=require('fs');eval(fs.readFileSync(process.argv[1],'utf8')+';globalThis.__I=I18N');console.log(JSON.stringify(globalThis.__I))"
        out = subprocess.run(['node', '-e', script, str(WEB / 'i18n.js')], capture_output=True, text=True, check=True).stdout
        cls.dict = json.loads(out)

    def test_same_keys_and_placeholders_in_it_and_en(self):
        it, en = self.dict['it'], self.dict['en']
        self.assertEqual(sorted(it), sorted(en))
        for key in it:
            self.assertTrue(it[key] and en[key], key)
            self.assertEqual(sorted(re.findall(r'\{(\w+)\}', it[key])), sorted(re.findall(r'\{(\w+)\}', en[key])), key)

    def test_every_key_referenced_by_html_and_js_exists(self):
        keys = set(self.dict['it'])
        refs = set()
        for name in ('dashboard.html', 'login.html'):
            refs |= set(re.findall(r'data-i18n(?:-title|-placeholder|-aria|-doc-title)?="([a-z0-9_]+)"', (WEB / name).read_text(encoding='utf-8')))
        for name in ('app.js', 'login.js'):
            refs |= set(re.findall(r"\bt\('([a-z0-9_]+)'", (WEB / name).read_text(encoding='utf-8')))
        dynamic = {p + s for p, ss in {
            'pt_': ('check', 'update', 'force', 'downgrade', 'auto'),
            'act_': ('check', 'auto', 'update', 'force', 'downgrade'),
            'lbl_': ('running', 'error', 'offline', 'available', 'updated', 'tocheck'),
            'badge_': ('running', 'error', 'offline', 'available', 'updated', 'tocheck')}.items() for s in ss}
        refs = {r for r in refs if not r.endswith('_')}  # prefixes like t('act_'+action)
        self.assertEqual(sorted((refs | dynamic) - keys), [])

    def test_no_italian_left_outside_the_dictionary(self):
        for name in ('app.js', 'login.js'):
            src = (WEB / name).read_text(encoding='utf-8')
            self.assertIsNone(re.search(r"'[^'\n]*[àèéìòù][^'\n]*'", src), name)


class EnglishFlowTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.td = tempfile.TemporaryDirectory()
        path = Path(self.td.name)
        self.patches = [mock.patch.object(core, 'STATE_DIR', path), mock.patch.object(core, 'STATE_FILE', path / 'state.json'),
                        mock.patch.object(core, 'CONFIG_FILE', path / 'config.json'), mock.patch.object(core, 'LOCK_FILE', path / 'op.lock')]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.td.cleanup()

    def run_check(self, lang):
        core.write_json(core.CONFIG_FILE, {'tv_ip': '192.0.2.1', 'tv_device': 'nuvio-lg', 'language': lang})
        release = {'version': '1.2.10', 'name': 'n.ipk', 'size': 1, 'notes': '', 'release_url': 'x', 'url': 'x', 'sha256': ''}
        with mock.patch.object(core, 'get_release', return_value=release), \
             mock.patch.object(core, 'tv_tcp_online', return_value=True), \
             mock.patch.object(core, 'get_installed', return_value={'present': True, 'version': '1.2.10', 'source': 't'}):
            core.perform('check')
        return core.state()

    def test_check_messages_follow_the_configured_language(self):
        st = self.run_check('en')
        self.assertEqual(st['message'], 'Already up to date.')
        self.assertEqual(st['logs'][0]['message'], 'Started: manual check')
        self.assertFalse(st['error'])
        st = self.run_check('it')
        self.assertEqual(st['message'], 'Già aggiornato.')

    def test_error_flag_and_prefix(self):
        core.write_json(core.CONFIG_FILE, {'tv_ip': '192.0.2.1', 'language': 'en'})
        with mock.patch.object(core, 'get_release', side_effect=RuntimeError(core.tr('gh_bad_format'))):
            with self.assertRaises(RuntimeError):
                core.perform('check')
        st = core.state()
        self.assertTrue(st['error'])
        self.assertEqual(st['message'], 'Error: Invalid GitHub release format.')

    def test_missing_language_keeps_italian_for_existing_installs(self):
        core.write_json(core.CONFIG_FILE, {'tv_ip': '192.0.2.1'})
        self.assertEqual(core.config()['language'], 'it')
        self.assertEqual(core.state()['message'], 'In attesa della prima verifica')


class LanguageEndpointTests(HttpTests):
    def login(self):
        status, headers, obj = self.request('POST', '/api/login', {'password': 'my-long-demo-password'})
        return {'Cookie': headers['Set-Cookie'].split(';')[0], 'X-CSRF-Token': obj['csrf']}

    def test_switch_language_and_errors_follow_it(self):
        h = self.login()
        status, _, obj = self.request('POST', '/api/settings/language', {'language': 'en'}, h)
        self.assertEqual((status, obj['language']), (200, 'en'))
        self.assertEqual(core.config()['language'], 'en')
        status, _, obj = self.request('GET', '/api/session', None, {'Cookie': h['Cookie']})
        self.assertEqual(obj['language'], 'en')
        status, _, obj = self.request('GET', '/api/status', None, {'Cookie': h['Cookie']})
        self.assertEqual(obj['config']['language'], 'en')
        status, _, obj = self.request('POST', '/api/login', {'password': 'wrong-password-123'})
        self.assertEqual((status, obj['error']), (401, 'Wrong password.'))

    def test_rejects_unknown_language_and_requires_csrf(self):
        h = self.login()
        status, _, _ = self.request('POST', '/api/settings/language', {'language': 'fr'}, h)
        self.assertEqual(status, 400)
        status, _, _ = self.request('POST', '/api/settings/language', {'language': 'en'}, {'Cookie': h['Cookie']})
        self.assertEqual(status, 403)
        self.assertEqual(core.config()['language'], 'it')

    def test_i18n_script_is_served(self):
        import http.client
        con = http.client.HTTPConnection('127.0.0.1', self.srv.server_port, timeout=2)
        con.request('GET', '/static/i18n.js')
        resp = con.getresponse()
        body = resp.read().decode()
        con.close()
        self.assertEqual(resp.status, 200)
        self.assertIn('const I18N', body)


if __name__ == '__main__':
    unittest.main()
