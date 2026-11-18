param([string]$Distro = 'Ubuntu', [switch]$PythonOnly)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$linux = & wsl.exe -d $Distro -- wslpath -a $root
if ($LASTEXITCODE -ne 0 -or !$linux) { throw 'WSL path unavailable. Run scripts/doctor.ps1.' }
$script = if ($PythonOnly) { 'scripts/smoke-python.sh' } else { 'scripts/smoke-linux.sh' }
& wsl.exe -d $Distro --cd "$linux" -- bash $script
exit $LASTEXITCODE
