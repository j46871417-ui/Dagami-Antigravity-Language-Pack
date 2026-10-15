# Инструкция по установке и использованию Dagami Antigravity Language Pack

**Dagami Antigravity Language Pack (v1.1.0)** — универсальный мультиязычный локализатор для **Google Antigravity Desktop** и **Antigravity IDE**.

* **Официальный репозиторий:** [GitHub](https://github.com/j46871417-ui/Antigravity-Localizer)
* **Telegram-сообщество:** [t.me/+8qU7020rMF84OWNi](https://t.me/+8qU7020rMF84OWNi)
* **Поддержать разработку (Донат):** [pay.cloudtips.ru/p/671fda86](https://pay.cloudtips.ru/p/671fda86)

---

## 🌍 Поддерживаемые языки

| Код | Язык | Команда переключения |
| :---: | :--- | :--- |
| `ru` | Русский (Russian) | `dagami-ag-localizer --lang ru` |
| `zh` | Китайский (Chinese / 简体中文) | `dagami-ag-localizer --lang zh` |
| `es` | Испанский (Spanish / Español) | `dagami-ag-localizer --lang es` |
| `ja` | Японский (Japanese / 日本語) | `dagami-ag-localizer --lang ja` |
| `de` | Немецкий (German / Deutsch) | `dagami-ag-localizer --lang de` |
| `fr` | Французский (French / Français) | `dagami-ag-localizer --lang fr` |

---

## 🪟 Инструкция для Windows

### Способ 1: Готовый исполняемый файл `.exe` (Рекомендуется, без установки Python)
1. Скачайте архив **`DagamiAntigravityLanguagePack-v1.1.0-Windows.zip`** со страницы [GitHub Releases](https://github.com/j46871417-ui/Antigravity-Localizer/releases).
2. Распакуйте архив в любую удобную папку.
3. Запустите **`AntigravityLocalizer.exe`**.
4. В появившемся графическом интерфейсе выберите желаемый язык (Русский, Китайский, Испанский, Японский и др.) и нажмите **«Применить»**.
5. Локализатор автоматически завершит процессы Antigravity, применит языковой пакет и создаст резервную копию.

### Способ 2: Через командную строку / батник (CLI)
Если у вас установлен Python 3.8+:
1. Откройте командную строку (`cmd`) или PowerShell в папке проекта.
2. Для установки русского языка выполните:
   ```cmd
   dagami-ag-localizer.cmd --lang ru
   ```
3. Для переключения на другой язык:
   ```cmd
   dagami-ag-localizer.cmd --lang zh
   dagami-ag-localizer.cmd --lang es
   dagami-ag-localizer.cmd --lang ja
   ```
4. Для просмотра всех доступных языков:
   ```cmd
   dagami-ag-localizer.cmd --list
   ```
5. Для восстановления оригинального английского языка:
   ```cmd
   dagami-ag-localizer.cmd --restore
   ```

### Способ 3: Установка одной командой через PowerShell
Откройте PowerShell и вставьте:
```powershell
irm https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.ps1 | iex
```

---

## 🐧 Инструкция для Linux (Ubuntu, Debian, Fedora, Arch, openSUSE)

### Способ 1: Из скачанного архива
1. Скачайте архив **`DagamiAntigravityLanguagePack-v1.1.0-Linux.tar.gz`** со страницы [GitHub Releases](https://github.com/j46871417-ui/Antigravity-Localizer/releases).
2. Распакуйте архив:
   ```bash
   tar -xzf DagamiAntigravityLanguagePack-v1.1.0-Linux.tar.gz
   cd DagamiAntigravityLanguagePack-v1.1.0-Linux
   ```
3. Сделайте скрипты исполняемыми:
   ```bash
   chmod +x install.sh dagami-ag-localizer.sh
   ```
4. Запустите установку русского языка:
   ```bash
   ./install.sh --lang ru
   ```
   *(Если Antigravity установлен в `/opt/Google/Antigravity` или `/usr/lib/antigravity`, запустите с `sudo`)*:
   ```bash
   sudo ./install.sh --lang ru
   ```

### Способ 2: Установка одной строкой через терминал
```bash
curl -fsSL https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.sh | bash
```
Скрипт откроет интерактивное меню, где вы сможете нажать цифру нужного языка.

### Способ 3: Использование CLI-команд в Linux
```bash
./dagami-ag-localizer.sh --lang ru      # Установить русский
./dagami-ag-localizer.sh --lang zh      # Установить китайский
./dagami-ag-localizer.sh --lang es      # Установить испанский
./dagami-ag-localizer.sh --lang ja      # Установить японский
./dagami-ag-localizer.sh --list         # Список доступных языков
./dagami-ag-localizer.sh --update       # Обновить языковые словари
./dagami-ag-localizer.sh --restore      # Восстановить оригинальный интерфейс
```

---

## 🍏 Инструкция для macOS (Apple Silicon M1/M2/M3/M4 и Intel)

### Способ 1: Из скачанного архива
1. Скачайте архив **`DagamiAntigravityLanguagePack-v1.1.0-macOS.zip`** со страницы [GitHub Releases](https://github.com/j46871417-ui/Antigravity-Localizer/releases).
2. Распакуйте архив в папку Загрузки или любую удобную директорию.
3. Откройте приложение **Терминал** (`Terminal.app`) и перейдите в папку:
   ```bash
   cd ~/Downloads/DagamiAntigravityLanguagePack-v1.1.0-macOS
   ```
4. Сделайте скрипт исполняемым и запустите:
   ```bash
   chmod +x install.sh dagami-ag-localizer.sh
   ./install.sh --lang ru
   ```
   *Примечание:* Если система macOS запросит права администратора для записи в `/Applications/Antigravity.app`, выполните:
   ```bash
   sudo ./install.sh --lang ru
   ```

### Способ 2: Установка одной строкой через Терминал
```bash
curl -fsSL https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.sh | bash
```

### Способ 3: CLI-команды на macOS
```bash
./dagami-ag-localizer.sh --lang ru      # Установить русский
./dagami-ag-localizer.sh --lang zh      # Установить китайский
./dagami-ag-localizer.sh --lang es      # Установить испанский
./dagami-ag-localizer.sh --lang ja      # Установить японский
./dagami-ag-localizer.sh --list         # Список доступных языков
./dagami-ag-localizer.sh --update       # Обновить словари
./dagami-ag-localizer.sh --restore      # Восстановить оригинальный интерфейс
```

---

## ⚡ Особенности перевода рассуждений (Thinking Process)

В интерфейсе чата Antigravity блоки рассуждений моделей ("Thought for X seconds") оснащены удобной панелью:
* **Кнопка `🌐 РУ` (или выбранный язык)**: мгновенно переводит текст рассуждений модели на выбранный язык с сохранением исходного текста. Повторное нажатие (`🌐 EN`) возвращает оригинальный английский текст.
* **Кнопка `⚡ Авто: ВКЛ / ВЫКЛ`**: переключает режим автоматического потокового перевода рассуждений на лету при получении ответа от модели.
* **Перевод карточек действий**: названия операций инструмента (`Searching for ...`, `Reading ...`, `Editing ...`, `Executing ...`, `Ran ...`, `Analyzed ...`) автоматически локализуются на лету.

---

## 🛠️ Резервные копии и восстановление

При каждой установке локализатор создает резервные копии оригинальных файлов с суффиксом `.ag_bak`:
* Для отката к исходному состоянию используйте:
  * Windows: `dagami-ag-localizer.cmd --restore`
  * Linux / macOS: `./dagami-ag-localizer.sh --restore`
  * Либо выберите пункт **«Восстановить»** в графическом интерфейсе (`AntigravityLocalizer.exe`).

---

## 💬 Сообщество и поддержка
* Обсуждение, вопросы и предложения в Telegram: **[https://t.me/+8qU7020rMF84OWNi](https://t.me/+8qU7020rMF84OWNi)**
* Поддержать проект донатом: **[https://pay.cloudtips.ru/p/671fda86](https://pay.cloudtips.ru/p/671fda86)**
