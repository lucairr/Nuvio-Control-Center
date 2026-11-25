import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock
from http.server import ThreadingHTTPServer
from nuvio import core, server
from test_core import make_ipk


def release(tag, ipk=True, prerelease=False):
    return {'tag_name':tag, 'draft':False, 'prerelease':prerelease,
            'assets':([{'name':f'space.nuvio.webos_{tag}_all.ipk',
                       'size':2000,
                       'browser_download_url':f'https://github.com/NuvioMedia/NuvioTVSmart/releases/download/{tag}/nuvio.ipk',
                       'digest':'sha256:'+'a'*64}] if ipk else []),
            'published_at':'2026-11-10T12:00:00Z', 'body':'Bugfixes'}


class ReleaseTests(unittest.TestCase):
    def test_release_listing_filters_non_ipk_and_unstable(self):
        with mock.patch.object(core,'github_json', return_value=[release('1.3.11'),release('1.4.0'),release('1.3.9',ipk=False),release('1.3.10',prerelease=True)]):
            result=core.get_previous_releases()
        self.assertEqual([r['version'] for r in result],['1.4.0','1.3.11'])
        self.assertTrue(all('url' not in r for r in result))

    def test_release_tag_validated(self):
        with self.assertRaises(ValueError): core.get_release_by_tag('../../bad')
        with self.assertRaises(ValueError): core.get_release_by_tag('1.3.0-rc.1')
        with mock.patch.object(core,'github_json', return_value=release('1.3.11')):
            self.assertEqual(core.get_release_by_tag('1.3.11')['version'],'1.3.11')
            with self.assertRaises(RuntimeError): core.get_release_by_tag('1.3.10')

    def test_mismatched_tag_asset_blocked(self):
        item=release('1.3.11')
        item['assets'][0]['browser_download_url']='https://github.com/NuvioMedia/NuvioTVSmart/releases/download/1.4.0/nuvio.ipk'
        with self.assertRaises(RuntimeError): core.parse_release(item)


