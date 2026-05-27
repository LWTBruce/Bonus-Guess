@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "TCL_LIBRARY=%~dp0tcl\tcl8.6"
set "TK_LIBRARY=%~dp0tcl\tk8.6"
set "GAME_LAUNCHER=%~dp0launch_game.pyw"

where pyw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pyw.exe -3 "%GAME_LAUNCHER%"
    exit /b 0
)

for %%P in (
    "%LocalAppData%\Programs\Python\Python314\pythonw.exe"
    "%LocalAppData%\Programs\Python\Python313\pythonw.exe"
    "%LocalAppData%\Programs\Python\Python312\pythonw.exe"
    "%LocalAppData%\Programs\Python\Python311\pythonw.exe"
    "%LocalAppData%\Programs\Python\Python310\pythonw.exe"
) do (
    if exist "%%~fP" (
        start "" "%%~fP" "%GAME_LAUNCHER%"
        exit /b 0
    )
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pythonw.exe "%GAME_LAUNCHER%"
    exit /b 0
)

start "" python "%GAME_LAUNCHER%"
