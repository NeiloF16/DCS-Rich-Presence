import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import MagicMock, patch

import presence
from app_data import APP_ID, config_path, data_dir


class BackgroundTests(unittest.TestCase):
    def test_stop_request(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / 'stop'
            self.assertFalse(presence.wait_for_stop(path, 0))
            path.touch()
            self.assertTrue(presence.wait_for_stop(path, 15))

    def test_windowless_shutdown_and_dcs_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict('os.environ', LOCALAPPDATA=tmp):
                data_dir().mkdir()
                config_path().write_text(json.dumps({
                    'application_id': APP_ID, 'dcs_saved_games': tmp,
                    'language': 'auto', 'large_image': 'dcs_logo',
                }), encoding='utf-8')
                rpc = MagicMock()
                fake = ModuleType('pypresence')
                fake.Presence = lambda *args: rpc
                fake_lock = MagicMock()
                def stop_after_first(*args):
                    (data_dir() / (APP_ID + '.stop')).write_text('stop')
                    return True
                with patch.dict(sys.modules, {'pypresence': fake, 'msvcrt': fake_lock}), \
                     patch.object(presence, 'process_running', return_value=True), \
                     patch.object(presence, 'wait_for_stop', side_effect=stop_after_first), \
                     patch.object(presence.logging, 'basicConfig') as log_setup, \
                     patch.object(sys, 'stderr', None):
                    presence.main()
                rpc.connect.assert_called_once()
                rpc.update.assert_called_once()
                rpc.clear.assert_called_once()
                rpc.close.assert_called_once()
                self.assertEqual(rpc.update.call_args.kwargs['large_image'], 'dcs_logo')
                self.assertFalse((data_dir() / (APP_ID + '.stop')).exists())
                handlers = next(x.kwargs['handlers'] for x in log_setup.call_args_list
                                if 'handlers' in x.kwargs)
                for handler in handlers:
                    handler.close()

    def test_crash_safe_missing_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict('os.environ', LOCALAPPDATA=tmp):
                fake = ModuleType('pypresence')
                fake.Presence = MagicMock()
                with patch.dict(sys.modules, {'pypresence': fake}):
                    with self.assertRaises(FileNotFoundError):
                        presence.main()

if __name__ == '__main__':
    unittest.main()
