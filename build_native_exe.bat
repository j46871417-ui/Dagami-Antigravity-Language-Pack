@echo off
chcp 65001 >nul
echo ==========================================================
echo    Сборка автономного AntigravityLocalizer.exe (.NET / C#)
echo ==========================================================
echo.

echo [*] Упаковка встроенных ресурсов в payload.zip...
powershell -ExecutionPolicy Bypass -Command "if (Test-Path payload.zip) { Remove-Item payload.zip }; Add-Type -Assembly System.IO.Compression.FileSystem; $zip = [System.IO.Compression.ZipFile]::Open('payload.zip', 'Create'); Get-ChildItem -Recurse 'resources' | Where-Object { -not $_.PSIsContainer } | ForEach-Object { [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $_.FullName.Substring((Get-Item '.').FullName.Length + 1).Replace('\', '/')) }; Get-ChildItem -Recurse 'translations' | Where-Object { -not $_.PSIsContainer } | ForEach-Object { [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $_.FullName.Substring((Get-Item '.').FullName.Length + 1).Replace('\', '/')) }; $zip.Dispose()"

echo [*] Компиляция через системный csc.exe...
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /optimize+ /platform:anycpu /r:System.dll /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.IO.Compression.dll /r:System.IO.Compression.FileSystem.dll /r:System.Core.dll /r:System.Web.Extensions.dll /resource:payload.zip,payload.zip /out:AntigravityLocalizer.exe Program.cs

if exist AntigravityLocalizer.exe copy /y AntigravityLocalizer.exe AntigravityLocalizer_v0.9.5.exe

if exist payload.zip del payload.zip
echo.
echo [✓] Готово! Создан чистый автономный AntigravityLocalizer.exe и AntigravityLocalizer_v0.9.5.exe
