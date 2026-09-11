@echo off
chcp 65001 >nul
echo [1/3] Завершение всех процессов Antigravity...
taskkill /F /T /IM "Antigravity IDE.exe" 2>nul
taskkill /F /T /IM "Antigravity.exe" 2>nul
timeout /t 1 /nobreak >nul

echo [2/3] Запуск установщика русификации...
if exist "AntigravityLocalizer.exe" (
    start "" "AntigravityLocalizer.exe"
) else (
    python antigravity_localizer.py
)
