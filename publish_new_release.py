import os
import sys
import subprocess
import urllib.request
import json
import re
import zipfile
import shutil

repo_root = r"c:\Users\gabov\Documents\antigravity\happy-bose"

# 1. Get credentials
p = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True)
creds = dict(line.split('=', 1) for line in p.stdout.splitlines() if '=' in line)
token = creds.get('password')

headers = {
    'Authorization': f'token {token}',
    'User-Agent': 'Python',
    'Accept': 'application/vnd.github+json',
    'Content-Type': 'application/json'
}

repo_api = 'https://api.github.com/repos/j46871417-ui/Antigravity-Localizer'

# 2. Determine tag version
if len(sys.argv) > 1:
    new_tag = sys.argv[1].strip()
else:
    new_tag = "0.0.15"

print(f"[*] Target release tag: {new_tag}")

# 3. Update version in Program.cs
prog_cs_path = os.path.join(repo_root, "Program.cs")
with open(prog_cs_path, "r", encoding="utf-8") as f:
    prog_content = f.read()

prog_content = re.sub(
    r'public const string Version = "[^"]+";',
    f'public const string Version = "{new_tag}";',
    prog_content
)
prog_content = re.sub(
    r'\[assembly: AssemblyVersion\("[^"]+"\)]',
    f'[assembly: AssemblyVersion("{new_tag}.0")]',
    prog_content
)
prog_content = re.sub(
    r'\[assembly: AssemblyFileVersion\("[^"]+"\)]',
    f'[assembly: AssemblyFileVersion("{new_tag}.0")]',
    prog_content
)
with open(prog_cs_path, "w", encoding="utf-8") as f:
    f.write(prog_content)
print(f"[+] Updated Program.cs version to {new_tag}")

# 4. Rebuild payload.zip
payload_zip_path = os.path.join(repo_root, "payload.zip")
if os.path.exists(payload_zip_path):
    os.remove(payload_zip_path)

with zipfile.ZipFile(payload_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(repo_root, "resources", "app.asar"), "resources/app.asar")
    wb_dir = os.path.join(repo_root, "resources", "web_bundle_ru")
    for root, dirs, files in os.walk(wb_dir):
        for fl in files:
            full = os.path.join(root, fl)
            rel = os.path.relpath(full, repo_root).replace("\\", "/")
            z.write(full, rel)
    ide_json = os.path.join(repo_root, "translations", "ide_strings.json")
    if os.path.exists(ide_json):
        z.write(ide_json, "translations/ide_strings.json")
print("[+] payload.zip rebuilt")

# 5. Compile Standalone C# Executable FIRST (so Inno Setup can bundle it)
standalone_exe_name = f"AntigravityLocalizer_Standalone_v{new_tag}.exe"
standalone_exe_path = os.path.join(repo_root, standalone_exe_name)
standard_exe_path = os.path.join(repo_root, "AntigravityLocalizer.exe")

csc_path = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
csc_cmd = [
    csc_path,
    "/nologo",
    "/target:winexe",
    "/optimize+",
    f"/out:{standard_exe_path}",
    f"/resource:{payload_zip_path},payload.zip",
    "/r:System.dll",
    "/r:System.Windows.Forms.dll",
    "/r:System.Drawing.dll",
    "/r:System.IO.Compression.dll",
    "/r:System.IO.Compression.FileSystem.dll",
    "/r:System.Web.Extensions.dll",
    prog_cs_path
]
print(f"[*] Compiling AntigravityLocalizer.exe...")
subprocess.run(csc_cmd, check=True)
shutil.copy(standard_exe_path, standalone_exe_path)
print(f"[+] Compiled successfully! Size: {os.path.getsize(standard_exe_path):,} bytes")

# 6. Build Inno Setup Installer
iscc_paths = [
    r"C:\Users\gabov\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe"
]
iscc_exe = next((p for p in iscc_paths if os.path.exists(p)), None)

installer_exe_name = f"AntigravityLocalizer_v{new_tag}.exe"
installer_exe_path = os.path.join(repo_root, installer_exe_name)

