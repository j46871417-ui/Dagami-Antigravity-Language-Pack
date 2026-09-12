<#
.SYNOPSIS
    Google Antigravity (Desktop & IDE) — Установщик русской локализации (Open Source)
.DESCRIPTION
    Устанавливает или удаляет русификацию десктопного приложения Antigravity 2.0 и Antigravity IDE.
    100% открытый исходный код без срабатываний антивирусов.
    Поддерживает запуск одной строкой через консоль PowerShell:
    irm https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.ps1 | iex
.LINK
    https://github.com/j46871417-ui/Antigravity-Localizer
#>

param(
    [switch]$Install,
    [switch]$Uninstall,
    [string]$AppDir = "$env:LOCALAPPDATA\Programs\antigravity",
    [string]$IdeDir = "$env:LOCALAPPDATA\Programs\Antigravity IDE"
)

$Host.UI.RawUI.WindowTitle = "Google Antigravity - Русификатор"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    Google Antigravity — Русская локализация (RU)         " -ForegroundColor Green
Write-Host "    Репозиторий: https://github.com/j46871417-ui/Antigravity-Localizer" -ForegroundColor Gray
Write-Host "    Telegram:    https://t.me/+8qU7020rMF84OWNi" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Проверка путей
$HasDesktop = Test-Path "$AppDir\Antigravity.exe"
$HasIde = Test-Path "$IdeDir\Antigravity.exe"

if (-not $HasDesktop -and -not (Test-Path "$AppDir")) {
    $altPath = "$env:PROGRAMFILES\antigravity"
    if (Test-Path "$altPath\Antigravity.exe") {
        $AppDir = $altPath
        $HasDesktop = $true
    }
}

if (-not $HasDesktop -and -not $HasIde) {
    Write-Host "[!] Antigravity не найден в стандартных каталогах." -ForegroundColor Yellow
    $manualPath = Read-Host "Введите полный путь к каталогу с Antigravity.exe"
    if (Test-Path "$manualPath\Antigravity.exe") {
        $AppDir = $manualPath
        $HasDesktop = $true
    } else {
        Write-Host "[-] Antigravity.exe не найден по указанному пути. Прерывание." -ForegroundColor Red
        return
    }
}

if ($HasDesktop) {
    Write-Host "[+] Обнаружен Antigravity 2.0 Desktop: $AppDir" -ForegroundColor Green
}
if ($HasIde) {
    Write-Host "[+] Обнаружен Antigravity IDE (VS Code Edition): $IdeDir" -ForegroundColor Green
}

