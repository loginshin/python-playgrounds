"""Direct-run and PyInstaller entry point for the Windows app."""

import sys
from pathlib import Path


# 직접 실행할 때도 상위 폴더의 패키지를 찾을 수 있게 합니다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from login_keyboard_windows.app import run_with_error_dialog


if __name__ == "__main__":
    run_with_error_dialog()
