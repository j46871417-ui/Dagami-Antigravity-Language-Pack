@echo off
chcp 65001 >nul
echo Building AntigravityLocalizer.exe...
.venv\Scripts\python.exe -m PyInstaller --onefile --noconsole --name AntigravityLocalizer --add-data "translations;translations" --add-data "assets;assets" --clean antigravity_localizer.py
if %ERRORLEVEL% EQU 0 (
    copy /Y dist\AntigravityLocalizer.exe AntigravityLocalizer.exe
    echo Build completed successfully.
) else (
    echo Build failed.
)
