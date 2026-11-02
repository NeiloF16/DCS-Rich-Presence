"""Local DCS GameGUI JSON -> Discord IPC. No account token required."""
import csv
import io
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import subprocess
import time
import sys

ROOT = Path(__file__).resolve().parent
from app_data import data_dir, read_config, APP_ID
from localization import TEXT, detect_language, map_name
LOGO_URL = 'https://shared.fastly.steamstatic.com/community_assets/images/apps/223750/f709dbfd1d2ad385ae5baaa1824422c11a4a2dea.jpg'


def process_running():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, errors='replace', timeout=8,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError('Impossible de vérifier le processus DCS.exe')
    return any(row and row[0].lower() == 'dcs.exe'
               for row in csv.reader(io.StringIO(result.stdout)))

def read_state(path):
    # A short retry tolerates a concurrent hook write.
    for _ in range(3):
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            if not isinstance(data, dict) or data.get('schema') != 1:
                return None
            return data
        except (OSError, ValueError):
            time.sleep(0.05)
    return None

def clean(value, limit=120):
    value = ''.join(c for c in str(value or '') if c.isprintable()).strip()
    return value.encode('utf-8')[:limit].decode('utf-8', errors='ignore')

def payload(data, now, lang='en', logo=LOGO_URL):
    t = TEXT.get(lang, TEXT['en'])
    activity = {'name': 'DCS WORLD', 'large_image': logo,
                'large_text': 'DCS WORLD · Digital Combat Simulator'}
    status = data.get('status') if isinstance(data, dict) else None
    updated = data.get('updated', 0) if isinstance(data, dict) else 0
    stale = not isinstance(updated, (int, float)) or now - updated > 60
    persistent = status in ('menu', 'loading') or (data and data.get('paused'))
    if not data or (stale and not persistent):
        activity.update(details='DCS WORLD', state=t['waiting'])
    elif status in ('menu', 'loading'):
        activity.update(details=t[status], state=t['prepare'])
    else:
        aircraft = clean(data.get('aircraft'))
        details = t['cockpit'].format(aircraft=aircraft) if aircraft else t['spectator']
        if data.get('paused'):
            details = t['paused'].format(aircraft=aircraft or t['mission'])
        terrain = clean(data.get('theatre'))
        state = map_name(terrain, lang) if terrain else t['unavailable']
        state += ' · ' + t['multi' if data.get('multiplayer') else 'solo']
        activity.update(details=details, state=state)
        started = data.get('started')
        if isinstance(started, (int, float)) and 0 < started <= now:
            activity['start'] = int(started)
    for key in ('details', 'state'):
        activity[key] = clean(activity[key])
    return activity


def wait_for_stop(path, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.exists():
            return True
        time.sleep(min(1, max(0, deadline - time.monotonic())))
    return path.exists()


def main():
    from pypresence import Presence
    config = read_config()
    if config is None:
        raise FileNotFoundError('Installation incomplète. Lance DCSRichPresence.exe pour configurer DCS.')
    state_file = Path(config['dcs_saved_games']) / 'Logs' / 'NeiloRichPresence.json'
    client_id = str(config['application_id'])
    lang = detect_language(config.get('language', 'auto'))
    logo = config.get('large_image') or LOGO_URL
    if client_id != APP_ID:
        raise ValueError('Application ID invalide')
    # Prevent duplicate launchers, released automatically by Windows on exit.
    import msvcrt
    lock_path = data_dir()
    lock_path.mkdir(parents=True, exist_ok=True)
    lock = (lock_path / (client_id + '.lock')).open('a+b')
    if lock.tell() == 0:
        lock.write(b'0'); lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print('Le programme est déjà lancé. Ferme cette fenêtre.'); return
    stop_file = lock_path / (client_id + '.stop')
    stop_file.unlink(missing_ok=True)
    handler = RotatingFileHandler(lock_path / 'presence.log', maxBytes=250000,
                                  backupCount=1, encoding='utf-8')
    handlers = [handler]
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format='%(asctime)s %(message)s')
    logging.info('Neilo Rich Presence — ouvre Discord bureau et DCS. Ctrl+C pour arrêter.')
    logging.info('Lecture : %s | langue : %s | v1.0', state_file, lang)
    rpc = None
    previous = None
    last_sent = 0
    try:
        while not stop_file.exists():
            try:
                running = process_running()
                if not running:
                    if rpc:
                        rpc.clear(); rpc.close(); rpc = None
                        logging.info('DCS fermé : statut retiré.')
                    previous = None
                else:
                    if rpc is None:
                        rpc = Presence(client_id)
                        rpc.connect()
                        previous = None
                        logging.info('Connecté à Discord.')
                    activity = payload(read_state(state_file), time.time(), lang, logo)
                    if activity != previous or time.monotonic() - last_sent >= 60:
                        rpc.update(**activity)
                        previous = activity
                        last_sent = time.monotonic()
                        logging.info('%s | %s', activity['details'], activity['state'])
            except Exception as exc:
                logging.warning('%s: %s — nouvel essai dans 15 s.', type(exc).__name__, exc)
                if rpc:
                    try: rpc.close()
                    except Exception: pass
                rpc = None
                previous = None
            if wait_for_stop(stop_file, 15):
                break
    except KeyboardInterrupt:
        pass
    finally:
        if rpc:
            try: rpc.clear()
            except Exception: pass
            try: rpc.close()
            except Exception: pass
        stop_file.unlink(missing_ok=True)
        lock.close()

if __name__ == '__main__':
    import sys
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    main()
