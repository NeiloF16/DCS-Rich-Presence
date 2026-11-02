$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not $IsWindows -and $PSVersionTable.PSEdition -eq 'Core') {
    throw 'Windows is required to build the executable.'
}
python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Installing build dependencies failed.' }
python -m unittest discover -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed. Refusing to package.' }
python -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name DCSRichPresence --icon assets/app.ico `
    --add-data 'NeiloRichPresence.lua;.' `
    --add-data 'assets/app.ico;assets' `
    app.pyw
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
$locations = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "${env:ProgramFiles}\Inno Setup 6\ISCC.exe")
$iscc = $locations | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw 'Inno Setup 6 not found: https://jrsoftware.org/isinfo.php' }
& $iscc installer/DCSRichPresence.iss
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup build failed.' }
Get-ChildItem release/*.exe | Select-Object FullName, Length
