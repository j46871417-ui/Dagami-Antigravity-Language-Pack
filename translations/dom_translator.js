/**
 * Google Antigravity 2.0 — Russian Localization Engine (Open Source)
 * Автоматический перевод пользовательского интерфейса на русский язык.
 * Репозиторий: https://github.com/j46871417-ui/-Antigravity
 */
(function () {
  'use strict';

  const DICT = {
  "New Conversation": "Новый диалог",
  "New conversation": "Новый диалог",
  "Conversation History": "История диалогов",
  "Conversation history": "История диалогов",
  "Projects": "Проекты",
  "Scheduled Tasks": "Запланированные задачи",
  "Scheduled tasks": "Запланированные задачи",
  "Skills & Customizations": "Навыки и настройки",
  "Skills & customizations": "Навыки и настройки",
  "Customizations": "Кастомизация",
  "Customization": "Настройки",
  "Settings": "Настройки",
  "UI Plugins": "UI Плагины",
  "UI plugins": "UI Плагины",
  "Automations": "Автоматизации",
  "Recent Conversations": "Недавние диалоги",
  "Recent conversations": "Недавние диалоги",
  "Recent": "Недавние",
  "History": "История",
  "Running agents": "Запущенные агенты",
  "No agents running": "Нет запущенных агентов",
  "Open Settings": "Открыть настройки",
  "Global Settings": "Общие настройки",
  "Project Settings": "Настройки проекта",
  "Restart to Update": "Перезапуск для обновления",
  "Open IDE": "Открыть IDE",
  "Open in IDE": "Открыть в IDE",
  "Open Antigravity IDE": "Открыть Antigravity IDE",
  "Ask anything, @ to mention, / for actions": "Спросите что угодно, @ для упоминания, / для действий",
  "File": "Файл",
  "Edit": "Правка",
  "View": "Вид",
  "Window": "Окно",
  "Help": "Справка",
  "Local": "Локально",
  "MCP Error": "Ошибка MCP",
  "Show all": "Показать все",
  "See all": "Показать все",
  "Not in Project": "Вне проекта",
  "Conversations": "Диалоги",
  "Shortcuts": "Горячие клавиши",
  "Provide Feedback": "Оставить отзыв",
  "Provide feedback": "Оставить отзыв",
  "Feedback": "Обратная связь",
  "Pinned Conversations": "Закрепленные диалоги",
  "Other Conversations": "Другие диалоги",
  "Standalone Conversations": "Отдельные диалоги",
  "All Workspaces": "Все пространства",
  "Current Workspace": "Текущее пространство",
  "Workspaces": "Рабочие пространства",
  "Workspace": "Рабочее пространство",
  "Worktree": "Рабочее дерево",
  "Previous Worktrees": "Предыдущие рабочие деревья",
  "Add Workspace": "Добавить рабочую область",
  "New Workspace": "Новая рабочая область",
  "Archive Workspace": "Архивировать пространство",
  "Connect to Remote Workspace": "Подключиться к удаленной рабочей области",
  "Recent Remote Workspaces": "Недавние удаленные рабочие области",
  "Select Theme": "Выберите тему",
  "Select Antigravity Theme": "Выберите тему Antigravity",
  "Select Antigravityru Theme": "Выберите тему Antigravity",
  "Use theme to be imported with settings": "Использовать тему из импортированных настроек",
  "Light preview": "Светлая тема",
  "Dark preview": "Тёмная тема",
  "Light": "Светлая",
  "Dark": "Тёмная",
  "System": "Системная",
  "Inherit": "Как в системе",
  "Previous": "Назад",
  "Next": "Далее",
  "Get Started": "Начать",
  "Finish": "Готово",
  "Skip": "Пропустить",
  "Continue": "Продолжить",
  "Back": "Назад",
  "Complete Setup": "Завершить настройку",
  "Reset Onboarding": "Сбросить настройку",
  "Account": "Аккаунт",
  "Permissions": "Разрешения",
  "General": "Основные",
  "Appearance": "Внешний вид",
  "Tab": "Таб",
  "Editor": "Редактор",
  "Browser": "Браузер",
  "Notifications": "Уведомления",
  "Models": "Модели",
  "App": "Приложение",
  "Application": "Приложение",
  "Project General": "Общие проекта",
  "Project Folders": "Папки проекта",
  "Project Agent": "Агент проекта",
  "Jetski Chat": "Чат",
  "Labs": "Лаборатория",
  "CitC Settings": "Настройки CitC",
  "Best of N": "Best of N",
  "Developer": "Для разработчиков",
  "Regroup Google3 Chats": "Перегруппировка чатов Google3",
  "Close Settings": "Закрыть настройки",
  "Manage Permissions": "Управление разрешениями",
  "Manage permissions": "Управление разрешениями",
  "Advanced Settings": "Расширенные настройки",
  "Advanced": "Расширенные",
  "Preferences": "Параметры",
  "Open Preferences": "Открыть параметры",
  "Manage your plan, credentials, and general preferences.": "Управление подпиской, учётными данными и общими параметрами.",
  "Manage Antigravity app settings.": "Управление настройками приложения Antigravity.",
  "Manage Antigravityru app settings.": "Управление настройками приложения Antigravity.",
  "Configure the agent's visual theme and display preferences.": "Настройка визуальной темы и отображения агента.",
  "Configure editor-specific behaviors and shortcuts.": "Настройка поведения редактора и сочетаний клавиш.",
  "Manage your notification preferences.": "Управление параметрами уведомлений.",
  "Keyboard shortcuts for quick navigation and control.": "Сочетания клавиш для быстрой навигации и управления.",
  "Configure tab completion, suggestions, and navigation behavior.": "Настройка автодополнения по клавише Tab, подсказок и навигации.",
  "Configure agent execution, queued message delivery, and permissions.": "Настройка выполнения агента, доставки сообщений в очереди и разрешений.",
  "Manage fine-grained permissions for GitHub.": "Управление детальными разрешениями для GitHub.",
  "Developer-only tools. These settings are stored locally in this browser and do not affect other users.": "Инструменты для разработчиков. Эти настройки сохраняются локально в этом браузере.",
  "Try out early-stage features before they ship. These may change or be removed at any time.": "Попробуйте экспериментальные функции до их официального релиза. Они могут изменяться или быть удалены в любое время.",
  "Manage settings specific to Google CitC workspaces development.": "Управление настройками рабочих областей Google CitC.",
  "Manage how Best of N sets up the workspaces its arms run in.": "Настройка рабочих пространств для режима Best of N.",
  "Prevent Sleep": "Запретить спящий режим",
  "Prevent the computer from sleeping while the app is running.": "Запрещать компьютеру переходить в спящий режим при работе приложения.",
  "Keep In Menu Bar": "Оставлять в строке меню",
  "Keep the app accessible from the menu bar and running in the background when all windows are closed.": "Держать приложение в строке меню и фоне при закрытии всех окон.",
  "Remote Control": "Удалённое управление",
  "Enable Remote Control": "Включить удалённое управление",
  "Work with local agents from another device.": "Работа с локальными агентами с других устройств.",
  "Manage your conversations from the companion website.": "Управление диалогами через сопутствующий веб-сайт.",
  "Notification Settings": "Настройки уведомлений",
  "To modify notification settings, open your operating system's system preferences.": "Для изменения настроек уведомлений откройте параметры операционной системы.",
  "Open System Preferences": "Открыть системные настройки",
  "Automatic Check for Updates": "Автопроверка обновлений",
  "Automatically prompt you to restart the app when a new update is available. When disabled, you can check for updates manually from the app menu.": "Автоматически предлагать перезапуск при наличии обновления. Если отключено, проверять обновления можно вручную в меню.",
  "Nickname": "Псевдоним",
  "A nickname for identifying this application in the companion website. Changing this will restart the connection.": "Имя для идентификации этого приложения на сопутствующем веб-сайте.",
  "Device Name": "Имя устройства",
  "Enter device name...": "Введите имя устройства...",
  "Allow List Terminal Commands": "Список разрешённых команд",
  "Deny List Terminal Commands": "Список запрещённых команд",
  "Agent Auto-Fix Lints": "Автоисправление ошибок линтера",
  "Give the agent awareness of lint errors created by its edits so it can fix them without explicit prompting.": "Сообщать агенту об ошибках линтера в его правках для их автоматического исправления.",
  "Queued Messages": "Сообщения в очереди",
  "Configure when follow-up messages are sent.": "Настройка отправки последующих сообщений.",
  "Confirm Window Reload": "Подтвердить перезагрузку окна",
  "Enable Demo Mode (Beta)": "Включить демонстрационный режим (Бета)",
  "Explain and Fix in Current Conversation": "Объяснять и исправлять в текущем диалоге",
  "Strict Mode": "Строгий режим",
  "Enforce settings that prevent the agent from autonomously running targeted exploits and require human review for all agent actions. Visit antigravity.google/docs/strict-mode for details.": "Включение ограничений, требующих подтверждения пользователем всех действий агента.",
  "Agent Non-Workspace File Access": "Доступ агента к файлам вне пространства",
  "Command Setup Script": "Скрипт подготовки команд",
  "A shell setup script run before every command the agent executes.": "Скрипт инициализации оболочки, выполняемый перед каждой командой агента.",
  "Enable Terminal Sandbox": "Включить песочницу терминала",
  "Run terminal commands with sandbox restrictions.": "Выполнять команды терминала с ограничениями песочницы.",
  "Sandbox Allow Network": "Разрешить сеть в песочнице",
  "Enable Shell Integration": "Включить интеграцию с оболочкой",
  "Use the IDE's shell integration to detect and report terminal command execution. When disabled, the agent uses its own shell. Restart the application for this to take effect.": "Интеграция с оболочкой IDE для отслеживания команд. При отключении используется встроенная оболочка агента. Требуется перезапуск.",
  "Terminal Command Auto Execution": "Автовыполнение команд терминала",
  "Agent Host Address": "Хост-адрес агента",
  "Review Policy": "Политика проверки",
  "Specifies the agent's behavior when asking for review on artifacts, which are documents it creates to enable a richer conversation experience.": "Определяет поведение агента при запросе проверки артефактов.",
  "Enable Sounds for Agent": "Звуковые сигналы агента",
  "Play a sound when the agent finishes generating a response.": "Воспроизводить звук, когда агент завершает генерацию ответа.",
  "Enable Notifications for Agent": "Включить уведомления агента",
  "Show browser notifications when your action is needed or execution finishes.": "Показывать системные уведомления, когда требуется действие или задача завершена.",
  "Auto-Expand Changes Overview": "Автораскрытие обзора изменений",
  "Automatically expand the Changes Overview toolbar when the agent finishes generating a response.": "Автоматически раскрывать панель обзора изменений после завершения ответа агента.",
  "Knowledge": "База знаний",
  "Let the agent access its knowledge base to inform its responses and automatically generate knowledge items in the background. Turning this off prevents the agent from accessing existing knowledge items, but doesn't delete them.": "Разрешить агенту обращаться к базе знаний и автоматически создавать записи в фоне.",
  "Auto-Open Edited Files": "Автооткрытие изменённых файлов",
  "Open files in the background if the agent creates or edits them": "Открывать файлы в фоне, если агент создаёт или редактирует их",
  "Open Agent on Reload": "Открывать агента при перезагрузке",
  "Open the agent panel on window reload": "Открывать панель агента при перезагрузке окна",
  "Verbose Agent Chat": "Подробный чат агента",
  "Display and preserve intermediate thinking steps.": "Отображать и сохранять промежуточные шаги рассуждений.",
  "Conversation Width": "Ширина панели диалога",
  "Configure the maximum width of the conversation panel.": "Настройка максимальной ширины панели переписки.",
  "Suggestions in Editor": "Подсказки в редакторе",
  "Show suggestions when typing in the editor": "Показывать подсказки при вводе текста в редакторе",
  "Tab to Jump": "Переход по Tab",
  "Predict the location of your next edit and navigate you there with a tab keypress.": "Предугадывать место следующей правки и перемещаться туда клавишей Tab.",
  "Tab to Import": "Импорт по Tab",
  "Quickly add and update imports with a tab keypress.": "Быстро добавлять и обновлять импорты нажатием клавиши Tab.",
  "Tab Speed": "Скорость подсказок Tab",
  "Set the speed of tab suggestions": "Скорость появления подсказок Tab",
  "Highlight After Accept": "Подсветка после принятия",
  "Highlight newly inserted text after accepting a Tab completion.": "Подсвечивать вставленный текст после принятия автодополнения Tab.",
  "Tab Gitignore Access": "Доступ Tab к .gitignore",
  "Allow Tab to view and edit the files in .gitignore. Use with caution if your .gitignore lists files containing credentials, secrets, or other sensitive information.": "Разрешить Tab просматривать и редактировать файлы из .gitignore. Используйте осторожно, если в .gitignore указаны файлы с секретами или паролями.",
  "Enable Browser Tools": "Включить инструменты браузера",
  "Let the agent use browser tools to open URLs, read web pages, and interact with browser content. This gives the agent access to important (and often critical) knowledge and methods of validation, but any browser integration does increase exposure to external malicious parties for security exploits.": "Разрешить агенту открывать ссылки, читать веб-страницы и взаимодействовать с браузером.",
  "Browser Javascript Execution Policy": "Политика исполнения JavaScript в браузере",
  "Controls whether the agent can run custom JavaScript to automate complex browser actions.": "Разрешить ли агенту исполнять пользовательский JavaScript в браузере.",
  "Chrome Binary Path": "Путь к исполняемому файлу Chrome",
  "Path to the Chrome/Chromium executable. Leave empty for auto-detection.": "Путь к Google Chrome или Chromium. Оставьте пустым для автоопределения.",
  "Browser User Profile Path": "Путь к профилю браузера",
  "Custom path for the browser user profile directory. Leave empty for default (~/.gemini/antigravity-browser-profile).": "Кастомный путь к профилю браузера. Оставьте пустым для значения по умолчанию.",
  "Browser CDP Port": "Порт Chrome DevTools Protocol",
  "Port number for Chrome DevTools Protocol remote debugging. Leave empty for default (9222).": "Порт для удалённой отладки CDP. Оставьте пустым по умолчанию (9222).",
  "Show Selection Actions": "Действия с выделенным текстом",
  "Include Jetski Default Customizations": "Включать стандартные кастомизации",
  "Include default customizations, such as default skills.": "Включать встроенные кастомизации и стандартные навыки.",
  "Enable Personal Customizations": "Включить личные настройки",
  "Layer your personal customizations (skills, rules, etc.) from your config on top of the active profile.": "Применять персональные настройки (навыки, правила и др.) поверх активного профиля.",
  "Inline Actions": "Быстрые действия",
  "Show a floating notification card when background conversations need your input. Answer questions, approve commands, and grant permissions without leaving your current conversation. Share feedback at go/inline-actions-feedback.": "Отображать карточку уведомлений, когда фоновым задачам требуется подтверждение.",
  "Always Proceed": "Всегда продолжать",
  "Always Ask": "Всегда спрашивать",
  "Always ask": "Всегда спрашивать",
  "Ask First": "Сначала спросить",
  "Ask first": "Сначала спросить",
  "Request Review": "Запрашивать проверку",
  "Request review": "Запрашивать проверку",
  "Always allow": "Всегда разрешать",
  "Always Allow": "Всегда разрешать",
  "Allow Once": "Разрешить один раз",
  "Allow once": "Разрешить один раз",
  "Deny": "Запретить",
  "Approve": "Одобрить",
  "Reject": "Отклонить",
  "Allow": "Разрешить",
  "Action required": "Требуется действие",
  "Confirmation required to execute this step": "Требуется подтверждение для выполнения этого шага",
  "Permission Grants": "Выданные разрешения",
  "Access grants": "Предоставление доступа",
  "Access rules": "Правила доступа",
  "Network Access Rules": "Правила доступа к сети",
  "File Access Rules": "Правила доступа к файлам",
  "Browser Actuation Rules": "Правила управления браузером",
  "Model Selection": "Выбор модели",
  "Select Model": "Выбрать модель",
  "Default Model": "Модель по умолчанию",
  "Custom Model": "Пользовательская модель",
  "Custom Models": "Пользовательские модели",
  "Add Custom Model": "Добавить модель",
  "Add Model": "Добавить модель",
  "Edit Model": "Редактировать модель",
  "Model Quota": "Квота модели",
  "Model quota reached": "Квота модели исчерпана",
  "Recommended": "Рекомендуется",
  "Experimental": "Экспериментальная",
  "Experimental model. Click to provide feedback or opt out.": "Экспериментальная модель. Нажмите, чтобы оставить отзыв.",
  "Error Loading Models": "Ошибка загрузки моделей",
  "No Model Selected": "Модель не выбрана",
  "No Models Available": "Нет доступных моделей",
  "No models available": "Нет доступных моделей",
  "Type a message...": "Введите сообщение...",
  "Ask a question or provide instructions...": "Задайте вопрос или опишите задачу...",
  "Ask anything...": "Спросите что угодно...",
  "Reply to agent...": "Ответить агенту...",
  "Send a message...": "Отправить сообщение...",
  "Describe your task...": "Опишите вашу задачу...",
  "Enter a prompt for the agent to run...": "Введите задачу для агента...",
  "Attach files": "Прикрепить файлы",
  "Attach a screenshot (optional)": "Прикрепить снимок экрана (необязательно)",
  "Drop to add to Agent": "Перетащите, чтобы передать агенту",
  "Drop files here": "Перетащите файлы сюда",
  "Paste code here": "Вставьте код сюда",
  "Quote Selection": "Цитировать выделенное",
  "Add to Chat": "Добавить в чат",
  "Add to Chat/Quote": "Добавить в чат/цитировать",
  "Terminal: Add to Chat": "Терминал: добавить в чат",
  "Start Voice Recording": "Начать запись голоса",
  "Stop Voice Recording": "Остановить запись голоса",
  "Toggle Voice Recording": "Голосовой ввод",
  "Send": "Отправить",
  "Stop": "Остановить",
  "Thinking": "Рассуждения",
  "Thinking...": "Размышление...",
  "Generating...": "Генерация...",
  "Running...": "Выполняется...",
  "Running": "Выполняется",
  "Completed": "Завершено",
  "Failed": "Ошибка",
  "Cancelled": "Отменено",
  "Pending": "В ожидании",
  "Idle": "Ожидание",
  "Connected": "Подключено",
  "Disconnected": "Отключено",
  "Ready": "Готов",
  "In Progress": "В процессе",
  "Input required": "Требуется ввод",
  "Blocked on Your Input": "Ожидает вашего ввода",
  "Blocked, needs input": "Заблокировано, требуется ввод",
  "Copy thinking": "Скопировать рассуждения",
  "Copy conversation markdown": "Скопировать как Markdown",
  "Conversation copied as Markdown to clipboard": "Диалог скопирован в буфер обмена в формате Markdown",
  "Clear chat": "Очистить чат",
  "Continue Response": "Продолжить ответ",
  "Fork in current workspace": "Создать ответвление в текущей рабочей области",
  "Plan": "План",
  "Planning": "Планирование",
  "Proceed with Plan": "Выполнить план",
  "Artifacts": "Артефакты",
  "Subagents": "Субагенты",
  "Background Tasks": "Фоновые задачи",
  "Background tasks": "Фоновые задачи",
  "Files Changed": "Изменённые файлы",
  "Files changed": "Изменённые файлы",
  "Terminals": "Терминалы",
  "Terminal": "Терминал",
  "Console": "Консоль",
  "Output": "Вывод",
  "Logs": "Логи",
  "Preview": "Предпросмотр",
  "Diff": "Различия",
  "Overview": "Обзор",
  "Timeline": "Хронология",
  "Stop Subagent": "Остановить субагента",
  "Stop All Subagents": "Остановить всех субагентов",
  "Cancel step": "Отменить шаг",
  "Cancel task": "Отменить задачу",
  "Cancel All Tasks": "Отменить все задачи",
  "Delete Terminal": "Закрыть терминал",
  "New Terminal Tab": "Новая вкладка терминала",
  "Close Terminal Tab": "Закрыть терминал",
  "Split Terminal": "Разделить терминал",
  "Creating terminal...": "Создание терминала...",
  "No active terminals": "Нет активных терминалов",
  "No subagents": "Нет субагентов",
  "No background tasks": "Нет фоновых задач",
  "No artifacts yet": "Нет артефактов",
  "No changes detected": "Изменений не обнаружено",
  "No file changes": "Нет изменений файлов",
  "No changes to review": "Нет изменений для проверки",
  "Uncommitted": "Незафиксированные",
  "Staged index changes and working tree changes": "Проиндексированные и рабочие изменения",
  "Agent Edits": "Правки агента",
  "Files modified by the agent in this conversation": "Файлы, изменённые агентом в этом диалоге",
  "Branch": "Ветка",
  "All changes since the branch point": "Все изменения от точки ветвления",
  "Code Change Summary": "Сводка изменений кода",
  "Cancel": "Отмена",
  "Confirm": "Подтвердить",
  "Delete": "Удалить",
  "Save": "Сохранить",
  "Save Changes": "Сохранить изменения",
  "Save changes": "Сохранить изменения",
  "Close": "Закрыть",
  "Apply": "Применить",
  "Proceed": "Продолжить",
  "Proceed Anyway": "Все равно продолжить",
  "Run": "Запустить",
  "Rerun": "Перезапустить",
  "Restart": "Перезапустить",
  "Pause": "Пауза",
  "Resume": "Возобновить",
  "Retry": "Повторить",
  "Try Again": "Попробовать снова",
  "Try again": "Попробовать снова",
  "Copy": "Копировать",
  "Copied!": "Скопировано!",
  "Copied": "Скопировано",
  "Copy Content": "Скопировать содержимое",
  "Copy File Name": "Скопировать имя файла",
  "Copy File Path": "Скопировать путь к файлу",
  "Copy Image": "Скопировать изображение",
  "Copy Path": "Копировать путь",
  "Copy output": "Скопировать вывод",
  "Copy debug info": "Копировать отладку",
  "Edit Config": "Редактировать конфигурацию",
  "Edit Comment": "Редактировать комментарий",
  "Clear": "Очистить",
  "Clear all": "Очистить всё",
  "Reset": "Сбросить",
  "Done": "Готово",
  "Open": "Открыть",
  "Open Folder": "Открыть папку",
  "Open Project": "Открыть проект",
  "Add Project": "Добавить проект",
  "Add Folder": "Добавить папку",
  "Create Project": "Создать проект",
  "Archive project": "Архивировать проект",
  "Delete project": "Удалить проект",
  "Delete Task": "Удалить задачу",
  "Delete Conversation": "Удалить диалог",
  "Archive this conversation": "Архивировать диалог",
  "Delete Permanently": "Удалить навсегда",
  "Select All": "Выделить всё",
  "Undo": "Отменить",
  "Redo": "Повторить",
  "Cut": "Вырезать",
  "Paste": "Вставить",
  "Refresh": "Обновить",
  "Reload": "Перезагрузить",
  "Reload Window": "Перезагрузить окно",
  "Dismiss": "Закрыть",
  "Got it": "Понятно",
  "Learn more": "Подробнее",
  "Learn more.": "Подробнее.",
  "Manage": "Управление",
  "Install": "Установить",
  "Installed": "Установлено",
  "Installing...": "Установка...",
  "Install IDE": "Установить IDE",
  "Download": "Скачать",
  "Download Diagnostics": "Скачать диагностику",
  "Upload": "Загрузить",
  "Expand All": "Развернуть всё",
  "Collapse All": "Свернуть всё",
  "Expand All Folders": "Развернуть все папки",
  "Collapse All Folders": "Свернуть все папки",
  "Submit": "Отправить",
  "Submitting...": "Отправка...",
  "Search...": "Поиск...",
  "Search tasks...": "Поиск задач...",
  "Search plugins...": "Поиск плагинов...",
  "Search automations...": "Поиск автоматизаций...",
  "Search conversations...": "Поиск диалогов...",
  "Search projects...": "Поиск проектов...",
  "Search settings...": "Поиск настроек...",
  "Search workspaces...": "Поиск рабочих областей...",
  "Search across files...": "Поиск по файлам...",
  "Type to search...": "Введите для поиска...",
  "Filter": "Фильтр",
  "Sort Conversations": "Сортировка диалогов",
  "Group By": "Группировать по",
  "Group By Project": "По проектам",
  "Group By Workspace": "По пространствам",
  "Open Keyboard Shortcuts": "Открыть список горячих клавиш",
  "Toggle Sidebar": "Боковая панель",
  "Find in conversation": "Поиск в диалоге",
  "Toggle Model Selector": "Выбор модели",
  "Toggle Terminal": "Скрыть/показать терминал",
  "Toggle File Viewer": "Просмотр файлов",
  "Toggle Editor": "Скрыть/показать редактор",
  "Toggle Project Selector": "Выбор проекта",
  "Toggle Environment Selector": "Выбор окружения",
  "Toggle Auxiliary Pane": "Вспомогательная панель",
  "New Editor Window": "Новое окно редактора",
  "Close Tab": "Закрыть вкладку",
  "File Picker": "Выбор файла",
  "Open Command Palette": "Палитра команд",
  "Open Conversation Picker": "Выбор диалога",
  "Open Workspace Selector": "Выбор рабочей области",
  "Focus Input": "Фокус в поле ввода",
  "Zoom In": "Увеличить масштаб",
  "Zoom Out": "Уменьшить масштаб",
  "Reset Zoom": "Сбросить масштаб",
  "Find in Pane": "Поиск на панели",
  "Go Back": "Назад",
  "Go Forward": "Вперёд",
  "Code Search": "Поиск по коду",
  "Open Commit Graph": "Граф коммитов",
  "Open Conversation History": "Открыть историю диалогов",
  "Open Conversation": "Открыть диалог",
  "Mark as Read": "Отметить как прочитанное",
  "Mark as Unread": "Отметить как непрочитанное",
  "Archive / Restore": "Архивировать / Восстановить",
  "Close (Escape)": "Закрыть (Escape)",
  "Next match (Enter)": "Следующее совпадение (Enter)",
  "Previous match (Shift+Enter)": "Предыдущее совпадение (Shift+Enter)",
  "Today": "Сегодня",
  "Yesterday": "Вчера",
  "Previous 7 Days": "Предыдущие 7 дней",
  "Previous 30 Days": "Предыдущие 30 дней",
  "Last 7 days": "За последние 7 дней",
  "Older": "Ранее",
  "Monday": "Понедельник",
  "Tuesday": "Вторник",
  "Wednesday": "Среда",
  "Thursday": "Четверг",
  "Friday": "Пятница",
  "Saturday": "Суббота",
  "Sunday": "Воскресенье",
  "Daily": "Ежедневно",
  "Weekly": "Еженедельно",
  "Hourly": "Ежечасно",
  "Something went wrong": "Что-то пошло не так",
  "Something went wrong!": "Что-то пошло не так!",
  "File not found": "Файл не найден",
  "Task not found": "Задача не найдена",
  "Failed to load conversation": "Не удалось загрузить диалог",
  "Failed to delete conversation": "Не удалось удалить диалог",
  "Failed to start conversation": "Не удалось начать диалог",
  "Failed to stop agent": "Не удалось остановить агента",
  "Connecting to language server...": "Подключение к языковому серверу...",
  "No internet. Agent features may not work.": "Нет подключения к Интернету. Функции агента могут не работать.",
  "No items found": "Ничего не найдено",
  "No results found.": "Результаты не найдены.",
  "No matching results": "Нет подходящих результатов",
  "No conversations yet": "Пока нет диалогов",
  "No tasks found": "Задачи не найдены",
  "No scheduled tasks": "Нет запланированных задач",
  "No projects found": "Проекты не найдены",
  "No projects created": "Проекты еще не созданы",
  "No folders added yet.": "Папки пока не добавлены.",
  "No workspaces found": "Рабочие области не найдены",
  "No workspaces open.": "Нет открытых рабочих областей.",
  "No skills available": "Навыки недоступны",
  "No skills loaded.": "Навыки не загружены.",
  "No plugins available": "Плагины недоступны",
  "No MCP servers installed": "Серверы MCP не установлены",
  "Models & Usage": "Модели и использование",
  "Manage your model quota and credits.": "Управление квотами моделей и кредитами.",
  "Your Plan:": "Ваш тариф:",
  "Your Plan: Google AI Pro": "Ваш тариф: Google AI Pro",
  "You can upgrade to a Google AI Ultra plan to receive higher rate limits.": "Вы можете перейти на тариф Google AI Ultra для получения более высоких лимитов.",
  "Upgrade": "Улучшить тариф",
  "Model Credits": "Кредиты модели",
  "Enable AI Credit Overages": "Разрешить перерасход AI-кредитов",
  "Gemini Models": "Модели Gemini",
  "Claude and GPT models": "Модели Claude и GPT",
  "Weekly Limit Remaining": "Остаток недельного лимита",
  "Five Hour Limit Remaining": "Остаток лимита на 5 часов",
  "No quota information available.": "Информация о квоте недоступна.",
  "Refresh quota and credits data": "Обновить данные о квоте и кредитах",
  "Execution": "Выполнение",
  "Queue": "В очередь",
  "Send Immediately": "Отправлять сразу",
  "Keyboard shortcuts": "Горячие клавиши",
  "Agent Settings": "Настройки агента",
  "Security Preset": "Предустановка безопасности",
  "Choose a predefined security preset for the agent. This controls terminal auto-execution policy, and file access policy.": "Выберите готовую предустановку безопасности для агента. Это определяет политику автоматического выполнения команд терминала и доступа к файлам.",
  "Turbo Mode": "Режим Турбо",
  "Turbo": "Турбо",
  "Learn more about Turbo mode": "Подробнее о режиме Турбо",
  "Agent Behavior": "Поведение агента",
  "Artifact Review Policy": "Политика проверки артефактов",
  "Specifies Agent's behavior when asking for review on artifacts, which are documents it creates to enable a richer conversation experience.": "Определяет поведение агента при запросе проверки артефактов.",
  "File Permissions": "Права доступа к файлам",
  "Configure allowed and denied paths for file reads and writes.": "Настройка разрешенных и запрещенных путей для чтения и записи файлов.",
  "Network Permissions": "Сетевые разрешения",
  "Configure allowed and denied URLs for reading.": "Настройка разрешенных и запрещенных URL для чтения.",
  "Terminal & Tooling Permissions": "Разрешения терминала и инструментов",
  "Terminal Commands": "Команды терминала",
  "Configure allowed terminal commands.": "Настройка разрешенных команд терминала.",
  "Commands Outside Sandbox": "Команды вне песочницы",
  "Configure allowed commands outside the sandbox.": "Настройка разрешенных команд вне песочницы.",
  "MCP Tools": "Инструменты MCP",
  "Configure external tools via Model Context Protocol.": "Настройка внешних инструментов через Model Context Protocol (MCP).",
  "Allow/deny specific terminal commands.": "Разрешить или запретить конкретные команды терминала.",
  "Allow/deny agent command execution outside the sandbox.": "Разрешить или запретить запуск команд агента вне песочницы.",
  "External tools the agent can call via Model Context Protocol.": "Внешние инструменты, которые агент может вызывать через MCP.",
  "Allow/deny agent read access to specific files or directories.": "Разрешить/запретить агенту чтение файлов или каталогов.",
  "Allow/deny agent write access to specific files or directories.": "Разрешить/запретить агенту запись в файлы или каталоги.",
  "Allow/deny agent read access to specific URLs or domains.": "Разрешить/запретить агенту чтение URL или доменов.",
  "Allow/deny agent browser actuation access to specific URLs.": "Разрешить/запретить агенту автоматизацию страниц по URL.",
  "Chat Settings": "Настройки чата",
  "Default": "По умолчанию",
  "Narrow": "Узкая",
  "Wide": "Широкая",
  "Theme": "Тема оформления",
  "Light Theme": "Светлая тема",
  "Dark Theme": "Тёмная тема",
  "Preset": "Предустановка",
  "Default Light": "Стандартная светлая",
  "Default Dark": "Стандартная тёмная",
  "Background": "Цвет фона",
  "Foreground": "Цвет текста",
  "Requires manual review for all terminal commands and file accesses outside of the working folders.": "Запрос подтверждения для всех команд и доступа к файлам вне рабочих папок.",
  "Full machine": "Полный доступ к системе",
  "Machine": "Система",
  "All terminal commands require review. The agent can read or write to any file in the machine.": "Все команды требуют подтверждения. Чтение и запись любых файлов на компьютере.",
  "Turbo mode": "Режим Турбо",
  "Disables all safety barriers for maximal iteration velocity.": "Отключает барьеры безопасности для максимальной скорости работы.",
  "Custom": "Пользовательский",
  "Manually customize individual settings.": "Ручная настройка отдельных параметров.",
  "Inherit General": "Использовать общие",
  "Inherits your General settings when working in this project.": "Использовать общие настройки при работе в этом проекте.",
  "Useful for typical development with an emphasis on security. It prioritizes safety over speed by requiring manual approval for all terminal commands and files outside the project directory.": "Оптимально для стандартной разработки. Приоритет безопасности: требует подтверждения для всех команд терминала и файлов вне каталога проекта.",
  "Useful for tasks that require file access across your full machine. The agent has full read and write access to all local files, but all proposed terminal commands require manual review and approval before running.": "Для задач с доступом ко всем файлам системы. Полный доступ на чтение/запись файлов, команды терминала требуют подтверждения.",
  "A high-risk mode that disables all safety barriers. The agent operates with full system access, auto-executes all terminal commands, and reads or writes to all local files without review prompts.": "Режим повышенного риска без ограничений. Агент выполняет команды терминала и работает с файлами без запросов подтверждения.",
  "Configure default behaviors, skills, and MCP servers.": "Настройка поведения по умолчанию, навыков и серверов MCP.",
  "Token Usage": "Использование токенов",
  "The breakdown below shows token usage from customizations like skills, rules, and MCP. If the budget is exceeded, large customizations will be truncated automatically.": "Расход токенов на настройки (навыки, правила, MCP). При превышении лимита крупные элементы автоматически усекаются.",
  "% of the customization budget is available.": "% бюджета настроек доступно.",
  "Customization token budget exceeded. Large customizations will be truncated.": "Лимит токенов на настройки превышен. Крупные элементы будут усечены.",
  "There are no customizations enabled.": "Настройки не включены.",
  "Loading token usage...": "Загрузка расхода токенов...",
  "Rules": "Правила",
  "Skills": "Навыки",
  "Mcp Tools": "Инструменты MCP",
  "System Prompt": "Системный промпт",
  "tokens)": "токенов)",
  "tokens": "токенов",
  "token": "токен",
  "Hide breakdown": "Скрыть детали",
  "Default Customizations": "Стандартные настройки",
  "Personal Customizations": "Личные настройки",
  "When enabled, the agent will include default customizations, including default skills.": "Если включено, агент будет использовать стандартные встроенные навыки.",
  "Plugins": "Плагины",
  "Build With Google Plugins": "Плагины от Google",
  "Browse and enable plugins from the Build With Google catalog.": "Просмотр и включение плагинов из каталога Build With Google.",
  "Customize": "Настроить",
  "Hooks": "Хуки",
  "Manage Hooks": "Управление хуками",
  "Configure hooks that run on agent lifecycle events.": "Настройка хуков для событий жизненного цикла агента.",
  "Search for MCP servers to add to your configuration": "Поиск серверов MCP для добавления в конфигурацию",
  "MCP Install Error:": "Ошибка установки MCP:",
  "Skills Configuration Error:": "Ошибка настройки навыков:",
  "MCP Configuration Error:": "Ошибка конфигурации MCP:",
  "Clear search": "Очистить поиск",
  "Customize Global Skills": "Настроить общие навыки",
  "Custom Agents": "Пользовательские агенты",
  "MCP Servers": "Серверы MCP",
  "Installed Skills": "Установленные навыки",
  "Installed MCP Servers": "Установленные серверы MCP",
  "Add MCP Servers": "Добавить серверы MCP",
  "Manage Skills": "Управление навыками",
  "Browser Settings": "Настройки браузера",
  "Configure the browser subagent. It requires": "Настройка субагента браузера. Требуется",
  "to be installed.": "установленный в системе.",
  "The browser subagent can be invoked by typing /browser in the conversation input box.": "Субагента браузера можно вызвать командой /browser в поле ввода.",
  "Actuation Permissions": "Разрешения на управление",
  "Configure allowed and denied URLs for browser actuation.": "Настройка разрешенных и запрещенных URL для управления браузером.",
  "Browser Actuation Permissions": "Разрешения на управление браузером",
  "Feature Disabled": "Функция отключена",
  "Access to the browser agent tools is blocked by your organization's admin controls policy.": "Доступ к инструментам браузера заблокирован политикой вашей организации.",
  "The browser subagent has been disabled by your administrator.": "Субагент браузера отключен вашим администратором.",
  "Organization Allowed Domains (Read-Only)": "Разрешенные домены организации (только чтение)",
  "Execute URLs": "Выполнение URL",
  "URLs the agent can actuate on in this workspace.": "URL для автоматизации браузера в этом пространстве.",
  "URLs the agent can actuate on using the browser.": "URL, на которых агент может совершать действия через браузер.",
  "Command and file access granted to the automation agents.": "Доступ к командам и файлам для агентов автоматизации.",
  "Override feature environment": "Переопределить окружение функций",
  "Operating System": "Операционная система",
  "Simulate running on a different OS.": "Симуляция работы в другой ОС.",
  "Host Environment": "Окружение хоста",
  "Simulate a different host (Electron, desktop or mobile Web, Extension, or remote control).": "Симуляция другого хоста (Electron, Web, расширение, Remote Control).",
  "User Type": "Тип пользователя",
  "Simulate a different user cohort (Google, External, Enterprise).": "Симуляция группы пользователей (Google, Внешние, Enterprise).",
  "Outside of folders file access policy": "Политика доступа к файлам вне папок проекта",
  "Configures how the agent tries to access files outside of its working folders.": "Настройка доступа агента к файлам за пределами рабочих папок.",
  "Controls whether terminal commands require your approval before running.": "Определяет, требуют ли команды терминала вашего подтверждения перед запуском.",
  "Enable Sandbox Mode (Preview)": "Включить режим песочницы (превью)",
  "Restricts agent tools to a secure, isolated local sandbox.": "Ограничивает инструменты агента изолированной локальной песочницей.",
  "A shell setup script run before every command the agent executes in this project. Overrides the global script.": "Скрипт инициализации оболочки для текущего проекта (переопределяет глобальный).",
  "Open files in the background if Agent creates or edits them": "Открывать файлы в фоне, если агент создаёт или редактирует их",
  "Open Agent panel on window reload": "Открывать панель агента при перезагрузке окна",
  "A label for this computer when you connect from another device. Changing it reconnects.": "Имя этого компьютера при подключении с другого устройства.",
  "Continue your work from another device with Remote Control. Scan the QR code or open the link below.": "Продолжите работу с другого устройства через Remote Control. Отсканируйте QR-код или откройте ссылку.",
  "Paths the agent can read inside this workspace.": "Пути, доступные агенту для чтения внутри этого пространства.",
  "Paths the agent can modify inside this workspace.": "Пути, доступные агенту для изменения внутри этого пространства.",
  "Terminal commands the agent can execute in this workspace.": "Команды терминала, разрешённые агенту в этом пространстве.",
  "URLs the agent can read or open in this workspace.": "URL, доступные для чтения в этом пространстве.",
  "Paths the agent can read.": "Пути, доступные агенту для чтения.",
  "Paths the agent can modify.": "Пути, доступные агенту для изменения.",
  "Terminal commands the agent can execute.": "Команды терминала, которые агент может выполнять.",
  "URLs the agent can read or open in the browser.": "URL, которые агент может читать или открывать в браузере.",
  "When enabled, sandboxed commands are allowed to make network requests.": "Если включено, изолированным командам разрешено выполнять сетевые запросы.",
  "When enabled, Agent will use IDE's shell integration to detect and report terminal command execution.": "Использовать интеграцию с оболочкой IDE для отслеживания выполнения команд.",
  "Allows the agent to access files outside of your current workspace.": "Разрешает агенту доступ к файлам вне текущего рабочего пространства.",
  "When enabled, Agent is given awareness of lint errors created by its edits and may fix them without explicit user prompting.": "Агент будет отслеживать ошибки линтера и исправлять их автоматически.",
  "When enabled, the agent will be able to access past conversations to inform its responses.": "Если включено, агент сможет обращаться к прошлым диалогам для улучшения ответов.",
  "When enabled, the agent will be able to access its knowledge base to inform its responses and automatically generate knowledge items in the background.": "Если включено, агент сможет использовать базу знаний и автоматически наполнять её в фоне.",
  "When enabled, 'Explain and Fix' actions will continue in the current conversation instead of starting a new one.": "Действия «Объяснить и исправить» продолжат текущий диалог вместо создания нового.",
  "When enabled, Antigravity will play a sound when Agent finishes generating a response.": "Звуковой сигнал при завершении генерации ответа.",
  "When enabled, the Changes Overview toolbar will automatically expand when Agent finishes generating a response.": "Автоматически раскрывать панель изменений при завершении ответа.",
  "Accept Step": "Принять шаг",
  "Reject Step": "Отклонить шаг",
  "Open Launchpad": "Открыть Launchpad",
  "Split Conversation Vertically": "Разделить диалог по вертикали",
  "Split Conversation Horizontally": "Разделить диалог по горизонтали",
  "Go Back in Pane": "Назад в панели",
  "Go Forward in Pane": "Вперед в панели",
  "Complete Onboarding Step": "Завершить шаг настройки",
  "Select Next Conversation": "Следующий диалог",
  "Select Previous Conversation": "Предыдущий диалог",
  "Restart Main Language Server": "Перезапустить языковой сервер",
  "Previous Aux Pane Tab": "Предыдущая вкладка",
  "Next Aux Pane Tab": "Следующая вкладка",
  "Open in Code Search": "Открыть в поиске кода",
  "Add inline comment": "Добавить комментарий",
  "Updater": "Обновление",
  "Experimental Features": "Экспериментальные функции",
  "Workspace Settings": "Настройки рабочего пространства",
  "Danger Zone": "Опасная зона",
  "Standalone Terminals": "Отдельные терминалы",
  "Folders": "Папки",
  "Uploads": "Загрузки",
  "New Worktree": "Новое рабочее дерево",
  "New worktree": "Новое рабочее дерево",
  "Clone current workspace into a new independent workspace": "Клонировать текущую рабочую область в новую независимую",
  "Run in your current workspace": "Запуск в текущей рабочей области",
  "Run in a new worktree": "Запуск в новом рабочем дереве",
  "Ask a quick question without interrupting the main conversation.": "Задать быстрый вопрос без прерывания основного диалога.",
  "Meta-agent for managing conversations": "Мета-агент для управления диалогами",
  "Team of subagents to do long running work": "Команда субагентов для длительных задач",
  "Workspace File Access": "Доступ к файлам рабочей области",
  "Workspace Command Access": "Доступ к командам рабочей области",
  "Workspace Web Access": "Веб-доступ рабочей области",
  "Search customizations...": "Поиск настроек...",
  "Search flags": "Поиск флагов",
  "Search all convos...": "Поиск по всем диалогам...",
  "Enter file or directory path...": "Введите путь к файлу или папке...",
  "Enter tool name or server...": "Введите имя инструмента или сервера...",
  "Enter URL pattern...": "Введите шаблон URL...",
  "Enter directory path...": "Введите путь к папке...",
  "Paste auth code": "Вставьте код авторизации",
  "Please list the steps to reproduce the issue": "Опишите шаги для воспроизведения проблемы",
  "Type absolute path or navigate folders...": "Введите путь или выберите папку...",
  "New hook name": "Имя нового хука",
  "Add recent remote workspace": "Добавить недавнюю рабочую область",
  "Search MCP servers by name": "Поиск серверов MCP по имени",
  "Select branch": "Выберите ветку",
  "Enter project name...": "Введите имя проекта...",
  "Prompt to execute on schedule...": "Промпт для выполнения по расписанию...",
  "Search steps...": "Поиск шагов...",
  "Edit comment": "Редактировать комментарий",
  "Delete comment": "Удалить комментарий",
  "Unstage change": "Убрать из индекса",
  "Stage change": "Индексировать изменение",
  "Discard unstaged changes": "Отменить неиндексированные изменения",
  "Send Now": "Отправить сейчас",
  "More Actions": "Другие действия",
  "More actions": "Другие действия",
  "Command Center": "Командный центр",
  "Rename": "Переименовать",
  "Open in Notebook View": "Открыть в виде блокнота",
  "Enable Telemetry": "Включить телеметрию",
  "Marketing Emails": "Рассылка новостей",
  "Sign Out": "Выйти",
  "Signing Out...": "Выход...",
  "Sign In": "Войти",
  "Not Signed In": "Вход не выполнен",
  "By using this app, you agree to its": "Используя приложение, вы принимаете",
  "Terms of Service": "Условия использования",
  "Privacy Notice": "Уведомление о конфиденциальности",
  "Google Privacy Policy": "Политика конфиденциальности Google",
  "Email": "Электронная почта",
  "You cannot sign out from Remote Control. Please sign out on your local application.": "Нельзя выйти через Remote Control. Выйдите в локальном приложении.",
  "Agent Script": "Скрипт агента",
  "Editor Settings": "Настройки редактора",
  "Notification Preferences": "Настройки уведомлений",
  "Permission Settings": "Настройки разрешений",
  "Local Permissions": "Локальные разрешения",
  "Tool Permissions": "Разрешения инструментов",
  "GitHub Permissions": "Разрешения GitHub",
  "GitHub Policies": "Политики GitHub",
  "Experimental features": "Экспериментальные функции",
  "Terminal Sandbox": "Песочница терминала",
  "Enable Overages": "Разрешить перерасход",
  "Enable Chat": "Включить чат",
  "Enable Notifications": "Включить уведомления",
  "Agent always asks for review.": "Агент всегда запрашивает проверку.",
  "Agent never asks for review. This maximizes the autonomy of the Agent, but also has the highest risk of the Agent operating over unsafe or injected Artifact content.": "Агент никогда не запрашивает проверку. Максимальная автономность, но повышенный риск работы с небезопасным содержимым.",
  "Whether the agent asks you to review its documents.": "Запрашивает ли агент проверку документов у пользователя.",
  "A Gemini-powered security agent decides if commands should be auto-approved.": "Агент безопасности на базе Gemini решает, подтверждать ли команды автоматически.",
  "Every terminal command requires approval.": "Каждая команда терминала требует подтверждения.",
  "The agent asks for permission before executing commands matched by a deny list entry.": "Агент запрашивает подтверждение перед выполнением команд из списка запрета.",
  "The agent auto-executes commands matched by an allow list entry.": "Агент автоматически выполняет команды из списка разрешений.",
  "Allow sandboxed commands to make network requests.": "Разрешить изолированным командам доступ к сети.",
  "Allow the agent to run without restrictions.": "Разрешить агенту работу без ограничений.",
  "Commands the agent can run outside the sandbox in this workspace.": "Команды, которые агент может запускать вне песочницы в этом пространстве.",
  "Commands the agent can run outside the sandbox.": "Команды, которые агент может запускать вне песочницы.",
  "File Reads": "Чтение файлов",
  "File Writes": "Запись файлов",
  "Read Files": "Чтение файлов",
  "Write Files": "Запись файлов",
  "Layer your personal customizations (skills, rules, etc.) from your config on top of workspace customizations.": "Накладывать личные навыки и правила поверх настроек рабочего пространства.",
  "Let the agent access past conversations to inform its responses.": "Разрешить агенту доступ к истории прошлых диалогов.",
  "Side-by-side layout": "Раздельный вид (рядом)",
  "Stacked layout": "Вертикальный вид (друг под другом)",
  "Sidebar grouped by project": "Группировка по проектам",
  "Sidebar grouped by workspace": "Группировка по пространствам",
  "Purchase Credits": "Купить кредиты",
  "Insufficient AI Credits": "Недостаточно AI-кредитов",
  "Baseline model quota reached": "Базовая квота модели исчерпана",
  "Tokens": "Токены",
  "Time to First Token (TTFT)": "Время до первого токена",
  "Delete MCP Server": "Удалить MCP-сервер",
  "Delete Handler": "Удалить обработчик",
  "Delete Hook": "Удалить хук",
  "Confirm Undo": "Подтвердить откат",
  "Share Conversation (Preview)": "Поделиться диалогом (превью)",
  "Attach Antigravity server logs": "Прикрепить логи сервера Antigravity",
  "Check for Updates": "Проверить обновления",
  "Check for updates": "Проверить обновления",
  "Update Available": "Доступно обновление",
  "New Session": "Новая сессия",
  "Conversation": "Диалог",
  "Chats": "Чаты",
  "Project": "Проект",
  "Create New Project": "Создать новый проект",
  "Project options": "Параметры проекта",
  "New Conversation in Project": "Новый диалог в проекте",
  "Current workspace": "Текущее пространство",
  "Open Workspace": "Открыть пространство",
  "Clone current workspace": "Клонировать рабочее пространство",
  "Skill": "Навык",
  "Rule": "Правило",
  "Global Rules": "Глобальные правила",
  "Workspace Rules": "Правила пространства",
  "Documentation": "Документация",
  "Docs": "Справка",
  "Send Feedback": "Отправить отзыв",
  "Help & Feedback": "Справка и отзывы",
  "Changelog": "История изменений",
  "Sign in": "Войти",
  "Sign out": "Выйти",
  "Log in": "Войти",
  "Log In": "Войти",
  "Log out": "Выйти",
  "Logout": "Выйти",
  "Load older messages": "Загрузить ранние сообщения",
  "Sidebar": "Боковая панель",
  "Maximize Pane": "Развернуть панель",
  "Equalize Split Panes": "Выровнять панели",
  "Display Options": "Параметры отображения",
  "More options": "Дополнительные параметры",
  "Pin conversation": "Закрепить диалог",
  "Archive conversation": "Архивировать диалог",
  "Conversation Archived": "Диалог архивирован",
  "Conversation ID": "Идентификатор диалога",
  "Select model": "Выбрать модель",
  "Switch Model": "Сменить модель",
  "Thinking Process": "Ход рассуждений",
  "Hide reasoning": "Скрыть рассуждения",
  "Show reasoning": "Показать рассуждения",
  "Planning Mode": "Режим планирования",
  "Fast": "Быстрый",
  "Pro": "Профессиональный",
  "High": "Высокая точность",
  "Low": "Экономный",
  "Balanced": "Сбалансированный",
  "Ask anything, @ to mention, / for workflows": "Спросите что угодно, @ для упоминания, / для процессов",
  "Ask anything": "Спросите что угодно...",
  "Message input": "Поле ввода сообщения",
  "Send message": "Отправить сообщение",
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
  "Clear conversation": "Очистить диалог",
  "Active Agents": "Активные агенты",
  "Follow along": "Следить за ходом",
  "Agent response": "Ответ агента",
  "User message": "Сообщение пользователя",
  "Artifact": "Артефакт",
  "Artifact Viewer": "Просмотр артефактов",
  "Artifact Viewer header": "Заголовок артефактов",
  "Table of contents": "Оглавление",
  "Subagent": "Субагент",
  "Active Subagents": "Активные субагенты",
  "No subagents running": "Нет запущенных субагентов",
  "Running Tasks": "Запущенные задачи",
  "Completed Tasks": "Завершённые задачи",
  "Changes": "Изменения",
  "Review changes": "Просмотр изменений",
  "No files changed": "Файлы не изменены",
  "Terminal tab": "Вкладка «Терминал»",
  "New Terminal": "Новый терминал",
  "Clear Terminal": "Очистить терминал",
  "Overview tab": "Вкладка «Обзор»",
  "Review": "Проверка",
  "Review tab": "Вкладка «Проверка»",
  "Review required": "Требуется проверка",
  "User Review Required": "Требуется проверка пользователя",
  "Implementation Plan": "План реализации",
  "Walkthrough": "Отчёт о работе",
  "Console logs": "Логи консоли",
  "Capture console logs": "Захват логов консоли",
  "Capture screenshot": "Сделать снимок экрана",
  "Accept": "Принять",
  "Accept All": "Принять все",
  "Reject All": "Отклонить все",
  "Copy path": "Скопировать путь",
  "Copy full URL to clipboard": "Скопировать URL",
  "Copy error to clipboard": "Скопировать ошибку",
  "Discard": "Отменить",
  "Open folder": "Открыть папку",
  "Open in Editor": "Открыть в редакторе",
  "Restore": "Восстановить",
  "Collapse": "Свернуть",
  "Expand": "Развернуть",
  "Clear search (Esc)": "Очистить поиск (Esc)",
  "Click to copy URL": "Нажмите, чтобы скопировать URL",
  "Click to copy full command": "Нажмите, чтобы скопировать команду",
  "Show output": "Показать вывод",
  "Hide output": "Скрыть вывод",
  "Details": "Подробности",
  "Working...": "Работаю...",
  "Waiting": "Ожидание",
  "Success": "Успешно",
  "Warning": "Предупреждение",
  "Error": "Ошибка",
  "Errors": "Ошибки",
  "Paused": "На паузе",
  "Connecting...": "Подключение...",
  "Reconnecting...": "Переподключение...",
  "Blocked": "Заблокировано",
  "Disabled": "Отключено",
  "Enabled": "Включено",
  "Keyboard Shortcuts": "Горячие клавиши",
  "Command Palette": "Палитра команд",
  "Commands": "Команды",
  "Discover helpful skills & plugins": "Каталог навыков и плагинов",
  "Browse the Marketplace": "Каталог плагинов",
  "All": "Все",
  "Search": "Поиск",
  "Search conversations": "Поиск диалогов",
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
  "Agent execution terminated due to error.": "Выполнение агента прервано из-за ошибки.",
  "Investigation timer: Timer has expired": "Таймер исследования: время истекло",
  "Error ID:": "ID ошибки:",
  "Planning...": "Планирование...",
  "Executing...": "Выполнение...",
  "Analyzing...": "Анализ...",
  "Searching...": "Поиск...",
  "Editing...": "Редактирование...",
  "Copy code": "Копировать код",
  "Copy link": "Копировать ссылку",
  "Link copied": "Ссылка скопирована",
  "New Chat": "Новый чат",
  "New chat": "Новый чат",
  "New Project": "Новый проект",
  "New project": "Новый проект",
  "Close Workspace": "Закрыть рабочую область",
  "Thinking Budget": "Бюджет размышлений",
  "Context Window": "Окно контекста",
  "Token Limit": "Лимит токенов",
  "Sign in with Google": "Войти с аккаунтом Google",
  "Logged in as": "Вы вошли как",
  "Run in Terminal": "Запустить в терминале",
  "Run command": "Выполнить команду",
  "Running command": "Выполнение команды",
  "Apply changes": "Применить изменения",
  "Discard changes": "Отменить изменения",
  "Keep changes": "Сохранить изменения",
  "Accept all": "Принять все",
  "Reject all": "Отклонить все",
  "Show diff": "Показать различия",
  "Hide diff": "Скрыть различия",
  "View details": "Подробнее",
  "Changes saved": "Изменения сохранены",
  "Auto-save": "Автосохранение",
  "Auto-saved": "Автосохранено",
  "Deselect All": "Снять выбор",
  "Remove": "Удалить",
  "Save as...": "Сохранить как...",
  "Browse...": "Обзор...",
  "Select Folder": "Выбрать папку",
  "Select File": "Выбрать файл",
  "Import": "Импорт",
  "Export": "Экспорт",
  "Share": "Поделиться"
  };

  function formatTime(str) {
    if (!str) return '';
    return str
      .replace(/(\d+)\s+days?/gi, '$1 дн.')
      .replace(/(\d+)\s+hours?/gi, '$1 ч.')
      .replace(/(\d+)\s+minutes?/gi, '$1 мин.')
      .replace(/(\d+)\s+seconds?/gi, '$1 сек.');
  }

  const RULES = [
    {
      regex: /^Select (.*) Theme$/i,
      replace: function (m) { return "Выберите тему Antigravity"; }
    },
    {
      regex: /^Manage (.*) app settings\.?$/i,
      replace: function (m) { return "Управление настройками приложения Antigravity."; }
    },
    {
      regex: /^Your Plan:\s*(.*)$/i,
      replace: function (m) { return "Ваш тариф: " + m[1]; }
    },
    {
      regex: /^When toggled on, .* will use your AI credits to fulfill model requests once you're out of model quota\..* will always use your model quota first before using AI credits\.$/i,
      replace: function (m) {
        return "При включении приложение будет использовать кредиты AI для выполнения запросов при исчерпании квоты моделей. В первую очередь всегда расходуется квота моделей.";
      }
    },
    {
      regex: /^Available AI Credits:\s*(.*)$/i,
      replace: function (m) { return "Доступно кредитов AI: " + m[1]; }
    },
    {
      regex: /^You have used some of your weekly limit, it will fully refresh in (.*)$/i,
      replace: function (m) {
        return "Часть недельного лимита израсходована, полное обновление через " + formatTime(m[1]);
      }
    },
    {
      regex: /^You have used some of your 5-hour limit, it will fully refresh in (.*)$/i,
      replace: function (m) {
        return "Часть 5-часового лимита израсходована, полное обновление через " + formatTime(m[1]);
      }
    },
    {
      regex: /^You have used some of your weekly \.\.\.$/i,
      replace: function (m) { return "Часть недельного лимита израсходована..."; }
    },
    {
      regex: /^You have used some of your 5-hour \.\.\.$/i,
      replace: function (m) { return "Часть 5-часового лимита израсходована..."; }
    },
    {
      regex: /^Learn more about (.*)$/i,
      replace: function (m) {
        const item = m[1].trim();
        if (item.toLowerCase() === 'turbo mode') return "Подробнее о режиме Турбо";
        return "Подробнее о " + item;
      }
    },
    {
      regex: /^Choose a permission preset\..*$/i,
      replace: function (m) {
        return "Выберите предустановку безопасности для агента.";
      }
    },
    {
      regex: /^Show\s+(\d+)\s+breakdowns?$/i,
      replace: function (m) { return "Подробнее (" + m[1] + ")"; }
    },
    {
      regex: /^No MCP servers found for "(.*)"$/i,
      replace: function (m) { return 'Не найдены серверы MCP по запросу "' + m[1] + '"'; }
    },
    {
      regex: /^See all \((\d+)\)$/i,
      replace: function (m) { return "Показать все (" + m[1] + ")"; }
    },
    {
      regex: /^When toggled on, .* collects usage data to help Google enhance performance and features\.?$/i,
      replace: function (m) {
        return "При включении данные об использовании отправляются в Google для улучшения функций.";
      }
    },
    {
      regex: /^Receive product updates, tips, and promotions from Google .* via email\.?$/i,
      replace: function (m) {
        return "Получать новости, советы и акции от Google по электронной почте.";
      }
    },
    {
      regex: /^Sign in to use (.*)!$/i,
      replace: function (m) {
        return "Войдите, чтобы использовать " + m[1] + "!";
      }
    },
    {
      regex: /^Show all \((\d+)\)$/i,
      replace: function (m) { return "Показать все (" + m[1] + ")"; }
    },
    {
      regex: /^(\d+)\s+conversations?$/i,
      replace: function (m) { return m[1] + " диалог(ов)"; }
    },
    {
      regex: /^(\d+)\s+projects?$/i,
      replace: function (m) { return m[1] + " проект(ов)"; }
    },
    {
      regex: /^(\d+)\s+tasks?$/i,
      replace: function (m) { return m[1] + " задач(и)"; }
    },
    {
      regex: /^(\d+)\s+files? changed$/i,
      replace: function (m) { return "Изменено файлов: " + m[1]; }
    },
    {
      regex: /^(\d+)\s+agents? running$/i,
      replace: function (m) { return "Запущено агентов: " + m[1]; }
    },
    {
      regex: /^(\d+)\s+of\s+(\d+)$/i,
      replace: function (m) { return m[1] + " из " + m[2]; }
    },
    {
      regex: /^(\d+)\s+items?$/i,
      replace: function (m) { return m[1] + " эл."; }
    }
  ];

  const IGNORE_TAGS = new Set([
    'SCRIPT', 'STYLE', 'CODE', 'PRE', 'TEXTAREA', 'INPUT'
  ]);

  function isIgnored(node) {
    if (!node) return true;
    let el = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    while (el) {
      if (IGNORE_TAGS.has(el.tagName)) return true;
      if (
        el.classList &&
        (el.classList.contains('token') ||
         el.classList.contains('prism') ||
         el.classList.contains('monaco-editor') ||
         el.classList.contains('cm-editor') ||
         el.classList.contains('xterm'))
      ) {
        return true;
      }
      if (el.getAttribute && el.getAttribute('data-notranslate') !== null) {
        return true;
      }
      el = el.parentElement;
    }
    return false;
  }

  function translateString(text) {
    if (typeof text !== 'string') return null;
    const trimmed = text.trim();
    if (!trimmed) return null;

    const startSpace = text.match(/^\s*/)[0];
    const endSpace = text.match(/\s*$/)[0];

    for (let i = 0; i < RULES.length; i++) {
      const match = trimmed.match(RULES[i].regex);
      if (match) {
        return startSpace + RULES[i].replace(match) + endSpace;
      }
    }

    if (DICT[trimmed]) {
      return startSpace + DICT[trimmed] + endSpace;
    }

    return null;
  }

  function translateNode(node) {
    if (!node) return;
    if (node.nodeType === Node.TEXT_NODE) {
      if (isIgnored(node)) return;
      const translated = translateString(node.nodeValue);
      if (translated && translated !== node.nodeValue) {
        node.nodeValue = translated;
      }
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      if (isIgnored(node)) return;

      if (node.hasAttribute('placeholder')) {
        const trans = translateString(node.getAttribute('placeholder'));
        if (trans) node.setAttribute('placeholder', trans);
      }
      if (node.hasAttribute('title')) {
        const trans = translateString(node.getAttribute('title'));
        if (trans) node.setAttribute('title', trans);
      }
      if (node.hasAttribute('aria-label')) {
        const trans = translateString(node.getAttribute('aria-label'));
        if (trans) node.setAttribute('aria-label', trans);
      }

      for (let child = node.firstChild; child; child = child.nextSibling) {
        translateNode(child);
      }
    }
  }

  try {
    const origNodeValueDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'nodeValue');
    if (origNodeValueDesc && origNodeValueDesc.set) {
      const origSet = origNodeValueDesc.set;
      Object.defineProperty(Node.prototype, 'nodeValue', {
        get: origNodeValueDesc.get,
        set: function (val) {
          if (this.nodeType === Node.TEXT_NODE && typeof val === 'string' && !isIgnored(this)) {
            const trans = translateString(val);
            if (trans) val = trans;
          }
          return origSet.call(this, val);
        },
        configurable: true,
        enumerable: true
      });
    }

    const origTextContentDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
    if (origTextContentDesc && origTextContentDesc.set) {
      const origTextSet = origTextContentDesc.set;
      Object.defineProperty(Node.prototype, 'textContent', {
        get: origTextContentDesc.get,
        set: function (val) {
          if (typeof val === 'string' && !isIgnored(this)) {
            const trans = translateString(val);
            if (trans) val = trans;
          }
          return origTextSet.call(this, val);
        },
        configurable: true,
        enumerable: true
      });
    }
  } catch (e) {
    console.warn('[i18n-ru] Hook setup error:', e);
  }

  function startObserver() {
    const observer = new MutationObserver((mutations) => {
      for (let i = 0; i < mutations.length; i++) {
        const m = mutations[i];
        if (m.type === 'childList') {
          for (let j = 0; j < m.addedNodes.length; j++) {
            translateNode(m.addedNodes[j]);
          }
        } else if (m.type === 'characterData') {
          translateNode(m.target);
        } else if (m.type === 'attributes') {
          if (['placeholder', 'title', 'aria-label'].includes(m.attributeName)) {
            const val = m.target.getAttribute(m.attributeName);
            const trans = translateString(val);
            if (trans && trans !== val) {
              m.target.setAttribute(m.attributeName, trans);
            }
          }
        }
      }
    });

    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['placeholder', 'title', 'aria-label']
    });

    setInterval(() => {
      translateNode(document.body);
    }, 200);

    translateNode(document.body || document.documentElement);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startObserver);
  } else {
    startObserver();
  }

  
