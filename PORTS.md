# Порты Linux и macOS

## Что есть сейчас

Новая иконка: свой знак A/Я в цветах Dagami.
Есть SVG, PNG, ICO для Windows и ICNS для macOS.
Иконка задана для EXE, окна, .app и меню Linux.

Папки `ports/Linux` и `ports/macOS` — версии из исходников.
Это не готовые ELF или .app. Для них нужны Python 3.10+ и Tk.
На этом ПК нет среды Linux и macOS, поэтому их нативные файлы
здесь не собраны и запуск на этих ОС пока не проверен.

## Запуск исходников

Linux, из папки порта:

```sh
sh dagami-ag-localizer.sh --gui
```

Для Tk на Ubuntu/Debian нужен пакет `python3-tk`.
GUI требует X11 или XWayland с DISPLAY. CLI работает без него:

```sh
sh dagami-ag-localizer.sh --list
```

Для записи в системную папку Antigravity нужны права на неё.
Лучше выбрать свою копию приложения; весь GUI через sudo не запускайте.

macOS, из папки порта:

```sh
sh Launch.command
```

Нужен Python с Tcl/Tk. Папку .app можно указать в поле пути.
На macOS с подписью Antigravity или ElectronAsarIntegrity ядро пока
даёт отказ до записи. Режим правки и новой подписи этой IDE ещё не готов.
Сам порт утилиты может запускаться; это не снимает данную рамку.

## Нативная сборка

Сборка идёт на целевой ОС, не на Windows для всех трёх систем.
В папке исходников нужны Python 3.12+, Tk, Node и PyInstaller:

```sh
python3 -m pip install -r requirements.txt
python3 build_release.py --no-package
```

На Windows вместо `python3` используйте `python`.
Иконки уже входят в код; Pillow не нужен для обычной сборки.
Для правки иконки нужен Pillow и `python3 build_icon.py`.

Результат:

- Windows: `dist/AntigravityLocalizer/AntigravityLocalizer.exe`.
- Linux: `dist/DagamiLanguagePack/DagamiLanguagePack` и папка `_internal`.
- macOS: `dist/DagamiLanguagePack.app`.

Весь результат надо переносить целиком.
Нативным сборкам системный Python для запуска не нужен.

Флаг `--package` создаёт пакет для ОС и CPU с SHA-256.
TAR на Linux/macOS хранит права запуска и ссылки внутри .app.
Номер версии 1.2.0; готовые файлы есть на странице релиза.

## Меню Linux

Запустите сам файл `DagamiLanguagePack`.
При нужде можно добавить пункт меню для своего входа:

```sh
python3 install_desktop.py
```

Этот шаг пишет лишь в `$XDG_DATA_HOME/applications` или
`~/.local/share/applications`; sudo не нужен.
Здесь Python нужен только для создания пункта меню, не для самой GUI.

## Сборка в GitHub Actions

Файл `.github/workflows/native-ports.yml` содержит пять задач:
Windows x64, Linux x64/ARM64 и macOS Intel/Apple Silicon.
Выбраны Ubuntu 22.04 и macOS 15. Метки взяты из runner-images.

https://github.com/actions/runner-images#available-images

Ветка `codex/native-ports-*` запускает сборку при push.
Готовые файлы и отчёт по ОС хранятся в Artifacts нужного прогона.
Статус и состав пакета надо сверять по итогу этого прогона.

У macOS по умолчанию локальная подпись ad hoc, не Developer ID.
Для своей подписи есть `--codesign-identity "имя ключа"`.
Вход Apple и ключи в код не входят; notarization здесь не сделана.
Проверка ресурсов — часть сборки. Она не доказывает вид GUI,
запись языка в настоящую IDE или работу аккаунта.

## Факт проверки

Windows x64 собран новым общим скриптом с новой иконкой.
Встроенная проверка ресурсов дала код 0.
Сборщик пакета сверяет тип файла: PE, ELF или Mach-O, а также CPU
для Linux/macOS. Исходники не выдаются за нативный бинарный файл.
Для папок портов есть FILES_SHA256.json со списком хешей.
Проверка YAML отдельным парсером пока не сделана: его нет в среде.
