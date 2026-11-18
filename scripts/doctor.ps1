param([string]$Distro = 'Ubuntu')
$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
Write-Host "GeoTree: $root"
$missing = $false
foreach ($cmd in 'git','py','docker','wsl','codex') {
    $tool = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($tool) { Write-Host "[FOUND] $cmd -- $($tool.Source)" }
    else { Write-Host "[MISSING] $cmd on Windows PATH (Codex is optional for Mock; Docker can run via WSL)." }
}
foreach ($relative in 'pyproject.toml','requirements.lock','src/geotree/enhanced_agent_l.py','bridge/windows/relay.py','bridge/windows/action-schema.json','tests/test_harbor_agent_abi.py') {
    if (!(Test-Path -LiteralPath (Join-Path $root $relative))) { Write-Host "[BLOCKED] $relative missing"; $missing = $true }
}
if (Get-Command py -ErrorAction SilentlyContinue) { & py -0p }
if (!(Get-Command wsl.exe -ErrorAction SilentlyContinue)) { Write-Host 'Install WSL2 and Ubuntu, then enable Docker Desktop WSL integration.'; exit 2 }
& wsl.exe --list --verbose
$oldError = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& wsl.exe -d $Distro -- bash -lc 'grep -qi microsoft-standard /proc/sys/kernel/osrelease || { echo "Expected a WSL2 kernel"; exit 2; }; python3 --version; command -v uv || { echo "Install uv in Ubuntu"; exit 3; }; docker info --format "{{.OSType}}" | grep -qx linux || { echo "Start Docker Desktop with Linux containers and WSL integration"; exit 4; }; echo "WSL2/Docker/uv: ready"'
$status = $LASTEXITCODE
$ErrorActionPreference = $oldError
if ($status -ne 0) { Write-Host "Install or select a WSL2 Ubuntu distribution, then rerun with -Distro <name>."; exit 2 }
if ($missing) { exit 2 }
exit 0
