# LoGinKeyboard Python

Windows 전역 키보드 입력을 재매핑하는 유틸리티입니다. 실행 진입점은
`login_keyboard.py`이며 실제 Windows 구현은 `login_keyboard_windows/` 패키지에
나뉘어 있습니다.

## 지원 환경

- 권장: Windows 10/11, Python 3.12 64-bit
- Windows 10/11만 대상으로 빌드: Python 3.14 64-bit 사용 가능
- Windows 7까지 지원해야 하는 별도 빌드: Python 3.8 기반 검토 필요

전역 키보드 입력을 가로채므로 일부 PC에서는 관리자 권한이 필요할 수 있습니다.

## 처음 설치하기

PowerShell을 열고 프로젝트 폴더로 이동합니다.

```powershell
cd C:\workspace\GitHub\python-playgrounds\LoginKeyboard
```

Python 버전을 확인합니다.

```powershell
py --version
```

필요한 패키지를 설치합니다.

```powershell
py -m pip install -r requirements.txt
```

`py` 명령을 찾을 수 없다면 Python을 설치할 때 **Python Launcher**를 함께
설치해야 합니다. 이 PC에서는 `python` 명령이 Microsoft Store 실행 별칭을
가리켜 `Python`만 출력할 수 있으므로 `py` 사용을 권장합니다.

## Python으로 실행하기

```powershell
py .\login_keyboard.py
```

프로그램은 콘솔에서 계속 실행되며 시스템 트레이에 아이콘이 표시됩니다.
키 입력이 동작하지 않으면 PowerShell을 관리자 권한으로 열고 다시 실행합니다.

종료 방법:

- `Ctrl + Shift + Q`
- 시스템 트레이 아이콘을 우클릭한 뒤 `종료`
- 콘솔에서 `Ctrl + C`

코드를 수정한 경우 실행 중인 프로그램을 종료한 뒤 다시 실행해야 변경 내용이
반영됩니다.

## 주요 단축키

| 단축키 | 입력 결과 |
| --- | --- |
| `Right Ctrl + Left` | 실제 `Home` 키 입력 |
| `Right Ctrl + Right` | 실제 `End` 키 입력 |
| `Right Ctrl + Up` | 실제 `Page Up` 키 입력 |
| `Right Ctrl + Down` | 실제 `Page Down` 키 입력 |
| `Right Ctrl + Enter` | 선택한 문자열 Google 검색 |
| `Right Ctrl + Right Shift` | 선택한 문자열 Google 번역 |
| `Right Ctrl + CapsLock` | 도움말 GUI 열기 |
| `CapsLock + I/J/K/L` | 방향키 입력 |
| `CapsLock + H + J/L/I/K` | `Home` / `End` / `Page Up` / `Page Down` 입력 |
| `CapsLock + Space/Z/X/C/A/S/D/Q/W/E` | 실제 넘버패드 `0`-`9` 키 입력 |
| `CapsLock + Tab` | 실제 CapsLock 토글 |
| `Right Shift + Esc` | `~` 키 입력 |
| `Right Shift + Left Shift + Esc` | 백틱 키 입력 |
| `Ctrl + Shift + Q` | 프로그램 종료 |

## 단일 EXE 만들기

EXE는 반드시 Windows에서 빌드해야 합니다. 먼저 실행 중인 LoGinKeyboard를
종료한 다음 PyInstaller를 설치합니다.

```powershell
py -m pip install pyinstaller
```

콘솔 창이 표시되지 않는 단일 EXE를 빌드합니다.

```powershell
py -m PyInstaller --clean --noconfirm --onefile --noconsole --name LoGinKeyboard .\login_keyboard.py
```

빌드가 끝나면 다음 파일이 생성됩니다.

```text
dist\LoGinKeyboard.exe
```

`--onefile` 옵션이 `login_keyboard_windows/` 패키지와 필요한 라이브러리를
하나의 EXE 안에 묶습니다. 소스 코드를 실제 한 파일로 합칠 필요는 없습니다.

오류를 확인하기 위한 콘솔 포함 EXE가 필요하면 `--noconsole`을 빼고 빌드합니다.

```powershell
py -m PyInstaller --clean --noconfirm --onefile --name LoGinKeyboard-debug .\login_keyboard.py
```

소스를 수정한 후에는 기존 EXE가 자동으로 바뀌지 않습니다. 같은 빌드 명령을
다시 실행하고 새로 생성된 `dist\LoGinKeyboard.exe`를 사용해야 합니다.

## 다른 컴퓨터에서 실행하기

다른 Windows 컴퓨터에는 Python이나 소스 파일이 없어도 EXE 하나만 전달하면
됩니다. 다만 다음 제한이 있습니다.

- Windows 전용 프로그램이며 macOS에서는 Windows EXE를 실행할 수 없습니다.
- 전역 키보드 훅 특성상 관리자 권한이 필요할 수 있습니다.
- 서명되지 않은 개인 EXE이므로 Windows Defender 또는 SmartScreen 경고가
  표시될 수 있습니다.
- 낮은 Windows 버전 지원 범위는 EXE를 만든 Python 버전에 영향을 받습니다.

macOS 구현과 `.app` 빌드 방법은 `macos/README_macos.md`를 참고하세요. 상세한
개발 구조와 버전별 배포 명령은 `DEVELOPMENT.md`에 정리되어 있습니다.
