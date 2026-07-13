[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Date = (Get-Date -Format 'yyyy-MM-dd'),

    [ValidateRange(1, 1000)]
    [int]$Count = 1,

    [string]$RepositoryPath = (Get-Location).Path,

    [string]$LogFile = '.github-grass.log',

    [switch]$NoPush,

    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $output = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed:`n$($output -join [Environment]::NewLine)"
    }

    return $output
}

$parsedDate = [DateTime]::MinValue
$validDate = [DateTime]::TryParseExact(
    $Date,
    'yyyy-MM-dd',
    [Globalization.CultureInfo]::InvariantCulture,
    [Globalization.DateTimeStyles]::None,
    [ref]$parsedDate
)

if (-not $validDate) {
    throw "Date must be a real date in yyyy-MM-dd format: $Date"
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git is not installed or is not available on PATH.'
}

$repository = (Resolve-Path -LiteralPath $RepositoryPath).Path
Push-Location -LiteralPath $repository

try {
    $insideWorkTree = (Invoke-Git -Arguments @('rev-parse', '--is-inside-work-tree')) -join ''
    if ($insideWorkTree.Trim() -ne 'true') {
        throw "Not a Git repository: $repository"
    }

    $branch = ((Invoke-Git -Arguments @('branch', '--show-current')) -join '').Trim()
    if ([string]::IsNullOrWhiteSpace($branch)) {
        throw 'A detached HEAD is not supported. Check out the repository default branch first.'
    }

    $userName = ((Invoke-Git -Arguments @('config', 'user.name')) -join '').Trim()
    $userEmail = ((Invoke-Git -Arguments @('config', 'user.email')) -join '').Trim()
    if ([string]::IsNullOrWhiteSpace($userName) -or [string]::IsNullOrWhiteSpace($userEmail)) {
        throw 'Configure git user.name and user.email before running this script.'
    }

    $status = (Invoke-Git -Arguments @('status', '--porcelain', '--untracked-files=all')) -join [Environment]::NewLine
    if (-not [string]::IsNullOrWhiteSpace($status)) {
        throw "The working tree must be clean so unrelated changes are not committed:`n$status"
    }

    $hasOrigin = $true
    try {
        $null = Invoke-Git -Arguments @('remote', 'get-url', 'origin')
    }
    catch {
        $hasOrigin = $false
    }

    if (-not $NoPush -and -not $hasOrigin) {
        throw 'The repository has no origin remote. Add one or use -NoPush.'
    }

    $offset = [DateTimeOffset]::Now.Offset
    $baseDate = [DateTimeOffset]::new(
        $parsedDate.Year,
        $parsedDate.Month,
        $parsedDate.Day,
        12,
        0,
        0,
        $offset
    )

    Write-Host "Repository : $repository"
    Write-Host "Branch     : $branch"
    Write-Host "Author     : $userName <$userEmail>"
    Write-Host "Date       : $($baseDate.ToString('yyyy-MM-dd HH:mm:ss zzz'))"
    Write-Host "Commits    : $Count"
    Write-Host "Log file   : $LogFile"
    Write-Host "Push       : $(-not $NoPush)"

    if ($DryRun) {
        Write-Host 'Dry run complete. No file, commit, or remote was changed.'
        return
    }

    $oldAuthorDate = $env:GIT_AUTHOR_DATE
    $oldCommitterDate = $env:GIT_COMMITTER_DATE

    try {
        for ($i = 1; $i -le $Count; $i++) {
            $commitDate = $baseDate.AddSeconds($i - 1).ToString('yyyy-MM-ddTHH:mm:sszzz')
            Add-Content -LiteralPath $LogFile -Value "$commitDate commit $i/$Count" -Encoding utf8

            $null = Invoke-Git -Arguments @('add', '--', $LogFile)
            $env:GIT_AUTHOR_DATE = $commitDate
            $env:GIT_COMMITTER_DATE = $commitDate
            Invoke-Git -Arguments @('commit', '-m', "chore: contribution $Date ($i/$Count)") | Write-Host
        }
    }
    finally {
        $env:GIT_AUTHOR_DATE = $oldAuthorDate
        $env:GIT_COMMITTER_DATE = $oldCommitterDate
    }

    if (-not $NoPush) {
        Invoke-Git -Arguments @('push', '-u', 'origin', $branch) | Write-Host
        Write-Host "Pushed $Count commit(s) to origin/$branch."
    }
    else {
        Write-Host "Created $Count local commit(s). Push the branch when ready."
    }
}
finally {
    Pop-Location
}
