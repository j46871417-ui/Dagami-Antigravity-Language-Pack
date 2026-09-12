@echo off
chcp 65001 >nul
title Google Antigravity — Русификатор
cd /d "%~dp0"

echo ==========================================================
echo    Google Antigravity — Русификатор (Desktop + IDE)
echo    https://github.com/j46871417-ui/Antigravity-Localizer
echo ==========================================================
echo.

if exist "%~dp0install.ps1" (
    powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
) else (
    powershell -ExecutionPolicy Bypass -Command "$host.UI.RawUI.WindowTitle = 'Antigravity Русификатор'; & { $(irm https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.ps1) }"
)

pause
