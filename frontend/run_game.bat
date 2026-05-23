@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "TCL_LIBRARY=%~dp0tcl\tcl8.6"
set "TK_LIBRARY=%~dp0tcl\tk8.6"
python bonus_guess.py
if errorlevel 1 pause
