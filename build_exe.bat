@echo off
chcp 65001 >nul
echo Building AntigravityLocalizer.exe...
python -m PyInstaller --onefile --noconsole --name AntigravityLocalizer --add-data "translations;translations" --add-data "assets;assets" --add-data "resources;resources" --clean dagami_ag_localizer.py
if %ERRORLEVEL% EQU 0 (
    copy /Y dist\AntigravityLocalizer.exe AntigravityLocalizer.exe
    echo Verifying built artifact...
    python verify_build_artifact.py AntigravityLocalizer.exe
    if %ERRORLEVEL% EQU 0 (
        echo Build and verification completed successfully.
    ) else (
        echo Build artifact verification failed!
        exit /b 1
    )
) else (
    echo Build failed.
    exit /b 1
)
