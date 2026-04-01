param(
    [string]$FrontendDist = "..\PyTestFlow-FrontEnd\dist",
    [string]$Target = "pytestflow\backend\frontend"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$frontendDistPath = Resolve-Path (Join-Path $repoRoot $FrontendDist)
$targetPath = Join-Path $repoRoot $Target

if (-not (Test-Path (Join-Path $frontendDistPath "index.html"))) {
    throw "Frontend dist is invalid: index.html not found in $frontendDistPath"
}

if (-not (Test-Path $targetPath)) {
    New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
}

Get-ChildItem -Path $targetPath -Force | Remove-Item -Recurse -Force
Copy-Item -Path (Join-Path $frontendDistPath "*") -Destination $targetPath -Recurse -Force

Write-Host "Frontend assets synced from $frontendDistPath to $targetPath"
