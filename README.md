# Dagami Antigravity Language Pack

[![Лицензия: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/j46871417-ui/Antigravity-Localizer)](https://github.com/j46871417-ui/Antigravity-Localizer/releases)
[![Telegram](https://img.shields.io/badge/Telegram-Чат_сообщества-2CA5E0?logo=telegram&logoColor=white)](https://t.me/+8qU7020rMF84OWNi)
[![Donation](https://img.shields.io/badge/CloudTips-Поддержать_проект-FF6F00?logo=coffeescript&logoColor=white)](https://pay.cloudtips.ru/p/671fda86)

Универсальный пакет мультиязычной локализации для экосистемы **Google Antigravity**.

В Google Antigravity из коробки доступен только английский язык. **Dagami Antigravity Language Pack** снимает это ограничение и позволяет переключаться на **любой нужный язык** (русский, китайский, испанский, японский, немецкий, французский и др.) с живым нейропереводом мыслей и полной сохранностью синтаксиса кода.

---

## ⚡ Быстрый старт (CLI)

Утилита **`dagami-ag-localizer`** позволяет моментально переключать язык интерфейса одной командой:

```powershell
# Установить русский язык (Russian)
dagami-ag-localizer --lang ru

# Установить китайский язык (Chinese Simplified / 简体中文)
dagami-ag-localizer --lang zh

# Установить испанский язык (Spanish / Español)
dagami-ag-localizer --lang es

# Показать список доступных языковых пакетов
dagami-ag-localizer --list

# Проверить и обновить языковые пакеты
dagami-ag-localizer --update

# Вернуть оригинальный английский язык Google
dagami-ag-localizer --restore
```

### Интерактивный режим
Если запустить команду без параметров:
```powershell
dagami-ag-localizer
```
откроется удобное интерактивное меню с выбором языка, ссылкой на чат сообщества и возможностью поддержать проект.

---

## 📥 Установка через PowerShell (1 команда)

Открой **PowerShell** и выполни команду:
```powershell
irm https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.ps1 | iex
```

> **Откат к оригинальной английской версии:**
> ```powershell
> & ([scriptblock]::Create((irm https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.ps1))) -Uninstall
> ```

---

## ☕ Поддержка и развитие проекта

Разработка и поддержка новых языковых пакетов ведётся сообществом. Если проект экономит ваше время и делает работу комфортнее, вы можете поддержать автора:

👉 **[Поддержать проект через CloudTips (банковские карты / СБП)](https://pay.cloudtips.ru/p/671fda86)**  
👉 **[Чат сообщества в Telegram](https://t.me/+8qU7020rMF84OWNi)**


---

## 🌍 Поддерживаемые языки

| Код | Флаг | Язык | Нативное название | Статус |
|:---:|:---:|:---|:---|:---:|
| **`ru`** | 🇷🇺 | Russian | Русский | ✅ 4 500+ терминов + IDE |
| **`zh`** | 🇨🇳 | Chinese (Simplified) | 简体中文 | ✅ Базовый + перевод мыслей |
| **`es`** | 🇪🇸 | Spanish | Español | ✅ Базовый + перевод мыслей |
| **`ja`** | 🇯🇵 | Japanese | 日本語 | ✅ Базовый + перевод мыслей |
| **`de`** | 🇩🇪 | German | Deutsch | ✅ Базовый + перевод мыслей |
| **`fr`** | 🇫🇷 | French | Français | ✅ Базовый + перевод мыслей |

Любой пользователь может расширить словари или добавить новый язык в каталог `translations/languages/<код>/`!

---

## 🧠 Принципы работы и совместимость с последними версиями

Dagami Antigravity Language Pack полностью совместим с **Antigravity 2.23.1** и всеми последующими обновлениями благодаря принципу **безопасной in-place модификации**:

1. **Никакой перезаписи чужих бинарников**: инсталлятор не затирает системный `app.asar` устаревшими версиями, а аккуратно читает установленный на вашем ПК архив, создаёт резервную копию `app.asar.original_backup` и внедряет только необходимые языковые строки.
2. **Атомарная замена (Safe Atomic Replace)**: запись обновлённого архива выполняется во временный файл с проверкой контрольных сумм SHA-256 и атомарным переименованием (`os.replace`).
3. **Идемпотентный Preload-инжектор**: в `dist/preload.js` внедряется легковесный движок перехвата с маркером идемпотентности. При переключении с одного языка на другой старый код вычищается автоматически.
4. **Живой перевод мыслей ИИ (Thought Process)**: блоки рассуждений переводятся на лету на выбранный язык (`tl=ru`, `tl=zh-CN`, `tl=es` и др.) с сохранением блоков кода через маскирование `___AG_CODE_X___`.
5. **Защита кода и терминалов (isIgnored)**: элементы `<pre>`, `<code>`, `.monaco-editor`, `.xterm`, поля ввода и токены синтаксиса остаются нетронутыми.


---

## 💻 Кроссплатформенная поддержка и релизы

Пакет полностью поддерживает **Windows**, **Linux** и **macOS**!

| Платформа | Формат загрузки | Запуск / Установка |
| :--- | :--- | :--- |
| **Windows** | [`.exe` / `.zip`](https://github.com/j46871417-ui/Antigravity-Localizer/releases) | Запустить `AntigravityLocalizer.exe` или `dagami-ag-localizer.cmd --lang ru` |
| **Linux** | [`.tar.gz`](https://github.com/j46871417-ui/Antigravity-Localizer/releases) | `./install.sh --lang ru` или `./dagami-ag-localizer.sh --lang ru` |
| **macOS** | [`.zip`](https://github.com/j46871417-ui/Antigravity-Localizer/releases) | `./install.sh --lang ru` или `./dagami-ag-localizer.sh --lang ru` |

📖 Подробное пошаговое руководство со скриншотами и командами доступно в файле [**INSTRUCTIONS.md**](INSTRUCTIONS.md).

---

## 📁 Структура проекта

```
├── dagami_ag_localizer.py      # Основной кроссплатформенный модуль и точка входа
├── dagami_translator_builder.py# Генератор мультиязычного JS-рантайма
├── dagami-ag-localizer.cmd     # Консольный лаунчер для Windows (CMD / PowerShell)
├── dagami-ag-localizer.sh      # Консольный лаунчер для Linux и macOS (Bash)
├── install.ps1                 # Сценарий быстрой установки в PowerShell
├── install.bat                 # Пакетный лаунчер Windows
├── install.sh                  # Универсальный установщик Linux и macOS
├── INSTRUCTIONS.md             # Подробная инструкция для Windows, Linux и macOS
├── translations/
│   └── languages/              # Модульные языковые пакеты
│       ├── ru/                 # Русский языковой пакет (словарь, меню, настройки)
│       ├── zh/                 # Китайский языковой пакет
│       ├── es/                 # Испанский языковой пакет
│       ├── ja/                 # Японский языковой пакет
│       ├── de/                 # Немецкий языковой пакет
│       └── fr/                 # Французский языковой пакет
├── tests/                      # Набор регрессионных и интеграционных тестов
└── README.md
```

---

## 📄 Лицензия

Распространяется под свободной лицензией [MIT](LICENSE).
Права на оригинальное приложение Google Antigravity принадлежат **Google LLC**.
