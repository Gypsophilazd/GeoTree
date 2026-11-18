param([string]$Distro = 'Ubuntu', [switch]$BuildSmokeImage)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$linux = & wsl.exe -d $Distro -- wslpath -a $root
if ($LASTEXITCODE -ne 0 -or !$linux) { throw 'WSL path unavailable. Run scripts/doctor.ps1 and check the distro and repository mount.' }
& wsl.exe -d $Distro --cd "$linux" -- bash scripts/setup-linux.sh
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($BuildSmokeImage) {
    & wsl.exe -d $Distro --cd "$linux" -- docker build -f docker/smoke.Dockerfile -t geotree-smoke:freecad-1.1 .
    exit $LASTEXITCODE
}