class DowngradeTests(unittest.TestCase):
    def run_case(self, current, target, auto=True, wrong_app=False):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        td=Path(temp.name)
        stack=mock.patch.multiple(core, STATE_DIR=td, STATE_FILE=td/'state.json',CONFIG_FILE=td/'config.json', LOCK_FILE=td/'lock')
        stack.start();self.addCleanup(stack.stop)
        core.write_json(core.CONFIG_FILE,{'tv_ip':'127.0.0.1','tv_device':'nuvio-lg','auto_update':auto,'custom_keep':'yes'})
        current_data={'present':True,'version':current,'source':'appinfo'}
        target_data={'present':True,'version':target,'source':'appinfo'}
        latest={'version':'1.4.0','size':1024,'name':'latest.ipk','notes':'','release_url':'https://github.com/NuvioMedia/NuvioTVSmart/releases'}
        previous={'version':target,'size':123,'name':'old.ipk','notes':'','release_url':'https://github.com/NuvioMedia/NuvioTVSmart/releases','sha256':'','url':f'https://github.com/NuvioMedia/NuvioTVSmart/releases/download/{target}/old.ipk'}
        patches=[mock.patch.object(core,'get_release',return_value=latest),
                 mock.patch.object(core,'get_release_by_tag',return_value=previous),
                 mock.patch.object(core,'tv_tcp_online',return_value=True),
                 mock.patch.object(core,'get_installed',side_effect=[current_data,target_data]),
                 mock.patch.object(core,'download_release',side_effect=lambda r,p: (make_ipk(p,app_id=('wrong.app' if wrong_app else core.APP_ID),version=target) or 'oksha')),
                 mock.patch.object(core,'cli',return_value='Success!')]
        handles=[p.start() for p in patches]
        for p in patches:self.addCleanup(p.stop)
        if current is None or not core.version_key(target)<core.version_key(current):
            with self.assertRaises(RuntimeError):core.perform('downgrade',target)
        elif wrong_app:
            with self.assertRaises(RuntimeError):core.perform('downgrade',target)
        else:
            core.perform('downgrade',target)
        return core.state(),core.read_json(core.CONFIG_FILE,{}),handles

    def test_success_and_turns_auto_off(self):
        state,cfg,h=self.run_case('1.4.0','1.3.11')
        self.assertEqual(state['installed']['version'],'1.3.11')
        self.assertTrue(state['update_available'])
        self.assertEqual(state['history'][-1]['action'],'downgrade')
        self.assertEqual(state['history'][-1]['outcome'],'success')
        self.assertFalse(cfg['auto_update'])
        self.assertEqual(cfg['custom_keep'],'yes')
        cmd=h[-1].call_args_list[0]
        self.assertEqual(cmd.args[0],'ares-install')
        self.assertNotIn('--remove',cmd.args[1])

    def test_same_or_newer_blocked_without_install(self):
        for current,target in [('1.4.0','1.4.0'),('1.4.0','1.4.1')]:
            with self.subTest(current=current,target=target):
                state,cfg,h=self.run_case(current,target)
                h[-1].assert_not_called()
                self.assertTrue(cfg['auto_update'])
                self.assertEqual(state['history'][-1]['outcome'],'error')

    def test_wrong_app_package_not_installed(self):
        state,cfg,h=self.run_case('1.4.0','1.3.11',wrong_app=True)
        h[-1].assert_not_called()
        self.assertEqual(state['history'][-1]['outcome'],'error')

    def test_unknown_installed_version_blocked(self):
        state,cfg,h=self.run_case(None,'1.3.11')
        h[-1].assert_not_called()
        self.assertTrue(cfg['auto_update'])


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.http.server_close)
        self.addCleanup(self.http.shutdown)
        self.sid='test-cookie-for-downgrade'
        with server.MUTEX:server.SESSIONS[self.sid]={'csrf':'test-csrf','expires':time.time()+60}
        self.addCleanup(lambda:server.SESSIONS.pop(self.sid,None))

    def call(self,method,path,payload=None,authed=True,csrf=True):
        c=http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=3)
        headers={}
        if authed:headers['Cookie']=f'nuvio_sid={self.sid}'
        if csrf:headers['X-CSRF-Token']='test-csrf'
        if payload is not None:headers['Content-Type']='application/json'
        c.request(method,path,json.dumps(payload).encode() if payload is not None else None,headers)
        result=c.getresponse();code=result.status;body=json.loads(result.read());c.close()
        return code,body

    def test_list_requires_auth_and_is_read_only(self):
        with mock.patch.object(core,'get_previous_releases',return_value=[{'version':'1.3.11','tag':'1.3.11'}]) as fetcher:
            code,_=self.call('GET','/api/releases',authed=False)
            self.assertEqual(code,401)
            code,data=self.call('GET','/api/releases')
            self.assertEqual(code,200);self.assertEqual(len(data['releases']),1)
            fetcher.assert_called_once()

    def test_post_requires_csrf_confirmation_and_valid_tag(self):
        with mock.patch.object(server,'run_background',return_value=True) as enqueue:
            self.assertEqual(self.call('POST','/api/actions/downgrade',{'tag':'1.3.11','confirm':'DOWNGRADE'},csrf=False)[0],403)
            self.assertEqual(self.call('POST','/api/actions/downgrade',{'tag':'1.3.11'})[0],400)
            self.assertEqual(self.call('POST','/api/actions/downgrade',{'tag':'../../oops','confirm':'DOWNGRADE'})[0],400)
            self.assertEqual(self.call('POST','/api/actions/downgrade',{'tag':'1.3.11','confirm':'DOWNGRADE'})[0],202)
            enqueue.assert_called_once_with('downgrade','1.3.11')

if __name__=='__main__':unittest.main()
