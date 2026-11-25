"""Live local HTTP tests; all TV and GitHub actions are mocked."""
import http.client
import json
import tempfile
from pathlib import Path
import threading
import unittest
from unittest import mock
from http.server import ThreadingHTTPServer
from nuvio import core, server


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        path = Path(self.td.name)
        self.auth_patch = mock.patch.object(server, 'AUTH_FILE', path / 'auth.json')
        self.state_patch = mock.patch.object(core, 'STATE_FILE', path / 'state.json')
        self.config_patch = mock.patch.object(core, 'CONFIG_FILE', path / 'config.json')
        self.dir_patch = mock.patch.object(core, 'STATE_DIR', path)
        for p in (self.auth_patch, self.state_patch, self.config_patch, self.dir_patch): p.start()
        core.write_json(server.AUTH_FILE, server.hash_pw('my-long-demo-password'))
        core.write_json(core.CONFIG_FILE, {'tv_ip': '192.0.2.1', 'tv_device':'nuvio-lg', 'web_bind':'127.0.0.1', 'web_port':8765,'auto_update':False})
        server.SESSIONS.clear()
        server.LOGIN_ATTEMPTS.clear()
        self.srv = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.srv.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.thread.join(timeout=3)
        for p in (self.dir_patch, self.config_patch, self.state_patch, self.auth_patch): p.stop()
        self.td.cleanup()

    def request(self, method, path, data=None, headers=None):
        con = http.client.HTTPConnection('127.0.0.1', self.srv.server_port,timeout=2)
        content = json.dumps(data).encode() if data is not None else None
        h = dict(headers or {})
        if content: h['Content-Type'] = 'application/json'
        con.request(method,path,content,headers=h)
        resp = con.getresponse()
        status, headers, body = resp.status, dict(resp.getheaders()), resp.read()
        con.close()
        return status, headers, json.loads(body.decode())

    def test_rejects_unauthenticated_mutations(self):
        status, _, _ = self.request('POST','/api/actions/force',{})
        self.assertEqual(status,401)
        status, _, _ = self.request('GET','/api/status')
        self.assertEqual(status,401)

    def test_login_and_csrf(self):
        status, _, _ = self.request('POST','/api/login',{'password':'bad-password'})
        self.assertEqual(status,401)
        status, headers, obj = self.request('POST','/api/login',{'password':'my-long-demo-password'})
        self.assertEqual(status,200)
        self.assertTrue(obj['csrf'])
        cookie = headers['Set-Cookie'].split(';')[0]
        self.assertIn('HttpOnly',headers['Set-Cookie'])
        self.assertIn('SameSite=Strict',headers['Set-Cookie'])
        status, _, _ = self.request('POST','/api/actions/force',{}, {'Cookie':cookie})
        self.assertEqual(status,403)
        status, _, _ = self.request('POST','/api/actions/force',{}, {'Cookie':cookie,'X-CSRF-Token': 'bad'})
        self.assertEqual(status,403)
        with mock.patch.object(server,'run_background',return_value=True) as job:
            status, _, _ = self.request('POST','/api/actions/check',{}, {'Cookie':cookie,'X-CSRF-Token':obj['csrf']})
            self.assertEqual(status,202)
            job.assert_called_once_with('check')
        status, _, _ = self.request('GET','/api/status',None,{'Cookie':cookie})
        self.assertEqual(status,200)

    def test_cross_origin_rejected(self):
        status, _, _ = self.request('POST','/api/login',{'password':'my-long-demo-password'}, {'Origin':'http://attacker.example'})
        self.assertEqual(status,403)

if __name__ == '__main__': unittest.main()
