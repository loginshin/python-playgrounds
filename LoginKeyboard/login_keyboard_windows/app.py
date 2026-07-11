"""Windows app startup sequence for LoGinKeyboard."""

from tkinter import messagebox

import keyboard

from .help_gui import show_help_gui
from .hotkeys import register_hotkeys
from .native import ensure_single_instance, keep_lock_keys_stable, start_league_client_exit_hook
from .tray import start_tray_icon


# 앱의 시작 순서를 한 곳에서 관리합니다.
def main():
    ensure_single_instance()
    keep_lock_keys_stable()
    start_league_client_exit_hook()
    register_hotkeys()
    start_tray_icon()
    show_help_gui()
    keyboard.wait()


# PyInstaller 진입점에서 예외를 사용자에게 보여줄 때 사용합니다.
def run_with_error_dialog():
    try:
        main()
    except Exception as exc:
        messagebox.showerror("LoGinKeyboard", str(exc))

