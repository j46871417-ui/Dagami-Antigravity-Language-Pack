param(
    [string]$Lang = '', [switch]$Install, [switch]$Uninstall,
    [switch]$List, [switch]$Update, [string]$AppDir = '',
    [string]$IdeDir = '', [string]$ExpectedHash = ''
)
$ErrorActionPreference = 'Stop'
$scriptRoot = $PSScriptRoot
$sourceTemp = $null
try {
    if (-not $scriptRoot -or -not (Test-Path -LiteralPath (Join-Path $scriptRoot 'language_pack.py'))) {
        $sourceTemp = Join-Path ([IO.Path]::GetTempPath()) ('dagami-' + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $sourceTemp | Out-Null
        $zipPath = Join-Path $sourceTemp 'source.zip'
        Invoke-WebRequest -Uri 'https://github.com/j46871417-ui/Dagami-Antigravity-Language-Pack/archive/refs/heads/main.zip' -OutFile $zipPath
        if ($ExpectedHash -and (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash -ne $ExpectedHash) { throw 'SHA-256 не совпал.' }
        Expand-Archive -LiteralPath $zipPath -DestinationPath $sourceTemp
        $sourceRoots = @(Get-ChildItem -LiteralPath $sourceTemp -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'language_pack.py') })
        if ($sourceRoots.Count -ne 1) { throw 'Не найден файл запуска.' }
        $scriptRoot = $sourceRoots[0].FullName
    }
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) { $pythonCommand = Get-Command py -ErrorAction SilentlyContinue }
    if (-not $pythonCommand) { throw 'Нужен Python 3.10 или новее.' }
    if (-not $Install -and -not $Uninstall -and -not $List -and -not $Update -and -not $Lang) {
        Write-Host '1 ru | 2 zh | 3 es | 4 ja | 5 de | 6 fr | 7 список | 8 пакеты | 9 откат | 0 выход'
        switch (Read-Host 'Выбор') {
            '1' { $Lang='ru' } '2' { $Lang='zh' } '3' { $Lang='es' }
            '4' { $Lang='ja' } '5' { $Lang='de' } '6' { $Lang='fr' }
            '7' { $List=$true } '8' { $Update=$true } '9' { $Uninstall=$true }
            default { return }
        }
    }
    $cliArgs = @((Join-Path $scriptRoot 'language_pack.py'))
    if ($List) { $cliArgs += '--list' }
    elseif ($Update) { $cliArgs += '--update' }
    elseif ($Uninstall) { $cliArgs += '--restore' }
    else { if (-not $Lang) { $Lang='ru' }; $cliArgs += @('--lang', $Lang) }
    if ($AppDir) { $cliArgs += @('--desktop-path', $AppDir) }
    if ($IdeDir) { $cliArgs += @('--ide-path', $IdeDir) }
    & $pythonCommand.Source @cliArgs
    if ($LASTEXITCODE -ne 0) { throw "Сбой. Код: $LASTEXITCODE. См. журнал выше." }
}
finally {
    if ($sourceTemp) {
        $tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
        $resolvedTemp = [IO.Path]::GetFullPath($sourceTemp)
        if ($resolvedTemp.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase) -and ([IO.Path]::GetFileName($resolvedTemp) -match '^dagami-[a-f0-9]{32}$')) {
            Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
        }
    }
}
