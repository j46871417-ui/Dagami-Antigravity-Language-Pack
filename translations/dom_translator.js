// Antigravity UI Runtime Localizer (Comprehensive DOM Engine)
(function() {
    window.__antigravity_localizer_active = true;

    const UI_DICT = {
        // --- Навигация, боковая панель и окна ---
        "New Conversation": "Новый диалог",
        "New Session": "Новая сессия",
        "Conversations": "Диалоги",
        "Conversation History": "История диалогов",
        "Conversation": "Диалог",
        "Chats": "Чаты",
        "Projects": "Проекты",
        "Project": "Проект",
        "Create Project": "Создать проект",
        "Create New Project": "Создать новый проект",
        "Project options": "Параметры проекта",
        "New Conversation in Project": "Новый диалог в проекте",
        "Workspaces": "Рабочие пространства",
        "Workspace": "Рабочее пространство",
        "Current Workspace": "Текущее пространство",
        "Current workspace": "Текущее пространство",
        "All Workspaces": "Все пространства",
        "Open Workspace": "Открыть пространство",
        "Clone current workspace": "Клонировать рабочее пространство",
        "Scheduled Tasks": "Запланированные задачи",
        "Customizations": "Кастомизация",
        "Default Customizations": "Стандартные настройки",
        "Personal Customizations": "Личные настройки",
        "Skills": "Навыки",
        "Skill": "Навык",
        "Rules": "Правила",
        "Rule": "Правило",
        "Global Rules": "Глобальные правила",
        "Workspace Rules": "Правила пространства",
        "MCP Servers": "Серверы MCP",
        "Settings": "Настройки",
        "Close Settings": "Закрыть настройки",
        "Chat Settings": "Настройки чата",
        "Editor Settings": "Настройки редактора",
        "Browser Settings": "Настройки браузера",
        "Documentation": "Документация",
        "Docs": "Справка",
        "Feedback": "Обратная связь",
        "Send Feedback": "Отправить отзыв",
        "Help & Feedback": "Справка и отзывы",
        "Changelog": "История изменений",
        "Sign In": "Войти",
        "Sign in": "Войти",
        "Sign Out": "Выйти",
        "Sign out": "Выйти",
        "Log in": "Войти",
        "Log In": "Войти",
        "Log out": "Выйти",
        "Logout": "Выйти",
        "Open IDE": "Открыть IDE",
        "Load older messages": "Загрузить ранние сообщения",
        "Sidebar": "Боковая панель",
        "Toggle Sidebar": "Боковая панель",
        "Toggle Auxiliary Pane": "Вспомогательная панель",
        "Maximize Pane": "Развернуть панель",
        "Equalize Split Panes": "Выровнять панели",
        "Display Options": "Параметры отображения",
        "More options": "Дополнительные параметры",
        "More actions": "Другие действия",
        "Pin conversation": "Закрепить диалог",
        "Archive conversation": "Архивировать диалог",
        "Delete Conversation": "Удалить диалог",
        "Conversation Archived": "Диалог архивирован",
        "Conversation ID": "Идентификатор диалога",
        "Notifications": "Уведомления",
        "Go Back": "Назад",
        "Go Forward": "Вперёд",
        "History": "История",
        "Recent": "Недавние",
        "Recent Conversations": "Недавние диалоги",
        "Today": "Сегодня",
        "Yesterday": "Вчера",
        "Previous 7 Days": "Предыдущие 7 дней",
        "Previous 30 Days": "Предыдущие 30 дней",

        // --- Верхняя строка меню и окна ---
        "File": "Файл",
        "View": "Вид",
        "Window": "Окно",
        "Help": "Справка",
        "Edit": "Правка",

        // --- Выбор модели и режимы ---
        "Model Selection": "Выбор модели",
        "Select model": "Выбрать модель",
        "Select Model": "Выбрать модель",
        "Switch Model": "Сменить модель",
        "Thinking": "Рассуждения",
        "Thinking Process": "Ход рассуждений",
        "Hide reasoning": "Скрыть рассуждения",
        "Show reasoning": "Показать рассуждения",
        "Planning": "Планирование",
        "Planning Mode": "Режим планирования",
        "Fast": "Быстрый",
        "Pro": "Профессиональный",
        "High": "Высокая точность",
        "Low": "Экономный",
        "Balanced": "Сбалансированный",
        "Experimental Features": "Экспериментальные функции",
        "Experimental features": "Экспериментальные функции",

        // --- Ввод сообщений и чат ---
        "Ask anything, @ to mention, / for actions": "Спросите что угодно, @ для упоминания, / для действий",
        "Ask anything, @ to mention, / for workflows": "Спросите что угодно, @ для упоминания, / для процессов",
        "Ask anything...": "Спросите что угодно...",
        "Ask anything": "Спросите что угодно...",
        "Type a message...": "Введите сообщение...",
        "Message input": "Поле ввода сообщения",
        "Send message": "Отправить сообщение",
        "Send": "Отправить",
        "Record voice memo": "Голосовое сообщение",
        "Cancel (Ctrl+D)": "Отмена (Ctrl+D)",
        "Stop execution": "Остановить выполнение",
        "Stop generating": "Остановить генерацию",
        "Good response": "Хороший ответ",
        "Bad response": "Плохой ответ",
        "Undo changes up to this point": "Откатить изменения до этой точки",
        "Add context": "Добавить контекст",
        "Attach file": "Прикрепить файл",
        "Attach folder": "Прикрепить папку",
        "Clear chat": "Очистить чат",
        "Clear conversation": "Очистить диалог",
        "Active Agents": "Активные агенты",
        "Follow along": "Следить за ходом",
        "Agent response": "Ответ агента",
        "User message": "Сообщение пользователя",

        // --- Правая панель: Артефакты, Субагенты, Терминал, Изменения ---
        "Artifacts": "Артефакты",
        "Artifact": "Артефакт",
        "Artifact Viewer": "Просмотр артефактов",
        "Artifact Viewer header": "Заголовок артефактов",
        "Table of contents": "Оглавление",
        "No artifacts yet": "Нет артефактов",
        "Subagents": "Субагенты",
        "Subagent": "Субагент",
        "Active Subagents": "Активные субагенты",
        "No subagents running": "Нет запущенных субагентов",
        "Background Tasks": "Фоновые задачи",
        "Running Tasks": "Запущенные задачи",
        "Completed Tasks": "Завершённые задачи",
        "No background tasks": "Нет фоновых задач",
        "Files Changed": "Изменённые файлы",
        "Changes": "Изменения",
        "Review changes": "Просмотр изменений",
        "No files changed": "Файлы не изменены",
        "Terminal": "Терминал",
        "Terminals": "Терминалы",
        "Terminal tab": "Вкладка «Терминал»",
        "New Terminal": "Новый терминал",
        "Close Terminal Tab": "Закрыть терминал",
        "Clear Terminal": "Очистить терминал",
        "Overview": "Обзор",
        "Overview tab": "Вкладка «Обзор»",
        "Review": "Проверка",
        "Review tab": "Вкладка «Проверка»",
        "Review required": "Требуется проверка",
        "User Review Required": "Требуется проверка пользователя",
        "Implementation Plan": "План реализации",
        "Walkthrough": "Отчёт о работе",
        "Diff": "Различия",
        "Console": "Консоль",
        "Console logs": "Логи консоли",
        "Capture console logs": "Захват логов консоли",
        "Capture screenshot": "Сделать снимок экрана",

        // --- Кнопки действий ---
        "Accept": "Принять",
        "Accept All": "Принять все",
        "Reject": "Отклонить",
        "Reject All": "Отклонить все",
        "Proceed": "Продолжить",
        "Continue": "Продолжить",
        "Continue Response": "Продолжить ответ",
        "Retry": "Повторить",
        "Cancel": "Отмена",
        "Cancel All Tasks": "Отменить все задачи",
        "Close": "Закрыть",
        "Close Tab": "Закрыть вкладку",
        "Save": "Сохранить",
        "Save Changes": "Сохранить изменения",
        "Delete": "Удалить",
        "Delete Task": "Удалить задачу",
        "Delete Permanently": "Удалить навсегда",
        "Run": "Запустить",
        "Stop": "Остановить",
        "Copy": "Копировать",
        "Copied": "Скопировано",
        "Copy output": "Скопировать вывод",
        "Copy Content": "Скопировать содержимое",
        "Copy path": "Скопировать путь",
        "Copy File Path": "Скопировать путь к файлу",
        "Copy File Name": "Скопировать имя файла",
        "Copy Image": "Скопировать изображение",
        "Copy full URL to clipboard": "Скопировать URL",
        "Copy error to clipboard": "Скопировать ошибку",
        "Copy conversation markdown": "Скопировать как Markdown",
        "Copy thinking": "Скопировать рассуждения",
        "Apply": "Применить",
        "Discard": "Отменить",
        "Discard unstaged changes": "Отменить неиндексированные изменения",
        "Download": "Скачать",
        "Download Diagnostics": "Скачать диагностику",
        "Open": "Открыть",
        "Open folder": "Открыть папку",
        "Open in Editor": "Открыть в редакторе",
        "Restore": "Восстановить",
        "Collapse": "Свернуть",
        "Collapse All Folders": "Свернуть все папки",
        "Expand": "Развернуть",
        "Expand All Folders": "Развернуть все папки",
        "Confirm": "Подтвердить",
        "Dismiss": "Закрыть",
        "Back": "Назад",
        "Next": "Далее",
        "Finish": "Готово",
        "Reload": "Перезагрузить",
        "Restart": "Перезапустить",
        "Clear": "Очистить",
        "Clear search (Esc)": "Очистить поиск (Esc)",
        "Click to copy URL": "Нажмите, чтобы скопировать URL",
        "Click to copy full command": "Нажмите, чтобы скопировать команду",
        "Show output": "Показать вывод",
        "Hide output": "Скрыть вывод",
        "Details": "Подробности",

        // --- Статусы выполнения ---
        "Running": "Выполняется",
        "Working...": "Работаю...",
        "Completed": "Завершено",
        "Failed": "Ошибка",
        "Waiting": "Ожидание",
        "In Progress": "В процессе",
        "Done": "Готово",
        "Success": "Успешно",
        "Warning": "Предупреждение",
        "Error": "Ошибка",
        "Errors": "Ошибки",
        "Paused": "На паузе",
        "Connecting...": "Подключение...",
        "Connected": "Подключено",
        "Disconnected": "Отключено",
        "Reconnecting...": "Переподключение...",
        "Blocked": "Заблокировано",
        "Disabled": "Отключено",
        "Enabled": "Включено",

        // --- Настройки и темы ---
        "General": "Основные",
        "Appearance": "Внешний вид",
        "Theme": "Тема",
        "Dark Theme": "Тёмная тема",
        "Dark": "Тёмная",
        "Light": "Светлая",
        "System": "Системная",
        "Account": "Аккаунт",
        "Check for Updates": "Проверить обновления",
        "Check for updates": "Проверить обновления",
        "Keyboard Shortcuts": "Горячие клавиши",
        "Command Palette": "Палитра команд",
        "Danger Zone": "Опасная зона",
        "Developer": "Для разработчиков",
        "Permissions": "Разрешения",
        "File Permissions": "Права доступа к файлам",
        "File Access Rules": "Правила доступа к файлам",
        "Commands": "Команды",
        "Terminal Sandbox": "Песочница терминала",
        "Enable Telemetry": "Включить телеметрию",
        "Enable Notifications": "Включить уведомления",
        "Enable Browser Tools": "Включить инструменты браузера",
        "Enable Chat": "Включить чат",
        "Enable Personal Customizations": "Включить личные настройки",
        "Discover helpful skills & plugins": "Каталог навыков и плагинов",
        "Browse the Marketplace": "Каталог плагинов",
        "Build With Google Plugins": "Плагины от Google",
        "All": "Все",
        "Search": "Поиск",
        "Search conversations": "Поиск диалогов",
        "Search...": "Поиск...",
        "Filter": "Фильтр",
        "Find": "Найти",
        "Ran": "Запуск",
        "Edited": "Правка",
        "Explored": "Просмотр",
        "Timed": "Таймер",
        "Add": "Добавить",
        "Typeahead menu": "Меню автодополнения",
        "No conversations found": "Диалоги не найдены",
        "No tasks running": "Нет запущенных задач",
        "Are you sure?": "Вы уверены?",
        "This action cannot be undone.": "Это действие нельзя отменить.",
        // --- Полный перевод всех настроек (Settings) ---
        "A Gemini-powered security agent decides if commands should be auto-approved.": "Агент безопасности на базе Gemini решает, подтверждать ли команды автоматически.",
        "A shell setup script run before every command the agent executes in this project. Overrides the global script.": "Скрипт инициализации оболочки для текущего проекта (переопределяет глобальный).",
        "A shell setup script run before every command the agent executes.": "Скрипт инициализации оболочки, выполняемый перед каждой командой агента.",
        "Advanced Settings": "Расширенные настройки",
        "Agent Auto-Fix Lints": "Автоисправление ошибок линтера",
        "Agent Behavior": "Поведение агента",
        "Agent Edits": "Правки агента",
        "Agent Host Address": "Хост-адрес агента",
        "Agent Non-Workspace File Access": "Доступ агента к файлам вне пространства",
        "Agent Script": "Скрипт агента",
        "Agent Settings": "Настройки агента",
        "Agent always asks for review.": "Агент всегда запрашивает проверку.",
        "Agent never asks for review. This maximizes the autonomy of the Agent, but also has the highest risk of the Agent operating over unsafe or injected Artifact content.": "Агент никогда не запрашивает проверку. Максимальная автономность, но повышенный риск работы с небезопасным содержимым.",
        "Allow List Terminal Commands": "Список разрешённых команд",
        "Allow Tab to view and edit the files in .gitignore. Use with caution if your .gitignore lists files containing credentials, secrets, or other sensitive information.": "Разрешить Tab просматривать и редактировать файлы из .gitignore. Используйте осторожно, если в .gitignore указаны файлы с секретами или паролями.",
        "Allow sandboxed commands to make network requests.": "Разрешить изолированным командам доступ к сети.",
        "Allow the agent to run without restrictions.": "Разрешить агенту работу без ограничений.",
        "Allow/deny agent browser actuation access to specific URLs.": "Разрешить/запретить агенту автоматизацию страниц по URL.",
        "Allow/deny agent command execution outside the sandbox.": "Разрешить или запретить запуск команд агента вне песочницы.",
        "Allow/deny agent read access to specific URLs or domains.": "Разрешить/запретить агенту чтение URL или доменов.",
        "Allow/deny agent read access to specific files or directories.": "Разрешить/запретить агенту чтение файлов или каталогов.",
        "Allow/deny agent write access to specific files or directories.": "Разрешить/запретить агенту запись в файлы или каталоги.",
        "Allow/deny specific terminal commands.": "Разрешить или запретить конкретные команды терминала.",
        "Allows the agent to access files outside of your current workspace.": "Разрешает агенту доступ к файлам вне текущего рабочего пространства.",
        "Archive Workspace": "Архивировать пространство",
        "Archive project": "Архивировать проект",
        "Archive this conversation": "Архивировать диалог",
        "Artifact Review Policy": "Политика проверки артефактов",
        "Attach Antigravity server logs": "Прикрепить логи сервера Antigravity",
        "Auto-Expand Changes Overview": "Автораскрытие обзора изменений",
        "Auto-Open Edited Files": "Автооткрытие изменённых файлов",
        "Automatic Check for Updates": "Автопроверка обновлений",
        "Automatically expand the Changes Overview toolbar when the agent finishes generating a response.": "Автоматически раскрывать панель обзора изменений после завершения ответа агента.",
        "Automatically prompt you to restart the app when a new update is available. When disabled, you can check for updates manually from the app menu.": "Автоматически предлагать перезапуск при наличии обновления. Если отключено, проверять обновления можно вручную в меню.",
        "Baseline model quota reached": "Базовая квота модели исчерпана",
        "Browser Actuation Permissions": "Разрешения на управление браузером",
        "Browser Actuation Rules": "Правила управления браузером",
        "Browser CDP Port": "Порт Chrome DevTools Protocol",
        "Browser Javascript Execution Policy": "Политика исполнения JavaScript в браузере",
        "Browser Settings": "Настройки браузера",
        "Browser User Profile Path": "Путь к профилю браузера",
        "Chat Settings": "Настройки чата",
        "Check for Updates": "Проверить обновления",
        "Check for updates": "Проверить обновления",
        "Chrome Binary Path": "Путь к исполняемому файлу Chrome",
        "Command Setup Script": "Скрипт подготовки команд",
        "Commands Outside Sandbox": "Команды вне песочницы",
        "Commands the agent can run outside the sandbox in this workspace.": "Команды, которые агент может запускать вне песочницы в этом пространстве.",
        "Commands the agent can run outside the sandbox.": "Команды, которые агент может запускать вне песочницы.",
        "Configure the maximum width of the conversation panel.": "Настройка максимальной ширины панели переписки.",
        "Configures how the agent tries to access files outside of its working folders.": "Настройка доступа агента к файлам за пределами рабочих папок.",
        "Confirm Undo": "Подтвердить откат",
        "Confirm Window Reload": "Подтвердить перезагрузку окна",
        "Controls whether terminal commands require your approval before running.": "Определяет, требуют ли команды терминала вашего подтверждения перед запуском.",
        "Controls whether the agent can run custom JavaScript to automate complex browser actions.": "Разрешить ли агенту исполнять пользовательский JavaScript в браузере.",
        "Conversation Width": "Ширина панели диалога",
        "Custom path for the browser user profile directory. Leave empty for default (~/.gemini/antigravity-browser-profile).": "Кастомный путь к профилю браузера. Оставьте пустым для значения по умолчанию.",
        "Danger Zone": "Опасная зона",
        "Dark": "Тёмная",
        "Dark Theme": "Тёмная тема",
        "Default Customizations": "Стандартные настройки",
        "Delete Conversation": "Удалить диалог",
        "Delete Handler": "Удалить обработчик",
        "Delete Hook": "Удалить хук",
        "Delete MCP Server": "Удалить MCP-сервер",
        "Delete Permanently": "Удалить навсегда",
        "Delete Task": "Удалить задачу",
        "Deny List Terminal Commands": "Список запрещённых команд",
        "Display and preserve intermediate thinking steps.": "Отображать и сохранять промежуточные шаги рассуждений.",
        "Download Diagnostics": "Скачать диагностику",
        "Editor Settings": "Настройки редактора",
        "Enable AI Credit Overages": "Разрешить перерасход AI-кредитов",
        "Enable Browser Tools": "Включить инструменты браузера",
        "Enable Chat": "Включить чат",
        "Enable Notifications": "Включить уведомления",
        "Enable Notifications for Agent": "Включить уведомления агента",
        "Enable Overages": "Разрешить перерасход",
        "Enable Personal Customizations": "Включить личные настройки",
        "Enable Remote Control": "Включить удалённое управление",
        "Enable Sandbox Mode (Preview)": "Включить режим песочницы (превью)",
        "Enable Shell Integration": "Включить интеграцию с оболочкой",
        "Enable Sounds for Agent": "Звуковые сигналы агента",
        "Enable Telemetry": "Включить телеметрию",
        "Enable Terminal Sandbox": "Включить песочницу терминала",
        "Every terminal command requires approval.": "Каждая команда терминала требует подтверждения.",
        "Experimental Features": "Экспериментальные функции",
        "Experimental features": "Экспериментальные функции",
        "File Access Rules": "Правила доступа к файлам",
        "File Reads": "Чтение файлов",
        "File Writes": "Запись файлов",
        "GitHub Permissions": "Разрешения GitHub",
        "GitHub Policies": "Политики GitHub",
        "Give the agent awareness of lint errors created by its edits so it can fix them without explicit prompting.": "Сообщать агенту об ошибках линтера в его правках для их автоматического исправления.",
        "Group By Project": "По проектам",
        "Group By Workspace": "По пространствам",
        "Highlight After Accept": "Подсветка после принятия",
        "Highlight newly inserted text after accepting a Tab completion.": "Подсвечивать вставленный текст после принятия автодополнения Tab.",
        "Include Jetski Default Customizations": "Включать стандартные кастомизации",
        "Include default customizations, such as default skills.": "Включать встроенные кастомизации и стандартные навыки.",
        "Installed MCP Servers": "Установленные серверы MCP",
        "Installed Skills": "Установленные навыки",
        "Insufficient AI Credits": "Недостаточно AI-кредитов",
        "Keep In Menu Bar": "Оставлять в строке меню",
        "Keep the app accessible from the menu bar and running in the background when all windows are closed.": "Держать приложение в строке меню и фоне при закрытии всех окон.",
        "Layer your personal customizations (skills, rules, etc.) from your config on top of workspace customizations.": "Накладывать личные навыки и правила поверх настроек рабочего пространства.",
        "Let the agent access past conversations to inform its responses.": "Разрешить агенту доступ к истории прошлых диалогов.",
        "Light": "Светлая",
        "Light Theme": "Светлая тема",
        "Local Permissions": "Локальные разрешения",
        "Manage Hooks": "Управление хуками",
        "Manage Skills": "Управление навыками",
        "Manage your model quota and credits.": "Управление квотами моделей и кредитами.",
        "Manage your notification preferences.": "Управление параметрами уведомлений.",
        "Manage your plan, credentials, and general preferences.": "Управление подпиской, учётными данными и общими параметрами.",
        "Model Credits": "Кредиты модели",
        "Model Quota": "Квота модели",
        "Model quota reached": "Квота модели исчерпана",
        "Network Access Rules": "Правила доступа к сети",
        "Network Permissions": "Сетевые разрешения",
        "Notification Preferences": "Настройки уведомлений",
        "Open Agent on Reload": "Открывать агента при перезагрузке",
        "Open Agent panel on window reload": "Открывать панель агента при перезагрузке окна",
        "Open files in the background if Agent creates or edits them": "Открывать файлы в фоне, если агент создаёт или редактирует их",
        "Open files in the background if the agent creates or edits them": "Открывать файлы в фоне, если агент создаёт или редактирует их",
        "Open the agent panel on window reload": "Открывать панель агента при перезагрузке окна",
        "Outside of folders file access policy": "Политика доступа к файлам вне папок проекта",
        "Path to the Chrome/Chromium executable. Leave empty for auto-detection.": "Путь к Google Chrome или Chromium. Оставьте пустым для автоопределения.",
        "Paths the agent can modify inside this workspace.": "Пути, доступные агенту для изменения внутри этого пространства.",
        "Paths the agent can modify.": "Пути, доступные агенту для изменения.",
        "Paths the agent can read inside this workspace.": "Пути, доступные агенту для чтения внутри этого пространства.",
        "Paths the agent can read.": "Пути, доступные агенту для чтения.",
        "Permission Settings": "Настройки разрешений",
        "Permissions": "Разрешения",
        "Personal Customizations": "Личные настройки",
        "Play a sound when the agent finishes generating a response.": "Воспроизводить звук, когда агент завершает генерацию ответа.",
        "Port number for Chrome DevTools Protocol remote debugging. Leave empty for default (9222).": "Порт для удалённой отладки CDP. Оставьте пустым по умолчанию (9222).",
        "Predict the location of your next edit and navigate you there with a tab keypress.": "Предугадывать место следующей правки и перемещаться туда клавишей Tab.",
        "Prevent Sleep": "Запретить спящий режим",
        "Prevent the computer from sleeping while the app is running.": "Запрещать компьютеру переходить в спящий режим при работе приложения.",
        "Project Settings": "Настройки проекта",
        "Provide Feedback": "Оставить отзыв",
        "Provide feedback": "Оставить отзыв",
        "Purchase Credits": "Купить кредиты",
        "Quickly add and update imports with a tab keypress.": "Быстро добавлять и обновлять импорты нажатием клавиши Tab.",
        "Read Files": "Чтение файлов",
        "Remote Control": "Удалённое управление",
        "Restricts agent tools to a secure, isolated local sandbox.": "Ограничивает инструменты агента изолированной локальной песочницей.",
        "Review Policy": "Политика проверки",
        "Share Conversation (Preview)": "Поделиться диалогом (превью)",
        "Show browser notifications when your action is needed or execution finishes.": "Показывать системные уведомления, когда требуется действие или задача завершена.",
        "Show suggestions when typing in the editor": "Показывать подсказки при вводе текста в редакторе",
        "Side-by-side layout": "Раздельный вид (рядом)",
        "Sidebar grouped by project": "Группировка по проектам",
        "Sidebar grouped by workspace": "Группировка по пространствам",
        "Skills Configuration Error:": "Ошибка настройки навыков:",
        "Stacked layout": "Вертикальный вид (друг под другом)",
        "Suggestions in Editor": "Подсказки в редакторе",
        "System": "Системная",
        "Tab Gitignore Access": "Доступ Tab к .gitignore",
        "Tab to Import": "Импорт по Tab",
        "Tab to Jump": "Переход по Tab",
        "Terminal & Tooling Permissions": "Разрешения терминала и инструментов",
        "Terminal Command Auto Execution": "Автовыполнение команд терминала",
        "Terminal Commands": "Команды терминала",
        "Terminal Sandbox": "Песочница терминала",
        "Terminal commands the agent can execute in this workspace.": "Команды терминала, разрешённые агенту в этом пространстве.",
        "Terminal commands the agent can execute.": "Команды терминала, которые агент может выполнять.",
        "The agent asks for permission before executing commands matched by a deny list entry.": "Агент запрашивает подтверждение перед выполнением команд из списка запрета.",
        "The agent auto-executes commands matched by an allow list entry.": "Агент автоматически выполняет команды из списка разрешений.",
        "Theme": "Тема оформления",
        "Time to First Token (TTFT)": "Время до первого токена",
        "Token Usage": "Использование токенов",
        "Tokens": "Токены",
        "Tool Permissions": "Разрешения инструментов",
        "Try out early-stage features before they ship. These may change or be removed at any time.": "Попробуйте экспериментальные функции до их официального релиза. Они могут изменяться или быть удалены в любое время.",
        "URLs the agent can actuate on in this workspace.": "URL для автоматизации браузера в этом пространстве.",
        "URLs the agent can actuate on using the browser.": "URL, на которых агент может совершать действия через браузер.",
        "URLs the agent can read or open in the browser.": "URL, которые агент может читать или открывать в браузере.",
        "URLs the agent can read or open in this workspace.": "URL, доступные для чтения в этом пространстве.",
        "Update Available": "Доступно обновление",
        "When enabled, sandboxed commands are allowed to make network requests.": "Если включено, изолированным командам разрешено выполнять сетевые запросы.",
        "When enabled, the agent will be able to access its knowledge base to inform its responses and automatically generate knowledge items in the background.": "Если включено, агент сможет использовать базу знаний и автоматически наполнять её в фоне.",
        "When enabled, the agent will be able to access past conversations to inform its responses.": "Если включено, агент сможет обращаться к прошлым диалогам для улучшения ответов.",
        "When enabled, the agent will include default customizations, including default skills.": "Если включено, агент будет использовать стандартные встроенные навыки.",
        "Whether the agent asks you to review its documents.": "Запрашивает ли агент проверку документов у пользователя.",
        "Workspace Settings": "Настройки рабочего пространства",
        "Write Files": "Запись файлов",
    };

    // Динамические регулярные выражения
    const DYNAMIC_PATTERNS = [
        { re: /^Worked for\s+(\d+[smhd\s\d]*)$/i, fn: (m) => `Выполнялось ${translateDuration(m[1])}` },
        { re: /^Thought for\s+(\d+[smhd\s\d]*)$/i, fn: (m) => `Рассуждения: ${translateDuration(m[1])}` },
        { re: /^Ran\s+(\d+)\s+commands?$/i, fn: (m) => `Выполнено команд: ${m[1]}` },
        { re: /^(\d+)\s+commands?$/i, fn: (m) => `Команд: ${m[1]}` },
        { re: /^Edited\s+(\d+)\s+files?$/i, fn: (m) => `Изменено файлов: ${m[1]}` },
        { re: /^Explored\s+(\d+)\s+files?$/i, fn: (m) => `Исследовано файлов: ${m[1]}` },
        { re: /^(\d+)\s+files?\s+changed$/i, fn: (m) => `Изменено файлов: ${m[1]}` },
        { re: /^(\d+)\s+files?$/i, fn: (m) => `Файлов: ${m[1]}` },
        { re: /^Load older messages.*$/i, fn: () => `Загрузить более ранние сообщения` },
        { re: /^Select model, current:\s*(.*)$/i, fn: (m) => `Выбор модели (текущая: ${m[1]})` },
        { re: /^(.*)\s+tab$/i, fn: (m) => `Вкладка «${UI_DICT[m[1]] || m[1]}»` },
        { re: /^(\d+)\s*seconds?$/i, fn: (m) => `${m[1]} сек` },
        { re: /^(\d+)\s*minutes?$/i, fn: (m) => `${m[1]} мин` },
        { re: /^(\d+)\s*hours?$/i, fn: (m) => `${m[1]} ч` },
        { re: /^(\d+)mo$/i, fn: (m) => `${m[1]} мес` },
        { re: /^(\d+)d$/i, fn: (m) => `${m[1]} дн` },
        { re: /^(\d+)h$/i, fn: (m) => `${m[1]} ч` },
        { re: /^(\d+)m$/i, fn: (m) => `${m[1]} мин` },
        { re: /^(\d+)s$/i, fn: (m) => `${m[1]} с` },
    ];

    function translateDuration(d) {
        if (!d) return d;
        return d.replace(/(\d+)\s*s\b/g, '$1 с')
                .replace(/(\d+)\s*m\b/g, '$1 мин')
                .replace(/(\d+)\s*h\b/g, '$1 ч')
                .replace(/(\d+)\s*d\b/g, '$1 дн');
    }

    function translateText(text) {
        if (!text || typeof text !== 'string') return null;
        const trimmed = text.trim();
        if (!trimmed) return null;

        // 1. Прямое совпадение словаря
        if (UI_DICT[trimmed]) {
            return text.replace(trimmed, UI_DICT[trimmed]);
        }

        // 2. Бэджи со счётчиками: "Artifacts (3)" или "Subagents [0]"
        const badgeMatch = trimmed.match(/^(.+?)\s*([\(\[\{]\d+[\)\]\}])$/);
        if (badgeMatch) {
            const base = badgeMatch[1].trim();
            const badge = badgeMatch[2];
            if (UI_DICT[base]) {
                return text.replace(trimmed, UI_DICT[base] + ' ' + badge);
            }
        }

        // 3. Динамические шаблоны
        for (let i = 0; i < DYNAMIC_PATTERNS.length; i++) {
            const p = DYNAMIC_PATTERNS[i];
            const m = trimmed.match(p.re);
            if (m) {
                return text.replace(trimmed, p.fn(m));
            }
        }

        // 4. Двоеточие: "Status:", "Model:"
        if (trimmed.endsWith(':')) {
            const base = trimmed.slice(0, -1).trim();
            if (UI_DICT[base]) {
                return text.replace(trimmed, UI_DICT[base] + ':');
            }
        }

        // 5. Многоточие: "Thinking...", "Loading..."
        if (trimmed.endsWith('...')) {
            const base = trimmed.slice(0, -3).trim();
            if (UI_DICT[base]) {
                return text.replace(trimmed, UI_DICT[base] + '...');
            }
        }

        return null;
    }

    const ATTRS = ['placeholder', 'title', 'aria-label', 'alt', 'data-tooltip'];

    function translateNode(node) {
        if (!node) return;

        if (node.nodeType === Node.TEXT_NODE) {
            const val = node.nodeValue;
            const translated = translateText(val);
            if (translated !== null && translated !== val) {
                node.nodeValue = translated;
            }
            return;
        }

        if (node.nodeType === Node.ELEMENT_NODE) {
            // Атрибуты
            for (let i = 0; i < ATTRS.length; i++) {
                const attr = ATTRS[i];
                if (node.hasAttribute && node.hasAttribute(attr)) {
                    const val = node.getAttribute(attr);
                    const trans = translateText(val);
                    if (trans !== null && trans !== val) {
                        node.setAttribute(attr, trans);
                    }
                }
            }

            // Shadow DOM
            if (node.shadowRoot) {
                observeRoot(node.shadowRoot);
            }

            // Дочерние узлы
            const children = node.childNodes;
            for (let i = 0; i < children.length; i++) {
                translateNode(children[i]);
            }
        }
    }

    function observeRoot(root) {
        if (!root) return;
        translateNode(root);
        if (root.__antigravity_observed) return;
        root.__antigravity_observed = true;

        const observer = new MutationObserver(function(mutations) {
            for (let i = 0; i < mutations.length; i++) {
                const m = mutations[i];
                if (m.type === 'childList') {
                    for (let j = 0; j < m.addedNodes.length; j++) {
                        translateNode(m.addedNodes[j]);
                    }
                } else if (m.type === 'characterData') {
                    const val = m.target.nodeValue;
                    const trans = translateText(val);
                    if (trans !== null && trans !== val) {
                        m.target.nodeValue = trans;
                    }
                } else if (m.type === 'attributes') {
                    const attr = m.attributeName;
                    if (ATTRS.includes(attr) && m.target.getAttribute) {
                        const val = m.target.getAttribute(attr);
                        const trans = translateText(val);
                        if (trans !== null && trans !== val) {
                            m.target.setAttribute(attr, trans);
                        }
                    }
                }
            }
        });

        observer.observe(root, {
            childList: true,
            subtree: true,
            characterData: true,
            attributes: true,
            attributeFilter: ATTRS
        });
    }

    // Перехват динамически создаваемых Shadow Root
    if (typeof Element !== 'undefined' && Element.prototype.attachShadow) {
        const origAttachShadow = Element.prototype.attachShadow;
        Element.prototype.attachShadow = function(init) {
            const root = origAttachShadow.call(this, init);
            try {
                observeRoot(root);
            } catch (e) {}
            return root;
        };
    }

    // Перехват создания текстовых узлов
    if (typeof Document !== 'undefined' && Document.prototype.createTextNode) {
        const origCreateTextNode = Document.prototype.createTextNode;
        Document.prototype.createTextNode = function(text) {
            const trans = translateText(text);
            return origCreateTextNode.call(this, trans !== null ? trans : text);
        };
    }

    // Перехват Node.prototype.nodeValue
    try {
        const origNodeValueDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'nodeValue');
        if (origNodeValueDesc && origNodeValueDesc.set) {
            Object.defineProperty(Node.prototype, 'nodeValue', {
                set: function(val) {
                    const trans = (this.nodeType === Node.TEXT_NODE) ? translateText(val) : null;
                    return origNodeValueDesc.set.call(this, trans !== null ? trans : val);
                },
                get: origNodeValueDesc.get,
                configurable: true
            });
        }
    } catch(e) {}

    // Перехват плейсхолдеров инпутов
    try {
        const origInputPlaceholder = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'placeholder');
        if (origInputPlaceholder && origInputPlaceholder.set) {
            Object.defineProperty(HTMLInputElement.prototype, 'placeholder', {
                set: function(val) {
                    const trans = translateText(val);
                    return origInputPlaceholder.set.call(this, trans !== null ? trans : val);
                },
                get: origInputPlaceholder.get,
                configurable: true
            });
        }
    } catch(e) {}

    try {
        const origTextAreaPlaceholder = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'placeholder');
        if (origTextAreaPlaceholder && origTextAreaPlaceholder.set) {
            Object.defineProperty(HTMLTextAreaElement.prototype, 'placeholder', {
                set: function(val) {
                    const trans = translateText(val);
                    return origTextAreaPlaceholder.set.call(this, trans !== null ? trans : val);
                },
                get: origTextAreaPlaceholder.get,
                configurable: true
            });
        }
    } catch(e) {}

    function initTranslator() {
        if (!document.body) {
            setTimeout(initTranslator, 30);
            return;
        }
        observeRoot(document.body);
    }

    if (document.readyState === 'loading') {
        window.addEventListener('DOMContentLoaded', initTranslator);
    } else {
        initTranslator();
    }
})();
