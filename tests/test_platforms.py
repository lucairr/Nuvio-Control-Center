"""Platform helpers and packaging behaviors, no TV/network access."""
import datetime
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from nuvio import core

class HostTests(unittest.TestCase):
    @unittest.skipIf(os.name == 'nt', 'Linux HOME behavior tested on POSIX runners')
    def test_linux_cli_uses_service_home(self):
        with mock.patch('nuvio.core.sys.platform','linux'),mock.patch('nuvio.core.shutil.which',return_value='/usr/bin/ares-install'),mock.patch('nuvio.core.subprocess.run') as p:
            p.return_value.returncode=0;p.return_value.stdout='success';p.return_value.stderr=''
            core.cli('ares-install',['--version'])
            self.assertEqual(p.call_args.kwargs['env']['HOME'],str(core.STATE_DIR))

if __name__=='__main__':unittest.main()
