@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m PyInstaller --clean --noconfirm bonus_guess.spec
echo.
echo 构建完成后，exe 位于 dist\有（×）无奖竞猜.exe
