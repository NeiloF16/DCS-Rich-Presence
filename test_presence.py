import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from presence import payload, clean, read_state, LOGO_URL
from localization import TEXT, KEYS, language_for, detect_language, windows_display_tag

class PresenceTests(unittest.TestCase):
    def setUp(self):
        self.data = dict(schema=1,status='cockpit',aircraft='MiG-29 Fulcrum',theatre='Caucasus',updated=1000,started=900,multiplayer=True)
    def test_all_languages_and_states(self):
        for lang in TEXT:
            self.assertEqual(set(TEXT[lang]),set(KEYS))
            for status in ['cockpit','spectator','menu','loading']:
                for paused in [True,False]:
                    with self.subTest(lang=lang,status=status,paused=paused):
                        data=dict(self.data,status=status,paused=paused)
                        if status=='spectator':data['aircraft']=''
                        a=payload(data,1000,lang)
                        self.assertEqual(a['name'],'DCS WORLD')
                        self.assertEqual(a['large_image'],LOGO_URL)
                        for key in ['details','state']:
                            self.assertTrue(a[key]);self.assertLessEqual(len(a[key].encode()),120)
                            self.assertNotIn('{aircraft}',a[key])
    def test_regional_languages(self):
        for tag,lang in [('fr-FR','fr'),('fr_CA','fr'),('pt-BR','pt'),('ar-DZ','ar'),('ja-JP','ja'),('zh-TW','zh-hant'),('zh-Hant-HK','zh-hant'),('zh-CN','zh-hans'),('sv-SE','en')]:
            self.assertEqual(language_for(tag),lang)
    def test_auto_and_override(self):
        with patch('localization.windows_display_tag',return_value='fr-CA'):
            self.assertEqual(detect_language(),'fr');self.assertEqual(detect_language('en'),'en')
    def test_windows_ui_api(self):
        import ctypes
        from types import SimpleNamespace
        class Fn:
            def __call__(self,flags,count,buffer,size):
                self.assert_flags=flags
                count._obj.value=1
                if buffer is None:size._obj.value=7
                else:buffer.value='fr-FR'
                return 1
        fn=Fn()
        with patch('localization.sys.platform','win32'),patch('ctypes.WinDLL',return_value=SimpleNamespace(GetUserPreferredUILanguages=fn),create=True):
            self.assertEqual(windows_display_tag(),'fr-FR');self.assertEqual(fn.assert_flags,8)
    def test_french_and_english(self):
        self.assertEqual(payload(self.data,1000,'fr')['state'],'Caucase · Multijoueur')
        self.assertEqual(payload(self.data,1000,'en')['details'],'Flying MiG-29 Fulcrum')
    def test_unknown_aircraft_and_map(self):
        a=payload(dict(self.data,aircraft='MOD XYZ',theatre='FutureMap'),1000)
        self.assertIn('MOD XYZ',a['details']);self.assertIn('FutureMap',a['state'])
    def test_stale_and_pause_and_menu(self):
        self.assertEqual(payload(self.data,2000)['state'],TEXT['en']['waiting'])
        self.assertIn('Paused',payload(dict(self.data,paused=True),2000)['details'])
        self.assertEqual(payload(dict(self.data,status='menu'),2000)['details'],TEXT['en']['menu'])
    def test_timer(self):
        self.assertEqual(payload(self.data,1000)['start'],900)
        self.assertNotIn('start',payload(dict(self.data,status='menu'),1000))
        self.assertNotIn('start',payload(dict(self.data,started=2000),1000))
    def test_unicode_bounds(self):
        a=payload(dict(self.data,aircraft='機'*200+'\n',theatre='é'*200),1000,'ja')
        self.assertLessEqual(len(a['details'].encode()),120)
        self.assertLessEqual(len(a['state'].encode()),120)
        self.assertNotIn('\n',clean('a\nb'))
    def test_incomplete_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'data.json';p.write_text('{');self.assertIsNone(read_state(p))
            p.write_text(json.dumps(self.data));self.assertEqual(read_state(p),self.data)
    def test_real_library_payload(self):
        from pypresence.payloads import Payload
        a=payload(self.data,1000,'fr')
        message=Payload.set_activity(pid=1,activity=True,**a).data
        self.assertEqual(message['args']['activity']['name'],'DCS WORLD')
        self.assertEqual(message['args']['activity']['assets']['large_image'],LOGO_URL)

if __name__=='__main__': unittest.main()
