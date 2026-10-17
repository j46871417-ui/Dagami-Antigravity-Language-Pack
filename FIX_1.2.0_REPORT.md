# Language Pack 1.2.0 — итог проверки

Правки готовы локально. Публикации не было.

## Что изменено

Новый переводчик хранит исходный DOM и меняет текст лишь в копии блока.
Списки, заголовки, таблицы, ссылки, код и прежние действия кнопок остаются.
EN возвращает исходный блок и стили. Отмена и новый текст не дают старому
ответу занять место свежего. Код, URL и поля ввода исключены из запросов.
Работают очередь на два запроса, лимит кеша и таймаут.

В GUI есть «Обновления»: проверка GitHub при запуске и раз в шесть часов,
загрузка и установка лишь по кнопке. Есть флаги проверки и тестовых версий.
CLI: --check-update, --download-update.
Windows EXE проверяет размер, SHA-256 из API, имя продукта и номер версии.
План защищён DPAPI. Помощник ждёт выхода старой копии, без kill, хранит старый
EXE, отказывается от чужой правки и делает откат при сбое записи.
Итог, этап сбоя и код ошибки хранятся в last-result.json.
В исходниках и на Linux/macOS доступна проверка и загрузка, установка вручную.
Папки без прав записи не повышают права сами; нужен ручной перенос.

Один путь сборки даёт тот же EXE для ZIP и отдельного файла.
Старый .NET-путь и старый скрипт рассылки отключены.
CI проверяет и собирает файлы, но не публикует.
Скрипт GitHub работает с черновиком и сверяет хеши до публикации.

## Проверено

- 148 тестов Python: PASS.
- 26 проверок нового движка в настоящем Edge без сети: PASS.
- 14 прежних проверок JS: PASS.
- Синтаксис runtime всех шести языков: PASS.
- Современный тест ASAR: установка RU, повтор, смена на ES, откат;
  посторонние бинарные байты не меняются: PASS.
- Настоящий помощник из EXE: успех, отмена, занятый файл, подмена DPAPI-плана:
  PASS. Заменялись только тестовые EXE в отдельной папке.
- Реальное окно готового EXE 1.2.0 запущено скрыто и закрыто штатно: PASS.
- Реальный GitHub API: найден v1.1.0, корректно признан старее локальной
  1.2.0. Скачивание и установка при этом не начинались.
- Новые модули, точный JS и Tcl/Tk входят в EXE. EXE в обоих ZIP совпадает:
  PASS.

## Что нашли при проверке и исправили

- Tcl/Tk 9 в Python 3.14 хранит скрипты в DLL zipfs. Старый сборщик не включал
  их, и EXE падал ещё до старта. В сборку добавлена выгрузка этих файлов.
- Завершённый процесс может ещё иметь PID, пока открыт дескриптор родителя.
  Ожидание помощника теперь смотрит реальный выход, а не лишь наличие PID.
- При закрытии Tk удаляются таймеры. Ошибка таймеров после закрытия устранена.
- Возврат EN хранит точную запись стиля и не теряет чужие новые стили.
- Ошибка старта пишет отдельный startup-error.log.

## Пределы

Сетевой перевод Google и вход реального аккаунта не проверялись: в тесте
движка fetch подменён. Тестовые тексты никуда не отправлялись.
Работающая копия Antigravity, её ASAR, профиль, DNS и прокси не менялись.
После замены Language Pack нужно снова нажать «Установить язык», чтобы
движок внутри Antigravity обновился. Сначала закройте Antigravity сами.
Linux/macOS и путь UAC не проверены; автоматическая замена только Windows EXE.

## Файлы проверки

python-tests-final.log, helper-smoke.log, helper-smoke.json, frozen-gui.json,
build-final.log, change-files.json и audit.py лежат рядом с этим отчётом.
Исходники работы находятся в каталоге work. SHA256SUMS.txt — в release_dist.


## Smaller local build

Removed unused legacy resources/app.asar and web_bundle_ru from the new runtime.
They stay in the source tree for historical tests. Windows ZIP now holds the
standalone EXE and four docs, without a second runtime or Python source copy.
EXE: 23,778,245 -> 16,189,473 bytes. Windows ZIP: 32,303,458 -> 15,957,591 bytes.
The Python/Tk runtime is retained for standalone Windows use.

Checks on the smaller final EXE: bundle check, real hidden GUI open/close,
fixture ASAR RU install/repeat/ES switch/exact restore, four real helper cases
(success/cancel/locked/tampered), and 148 Python tests passed.
Real Antigravity, accounts and network settings were not changed. No publication.
Logs: build-lean.log, python-tests-lean.log. Smoke: lean_bundle_smoke.py.
