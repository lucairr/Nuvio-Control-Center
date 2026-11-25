import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock
from nuvio import core
from nuvio import server


def archive_entry(name, blob):
    name = (name + '/').ljust(16)[:16]
    header = (name + '0'.ljust(12) + '0'.ljust(6) + '0'.ljust(6)
              + '100644'.ljust(8) + str(len(blob)).ljust(10) + '`\n').encode()
    assert len(header) == 60
    return header + blob + (b'\n' if len(blob) % 2 else b'')


def make_ipk(path, app_id=core.APP_ID, version='1.4.0'):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as t:
        content = json.dumps({'id': app_id, 'version': version}).encode()
        info = tarfile.TarInfo('./usr/palm/applications/' + app_id + '/appinfo.json')
        info.size = len(content)
        t.addfile(info, io.BytesIO(content))
    path.write_bytes(b'!<arch>\n' + archive_entry('debian-binary', b'2.0\n')
                     + archive_entry('data.tar.gz', buf.getvalue()))


class UnitTests(unittest.TestCase):
    def test_versions(self):
        self.assertTrue(core.version_key('1.3.11') < core.version_key('1.4.0'))
        self.assertEqual(core.version_key('v1.4.0'), core.version_key('1.4.0'))
        self.assertIsNone(core.version_key('unavailable'))

    def test_parse_installed_json(self):
        self.assertEqual(core.parse_installed('[{"id":"space.nuvio.webos","version":"1.3.11"}]'), (True, '1.3.11'))
        self.assertEqual(core.parse_installed('[{"id":"com.other.app","version":"11.2.0"}]'), (False, None))

    def test_parse_installed_table(self):
        self.assertEqual(core.parse_installed('ID VERSION\nspace.nuvio.webos 1.3.11\n'), (True, '1.3.11'))
        self.assertEqual(core.parse_installed('space.nuvio.webos\n'), (True, None))

    def test_ipk_inspection(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'test.ipk'
            make_ipk(path)
            self.assertEqual(core.verify_ipk(path, '1.4.0')['id'], core.APP_ID)
            with self.assertRaises(RuntimeError): core.verify_ipk(path, '1.3.0')
            make_ipk(path, app_id='evil.app')
            with self.assertRaises(RuntimeError): core.verify_ipk(path, '1.4.0')
            path.write_text('fake IPK')
            with self.assertRaises(RuntimeError): core.verify_ipk(path, '1.4.0')

    def test_password_hashing(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(server, 'AUTH_FILE', Path(td) / 'auth.json'):
                core.write_json(server.AUTH_FILE, server.hash_pw('password-lunga-123'))
                self.assertTrue(server.check_pw('password-lunga-123'))
                self.assertFalse(server.check_pw('non-e-la-password'))
        with self.assertRaises(ValueError): server.hash_pw('short')

    def test_check_never_installs(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(core, 'STATE_DIR', Path(td)), \
                 mock.patch.object(core, 'STATE_FILE', Path(td) / 'state.json'), \
                 mock.patch.object(core, 'CONFIG_FILE', Path(td) / 'config.json'), \
                 mock.patch.object(core, 'LOCK_FILE', Path(td) / 'lock'), \
                 mock.patch.object(core, 'get_release', return_value={'version':'1.4.0','size':456,'name':'nuvio.ipk','notes':'notes','release_url':'https://github.com/NuvioMedia/NuvioTVSmart/releases'}), \
                 mock.patch.object(core, 'tv_tcp_online', return_value=True), \
                 mock.patch.object(core, 'get_installed', return_value={'present': True, 'version':'1.3.11','source':'listfull'}), \
                 mock.patch.object(core, 'download_release') as download:
                core.write_json(core.CONFIG_FILE, {'tv_ip':'127.0.0.1','tv_device':'test','auto_update':True})
                core.perform('check')
                self.assertTrue(core.state()['update_available'])
                self.assertFalse(core.state()['busy'])
                download.assert_not_called()

    def test_unknown_version_does_not_auto_install(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(core, 'STATE_DIR', Path(td)), \
                 mock.patch.object(core, 'STATE_FILE', Path(td) / 'state.json'), \
                 mock.patch.object(core, 'CONFIG_FILE', Path(td) / 'config.json'), \
                 mock.patch.object(core, 'LOCK_FILE', Path(td) / 'lock'), \
                 mock.patch.object(core, 'get_release', return_value={'version':'1.4.0','size':456,'name':'nuvio.ipk','notes':'notes','release_url':'https://github.com/NuvioMedia/NuvioTVSmart/releases'}), \
                 mock.patch.object(core, 'tv_tcp_online', return_value=True), \
                 mock.patch.object(core, 'get_installed', return_value={'present': True, 'version':None,'source':'presence-only'}), \
                 mock.patch.object(core, 'download_release') as download:
                core.write_json(core.CONFIG_FILE, {'tv_ip':'127.0.0.1','tv_device':'test','auto_update':True})
                core.perform('auto')
                download.assert_not_called()
                self.assertIn('Impossibile verificare', core.state()['message'])


if __name__ == '__main__': unittest.main()

class DeploymentTests(unittest.TestCase):
    def _run(self, action, local, latest, auto=True):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with mock.patch.object(core, 'STATE_DIR', td), \
                 mock.patch.object(core, 'STATE_FILE', td / 'state.json'), \
                 mock.patch.object(core, 'CONFIG_FILE', td / 'config.json'), \
                 mock.patch.object(core, 'LOCK_FILE', td / 'lock'), \
                 mock.patch.object(core, 'get_release', return_value={'version':latest,'size':123,'name':'nuvio.ipk','notes':'','release_url':'https://github.com/NuvioMedia/NuvioTVSmart/releases','sha256':'','url':'https://github.com/NuvioMedia/NuvioTVSmart/releases/download/1.4.0/nuvio.ipk'}), \
                 mock.patch.object(core, 'tv_tcp_online', return_value=True), \
                 mock.patch.object(core, 'get_installed', side_effect=[{'present':True,'version':local,'source':'appinfo'},{'present':True,'version':latest,'source':'appinfo'}]), \
                 mock.patch.object(core, 'download_release') as downloader, \
                 mock.patch.object(core, 'cli', return_value='Success!') as installer:
                def download(_release, path):
                    make_ipk(path, version=latest)
                    return 'abc123fake'
                downloader.side_effect = download
                core.write_json(core.CONFIG_FILE, {'tv_device':'nuvio-lg', 'tv_ip':'127.0.0.1', 'auto_update':auto})
                core.perform(action)
                return core.state(), installer.call_args_list

    def test_auto_installs_newer_and_verifies(self):
        s,calls = self._run('auto', '1.3.11', '1.4.0')
        self.assertEqual(s['installed']['version'], '1.4.0')
        self.assertEqual(s['history'][-1]['outcome'], 'success')
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][0], 'ares-install')
        self.assertNotIn('--remove', calls[0][0][1])

    def test_force_reinstalls_same_version(self):
        s,calls = self._run('force', '1.4.0', '1.4.0')
        self.assertEqual(s['history'][-1]['outcome'], 'success')
        self.assertEqual(len(calls), 1)
