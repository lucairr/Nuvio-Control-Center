"""Regression tests for Windows hardening and stale-state recovery (no TV, no network)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from nuvio import core, server


class IsolatedState(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        path = Path(self.td.name)
        self.patches = [
            mock.patch.object(core, 'STATE_DIR', path),
            mock.patch.object(core, 'STATE_FILE', path / 'state.json'),
            mock.patch.object(core, 'CONFIG_FILE', path / 'config.json'),
            mock.patch.object(core, 'LOCK_FILE', path / 'operation.lock'),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.td.cleanup()


class WriteRetryTests(IsolatedState):
    def test_write_json_retries_transient_permission_error(self):
        real_replace = os.replace
        calls = {'n': 0}

        def flaky(src, dst):
            calls['n'] += 1
            if calls['n'] < 3:
                raise PermissionError('file in use')
            return real_replace(src, dst)

        with mock.patch('nuvio.core.os.replace', side_effect=flaky), \
             mock.patch.object(core, '_RETRY_DELAY', 0):
            core.write_json(core.STATE_FILE, {'ok': True})
        self.assertEqual(core.read_json(core.STATE_FILE, {}), {'ok': True})
        self.assertEqual(calls['n'], 3)
        self.assertEqual([p for p in Path(self.td.name).iterdir() if p.name.startswith('.nuvio-')], [])

    def test_write_json_gives_up_and_cleans_temp(self):
        with mock.patch('nuvio.core.os.replace', side_effect=PermissionError('locked')), \
             mock.patch.object(core, '_RETRY_DELAY', 0):
            with self.assertRaises(PermissionError):
                core.write_json(core.STATE_FILE, {'ok': True})
        self.assertEqual(list(Path(self.td.name).iterdir()), [])


class StaleBusyTests(IsolatedState):
    def test_stale_busy_flag_is_cleared_when_lock_free(self):
        core.update_state(busy=True, job='auto')
        with mock.patch.object(core, 'perform') as perform:
            self.assertTrue(server.run_background('check'))
            server.ACTIVE_JOB.join(timeout=3)
        perform.assert_called_once_with('check', None)
        self.assertFalse(core.state()['busy'])

    def test_real_running_operation_still_blocks(self):
        core.update_state(busy=True, job='auto')
        with mock.patch.object(server, 'available', return_value=False), \
             mock.patch.object(core, 'perform') as perform:
            self.assertFalse(server.run_background('check'))
        perform.assert_not_called()


class WindowsCliTests(IsolatedState):
    def test_windows_cli_hides_console_and_keeps_user_home(self):
        with mock.patch.object(core, 'is_windows', return_value=True), \
             mock.patch.object(core, 'find_cli', return_value=r'C:\Users\x\AppData\Roaming\npm\ares-install.cmd'), \
             mock.patch('nuvio.core.subprocess.run') as run, \
             mock.patch.dict('os.environ', {'HOME': 'C:/Users/x'}, clear=False):
            run.return_value.returncode = 0
            run.return_value.stdout = 'ok'
            run.return_value.stderr = ''
            core.cli('ares-install', ['--list'])
        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs['creationflags'], 0x08000000)
        self.assertEqual(kwargs['env']['HOME'], 'C:/Users/x')

    def test_find_cli_falls_back_to_appdata_npm(self):
        npm = Path(self.td.name) / 'npm'
        npm.mkdir()
        (npm / 'ares-install.cmd').write_text('@echo off\n')
        with mock.patch.object(core, 'is_windows', return_value=True), \
             mock.patch('nuvio.core.shutil.which', return_value=None), \
             mock.patch.dict('os.environ', {'APPDATA': self.td.name}, clear=False):
            self.assertEqual(core.find_cli('ares-install'), str(npm / 'ares-install.cmd'))
            self.assertIsNone(core.find_cli('ares-novacom'))


if __name__ == '__main__':
    unittest.main()
