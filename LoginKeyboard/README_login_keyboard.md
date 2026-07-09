# LoginKeyboard Python

개발자용 구조/빌드/배포 명세는 `DEVELOPMENT.md`를 기준으로 확인하세요.

AutoHotkey로 작성했던 LoGinKeyboard를 Python으로 옮긴 버전입니다.

Windows 버전은 `login_keyboard.py`, macOS 별도 구현은 `macos/` 폴더를 사용합니다.

## 가능 여부

대부분의 기능은 Python으로 구현 가능합니다.

- 전역 단축키: `keyboard`
- 선택한 글자 복사 후 검색/번역: `keyboard`, `pyperclip`, `webbrowser`
- 안내 GUI: `tkinter`
- CapsLock/NumLock/ScrollLock 상태 제어: Windows API via `ctypes`

다만 AutoHotkey가 Windows 키보드 자동화에 특화되어 있어서, Python 버전은 관리자 권한이 필요할 수 있고 일부 키 이름은 키보드/IME/Windows 설정에 따라 다르게 잡힐 수 있습니다.

## 설치

권장 실행/빌드 환경:

- 일반 배포: Python `3.12` 64-bit 권장
- Windows 10/11 전용 배포: Python `3.14` 64-bit 사용 가능
- Windows 7까지 지원해야 하는 별도 배포: Python `3.8` 검토 필요

```powershell
cd C:\workspace\GitHub\python-playgrounds\LoginKeyboard
python -m pip install -r requirements.txt
```

## 실행

전역 키 입력을 잡아야 하므로 PowerShell 또는 빌드한 exe를 관리자 권한으로 실행하는 것을 권장합니다.

```powershell
python .\login_keyboard.py
```

## 구현된 단축키

- `Right Ctrl + CapsLock`: 사용법 GUI 표시
- `Right Ctrl + 방향키`: `Home`, `End`, `PageUp`, `PageDown`
- `Right Ctrl + Enter`: 선택한 텍스트 구글 검색
- `Right Ctrl + Right Shift`: 선택한 텍스트 구글 번역
- `Right Shift + Esc`: `~`
- `Right Shift + Left Shift + Esc`: 백틱
- `CapsLock + I/J/K/L`: 방향키
- `CapsLock + H + J/L/I/K`: `Home`, `End`, `PageUp`, `PageDown`
- `CapsLock + Space/Z/X/C/A/S/D/Q/W/E`: 숫자 `0`-`9`
- `CapsLock + 방향키`: 화살표 문자 `↑↓←→`
- `CapsLock + Tab`: CapsLock 토글
- `Ctrl + Shift + Q`: 종료

## exe 빌드

낮은 Windows 버전까지 고려하면 빌드에 사용한 Python 버전이 중요합니다. 현재 앱 코드는 Python 3.12에서도 동작하도록 유지하는 것을 권장합니다.

```powershell
python -m pip install pyinstaller
pyinstaller --onefile --name LoginKeyboard .\login_keyboard.py
```

콘솔 없이 실행하려면:

```powershell
pyinstaller --onefile --noconsole --name LoginKeyboard .\login_keyboard.py
```

## macOS 버전

macOS용 구현과 `.app` 패키징 방법은 `macos/README_macos.md`를 확인하세요. macOS 버전은 Caps Lock을 `F18`로 리매핑한 뒤 사용합니다.

## 참고

기존에 깨져 있던 파일은 `login_keyboard_broken.py`, `README_login_keyboard_broken.md`로 백업해 두었습니다.
