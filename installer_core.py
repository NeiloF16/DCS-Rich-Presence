"""User-scope installation, DCS hook lifecycle and opt-in Windows startup."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from app_data import APP_ID, data_dir, read_config, save_config

ROOT = Path(__file__).resolve().parent
HOOK_NAME = 'NeiloRichPresence.lua'
RUN_VALUE = 'DCS Rich Presence'


def hook_source():
    # PyInstaller 6 onedir bundles data in _internal; source tests use adjacent file.
    base = Path(getattr(sys, '_MEIPASS', ROOT))
    return base / HOOK_NAME


def is_dcs_folder(path):
    return path.is_dir() and (path / 'Config').is_dir()


def hook_path(path):
    return Path(path) / 'Scripts' / 'Hooks' / HOOK_NAME


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_hook(folder):
    folder = Path(folder).expanduser().resolve()
    if not is_dcs_folder(folder):
        raise ValueError('Dossier DCS invalide : le sous-dossier Config est absent.')
    source = hook_source()
    if not source.is_file():
        raise FileNotFoundError('Hook DCS introuvable : ' + str(source))
    destination = hook_path(folder)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and sha256(destination) == sha256(source):
        return 'Hook DCS déjà à jour.'
    if destination.exists():
        backup = destination.with_name(HOOK_NAME + '.' + time.strftime('%Y%m%d-%H%M%S') + '.bak')
        # Never overwrite an earlier same-second backup.
        index = 1
        while backup.exists():
            backup = destination.with_name(HOOK_NAME + '.' + time.strftime('%Y%m%d-%H%M%S') + f'.{index}.bak')
            index += 1
        shutil.copy2(destination, backup)
    temporary = destination.with_suffix('.tmp')
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return 'Hook DCS installé dans : ' + str(destination.parent)


def remove_hook(folder):
    target = hook_path(folder)
    if not target.is_file():
        return 'Aucun hook à supprimer.'
    # Never erase a third-party-modified hook, even if it happens to share our name.
    if sha256(target) != sha256(hook_source()):
        return 'Hook modifié détecté : conservé par sécurité (' + str(target) + ').'
    target.unlink()
    return 'Hook DCS supprimé.'


def control_path(name):
    return data_dir() / (APP_ID + '.' + name)


def request_stop():
    data_dir().mkdir(parents=True, exist_ok=True)
    control_path('stop').write_text('stop', encoding='ascii')


def wait_stopped(seconds=25):
    if os.name != 'nt':
        return True
    import msvcrt
    lockpath = control_path('lock')
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if not lockpath.exists():
            return True
        with lockpath.open('a+b') as lock:
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                time.sleep(0.35)
                continue
            else:
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                return True
    return False


def current_binary_args():
    if getattr(sys, 'frozen', False):
        return [sys.executable]
    return [sys.executable, str(ROOT / 'app.pyw')]


def run_background():
    cmd = current_binary_args() + ['--run']
    if os.name != 'nt':
        raise OSError('Windows est requis.')
    # Avoid invoking the old source v0.3 concurrently.
    request_stop()
    if not wait_stopped():
        raise TimeoutError('Ancienne présence encore en cours. Arrête-la avant de relancer.')
    control_path('stop').unlink(missing_ok=True)
    subprocess.Popen(cmd, cwd=str(ROOT), creationflags=0x08000000,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True)


def get_startup_enabled():
    if os.name != 'nt':
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
            return bool(winreg.QueryValueEx(key, RUN_VALUE)[0])
    except FileNotFoundError:
        return False


def configure_startup(enabled):
    if os.name != 'nt':
        raise OSError('Windows est requis.')
    import winreg
    path = r'Software\Microsoft\Windows\CurrentVersion\Run'
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            command = subprocess.list2cmdline(current_binary_args() + ['--run'])
            winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, command)
        else:
            try: winreg.DeleteValue(key, RUN_VALUE)
            except FileNotFoundError: pass


def cleanup_old_startup():
    # Only clean our precisely named old shortcut; leave other startup apps alone.
    if os.name != 'nt':
        return
    import ctypes
    from ctypes import wintypes
    buffer = ctypes.create_unicode_buffer(32768)
    # CSIDL_STARTUP = 0x0007
    if ctypes.windll.shell32.SHGetFolderPathW(None, 7, None, 0, buffer) == 0:
        (Path(buffer.value) / ('DCS Rich Presence ' + APP_ID + '.lnk')).unlink(missing_ok=True)


def uninstall_clean():
    request_stop()
    stopped = wait_stopped()
    configure_startup(False)
    cleanup_old_startup()
    config = read_config()
    message = 'Configuration absente.'
    if config is not None:
        message = remove_hook(config['dcs_saved_games'])
    if stopped:
        for name in (APP_ID + '.stop', APP_ID + '.lock', 'config.json', 'presence.log',
                     'presence.log.1', 'startup-error.log'):
            (data_dir() / name).unlink(missing_ok=True)
        try: data_dir().rmdir()
        except OSError: pass
    else:
        message += ' Processus en cours : journaux conservés.'
    return message