# 2. Выбор режима
if (-not $Install -and -not $Uninstall) {
    if ([Console]::IsInputRedirected -or [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        $Install = $true
    } else {
        Write-Host ""
        Write-Host "Выберите действие:" -ForegroundColor Yellow
        Write-Host " [1] Установить русификацию (Рекомендуется)" -ForegroundColor White
        Write-Host "     • Полный перевод 950+ элементов интерфейса, нативного меню, трея и настроек."
        Write-Host "     • Поддержка как Antigravity 2.0 Desktop, так и Antigravity IDE."
        Write-Host "     • Безопасная фильтрация: код, терминалы и теги не затрагиваются."
        Write-Host "     • Все проекты, история чатов, сессии и ключи API сохраняются."
        Write-Host "     • Автоматический бэкап оригинальных файлов ядра Google."
        Write-Host ""
        Write-Host " [2] Удалить русификацию (Восстановить официальный оригинал)" -ForegroundColor White
        Write-Host "     • Возвращает оригинальный английский app.asar от Google."
        Write-Host ""
        Write-Host " [0] Отмена" -ForegroundColor Gray
        Write-Host ""
        $choice = Read-Host "Введите номер действия [1]"
        if ($choice -eq "2") {
            $Uninstall = $true
        } elseif ($choice -eq "0") {
            Write-Host "[*] Отменено пользователем." -ForegroundColor Yellow
            return
        } else {
            $Install = $true
        }
    }
}

$ResourcesDir = Join-Path $AppDir "resources"
$TargetAsar = Join-Path $ResourcesDir "app.asar"
$BackupAsar = Join-Path $ResourcesDir "app.asar.original_backup"
$TargetBundle = Join-Path $ResourcesDir "web_bundle_ru"

# --- РЕЖИМ УДАЛЕНИЯ ---
if ($Uninstall) {
    Write-Host ""
    Write-Host "[*] Восстановление оригинальной версии от Google..." -ForegroundColor Cyan

    $procs = Get-Process -Name "Antigravity", "Antigravity IDE" -ErrorAction SilentlyContinue
    if ($procs) {
        Write-Host "[*] Закрытие запущенных процессов Antigravity..." -ForegroundColor Yellow
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    if (Test-Path $BackupAsar) {
        Copy-Item -Path $BackupAsar -Destination $TargetAsar -Force
        Write-Host "[+] Оригинальный app.asar успешно восстановлен из резервной копии." -ForegroundColor Green
    } else {
        Write-Host "[!] Резервная копия app.asar.original_backup не найдена." -ForegroundColor Yellow
    }

    if (Test-Path $TargetBundle) {
        Remove-Item -Path $TargetBundle -Recurse -Force
        Write-Host "[+] Каталог web_bundle_ru удалён." -ForegroundColor Green
    }

    # IDE restore
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
Write-Host "[*] Подготовка к установке русификатора..." -ForegroundColor Cyan

$ScriptDir = $PSScriptRoot
$IsRemote = $false

if ([string]::IsNullOrWhiteSpace($ScriptDir) -or (-not (Test-Path "$ScriptDir\resources\app.asar"))) {
    $IsRemote = $true
}

$TempDir = $null
if ($IsRemote) {
    Write-Host "[*] Загрузка актуальных файлов локализации с GitHub..." -ForegroundColor Cyan
    $ZipUrl = "https://github.com/j46871417-ui/Antigravity-Localizer/archive/refs/heads/main.zip"
    $TempDir = Join-Path $env:TEMP ("antigravity_ru_" + [guid]::NewGuid().ToString().Substring(0, 8))
    $TempZip = "$TempDir.zip"

    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $oldProgress = $ProgressPreference
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $ZipUrl -OutFile $TempZip -UseBasicParsing
        $ProgressPreference = $oldProgress
        Expand-Archive -Path $TempZip -DestinationPath $TempDir -Force
        
        $extractedRoot = Get-ChildItem -Path $TempDir -Directory | Select-Object -First 1
        if ($extractedRoot -and (Test-Path (Join-Path $extractedRoot.FullName "resources\app.asar"))) {
            $ScriptDir = $extractedRoot.FullName
        } else {
            $ScriptDir = Join-Path $TempDir "Antigravity-Localizer-main"
        }

        if (-not (Test-Path "$ScriptDir\resources\app.asar")) {
            throw "Не удалось обнаружить распакованные ресурсы в загруженном архиве."
        }
        Write-Host "[+] Файлы успешно загружены." -ForegroundColor Green
    } catch {
        Write-Host "[-] Ошибка загрузки архива: $_" -ForegroundColor Red
        if ($TempDir -and (Test-Path $TempDir)) { Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue }
        if ($TempZip -and (Test-Path $TempZip)) { Remove-Item -Path $TempZip -Force -ErrorAction SilentlyContinue }
        return
    }
}

# Закрытие запущенных процессов
$procs = Get-Process -Name "Antigravity", "Antigravity IDE" -ErrorAction SilentlyContinue
if ($procs) {
    Write-Host "[*] Закрытие запущенных процессов Antigravity..." -ForegroundColor Yellow
    $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    $timeout = 10
    while ((Get-Process -Name "Antigravity", "Antigravity IDE" -ErrorAction SilentlyContinue) -and ($timeout -gt 0)) {
        Start-Sleep -Milliseconds 500
        $timeout--
    }
    Start-Sleep -Seconds 1
}

try {
    # 1. Desktop русификация
    if ($HasDesktop) {
        if (-not (Test-Path $BackupAsar)) {
            if (Test-Path $TargetAsar) {
                Write-Host "[*] Создание резервной копии оригинального app.asar..." -ForegroundColor Cyan
                Copy-Item -Path $TargetAsar -Destination $BackupAsar -Force
                Write-Host "[+] Резервная копия сохранена: app.asar.original_backup" -ForegroundColor Green
            }
        } else {
            Write-Host "[*] Резервная копия уже существует: app.asar.original_backup" -ForegroundColor Gray
        }

        Write-Host "[*] Копирование языкового бандла (web_bundle_ru)..." -ForegroundColor Cyan
        if (-not (Test-Path $TargetBundle)) {
            New-Item -ItemType Directory -Path $TargetBundle -Force | Out-Null
        }
        Copy-Item -Path "$ScriptDir\resources\web_bundle_ru\*" -Destination $TargetBundle -Recurse -Force

        Write-Host "[*] Установка локализованного ядра Electron (app.asar)..." -ForegroundColor Cyan
        Copy-Item -Path "$ScriptDir\resources\app.asar" -Destination $TargetAsar -Force
        Write-Host "[+] Antigravity 2.0 Desktop успешно русифицирован!" -ForegroundColor Green
    }

    # 2. IDE русификация
    if ($HasIde) {
        Write-Host "[*] Применение локализации для Antigravity IDE..." -ForegroundColor Cyan
        $ideExtDir = Join-Path $IdeDir "resources\app\extensions\antigravity"
        $idePkg = Join-Path $ideExtDir "package.json"
        $idePkgBak = "$idePkg.bak.original"
        
        if (Test-Path $idePkg) {
            if (-not (Test-Path $idePkgBak)) {
                Copy-Item -Path $idePkg -Destination $idePkgBak -Force
            }
            # Патчим package.json командами на русском если есть translations
            $transPath = Join-Path $ScriptDir "translations\ide_strings.json"
            if (Test-Path $transPath) {
                try {
                    $jsonContent = Get-Content -Path $idePkg -Raw -Encoding UTF8 | ConvertFrom-Json
                    $transContent = Get-Content -Path $transPath -Raw -Encoding UTF8 | ConvertFrom-Json
                    
                    if ($transContent.commands -and $jsonContent.contributes.commands) {
                        foreach ($cmd in $jsonContent.contributes.commands) {
                            $cId = $cmd.command
                            if ($transContent.commands.$cId.ru) {
                                $cmd.title = $transContent.commands.$cId.ru
                            }
                        }
                    }
                    $jsonContent | ConvertTo-Json -Depth 20 | Set-Content -Path $idePkg -Encoding UTF8
                    Write-Host "[+] Команды Antigravity IDE переведены на русский язык!" -ForegroundColor Green
                } catch {
                    Write-Host "[!] Предупреждение при обновлении package.json: $_" -ForegroundColor Yellow
                }
            }
        }
    }

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "  Русификация Google Antigravity успешно установлена!     " -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "• Переведено более 950 элементов интерфейса, настроек и меню." -ForegroundColor White
    Write-Host "• Все ваши проекты, чаты, сессии и ключи полностью сохранены." -ForegroundColor White
    Write-Host "• Запустите Antigravity, чтобы работать в полностью русском интерфейсе!" -ForegroundColor White
    Write-Host "• Сообщество и группа в Telegram: https://t.me/+8qU7020rMF84OWNi" -ForegroundColor Cyan
    Write-Host "• Для отката запустите скрипт с параметром -Uninstall" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "[-] Ошибка установки: $_" -ForegroundColor Red
} finally {
    if ($TempDir -and (Test-Path $TempDir)) {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($TempZip -and (Test-Path $TempZip)) {
        Remove-Item -Path $TempZip -Force -ErrorAction SilentlyContinue
    }
}
