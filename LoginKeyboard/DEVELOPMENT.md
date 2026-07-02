# LoGinKeyboard Developer Notes

이 문서는 나중에 코드를 다시 볼 때 빠르게 구조와 배포 방법을 파악하기 위한 개발자용 명세입니다.

## 현재 버전

- 앱 버전: `3.1.0`
- 메인 코드: `login_keyboard.py`
- 배포 파일: `releases/3.1.0/LoGinKeyboard-v3.1.0.exe`
- 배포 메모: `releases/3.1.0/RELEASE_NOTES.txt`

## 앱 목적

LoGinKeyboard는 Windows 전용 키보드 보조 유틸리티입니다. AutoHotkey로 쓰던 키보드 레이어 기능을 Python으로 옮긴 버전이며, 전역 키보드 훅과 시스템 트레이를 사용합니다.

## 주요 기능

- `NumLock`은 켜진 상태로 유지합니다.
- `CapsLock`, `ScrollLock`은 꺼진 상태로 유지합니다.
- `CapsLock`은 한/영 전환 및 커스텀 키보드 레이어로 사용합니다.
- `Right Ctrl` 조합으로 탐색, 검색, 번역 기능을 제공합니다.
- Windows 시스템 트레이에서 실행 여부를 확인하고 종료할 수 있습니다.
- League Client 창이 포그라운드일 때 마우스 왼쪽 클릭을 감지하면 앱을 종료합니다.

## 코드 구조

- Windows API/상수: `ctypes` 기반 키 상태 제어, 포그라운드 프로세스 조회, 마우스 훅
- 단일 실행 보장: Windows Mutex 사용
- 트레이: `pystray`와 `Pillow`로 메모리 아이콘 생성
- GUI: `tkinter`로 도움말/연습 창 표시
- 키보드 레이어: `keyboard` 패키지의 전역 hotkey/hook 사용
- 클립보드 검색/번역: `pyperclip`, `webbrowser` 사용

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
| `CapsLock + Space/Z/X/C/A/S/D/Q/W/E` | 숫자 `0`-`9` |
| `CapsLock + 방향키` | 화살표 문자 `↑↓←→` 입력 |
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
- Python 3.14 64-bit
- PowerShell

설치:

```powershell
python -m pip install -r requirements.txt
```

로컬 실행:

```powershell
python .\login_keyboard.py
```

키보드 훅이 동작하지 않으면 PowerShell 또는 exe를 관리자 권한으로 실행합니다.

## 단일 exe 빌드

버전별 배포 폴더에 직접 빌드합니다.

```powershell
python -m PyInstaller --onefile --noconsole --name LoGinKeyboard-v3.1.0 --distpath releases\3.1.0 --workpath build\LoGinKeyboard-v3.1.0 --specpath build\LoGinKeyboard-v3.1.0 --hidden-import keyboard --hidden-import pyperclip --hidden-import pystray --hidden-import PIL login_keyboard.py
```

빌드 후 배포 대상:

```text
releases\3.1.0\LoGinKeyboard-v3.1.0.exe
```

## 버전 관리 규칙

새 버전 배포 시 권장 순서:

1. `login_keyboard.py`의 `APP_VERSION`을 변경합니다.
2. `releases/<version>/RELEASE_NOTES.txt`를 작성합니다.
3. PyInstaller 명령의 `--name`, `--distpath`, `--workpath`, `--specpath` 버전을 맞춥니다.
4. 빌드 후 `build/`, `__pycache__/`, 임시 `.spec` 파일은 삭제합니다.
5. 최종 배포 파일은 `releases/<version>/LoGinKeyboard-v<version>.exe`만 사용합니다.

## 배포 주의 사항

- 이 앱은 키보드 훅을 사용하므로 Windows Defender나 백신이 민감하게 볼 수 있습니다.
- 일부 PC에서는 관리자 권한 실행이 필요할 수 있습니다.
- 회사/학교 PC처럼 보안 정책이 강한 환경에서는 실행이 차단될 수 있습니다.
- exe는 Windows 전용입니다.
