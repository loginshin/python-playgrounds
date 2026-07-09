# LoGinKeyboard macOS

macOS용 LoGinKeyboard는 Windows 버전과 별도 구현입니다. Windows의 `SetWindowsHookExW`와 `keyboard` 패키지 대신 macOS Quartz Event Tap을 사용합니다.

## 중요한 차이

macOS의 기본 Caps Lock 키는 누름/뗌 이벤트가 안정적인 레이어 키처럼 동작하지 않습니다. 그래서 이 버전은 Caps Lock을 `F18`로 리매핑한 뒤, `F18`을 LoGinKeyboard 레이어 키로 사용합니다.

권장 설정:

1. Karabiner-Elements 설치
2. Caps Lock을 `F18`로 리매핑
3. LoGinKeyboard-macOS 실행
4. `System Settings > Privacy & Security > Accessibility`에서 앱 권한 허용

## 설치

```bash
cd LoginKeyboard
python3 -m pip install -r macos/requirements-macos.txt
```

## 실행

```bash
python3 macos/login_keyboard_macos.py
```

권한 오류가 나오면 macOS 설정에서 터미널 또는 빌드한 앱에 Accessibility 권한을 부여한 뒤 다시 실행하세요.

## 단축키

| 단축키 | 동작 |
| --- | --- |
| `F18 + I/J/K/L` | 방향키 |
| `F18 + H + J/L/I/K` | `Home` / `End` / `PageUp` / `PageDown` |
| `F18 + Space/Z/X/C/A/S/D/Q/W/E` | Keypad `0`-`9` |
| `F18 + 방향키` | 실제 방향키 입력 |
| `F18 + Tab` | 실제 Caps Lock 토글 |
| `F18` 짧게 누름 | 입력 소스 전환용 `Control + Space` |
| `F18` 1초 이상 누름 | 실제 Caps Lock 토글 |
| `Right Control + 방향키` | `Home` / `End` / `PageUp` / `PageDown` |
| `Right Control + Return` | 선택한 텍스트 Google 검색 |
| `Right Control + Right Shift` | 선택한 텍스트 Google 번역 |
| `Right Shift + Esc` | `~` 입력 |
| `Right Shift + Left Shift + Esc` | 백틱 입력 |
| `Control + Shift + Q` | 종료 |

## app 패키징

macOS에서 실행:

```bash
chmod +x macos/build_macos.sh
./macos/build_macos.sh
```

빌드 결과:

```text
releases/macos/LoGinKeyboard-macOS.app
```

## 배포 주의 사항

- 빌드는 macOS에서 해야 합니다. Windows에서 macOS `.app`을 만들 수 없습니다.
- 전역 키 입력을 감지하므로 Accessibility 권한이 필요합니다.
- 처음 실행 시 Gatekeeper 또는 보안 설정에서 차단될 수 있습니다.
- 서명/공증하지 않은 앱은 다른 Mac에서 실행할 때 추가 확인이 필요할 수 있습니다.
