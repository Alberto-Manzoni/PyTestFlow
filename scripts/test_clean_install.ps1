param(
    [string]$PackageSpec,
    [string]$Suffix = "smoke"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
    throw "pipx is not installed or not in PATH."
}

if (-not $PackageSpec) {
    $repoPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $repoUri = $repoPath -replace "\\", "/"
    $PackageSpec = "git+file:///$repoUri"
}

$appName = "pytestflow-am-$Suffix"
$quickstartDir = Join-Path $env:TEMP ("pytestflow-smoke-" + [guid]::NewGuid())
$outLog = Join-Path $env:TEMP ("pytestflow-smoke-out-" + [guid]::NewGuid() + ".log")
$errLog = Join-Path $env:TEMP ("pytestflow-smoke-err-" + [guid]::NewGuid() + ".log")
$proc = $null

try {
    Write-Host "[1/5] Uninstall previous smoke app (if present)..."
    pipx uninstall $appName | Out-Null

    Write-Host "[2/5] Installing from: $PackageSpec"
    pipx install --force --suffix "-$Suffix" $PackageSpec

    Write-Host "[3/5] Verifying quickstart artifact copy..."
    New-Item -ItemType Directory -Path $quickstartDir -Force | Out-Null
    & $appName quickstart --dest $quickstartDir --force

    $starterFile = Join-Path $quickstartDir "starter_here.md"
    if (-not (Test-Path $starterFile)) {
        throw "quickstart failed: starter_here.md was not created."
    }

    Write-Host "[4/5] Launching backend briefly and checking startup log..."
    $proc = Start-Process -FilePath $appName -ArgumentList "start" -PassThru `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog

    Start-Sleep -Seconds 6

    $stdout = if (Test-Path $outLog) { Get-Content $outLog -Raw } else { "" }
    if ($stdout -notmatch "PyTestFlow backend started") {
        $stderr = if (Test-Path $errLog) { Get-Content $errLog -Raw } else { "" }
        throw "backend smoke launch did not print expected startup banner.`nSTDOUT:`n$stdout`nSTDERR:`n$stderr"
    }

    Write-Host "[5/5] Smoke test passed."
}
finally {
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
    }

    if (Test-Path $quickstartDir) {
        Remove-Item -Path $quickstartDir -Recurse -Force
    }

    if (Test-Path $outLog) {
        Remove-Item -Path $outLog -Force
    }

    if (Test-Path $errLog) {
        Remove-Item -Path $errLog -Force
    }

    pipx uninstall $appName | Out-Null
}