if iscc_exe:
    print(f"[*] Compiling Inno Setup Installer {installer_exe_name}...")
    iss_path = os.path.join(repo_root, "setup.iss")
    with open(iss_path, "r", encoding="utf-8") as f:
        iss_content = f.read()
    iss_content = re.sub(r'#define MyAppVersion "[^"]+"', f'#define MyAppVersion "{new_tag}"', iss_content)
    iss_content = re.sub(r'OutputBaseFilename=AntigravityLocalizer_v[^\r\n]+', f'OutputBaseFilename=AntigravityLocalizer_v{new_tag}', iss_content)
    iss_content = re.sub(r'VersionInfoVersion=[^\r\n]+', f'VersionInfoVersion={new_tag}.0', iss_content)
    iss_content = re.sub(r'VersionInfoProductVersion=[^\r\n]+', f'VersionInfoProductVersion={new_tag}.0', iss_content)
    with open(iss_path, "w", encoding="utf-8") as f:
        f.write(iss_content)

    subprocess.run([iscc_exe, iss_path], check=True)
    print(f"[+] Inno Setup installer compiled! Size: {os.path.getsize(installer_exe_path):,} bytes")
else:
    print("[!] Warning: Inno Setup ISCC.exe not found!")

# 7. Commit and push git tag
subprocess.run([
    "git", "add",
    "Program.cs",
    "setup.iss",
    ".gitignore",
    "antigravity_localizer.py",
    "install.ps1",
    ".github/workflows/build.yml",
    "resources/app.asar",
    "ai_bridge.py",
    "resources/web_bundle_ru/i18n-ru.js",
    "resources/web_bundle_ru/main.js",
    "translations/chat_strings.json",
    "translations/dom_translator.js",
    "publish_new_release.py"
], cwd=repo_root, check=False)
subprocess.run([
    "git", "commit", "-m",
    f"fix: restore online translator with multi-tier failover & localize files changed and review diffs (v{new_tag})"
], cwd=repo_root, check=False)
subprocess.run(["git", "push", "origin", "main"], cwd=repo_root, check=False)

print(f"Creating git tag {new_tag}...")
subprocess.run(["git", "tag", "-a", new_tag, "-m", f"Release {new_tag}"], cwd=repo_root, check=False)
subprocess.run(["git", "push", "origin", new_tag], cwd=repo_root, check=False)

# 8. Create GitHub Release
release_title = f"Google Antigravity Localizer v{new_tag} - Custom AI Models & AI Bridge"
release_body = f"""# Google Antigravity Localizer v{new_tag} — Поддержка сторонних ИИ-моделей (AI Bridge)

Крупное обновление: добавлена возможность подключать **любые сторонние ИИ-модели** (Ollama, DeepSeek, OpenAI, OpenRouter и др.) через встроенный шлюз **AI Bridge** и графический интерфейс!

### 🤖 Сторонние ИИ-модели (AI Bridge + GUI):
- **Встроенный графический менеджер моделей**:
  - В главное окно русификатора добавлена кнопка **«Сторонние ИИ-модели (AI Bridge)»**.
  - Удобный диалог добавления и настройки провайдеров: **Ollama (локальный)**, **DeepSeek**, **OpenAI**, **OpenRouter**, **Custom**.
  - Быстрая проверка подключения к API моделей по кнопке «⚡ Проверить API».
- **Локальный шлюз-транслятор (AI Bridge)**:
  - Автономный высокоскоростной сервер на C# (.NET HttpListener), преобразующий запросы Gemini API (`generateContent` / `streamGenerateContent`) в формат OpenAI-совместимых эндпоинтов (`/v1/chat/completions`).
  - Полноценная поддержка стриминга (SSE) и передачи ролей/сообщений.
- **Разблокировка интерфейса кастомных моделей в Antigravity**:
  - В селекторе моделей Antigravity активирована вкладка **«Custom»** и кнопка **«+ Добавить модель»**.
  - Модели сохраняются реактивно и персистентно в `localStorage`.
  - В `languageServer.js` добавлена поддержка динамической переадресации через переменную окружения `AGY_API_SERVER_URL`.

### 🌐 Русификация и исправления:
- Обновлены и отполированы переводы интерфейса добавления моделей («Название модели», «URL модели», «Лимит токенов до сжатия» и подсказки).

---

## 💬 Сообщество и группа в Telegram
Обсуждение программ автора и сообщества:  
👉 **[Вступить в Telegram-группу](https://t.me/+8qU7020rMF84OWNi)** (Тема «Разработочная»)

---

## ⚡ Установка:
1. Скачайте **`{installer_exe_name}`** ниже.
2. Запустите установщик — он обновит русификатор и установит AI Bridge v{new_tag}.
"""

