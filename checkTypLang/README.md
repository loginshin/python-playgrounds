# 입력 언어 표시기

Windows의 텍스트 입력 커서 오른쪽 아래에 현재 입력 언어를 작게 표시합니다.

- 한국어: `한`
- 영어: `EN`
- 일본어: `日`
- 중국어: `中`
- 그 밖의 언어: Windows 언어 ID

## 실행

Python 3가 설치된 Windows에서 다음 명령을 실행합니다.

```powershell
python input_language_indicator.py
```

메모장이나 브라우저의 입력칸을 클릭하면 표시기가 나타나며, 입력칸을 벗어나면
자동으로 숨겨집니다. 종료하려면 실행한 터미널에서 `Ctrl+C`를 누르세요.

Python이 설치되어 있지 않다면 `reales` 폴더의 최신 버전 폴더에 있는
`InputLanguageIndicator.exe`를 실행하세요.

## 배포 버전

실행 파일은 아래와 같이 버전별로 보관합니다.

```text
reales/
├── v0.1.0/
│   ├── InputLanguageIndicator.exe
│   └── RELEASE_NOTES.txt
└── v0.2.0/
│   ├── InputLanguageIndicator.exe
│   └── RELEASE_NOTES.txt
└── v0.3.0/
│   ├── InputLanguageIndicator.exe
│   └── RELEASE_NOTES.txt
└── v0.4.0/
    ├── InputLanguageIndicator.exe
    └── RELEASE_NOTES.txt
```

## 시작할 때 자동 실행하기

`Win + R`을 누르고 `shell:startup`을 입력한 뒤, 아래 내용을 담은
`input-language-indicator.bat` 바로가기를 시작프로그램 폴더에 넣습니다.

```bat
@echo off
pythonw "C:\이 프로젝트의 경로\input_language_indicator.py"
```

위 경로는 실제 파일이 있는 경로로 바꾸세요.
