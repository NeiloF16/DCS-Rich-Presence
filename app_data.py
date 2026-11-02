"""Safe Windows per-user paths and public release constants."""
import json
import os
from pathlib import Path

APP_ID = '1566882349633765446'
RELEASE = '1.0.0'
APP_NAME = 'DCS Rich Presence'


def data_dir():
    base = os.environ.get('LOCALAPPDATA')
    if not base:
        base = str(Path.home() / 'AppData' / 'Local')
    return Path(base) / 'DCSRichPresence'


def config_path():
    return data_dir() / 'config.json'


def read_config():
    path = config_path()
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict) or str(data.get('application_id', APP_ID)) != APP_ID:
        raise ValueError('Configuration DCS Rich Presence invalide')
    return data


def save_config(saved_games, language='auto', image='dcs_logo'):
    target = data_dir()
    target.mkdir(parents=True, exist_ok=True)
    config = {
        'application_id': APP_ID,
        'dcs_saved_games': str(saved_games),
        'language': language,
        'large_image': image,
    }
    path = config_path()
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)
    return config


def saved_games_base():
    # SHGetKnownFolderPath(FOLDERID_SavedGames) supports relocated Saved Games.
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        import uuid
        class GUID(ctypes.Structure):
            _fields_ = [('Data1', wintypes.DWORD), ('Data2', wintypes.WORD),
                        ('Data3', wintypes.WORD), ('Data4', ctypes.c_byte * 8)]
        raw = uuid.UUID('4c5c32ff-bb9d-43b0-b5b4-2d72e54eaaa4').bytes_le
        guid = GUID.from_buffer_copy(raw)
        pointer = ctypes.c_wchar_p()
        func = ctypes.windll.shell32.SHGetKnownFolderPath
        func.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE,
                         ctypes.POINTER(ctypes.c_wchar_p)]
        func.restype = ctypes.c_long
        try:
            if func(ctypes.byref(guid), 0, None, ctypes.byref(pointer)) == 0:
                return Path(pointer.value)
        finally:
            if pointer.value:
                ctypes.windll.ole32.CoTaskMemFree(ctypes.cast(pointer, ctypes.c_void_p))
    return Path.home() / 'Saved Games'


def discover_dcs():
    base = saved_games_base()
    return sorted((p for p in base.glob('DCS*') if p.is_dir() and (p / 'Config').is_dir()),
                  key=lambda p: p.name.casefold()) if base.is_dir() else []
