@echo off
cd /d "%~dp0"
python build_release.py
exit /b %errorlevel%
