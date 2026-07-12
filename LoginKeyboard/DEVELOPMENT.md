# LoGinKeyboard Developer Notes

이 문서는 나중에 코드를 다시 볼 때 빠르게 구조와 배포 방법을 파악하기 위한 개발자용 명세입니다.

## 현재 버전

- 앱 버전: `3.1.5`
- 실행 진입점: `login_keyboard_windows/login_keyboard.py`
- Windows 구현 패키지: `login_keyboard_windows/`
- 배포 파일: `login_keyboard_windows/releases/3.1.5/LoGinKeyboard-v3.1.5.exe`
- 배포 메모: `login_keyboard_windows/releases/3.1.5/RELEASE_NOTES.txt`

## 앱 목적

LoGinKeyboard는 Windows 전용 키보드 보조 유틸리티입니다. AutoHotkey로 쓰던 키보드 레이어 기능을 Python으로 옮긴 버전이며, 전역 키보드 훅과 시스템 트레이를 사용합니다.

macOS용 실험 구현은 Windows 코드와 분리해 `macos/` 폴더에 둡니다. macOS 버전은 Quartz Event Tap을 사용하며 Caps Lock을 `F18`로 리매핑한 뒤 레이어 키로 사용합니다.

## 주요 기능

- `NumLock`은 켜진 상태로 유지합니다.
- `CapsLock`, `ScrollLock`은 꺼진 상태로 유지합니다.
- `CapsLock`은 한/영 전환 및 커스텀 키보드 레이어로 사용합니다.
- `Right Ctrl` 조합으로 탐색, 검색, 번역 기능을 제공합니다.
- Windows 시스템 트레이에서 실행 여부를 확인하고 종료할 수 있습니다.
- League Client 창이 포그라운드일 때 마우스 왼쪽 클릭을 감지하면 앱을 종료합니다.

## 코드 구조

- `login_keyboard_windows/login_keyboard.py`: Windows 직접 실행 및 PyInstaller 진입점
- `login_keyboard_windows/config.py`: 앱 버전, URL, 실행/빌드 설정
- `login_keyboard_windows/constants.py`: Windows 가상키, 트레이 메시지, 단축키 매핑
- `login_keyboard_windows/native.py`: `ctypes` 기반 키 입력, Lock 키 상태, 포그라운드 프로세스, 마우스 훅, Mutex
- `login_keyboard_windows/actions.py`: 검색/번역, 백틱, numpad, 방향키 입력 같은 사용자 동작
- `login_keyboard_windows/help_gui.py`: `tkinter` 도움말/연습 창
- `login_keyboard_windows/tray.py`: Windows Shell API 트레이 아이콘과 종료 메뉴
- `login_keyboard_windows/hotkeys.py`: `keyboard` 패키지의 전역 hotkey/hook 등록
- `login_keyboard_windows/app.py`: Windows 앱 시작 순서
- `login_keyboard_legacy.py`: 모듈 분리 전 단일 파일 백업

## 단축키 명세

| 단축키 | 동작 |
| --- | --- |
| `Right Ctrl + CapsLock` | 도움말/연습 GUI 열기 |
| `Right Ctrl + Left` | `Home` |
| `Right Ctrl + Right` | `End` |
| `Right Ctrl + Up` | `PageUp` |
| `Right Ctrl + Down` | `PageDown` |
| `Right Ctrl + Enter` | 선택한 텍스트를 Google 검색 |
| `Right Ctrl + Right Shift` | 선택한 텍스트를 Google 번역 |
| `Right Shift + Esc` | `~` 입력 |
| `Right Shift + Left Shift + Esc` | 백틱 입력 |
| `CapsLock + I/J/K/L` | 방향키 |
| `CapsLock + H + J/L/I/K` | `Home` / `End` / `PageUp` / `PageDown` |
| `Shift/Ctrl + CapsLock + I/J/K/L` | 선택/단어 이동 등 보조키 유지 |
| `Shift/Ctrl + CapsLock + H + J/L/I/K` | `Home` / `End` / `PageUp` / `PageDown` 선택/확장 |
| `CapsLock + Space/Z/X/C/A/S/D/Q/W/E` | `Numpad 0`-`Numpad 9` 실제 키 입력 |
| `CapsLock + 방향키` | 실제 방향키 입력 |
| `CapsLock + Tab` | 실제 CapsLock 토글 |
| `Ctrl + Shift + Q` | 앱 종료 |

