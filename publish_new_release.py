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
    new_tag = "0.0.9"

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
subprocess.run(["git", "add", "Program.cs", "setup.iss", "resources/web_bundle_ru/main.js", "resources/web_bundle_ru/i18n-ru.js", "publish_new_release.py"], cwd=repo_root, check=False)
subprocess.run(["git", "commit", "-m", f"chore: release v{new_tag} (full UI audit, login screens & model tiers)"], cwd=repo_root, check=False)
subprocess.run(["git", "push", "origin", "main"], cwd=repo_root, check=False)

print(f"Creating git tag {new_tag}...")
subprocess.run(["git", "tag", "-a", new_tag, "-m", f"Release {new_tag}"], cwd=repo_root, check=False)
subprocess.run(["git", "push", "origin", new_tag], cwd=repo_root, check=False)

# 8. Create GitHub Release
release_title = f"Google Antigravity Localizer v{new_tag}"
release_body = f"""# Google Antigravity Localizer v{new_tag}

Комплексный автономный русификатор для экосистемы **Google Antigravity**:
- **Экраны входа и авторизации переведены на 100%**:
  - «Добро пожаловать в Antigravity», «С возвращением!»
  - «Продолжить с Google», «Продолжить с Google Cloud», «Продолжить через расширенный SSO»
  - «Вход с рабочим аккаунтом», «Использовать рабочий аккаунт»
  - «Ожидание авторизации...», «Успешно, продолжаем...», «Вход в систему...»
  - «ID проекта Google Cloud», «Выберите регион», «Выберите вашу лицензию», «Скопировать ссылку для входа»
- **Полная локализация уровней моделей и селектора**:
  - Все уровни: **«Экономный»**, **«Средний»**, **«Высокая точность»** (больше никакого `Medium`)
  - Селектор: «Лучшая из N моделей», «Модель не выбрана», «Загрузка моделей...», «Информация о квотах недоступна»
- **Глубокий аудит всех разделов**:
  - Словарь расширен до **2080+ записей** (в 2 раза больше покрытия)
  - Настройки: Общие, Внешний вид, Модели, Навыки, Правила, Агенты, Горячие клавиши, Сеть, Терминал, Обратная связь, Лаборатория
  - Панель задач, фоновые задачи, статусы работы («Работает...», «Сжатие»)
- **Автоматический запуск**: сразу после распаковки установщик автоматически открывает окно русификатора
- **Чистые PE-заголовки**: отсутствие предупреждений о недопустимой цифровой подписи
- **Потоковый перевод размышлений**: защита от блокировок Google API и автоперевод на лету `[⚡ Авто]`

---

## 💬 Сообщество и группа в Telegram
Обсуждение программ автора и сообщества:  
👉 **[Вступить в Telegram-группу](https://t.me/+8qU7020rMF84OWNi)**

---

## ⚡ Установка:
1. Скачайте **`{installer_exe_name}`** ниже.
2. Запустите — установщик распакует файлы и **автоматически откроет окно русификатора**.
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

        print("[*] Отправка анонса и файла в Telegram через tg_client...")
        tg_text = f"""🚀 <b>Вышел новый релиз Google Antigravity Localizer v{new_tag}!</b>

✨ <b>Что нового в v{new_tag}:</b>
• <b>Экраны входа и авторизации</b>: 100% перевод всех элементов («Добро пожаловать в Antigravity», «Продолжить с Google», «Вход с рабочим аккаунтом», «Ожидание авторизации...», «ID проекта Google Cloud», «Выберите регион»)
• <b>Настройки моделей</b>: уровни «Экономный», «Средний», «Высокая точность» (устранён `Medium`), селектор и квоты
• <b>Комплексный аудит всех разделов</b>: словарь расширен до <b>2080+ записей</b> (Общие, Внешний вид, Модели, Навыки, Правила, Агенты, Горячие клавиши, Сеть, Терминал, Обратная связь)
• <b>Автоматический запуск</b>: сразу после распаковки установщик автоматически открывает окно русификатора
• <b>Чистая цифровая подпись</b>: убрана ошибка Windows «отсутствует допустимая цифровая подпись»

📦 <b>GitHub Release:</b> <a href="https://github.com/j46871417-ui/Antigravity-Localizer/releases/tag/{new_tag}">v{new_tag}</a>
💾 <b>Установщик: <code>{installer_exe_name}</code> прикреплён ниже 👇</b>"""

        tg_client.send_message(tg_text)
        if os.path.exists(installer_exe_path):
            print(f"[*] Загрузка {installer_exe_name} в Telegram...")
            tg_client.send_document(
                installer_exe_path,
                caption=f"🚀 <b>{installer_exe_name}</b>\n(Полный аудит всех разделов, экраны входа и уровни моделей)"
            )
            print("[+] Файл и анонс успешно опубликованы в Telegram!")
    else:
        print("[!] tg_client.py не найден по пути:", tg_client_path)
except Exception as tg_err:
    print(f"[!] Ошибка отправки в Telegram: {tg_err}")

print(f"Done: Release {new_tag} published successfully!")
