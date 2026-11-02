"""DCS Rich Presence — Windows launcher and graphical setup manager."""
import os
from pathlib import Path
import sys
import traceback

from app_data import APP_NAME, RELEASE, data_dir, discover_dcs, read_config, save_config
import installer_core as core


def log_start_error():
    try:
        data_dir().mkdir(parents=True, exist_ok=True)
        with (data_dir() / 'startup-error.log').open('a', encoding='utf-8') as log:
            log.write(traceback.format_exc() + '\n')
    except OSError:
        pass


def show_manager():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    root = tk.Tk()
    root.title(APP_NAME + ' · v' + RELEASE)
    root.geometry('690x465')
    root.minsize(620, 425)
    root.configure(bg='#101722')
    try:
        root.iconbitmap(str(core.hook_source().parent / 'assets' / 'app.ico'))
    except tk.TclError:
        pass
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('DRPC.TEntry', padding=7)
    style.configure('DRPC.TButton', font=('Segoe UI', 10), padding=(12, 9))
    style.configure('DRPC.TCheckbutton', background='#182230', foreground='#edf2fa',
                    font=('Segoe UI', 10))
    style.map('DRPC.TCheckbutton', background=[('active', '#182230')],
              foreground=[('active', '#ffffff')])
    fg = '#ecf3ff'
    sub = '#a6b7ce'
    panel = tk.Frame(root, bg='#182230', padx=26, pady=21)
    panel.pack(fill='both', expand=True, padx=18, pady=16)
    tk.Label(panel, text='DCS WORLD', font=('Segoe UI', 24, 'bold'),
             bg='#182230', fg=fg).pack(anchor='w')
    tk.Label(panel, text='DISCORD RICH PRESENCE   |   COMMUNITY EDITION',
             font=('Segoe UI', 9, 'bold'), bg='#182230', fg='#f3ac32').pack(anchor='w', pady=(0, 21))
    tk.Label(panel, text='DCS Saved Games folder   /   Dossier Parties enregistrées DCS',
             bg='#182230', fg=sub, font=('Segoe UI', 10)).pack(anchor='w')
    config = None
    try:
        config = read_config()
    except Exception as exc:
        messagebox.showwarning(APP_NAME, 'Configuration invalide : ' + str(exc))
    choices = discover_dcs()
    initial = config.get('dcs_saved_games', '') if config else (str(choices[0]) if choices else '')
    saved = tk.StringVar(value=initial)
    inputs = tk.Frame(panel, bg='#182230')
    inputs.pack(fill='x', pady=(9, 16))
    entry = ttk.Entry(inputs, textvariable=saved, style='DRPC.TEntry')
    entry.pack(side='left', fill='x', expand=True, padx=(0, 9))
    def browse():
        folder = filedialog.askdirectory(title='Choose the DCS Saved Games folder', initialdir=str(Path(saved.get()).parent) if saved.get() else str(Path.home()))
        if folder:
            saved.set(folder)
    ttk.Button(inputs, text='Browse…', style='DRPC.TButton', command=browse).pack(side='right')
    enabled = tk.BooleanVar(value=core.get_startup_enabled())
    ttk.Checkbutton(panel, text='Start silently with Windows  /  Démarrer avec Windows',
                    variable=enabled, style='DRPC.TCheckbutton').pack(anchor='w', pady=(0, 15))
    tk.Label(panel, text='Requires DCS World and the Discord desktop application. No account token.',
             bg='#182230', fg=sub, font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 12))
    status = tk.StringVar(value='Ready / Prêt')

    def install():
        try:
            folder = Path(saved.get().strip().strip('"'))
            if not core.is_dcs_folder(folder):
                raise ValueError('Choose Saved Games\\DCS (not the Steam game folder).')
            from presence import process_running
            if process_running():
                raise RuntimeError('Close DCS World before installing the Lua hook.')
            # Stop the previous version before updating the hook/configuration.
            core.request_stop()
            if not core.wait_stopped():
                raise TimeoutError('The previous Rich Presence instance did not stop.')
            text = core.install_hook(folder)
            previous = read_config()
            if previous and Path(previous['dcs_saved_games']).resolve() != folder.resolve():
                core.remove_hook(previous['dcs_saved_games'])
            old_lang = previous.get('language', 'auto') if previous else 'auto'
            save_config(folder, old_lang, 'dcs_logo')
            core.cleanup_old_startup()
            core.configure_startup(enabled.get())
            core.run_background()
            status.set('✓ Installed and started  /  Installé et lancé')
            messagebox.showinfo(APP_NAME, text + '\n\nRich Presence started. Open Discord + DCS World.')
        except Exception as exc:
            status.set('Error: ' + str(exc))
            messagebox.showerror(APP_NAME, str(exc))

    def stop():
        core.request_stop()
        status.set('Stop requested. / Arrêt demandé.')

    def remove():
        if not messagebox.askyesno(APP_NAME, 'Remove the DCS hook and disable automatic startup?\n\nSupprimer le hook et le démarrage automatique ?'):
            return
        try:
            from presence import process_running
            if process_running():
                raise RuntimeError('Close DCS World before removing its Lua hook.')
            core.request_stop()
            if not core.wait_stopped():
                raise TimeoutError('Rich Presence is still running.')
            core.configure_startup(False)
            enabled.set(False)
            old = read_config()
            result = core.remove_hook(old['dcs_saved_games']) if old else 'Nothing installed.'
            status.set(result)
            messagebox.showinfo(APP_NAME, result)
        except Exception as exc:
            status.set('Error: ' + str(exc))
            messagebox.showerror(APP_NAME, str(exc))

    controls = tk.Frame(panel, bg='#182230')
    controls.pack(fill='x', pady=(0, 14))
    ttk.Button(controls, text='Install & Start  /  Installer', style='DRPC.TButton',
               command=install).pack(side='left', padx=(0, 9))
    ttk.Button(controls, text='Stop / Arrêter', style='DRPC.TButton',
               command=stop).pack(side='left', padx=(0, 9))
    ttk.Button(controls, text='Remove Hook', style='DRPC.TButton',
               command=remove).pack(side='left')
    tk.Label(panel, textvariable=status, bg='#182230', fg='#f3ac32',
             font=('Segoe UI', 10), anchor='w', wraplength=580).pack(anchor='w')
    tk.Label(root, text='Independent fan utility · No telemetry · Not affiliated with Eagle Dynamics or Discord',
             font=('Segoe UI', 9), bg='#101722', fg='#8ea3bc').pack(pady=(0, 9))
    root.mainloop()


def main():
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action == '--run':
            try:
                from presence import main as presence_main
                presence_main()
            except Exception:
                log_start_error()
                sys.exit(1)
            return
        if action == '--stop':
            core.request_stop()
            return
        if action == '--uninstall-clean':
            try:
                core.uninstall_clean()
            except Exception:
                log_start_error()
                sys.exit(1)
            return
        raise ValueError('Unknown option: ' + action)
    show_manager()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        log_start_error()
        # A CLI/auto-start error must not pop up a dialog over the user's game.
        if len(sys.argv) == 1:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,
               'Launch failed. See %LOCALAPPDATA%\\DCSRichPresence\\startup-error.log',
               APP_NAME, 16)
        sys.exit(1)