## 트레이 메뉴

트레이 아이콘 우클릭 메뉴:

- `LoGinKeyboard 실행 중`: 상태 표시
- `도움말 열기`: GUI 열기
- `블로그 열기`: 안내 블로그 열기
- `종료`: 앱 종료

## 개발 환경

권장 환경:

- Windows 10/11
- Python 3.12 64-bit 권장
- Windows 10/11 전용 배포만 목표라면 Python 3.14 64-bit 사용 가능
- Windows 7까지 별도 지원해야 하면 Python 3.8 기반 빌드 검토
- PowerShell

Python 버전별 배포 기준:

| 대상 Windows | 권장 Python |
| --- | --- |
| Windows 10/11 | `3.14` 가능 |
| Windows 8.1 이상까지 고려 | `3.12` 권장 |
| Windows 7까지 고려 | `3.8` 별도 빌드 검토 |

설치:

```powershell
python -m pip install -r requirements.txt
```

로컬 실행:

```powershell
py .\login_keyboard_windows\login_keyboard.py
```

키보드 훅이 동작하지 않으면 PowerShell 또는 exe를 관리자 권한으로 실행합니다.

## 단일 exe 빌드

버전별 배포 폴더에 직접 빌드합니다.

```powershell
py -m PyInstaller --onefile --noconsole --name LoGinKeyboard-v3.1.5 --distpath login_keyboard_windows\releases\3.1.5 --workpath login_keyboard_windows\build\LoGinKeyboard-v3.1.5 --specpath login_keyboard_windows\build\LoGinKeyboard-v3.1.5 --hidden-import keyboard --hidden-import pyperclip login_keyboard_windows\login_keyboard.py
```

`login_keyboard_windows/login_keyboard.py`는 작은 진입점이지만, PyInstaller가 import 관계를 따라 Windows 패키지를 함께 포함합니다. exe 빌드를 위해 모든 코드를 한 파일에 둘 필요는 없습니다.

빌드 후 배포 대상:

```text
login_keyboard_windows\releases\3.1.5\LoGinKeyboard-v3.1.5.exe
```

## macOS app 빌드

macOS 빌드는 macOS 머신에서만 수행합니다.

```bash
chmod +x macos/build_macos.sh
./macos/build_macos.sh
```

빌드 후 배포 대상:

```text
releases/macos/LoGinKeyboard-macOS.app
```

## 버전 관리 규칙

새 버전 배포 시 권장 순서:

1. `login_keyboard_windows/config.py`의 `APP_VERSION`을 변경합니다.
2. `login_keyboard_windows/releases/<version>/RELEASE_NOTES.txt`를 작성합니다.
3. PyInstaller 명령의 `--name`, `--distpath`, `--workpath`, `--specpath` 버전을 맞춥니다.
4. 빌드 후 `build/`, `__pycache__/`, 임시 `.spec` 파일은 삭제합니다.
5. 최종 배포 파일은 `login_keyboard_windows/releases/<version>/LoGinKeyboard-v<version>.exe`만 사용합니다.

## 배포 주의 사항

- 이 앱은 키보드 훅을 사용하므로 Windows Defender나 백신이 민감하게 볼 수 있습니다.
- 일부 PC에서는 관리자 권한 실행이 필요할 수 있습니다.
- 회사/학교 PC처럼 보안 정책이 강한 환경에서는 실행이 차단될 수 있습니다.
- exe는 Windows 전용입니다.
