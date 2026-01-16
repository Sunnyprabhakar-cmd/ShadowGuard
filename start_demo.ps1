$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Get-Command bash -ErrorAction SilentlyContinue) {
    & bash ./start_demo.sh @args
    exit $LASTEXITCODE
}

throw "bash was not found in PATH. Run this from Git Bash/WSL or install Git for Windows and use .\start_demo.ps1 again."
