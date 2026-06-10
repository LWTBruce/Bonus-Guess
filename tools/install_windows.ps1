$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$FrontendDir = Join-Path $ProjectRoot "frontend"
$RunScript = Join-Path $FrontendDir "run_game_hidden.vbs"
$IconPath = Join-Path $FrontendDir "assets\bonus_guess.ico"
$Requirements = Join-Path $ProjectRoot "requirements.txt"

function Find-Python {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        return @{ Exe = $py.Source; Args = @("-3") }
    }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) {
        return @{ Exe = $python.Source; Args = @() }
    }
    throw "Python 3.10+ was not found. Install Python and enable Add Python to PATH."
}

function Invoke-GamePython {
    param([string[]] $PythonArgs)
    & $script:Python["Exe"] @(($script:Python["Args"]) + $PythonArgs)
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $($PythonArgs -join ' ')"
    }
}

if (!(Test-Path $RunScript)) {
    throw "Launch script not found: $RunScript"
}
if (!(Test-Path $Requirements)) {
    throw "Requirements file not found: $Requirements"
}

$script:Python = Find-Python
Write-Host "Using Python:" $script:Python["Exe"] ($script:Python["Args"] -join " ")
Invoke-GamePython @("-m", "pip", "install", "--upgrade", "pip")
Invoke-GamePython @("-m", "pip", "install", "-r", $Requirements)

$Desktop = [Environment]::GetFolderPath("DesktopDirectory")
$ShortcutName = -join ((0x6709, 0xff08, 0x00d7, 0xff09, 0x65e0, 0x5956, 0x7ade, 0x731c) | ForEach-Object { [char]$_ })
$ShortcutPath = Join-Path $Desktop ($ShortcutName + ".lnk")
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $RunScript
$Shortcut.WorkingDirectory = $FrontendDir
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
}
$Shortcut.Description = "Launch Bonus Guess"
$Shortcut.Save()

Write-Host "Install complete. Desktop shortcut:" $ShortcutPath
Write-Host "Offline data directory:" (Join-Path $ProjectRoot "profile")
