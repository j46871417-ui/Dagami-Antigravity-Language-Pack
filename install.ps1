<#
.SYNOPSIS
    Dagami Antigravity Language Pack — Универсальный мультиязычный установщик
.DESCRIPTION
    Устанавливает или удаляет языковые пакеты (ru, zh, es, ja, de, fr и др.) для Google Antigravity Desktop и IDE.
    100% безопасная модификация in-place без повреждения системных зависимостей и без привязки к устаревшим версиям.
    Поддерживает запуск одной строкой через консоль PowerShell:
    irm https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.ps1 | iex
.LINK
    https://github.com/j46871417-ui/Antigravity-Localizer
#>

param(
    [string]$Lang = "",
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$List,
    [switch]$Update,
    [string]$AppDir = "$env:LOCALAPPDATA\Programs\antigravity",
    [string]$IdeDir = "$env:LOCALAPPDATA\Programs\Antigravity IDE",
    [string]$ExpectedHash = ""
)

$ErrorActionPreference = 'Stop'

$Host.UI.RawUI.WindowTitle = "Dagami Antigravity Language Pack"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    🚀 Dagami Antigravity Language Pack                   " -ForegroundColor Green
Write-Host "    Мультиязычная локализация Google Antigravity (v1.1.0)" -ForegroundColor White
Write-Host "    Репозиторий: https://github.com/j46871417-ui/Antigravity-Localizer" -ForegroundColor Gray
Write-Host "    Telegram:    https://t.me/+8qU7020rMF84OWNi" -ForegroundColor Cyan
Write-Host "    Поддержка:   https://pay.cloudtips.ru/p/671fda86" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Поиск исполняемого файла Python
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonExe = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "C:\Python314\python.exe",
        "C:\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            $PythonExe = $c
            break
        }
    }
}

# 2. Проверка путей к приложению
$HasDesktop = Test-Path "$AppDir\Antigravity.exe"
$HasIde = Test-Path "$IdeDir\Antigravity.exe"
if (-not $HasIde) {
    $HasIde = Test-Path "$IdeDir\Antigravity IDE.exe"
}

if (-not $HasDesktop -and -not (Test-Path "$AppDir")) {
    $altPath = "$env:PROGRAMFILES\antigravity"
    if (Test-Path "$altPath\Antigravity.exe") {
        $AppDir = $altPath
        $HasDesktop = $true
    }
}

if ($HasDesktop) {
    Write-Host "[+] Обнаружен Antigravity Desktop: $AppDir" -ForegroundColor Green
}
if ($HasIde) {
    Write-Host "[+] Обнаружен Antigravity IDE:     $IdeDir" -ForegroundColor Green
}

# 3. Обработка флага --list
if ($List) {
    if ($PythonExe) {
        $ScriptPath = Join-Path $PSScriptRoot "dagami_ag_localizer.py"
        if (Test-Path $ScriptPath) {
            & $PythonExe $ScriptPath --list
            return
        }
    }
    Write-Host "Доступные языки: ru (Русский), zh (简体中文), es (Español), ja (日本語), de (Deutsch), fr (Français)" -ForegroundColor White
    return
}

