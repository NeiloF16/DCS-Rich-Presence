import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import app_data
import installer_core as core


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.saved = self.folder / 'Saved Games' / 'DCS'
        (self.saved / 'Config').mkdir(parents=True)
        self.local = self.folder / 'LocalAppData'
        self.mock_env = patch.dict(os.environ, {'LOCALAPPDATA': str(self.local)})
        self.mock_env.start()
        self.addCleanup(self.mock_env.stop)

    def test_install_and_remove_owned_hook(self):
        result = core.install_hook(self.saved)
        target = core.hook_path(self.saved)
        self.assertIn('Hook DCS installé', result)
        self.assertEqual(core.sha256(target), core.sha256(core.hook_source()))
        self.assertIn('déjà à jour', core.install_hook(self.saved))
        self.assertEqual(list(target.parent.glob('*.bak')), [])
        self.assertIn('supprimé', core.remove_hook(self.saved))
        self.assertFalse(target.exists())

    def test_backup_overwrite_and_keep_modified(self):
        target = core.hook_path(self.saved)
        target.parent.mkdir(parents=True)
        target.write_text('-- old hook', encoding='utf-8')
        core.install_hook(self.saved)
        self.assertEqual(len(list(target.parent.glob('*.bak'))), 1)
        target.write_text('-- changed by user', encoding='utf-8')
        self.assertIn('conservé', core.remove_hook(self.saved))
        self.assertTrue(target.is_file())

    def test_reject_wrong_game_directory(self):
        with self.assertRaises(ValueError):
            core.install_hook(self.folder)

    def test_configuration_and_default_art_asset(self):
        result = app_data.save_config(self.saved)
        self.assertEqual(result['large_image'], 'dcs_logo')
        self.assertEqual(app_data.read_config(), result)
        self.assertIn('LocalAppData', str(app_data.config_path()))

    def test_uninstall_does_not_erase_changed_hook(self):
        core.install_hook(self.saved)
        app_data.save_config(self.saved)
        core.hook_path(self.saved).write_text('-- different', encoding='utf-8')
        with patch.object(core, 'wait_stopped', return_value=True), \
             patch.object(core, 'configure_startup'), patch.object(core, 'cleanup_old_startup'):
            result = core.uninstall_clean()
        self.assertIn('conservé', result)
        self.assertTrue(core.hook_path(self.saved).exists())
        self.assertFalse(app_data.config_path().exists())

if __name__ == '__main__':
    unittest.main()