req_data = {
    "tag_name": new_tag,
    "name": release_title,
    "body": release_body,
    "draft": False,
    "prerelease": False
}

req = urllib.request.Request(
    f"{repo_api}/releases",
    data=json.dumps(req_data).encode('utf-8'),
    headers=headers,
    method='POST'
)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
release_id = res['id']
print(f"Created new GitHub Release: {res['name']} (ID: {release_id}, Tag: {res['tag_name']})")

def upload_asset(path, name):
    print(f"Uploading {name}...")
    with open(path, "rb") as f:
        data = f.read()
    upload_url = f"https://uploads.github.com/repos/j46871417-ui/Antigravity-Localizer/releases/{release_id}/assets?name={name}"
    req_upload = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            'Authorization': f'token {token}',
            'User-Agent': 'Python',
            'Content-Type': 'application/octet-stream',
            'Content-Length': str(len(data))
        },
        method='POST'
    )
    res_up = json.loads(urllib.request.urlopen(req_upload).read().decode('utf-8'))
    print(f"[+] Uploaded {name} ({res_up.get('size')} bytes)")

# Upload primary installer, standalone, and standard exe
if os.path.exists(installer_exe_path):
    upload_asset(installer_exe_path, installer_exe_name)
if os.path.exists(standalone_exe_path):
    upload_asset(standalone_exe_path, standalone_exe_name)
upload_asset(standard_exe_path, "AntigravityLocalizer.exe")
bat_path = os.path.join(repo_root, "install.bat")
if os.path.exists(bat_path):
    upload_asset(bat_path, "install.bat")

# 9. Broadcast to Telegram via tg_client.py
try:
    tg_client_path = r"C:\Users\gabov\.gemini\config\plugins\telegram-releases\scripts\tg_client.py"
    if os.path.exists(tg_client_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location("tg_client", tg_client_path)
        tg_client = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tg_client)

        print("[*] Отправка анонса и файла в Telegram через tg_client (тема «Разработочная»)...")
        tg_text = f"""🤖 <b>Вышел релиз Google Antigravity Localizer v{new_tag}!</b>

✨ <b>Что нового в v{new_tag}:</b>
• <b>Поддержка сторонних ИИ-моделей (AI Bridge)</b>: теперь можно подключать локальные и облачные модели через API (Ollama, DeepSeek, OpenAI, OpenRouter и любые совместимые)
• <b>Графический интерфейс управления моделями</b>: удобная форма добавления моделей, ввода API-ключей и проверки соединения прямо в приложении
• <b>Разблокирован встроенный UI Antigravity</b>: активна кнопка «+ Добавить модель» с персистентным сохранением
• <b>Локальный мост-транслятор</b>: прозрачная трансляция вызовов в фоновом режиме с поддержкой потокового вывода (SSE)

📦 <b>GitHub Release:</b> <a href="https://github.com/j46871417-ui/Antigravity-Localizer/releases/tag/{new_tag}">v{new_tag}</a>
💾 <b>Установщик: <code>{installer_exe_name}</code> прикреплён ниже 👇</b>"""

        tg_client.send_message(tg_text)
        if os.path.exists(installer_exe_path):
            print(f"[*] Загрузка {installer_exe_name} в Telegram...")
            tg_client.send_document(
                installer_exe_path,
                caption=f"🌐 <b>{installer_exe_name}</b>\n(Восстановление онлайн-переводчика + локализация диффов и файлов)"
            )
            print("[+] Файл и анонс успешно опубликованы в Telegram!")
    else:
        print("[!] tg_client.py не найден по пути:", tg_client_path)
except Exception as tg_err:
    print(f"[!] Ошибка отправки в Telegram: {tg_err}")

print(f"Done: Release {new_tag} published successfully!")
