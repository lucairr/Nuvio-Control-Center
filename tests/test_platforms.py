"""Platform helpers and packaging behaviors, no TV/network access."""
import datetime
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from nuvio import bootstrap, core, scheduler

class HostTests(unittest.TestCase):
    def test_schedule_only_at_local_1930_once_daily(self):
        tz=datetime.timezone(datetime.timedelta(hours=1))
        now=datetime.datetime(2026,11,13,19,30,tzinfo=tz)
        self.assertTrue(scheduler.should_run(now,None))
        self.assertFalse(scheduler.should_run(now,now.date()))
        self.assertFalse(scheduler.should_run(now.replace(minute=29),None))

    def test_bootstrap_preserves_private_configuration(self):
        with tempfile.TemporaryDirectory() as td:
            new=Path(td)/'config.json'
            with mock.patch.object(core,'CONFIG_FILE',new),mock.patch('sys.argv',['bootstrap','--tv-ip','192.0.2.10']):
                bootstrap.main()
            cfg=json.loads(new.read_text())
            self.assertFalse(cfg['auto_update'])
            self.assertEqual(cfg['web_bind'],'0.0.0.0')
            with mock.patch.object(core,'CONFIG_FILE',new),mock.patch('sys.argv',['bootstrap','--tv-ip','192.0.2.11']):
                bootstrap.main()
            self.assertEqual(json.loads(new.read_text())['tv_ip'],'192.0.2.10')

    def test_mac_cli_uses_interactive_home(self):
        with mock.patch('nuvio.core.sys.platform','darwin'),mock.patch('nuvio.core.shutil.which',return_value='/usr/local/bin/ares-install'),mock.patch('nuvio.core.subprocess.run') as p:
            p.return_value.returncode=0;p.return_value.stdout='success';p.return_value.stderr=''
            with mock.patch.dict('os.environ',{'HOME':'/Users/example','NUVIO_HOME':'/Users/example/Library/Application Support/NuvioControlCenter'},clear=False):
                core.cli('ares-install',['--version'])
            self.assertEqual(p.call_args.kwargs['env']['HOME'],'/Users/example')

    @unittest.skipIf(os.name == 'nt', 'Linux HOME behavior tested on POSIX runners')
    def test_linux_cli_uses_service_home(self):
        with mock.patch('nuvio.core.sys.platform','linux'),mock.patch('nuvio.core.shutil.which',return_value='/usr/bin/ares-install'),mock.patch('nuvio.core.subprocess.run') as p:
            p.return_value.returncode=0;p.return_value.stdout='success';p.return_value.stderr=''
            core.cli('ares-install',['--version'])
            self.assertEqual(p.call_args.kwargs['env']['HOME'],str(core.STATE_DIR))

if __name__=='__main__':unittest.main()
