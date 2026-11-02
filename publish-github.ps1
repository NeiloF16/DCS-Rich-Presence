# Publishes original source to YOUR GitHub account; Windows CI builds the .exe.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
foreach ($command in @('git', 'gh')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Missing $command. Install Git for Windows and GitHub CLI, then run this script again."
    }
}
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Sign into GitHub first: gh auth login' }
Write-Host "This command creates a PUBLIC repository 'DCS-Rich-Presence' in YOUR GitHub account," -ForegroundColor Yellow
Write-Host 'pushes the included source files, tags v1.0.0 and triggers the Windows EXE build.'
$confirm = Read-Host 'Type PUBLIC to authorize publishing these files on GitHub'
if ($confirm -cne 'PUBLIC') { Write-Host 'Cancelled.'; exit 0 }
if (-not (Test-Path '.git')) {
    git init -b main
    if ($LASTEXITCODE -ne 0) { throw 'Git initialization failed.' }
}
git add --all
if ($LASTEXITCODE -ne 0) { throw 'Git staging failed.' }
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m 'DCS World Rich Presence public v1.0.0'
    if ($LASTEXITCODE -ne 0) { throw 'Git commit failed. Configure git user.name and user.email.' }
}
$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remote)) {
    gh repo create DCS-Rich-Presence --public --source . --remote origin --push --description 'Unofficial DCS World Discord Rich Presence integration'
    if ($LASTEXITCODE -ne 0) { throw 'Repository creation failed.' }
} else {
    Write-Host "Reusing existing remote: $remote"
    git push -u origin HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Git push failed.' }
}
git rev-parse -q --verify refs/tags/v1.0.0 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { throw 'Tag v1.0.0 already exists. Refusing to overwrite a release tag.' }
git tag -a v1.0.0 -m 'DCS World Rich Presence v1.0.0'
if ($LASTEXITCODE -ne 0) { throw 'Tag creation failed.' }
git push origin v1.0.0
if ($LASTEXITCODE -ne 0) { throw 'Tag push failed.' }
Write-Host 'Source uploaded; Windows installer workflow triggered by the v1.0.0 tag.' -ForegroundColor Green
Write-Host 'Open your GitHub repository Actions and Releases tabs to check the build results.'
