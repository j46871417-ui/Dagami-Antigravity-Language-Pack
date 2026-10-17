@echo off
cd /d "%~dp0"
if exist "%~dp0AntigravityLocalizer.exe" (
    "%~dp0AntigravityLocalizer.exe" %*
) else (
    python "%~dp0language_pack.py" %*
)
exit /b %errorlevel%
