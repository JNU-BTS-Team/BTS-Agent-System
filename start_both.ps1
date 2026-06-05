$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$uiApp = Join-Path $root 'BTS_UI\app.py'
$dlcApp = Join-Path $root 'BTS_UI_DLC\app.py'

$pythonExe = $env:BTS_PYTHON
if (-not $pythonExe -or -not $pythonExe.Trim()) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        $pythonExe = $cmd.Source
    }
}
if (-not $pythonExe -or -not $pythonExe.Trim()) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python*\python.exe'),
        (Join-Path $env:USERPROFILE 'anaconda3\python.exe'),
        (Join-Path $env:USERPROFILE 'miniconda3\python.exe'),
        'C:\ProgramData\Anaconda3\python.exe',
        'C:\ProgramData\Miniconda3\python.exe'
    )
    foreach ($pattern in $candidates) {
        $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found -and $found.FullName) {
            $pythonExe = $found.FullName
            break
        }
    }
}
if (-not $pythonExe -or -not (Test-Path $pythonExe)) {
    Write-Host 'Python executable not found.'
    Write-Host 'Fix: set env var BTS_PYTHON to your python.exe full path, then rerun this script.'
    exit 1
}

$envFile = $env:BTS_START_ENV_FILE
if (-not $envFile -or -not $envFile.Trim()) {
    $envFile = Join-Path $root 'start_both.local.ps1'
}

$uiCmd = "& { Set-Location '$root'; if (Test-Path '$envFile') { . '$envFile' }; `$env:FLASK_HOST='0.0.0.0'; `$env:FLASK_PORT='5000'; `$env:FLASK_DEBUG='0'; & '$pythonExe' '$uiApp' }"
$dlcCmd = "& { Set-Location '$root'; if (Test-Path '$envFile') { . '$envFile' }; `$env:FLASK_HOST='0.0.0.0'; `$env:FLASK_PORT='5001'; `$env:FLASK_DEBUG='0'; & '$pythonExe' '$dlcApp' }"

Start-Process -FilePath 'powershell' -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $uiCmd) -WorkingDirectory $root
Start-Process -FilePath 'powershell' -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $dlcCmd) -WorkingDirectory $root

Write-Host 'Started: UI http://127.0.0.1:5000 , DLC http://127.0.0.1:5001'
