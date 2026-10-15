@echo off
chcp 65001 >nul
title Dagami Antigravity Language Pack
cd /d "%~dp0"

echo ==========================================================
echo    🚀 Dagami Antigravity Language Pack
echo    https://github.com/j46871417-ui/Antigravity-Localizer
echo    Telegram: https://t.me/+8qU7020rMF84OWNi
echo    Donation: https://pay.cloudtips.ru/p/671fda86
echo ==========================================================
echo.

if exist "%~dp0dagami_ag_localizer.py" (
    python "%~dp0dagami_ag_localizer.py" %*
) else if exist "%~dp0install.ps1" (
    powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
) else (
    powershell -ExecutionPolicy Bypass -Command "& { $(irm https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.ps1) }"
)

if "%1"=="" pause
