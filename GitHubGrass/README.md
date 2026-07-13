# GitHub Grass

원하는 날짜의 Git 커밋을 만들고 GitHub 원격 저장소에 푸시하는 PowerShell 도구입니다. 커밋 내용은 저장소 루트의 `.github-grass.log`에 한 줄씩 기록됩니다.

이 도구는 방금 사용한 방식과 동일하게 `GIT_AUTHOR_DATE`와 `GIT_COMMITTER_DATE`를 함께 지정합니다. 본인이 관리하는 저장소에서 실제 기록이 필요한 경우에만 사용하세요.

## 준비 사항

- Git과 PowerShell이 설치되어 있어야 합니다.
- 대상 저장소의 작업 트리가 깨끗해야 합니다.
- 현재 브랜치가 GitHub 저장소의 기본 브랜치여야 합니다.
- `git config user.email`이 본인의 GitHub 계정에 등록된 이메일이어야 합니다.
- 포크가 아닌 독립 저장소에서 실행해야 합니다.

설정을 확인하려면 다음 명령을 실행합니다.

```powershell
git status
git branch --show-current
git config user.name
git config user.email
```

## 사용법

대상 Git 저장소의 루트에서 실행합니다.

```powershell
.\GitHubGrass\github-grass.ps1 -Date '2026-07-13'
```

실행 정책 때문에 차단되면 현재 실행에만 우회 옵션을 적용할 수 있습니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\GitHubGrass\github-grass.ps1 -Date '2026-07-13'
```

여러 개의 커밋을 만들려면 `-Count`를 지정합니다.

```powershell
.\GitHubGrass\github-grass.ps1 -Date '2026-07-13' -Count 3
```

로컬 커밋만 만들고 자동 푸시는 생략할 수 있습니다.

```powershell
.\GitHubGrass\github-grass.ps1 -Date '2026-07-13' -NoPush
```

아무것도 변경하지 않고 설정과 실행 계획만 검사할 수도 있습니다.

```powershell
.\GitHubGrass\github-grass.ps1 -Date '2026-07-13' -DryRun
```

다른 저장소를 대상으로 실행할 때는 절대 경로를 지정합니다.

```powershell
.\GitHubGrass\github-grass.ps1 `
  -Date '2026-07-13' `
  -RepositoryPath 'C:\workspace\GitHub\my-project'
```

## 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `-Date` | 오늘 | 커밋 날짜, `yyyy-MM-dd` 형식 |
| `-Count` | `1` | 생성할 커밋 수, 1~1000 |
| `-RepositoryPath` | 현재 폴더 | 대상 Git 저장소 |
| `-LogFile` | `.github-grass.log` | 커밋에 사용할 기록 파일 |
| `-NoPush` | 꺼짐 | 커밋 후 자동 푸시 생략 |
| `-DryRun` | 꺼짐 | 변경 없이 사전 검사만 수행 |

## GitHub 잔디 반영 조건

GitHub 공식 문서 기준으로 커밋 기여가 표시되려면 다음 조건을 만족해야 합니다.

- 커밋 이메일이 GitHub 계정과 연결되어 있어야 합니다.
- 포크가 아닌 독립 저장소여야 합니다.
- 저장소의 기본 브랜치 또는 `gh-pages` 브랜치에 커밋이 있어야 합니다.
- 프로필의 날짜 계산에는 Git 작성자 날짜(author date)가 사용됩니다.

스크립트는 작성자 날짜와 커미터 날짜를 같은 값으로 설정하지만, 이메일 등록 여부와 현재 브랜치가 기본 브랜치인지는 GitHub에서 직접 확인해야 합니다. 조건을 만족해도 기여 그래프 반영에 최대 24시간이 걸릴 수 있습니다.

참고: [GitHub 프로필 기여 기준](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference), [누락된 기여 문제 해결](https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/troubleshooting-missing-contributions)

## 생성 결과

기본 실행 시 다음 두 작업을 수행합니다.

1. 저장소 루트의 `.github-grass.log`에 기록을 추가하고 지정 날짜로 커밋합니다.
2. 현재 브랜치를 `origin`에 푸시합니다.

작업 트리에 다른 변경이 있으면 관련 없는 파일이 섞이지 않도록 실행을 중단합니다.
