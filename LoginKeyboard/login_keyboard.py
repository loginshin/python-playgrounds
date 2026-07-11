"""PyInstaller entry point for the Windows LoGinKeyboard app."""

from login_keyboard_windows.app import run_with_error_dialog


if __name__ == "__main__":
    run_with_error_dialog()