// =========================================================================
// Dynamic On-the-Fly Thinking / Thought Process Translator
// =========================================================================
(function () {
  const STORAGE_KEY_AUTO = 'ag_thoughts_auto_translate';
  const CACHE = new Map();

  function isAutoTranslate() {
    try {
      return localStorage.getItem(STORAGE_KEY_AUTO) === 'true';
    } catch (e) {
      return false;
    }
  }

  function setAutoTranslate(val) {
    try {
      localStorage.setItem(STORAGE_KEY_AUTO, val ? 'true' : 'false');
    } catch (e) {}
  }

  async function translateText(text) {
    if (!text || !text.trim()) return text;
    const trimmed = text.trim();
    if (CACHE.has(trimmed)) return CACHE.get(trimmed);

    try {
      const url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&q=' + encodeURIComponent(trimmed);
      const res = await fetch(url);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      if (Array.isArray(data) && Array.isArray(data[0])) {
        const translated = data[0].map(function (item) { return item[0] || ''; }).join('');
        if (translated) {
          CACHE.set(trimmed, translated);
          return translated;
        }
      }
    } catch (e) {
      console.warn('[i18n-ru] Thought translation error:', e);
    }
    return text;
  }

  function processThinkingBlock(triggerEl) {
    if (!triggerEl || triggerEl.dataset.hasTranslateControls) return;
    triggerEl.dataset.hasTranslateControls = 'true';

    var collapsible = triggerEl.closest('[data-testid="thinking-collapsible-trigger"]') || triggerEl;
    var parentContainer = collapsible.parentElement;
    if (!parentContainer) return;

    var toolbar = document.createElement('span');
    toolbar.className = 'ag-thought-toolbar';
    toolbar.style.cssText = 'display:inline-flex; align-items:center; gap:6px; margin-left:10px; font-size:11px; font-family:sans-serif; vertical-align:middle; z-index:10;';

    // 1. RU / EN Button
    var btnTranslate = document.createElement('button');
    btnTranslate.type = 'button';
    btnTranslate.className = 'ag-btn-ru-en';
    btnTranslate.innerText = '🌐 RU';
    btnTranslate.title = 'Перевести размышления на русский';
    btnTranslate.style.cssText = 'padding:1px 6px; border-radius:4px; border:1px solid rgba(128,128,128,0.3); background:rgba(128,128,128,0.1); cursor:pointer; font-size:11px; color:inherit; font-weight:bold;';

    // 2. Auto toggle
    var btnAuto = document.createElement('button');
    btnAuto.type = 'button';
    btnAuto.className = 'ag-btn-auto';

    function updateAutoBtn() {
      var auto = isAutoTranslate();
      btnAuto.innerText = auto ? '⚡ Авто: ВКЛ' : '⚡ Авто: ВЫКЛ';
      btnAuto.style.cssText = 'padding:1px 6px; border-radius:4px; border:1px solid ' + (auto ? '#22c55e' : 'rgba(128,128,128,0.3)') + '; background:' + (auto ? 'rgba(34,197,94,0.15)' : 'rgba(128,128,128,0.1)') + '; color:' + (auto ? '#16a34a' : 'inherit') + '; cursor:pointer; font-size:11px;';
      btnAuto.title = auto ? 'Автоперевод включен. Кликните для отключения' : 'Автоперевод выключен. Кликните для автоматического перевода мыслей';
    }
    updateAutoBtn();

    btnAuto.onclick = function (e) {
      e.stopPropagation();
      setAutoTranslate(!isAutoTranslate());
      var allBtns = document.querySelectorAll('.ag-btn-auto');
      for (var i = 0; i < allBtns.length; i++) {
        var auto = isAutoTranslate();
        allBtns[i].innerText = auto ? '⚡ Авто: ВКЛ' : '⚡ Авто: ВЫКЛ';
        allBtns[i].style.borderColor = auto ? '#22c55e' : 'rgba(128,128,128,0.3)';
        allBtns[i].style.backgroundColor = auto ? 'rgba(34,197,94,0.15)' : 'rgba(128,128,128,0.1)';
        allBtns[i].style.color = auto ? '#16a34a' : 'inherit';
      }
      if (isAutoTranslate()) {
        doTranslate();
      }
    };

    var isShowingRussian = false;
    var originalText = null;

    async function doTranslate() {
      var contentEl = parentContainer.querySelector('.cursor-edit') || parentContainer.querySelector('pre') || parentContainer;
      if (!contentEl) return;

      if (!originalText) {
        originalText = contentEl.innerText;
      }

      btnTranslate.innerText = '⏳ ...';
      var ru = await translateText(originalText);
      if (ru && ru !== originalText) {
        contentEl.innerText = ru;
        isShowingRussian = true;
        btnTranslate.innerText = '🌐 EN';
        btnTranslate.title = 'Показать оригинальный английский текст';
        btnTranslate.style.backgroundColor = 'rgba(59, 130, 246, 0.2)';
        btnTranslate.style.borderColor = '#3b82f6';
      } else {
        btnTranslate.innerText = '🌐 RU';
      }
    }

    function doShowEnglish() {
      var contentEl = parentContainer.querySelector('.cursor-edit') || parentContainer.querySelector('pre') || parentContainer;
      if (contentEl && originalText) {
        contentEl.innerText = originalText;
        isShowingRussian = false;
        btnTranslate.innerText = '🌐 RU';
        btnTranslate.title = 'Перевести размышления на русский';
        btnTranslate.style.backgroundColor = 'rgba(128,128,128,0.1)';
        btnTranslate.style.borderColor = 'rgba(128,128,128,0.3)';
      }
    }

    btnTranslate.onclick = function (e) {
      e.stopPropagation();
      if (isShowingRussian) {
        doShowEnglish();
      } else {
        doTranslate();
      }
    };

    toolbar.appendChild(btnTranslate);
    toolbar.appendChild(btnAuto);
    triggerEl.appendChild(toolbar);

    if (isAutoTranslate()) {
      setTimeout(doTranslate, 600);
    }
  }

  function scanForThinkingBlocks() {
    var triggers = document.querySelectorAll('[data-testid="thinking-collapsible-trigger"]');
    for (var i = 0; i < triggers.length; i++) {
      processThinkingBlock(triggers[i]);
    }

    var copyBtns = document.querySelectorAll('button[title="Copy thinking"], button[title="Копировать размышления"]');
    for (var j = 0; j < copyBtns.length; j++) {
      var btn = copyBtns[j];
      var parent = btn.closest('div');
      if (parent && !parent.dataset.hasTranslateControls) {
        parent.dataset.hasTranslateControls = 'true';
        (function (b, p) {
          var ruBtn = document.createElement('button');
          ruBtn.type = 'button';
          ruBtn.innerText = '🌐 RU';
          ruBtn.title = 'Перевести размышления на русский';
          ruBtn.style.cssText = 'padding:1px 5px; font-size:10px; border-radius:3px; border:1px solid rgba(128,128,128,0.3); background:rgba(128,128,128,0.1); cursor:pointer; margin-right:4px; color:inherit;';
          ruBtn.onclick = async function (e) {
            e.stopPropagation();
            var pre = p.parentElement ? p.parentElement.querySelector('pre') : null;
            if (pre) {
              if (!pre._origEn) pre._origEn = pre.innerText;
              if (pre._isRu) {
                pre.innerText = pre._origEn;
                pre._isRu = false;
                ruBtn.innerText = '🌐 RU';
              } else {
                ruBtn.innerText = '...';
                var tr = await translateText(pre._origEn);
                pre.innerText = tr;
                pre._isRu = true;
                ruBtn.innerText = '🌐 EN';
              }
            }
          };
          b.parentElement.insertBefore(ruBtn, b);
        })(btn, parent);
      }
    }
  }

  setInterval(scanForThinkingBlocks, 500);
})();


  console.log('[i18n-ru] Russian localization fully active with ' + Object.keys(DICT).length + ' strings');
})();