# 4. Режим интерактивного выбора действия
if (-not $Install -and -not $Uninstall -and -not $Update -and [string]::IsNullOrWhiteSpace($Lang)) {
    if ([Console]::IsInputRedirected -or [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        $Lang = "ru"
        $Install = $true
    } else {
        Write-Host "Выберите действие:" -ForegroundColor Yellow
        Write-Host " [1] Установить русский язык (Russian / ru)" -ForegroundColor White
        Write-Host " [2] Установить китайский язык (Chinese / zh)" -ForegroundColor White
        Write-Host " [3] Установить испанский язык (Spanish / es)" -ForegroundColor White
        Write-Host " [4] Установить японский язык (Japanese / ja)" -ForegroundColor White
        Write-Host " [5] Ввести другой код языка..." -ForegroundColor White
        Write-Host " [6] Восстановить оригинальную версию Google (English)" -ForegroundColor White
        Write-Host " [7] Показать список всех языков (--list)" -ForegroundColor White
        Write-Host " [0] Отмена" -ForegroundColor Gray
        Write-Host ""
        $choice = Read-Host "Введите номер действия [1]"
        if ($choice -eq "2") {
            $Lang = "zh"
            $Install = $true
        } elseif ($choice -eq "3") {
            $Lang = "es"
            $Install = $true
        } elseif ($choice -eq "4") {
            $Lang = "ja"
            $Install = $true
        } elseif ($choice -eq "5") {
            $Lang = Read-Host "Введите код языка (например, de, fr)"
            $Install = $true
        } elseif ($choice -eq "6") {
            $Uninstall = $true
        } elseif ($choice -eq "7") {
            $List = $true
        } elseif ($choice -eq "0") {
            Write-Host "[*] Отменено пользователем." -ForegroundColor Yellow
            return
        } else {
            $Lang = "ru"
            $Install = $true
        }
    }
}

if ([string]::IsNullOrWhiteSpace($Lang)) {
    $Lang = "ru"
}

$ResourcesDir = Join-Path $AppDir "resources"
$TargetAsar = Join-Path $ResourcesDir "app.asar"
$BackupAsar = Join-Path $ResourcesDir "app.asar.original_backup"

# --- РЕЖИМ УДАЛЕНИЯ / ВОССТАНОВЛЕНИЯ ---
if ($Uninstall) {
    Write-Host ""
    Write-Host "[*] Восстановление оригинальной английской версии Google..." -ForegroundColor Cyan

    $procs = Get-Process -Name "Antigravity", "Antigravity IDE" -ErrorAction SilentlyContinue
    if ($procs) {
        Write-Host "[*] Закрытие запущенных процессов Antigravity..." -ForegroundColor Yellow
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    $asarRestored = $false
    if (Test-Path $BackupAsar) {
        Copy-Item -Path $BackupAsar -Destination $TargetAsar -Force
        Write-Host "[+] Оригинальный app.asar успешно восстановлен из резервной копии." -ForegroundColor Green
        $asarRestored = $true
    } else {
        $bakAlt = "$TargetAsar.bak.original"
        if (Test-Path $bakAlt) {
            Copy-Item -Path $bakAlt -Destination $TargetAsar -Force
            Write-Host "[+] Оригинальный app.asar успешно восстановлен из .bak.original." -ForegroundColor Green
            $asarRestored = $true
        } else {
            $latestBak = Get-ChildItem -Path $ResourcesDir -Filter "app.asar.bak.v*" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($latestBak) {
                Copy-Item -Path $latestBak.FullName -Destination $TargetAsar -Force
                Write-Host "[+] Оригинальный app.asar восстановлен из версионированного бэкапа ($($latestBak.Name))." -ForegroundColor Green
                $asarRestored = $true
            } else {
                Write-Host "[!] Резервная копия app.asar не найдена." -ForegroundColor Yellow
            }
        }
    }

    if (Test-Path $TargetBundle) {
        if ($asarRestored) {
            Remove-Item -Path $TargetBundle -Recurse -Force
            Write-Host "[+] Каталог web_bundle_ru удалён." -ForegroundColor Green
        } else {
            Write-Host "[!] ВНИМАНИЕ: web_bundle_ru сохранён, так как app.asar не был восстановлен из бэкапа. Это предотвращает поломку приложения." -ForegroundColor Yellow
        }
    }
    if ($HasIde) {
        $ideExtPkg = Join-Path $IdeDir "resources\app\extensions\antigravity\package.json"
        $ideExtPkgBak = "$ideExtPkg.bak.original"
        if (Test-Path $ideExtPkgBak) {
            Copy-Item -Path $ideExtPkgBak -Destination $ideExtPkg -Force
            Write-Host "[+] Оригинальный package.json для IDE восстановлен." -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "  Оригинальная версия Google Antigravity восстановлена!  " -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    return
}

# --- РЕЖИМ УСТАНОВКИ ---
Write-Host ""
Write-Host "[*] Подготовка к установке языкового пакета '$Lang'..." -ForegroundColor Cyan

$ScriptDir = $PSScriptRoot
$IsRemote = $false

if ([string]::IsNullOrWhiteSpace($ScriptDir) -or (-not (Test-Path "$ScriptDir\dagami_ag_localizer.py"))) {
    $IsRemote = $true
}

$TempDir = $null
$TempZip = $null

try {
    if ($IsRemote) {
        Write-Host "[*] Загрузка актуальных файлов Dagami Language Pack с GitHub..." -ForegroundColor Cyan
        $ZipUrl = "https://github.com/j46871417-ui/Antigravity-Localizer/archive/refs/heads/main.zip"
        $TempDir = Join-Path $env:TEMP ("dagami_ag_" + [guid]::NewGuid().ToString().Substring(0, 8))
        $TempZip = "$TempDir.zip"

        New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $oldProgress = $ProgressPreference
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $ZipUrl -OutFile $TempZip -UseBasicParsing
        $ProgressPreference = $oldProgress

        Expand-Archive -Path $TempZip -DestinationPath $TempDir -Force
        
        $extractedRoot = Get-ChildItem -Path $TempDir -Directory | Select-Object -First 1
        if ($extractedRoot) {
            $ScriptDir = $extractedRoot.FullName
        } else {
            $ScriptDir = Join-Path $TempDir "Antigravity-Localizer-main"
        }
    }

    # Запуск Python-локализатора для гарантированной совместимости с любой версией Antigravity
    if ($PythonExe -and (Test-Path "$ScriptDir\dagami_ag_localizer.py")) {
        Write-Host "[*] Выполнение безопасного патча через Dagami Localizer Core..." -ForegroundColor Cyan
        $argsList = @(
            "$ScriptDir\dagami_ag_localizer.py",
            "--lang", $Lang,
            "--desktop-path", $AppDir
        )
        if ($HasIde) {
            $argsList += @("--ide-path", $IdeDir)

        }
        & $PythonExe $argsList
    } else {
        throw "Не удалось обнаружить исполняемый файл Python или dagami_ag_localizer.py."
    }

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "  Dagami Antigravity Language Pack успешно применён!     " -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "• Telegram сообщество: https://t.me/+8qU7020rMF84OWNi" -ForegroundColor Cyan
    Write-Host "• Поддержать проект:   https://pay.cloudtips.ru/p/671fda86" -ForegroundColor Yellow
    Write-Host "• Для переключения на другой язык: dagami-ag-localizer --lang <код>" -ForegroundColor White
    Write-Host "• Для отката: install.ps1 -Uninstall" -ForegroundColor Gray
    Write-Host ""
}
catch {
    Write-Host "[-] Ошибка установки: $_" -ForegroundColor Red
}
finally {
    if ($TempDir -and (Test-Path $TempDir)) {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($TempZip -and (Test-Path $TempZip)) {
        Remove-Item -Path $TempZip -Force -ErrorAction SilentlyContinue
    }
}
