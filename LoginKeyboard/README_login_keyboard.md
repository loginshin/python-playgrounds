# Login Keyboard

키보드 입력 자동화/클립보드 처리를 위한 Python 스크립트입니다.

## 준비 사항

- Windows
- Python 3.10 이상 권장

`keyboard` 패키지는 전역 키 입력을 감지하거나 제어할 때 관리자 권한이 필요할 수 있습니다. 실행이 되지 않거나 키 입력이 감지되지 않으면 PowerShell 또는 생성된 exe를 **관리자 권한으로 실행**하세요.

## 실행 방법

1. 프로젝트 폴더로 이동합니다.

```powershell
cd C:\workspace\GitHub\python-playgrounds\LoginKeyboard
```

2. 가상환경을 생성하고 활성화합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

PowerShell에서 스크립트 실행 정책 오류가 나면 아래 명령을 한 번 실행한 뒤 다시 활성화합니다.

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. 필요한 패키지를 설치합니다.

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. 프로그램을 실행합니다.

```powershell
python .\login_keyboard.py
```

키보드 후킹이 동작하지 않으면 PowerShell을 관리자 권한으로 열고 다시 실행하세요.

## exe 파일 만들기

`PyInstaller`를 사용하면 Python이 설치되지 않은 PC에서도 실행할 수 있는 exe 파일을 만들 수 있습니다.

1. 가상환경이 활성화된 상태에서 PyInstaller를 설치합니다.

```powershell
pip install pyinstaller
```

2. exe 파일을 생성합니다.

```powershell
pyinstaller --onefile --name LoginKeyboard .\login_keyboard.py
```

3. 빌드가 끝나면 아래 경로에 exe 파일이 생성됩니다.

```text
dist\LoginKeyboard.exe
```

실행:

```powershell
.\dist\LoginKeyboard.exe
```

콘솔 창 없이 실행하고 싶다면 아래 옵션을 사용할 수 있습니다.

```powershell
pyinstaller --onefile --noconsole --name LoginKeyboard .\login_keyboard.py
```

다만 오류 메시지를 확인하기 어렵기 때문에, 처음 빌드할 때는 `--noconsole` 없이 만드는 것을 권장합니다.

## 빌드 파일 정리

PyInstaller 실행 후 생성되는 `build` 폴더와 `.spec` 파일은 다시 빌드할 때 없어도 됩니다.

```powershell
Remove-Item -Recurse -Force .\build
Remove-Item -Force .\LoginKeyboard.spec
```

완성된 exe만 배포하려면 `dist\LoginKeyboard.exe` 파일을 전달하면 됩니다.
