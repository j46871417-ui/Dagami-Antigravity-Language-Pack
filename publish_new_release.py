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

# 2. Determine next tag version
if len(sys.argv) > 1:
    new_tag = sys.argv[1].strip()
else:
    req = urllib.request.Request(f"{repo_api}/releases", headers=headers)
    releases = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    tags = [r['tag_name'] for r in releases if re.match(r'^\d+\.\d+\.\d+$', r['tag_name'])]
    if tags:
        parts = [int(x) for x in tags[0].split('.')]
        parts[-1] += 1
        new_tag = '.'.join(str(x) for x in parts)
    else:
        new_tag = "0.0.6"

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

# 5. Helper function for Authenticode code signing
def sign_file(file_path):
    print(f"[*] Signing {os.path.basename(file_path)} with Authenticode...")
    ps_cmd = f"""
    $cert = Get-ChildItem Cert:\\CurrentUser\\My -CodeSigningCert | Where-Object {{ $_.Subject -like "*Antigravity*" }} | Select-Object -First 1
    if (-not $cert) {{
        $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Antigravity Open Source Community, O=Antigravity Localizer, C=RU" -CertStoreLocation "Cert:\\CurrentUser\\My" -NotAfter (Get-Date).AddYears(5)
    }}
    Set-AuthenticodeSignature -FilePath "{file_path}" -Certificate $cert | Out-Null
    $sig = Get-AuthenticodeSignature -FilePath "{file_path}"
    Write-Host "Signed: $($sig.SignerCertificate.Subject)"
    """
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], check=True)
    print(f"[+] Authenticode signature applied to {os.path.basename(file_path)}")

# 6. Build Inno Setup Installer (Primary: low antivirus detections, trusted PE stub)
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
    sign_file(installer_exe_path)
    print(f"[+] Inno Setup installer compiled & signed! Size: {os.path.getsize(installer_exe_path):,} bytes")
else:
    print("[!] Warning: Inno Setup ISCC.exe not found!")

# 7. Compile Standalone C# Executable (Portable single-file)
standalone_exe_name = f"AntigravityLocalizer_Standalone_v{new_tag}.exe"
standalone_exe_path = os.path.join(repo_root, standalone_exe_name)
standard_exe_path = os.path.join(repo_root, "AntigravityLocalizer.exe")

csc_path = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
csc_cmd = [
    csc_path,
    "/nologo",
    "/target:winexe",
    "/optimize+",
    f"/out:{standalone_exe_path}",
    f"/resource:{payload_zip_path},payload.zip",
    "/r:System.dll",
    "/r:System.Windows.Forms.dll",
    "/r:System.Drawing.dll",
    "/r:System.IO.Compression.dll",
    "/r:System.IO.Compression.FileSystem.dll",
    prog_cs_path
]
print(f"[*] Compiling standalone {standalone_exe_name}...")
subprocess.run(csc_cmd, check=True)
sign_file(standalone_exe_path)
shutil.copy(standalone_exe_path, standard_exe_path)
sign_file(standard_exe_path)
print(f"[+] Standalone compiled & signed! Size: {os.path.getsize(standalone_exe_path):,} bytes")

# 8. Commit and push git tag
subprocess.run(["git", "add", "Program.cs", "setup.iss", "resources/web_bundle_ru/main.js", "resources/web_bundle_ru/i18n-ru.js", "publish_new_release.py"], cwd=repo_root, check=False)
subprocess.run(["git", "commit", "-m", f"chore: release v{new_tag} (full translation + signed installer)"], cwd=repo_root, check=False)
subprocess.run(["git", "push", "origin", "main"], cwd=repo_root, check=False)

print(f"Creating git tag {new_tag}...")
subprocess.run(["git", "tag", "-a", new_tag, "-m", f"Release {new_tag}"], cwd=repo_root, check=False)
subprocess.run(["git", "push", "origin", new_tag], cwd=repo_root, check=False)

# 9. Create GitHub Release
release_title = f"Google Antigravity Localizer v{new_tag}"
release_body = f"""# Google Antigravity Localizer v{new_tag}

Автономный русификатор для экосистемы **Google Antigravity**:
- **Минимум ложных срабатываний антивирусов**: инсталлятор собран на доверенном движке Inno Setup и подписан цифровой подписью Authenticode
- **100% русификация интерфейса**:
  - Настройки (Внешний вид, Команды терминала, Сетевые разрешения, Окно)
  - Окно «Горячие клавиши» (навигация, диалоги, подсказки, удерживание/отпускание клавиш)
  - Окно «Оставить отзыв» (все категории, формы, подсказки и отправка)
  - Статус-бар и агенты («Основной агент», переключение агентов, подагенты)
  - Раздел «Навыки» (Skills) и кастомизации
  - Перевод размышлений («Размышлял 15 с», «Работал 2 мин», счетчики действий)
- **Потоковый перевод размышлений агента на лету** с тумблером `[⚡ Авто]` и переключателем `[🌐 RU / EN]`
- **Antigravity IDE (VS Code Edition)** (15 000+ строк интерфейса)

---

## 💬 Сообщество и группа в Telegram
Обсуждение программ автора и сообщества:  
👉 **[Вступить в Telegram-группу](https://t.me/+8qU7020rMF84OWNi)**

---

## ⚡ Установка:
1. Скачайте **`{installer_exe_name}`** ниже.
2. Запустите инсталлятор и следуйте простым подсказкам мастера.
*(Для любителей portable доступен `{standalone_exe_name}`)*
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

# 10. Notify Telegram Group / Topic
try:
    import tg_notifier
    conf, _ = tg_notifier.get_env()
    tg_token = conf.get('TG_BOT_TOKEN')
    tg_chat_id = conf.get('TG_CHAT_ID')
    tg_thread_id = conf.get('TG_THREAD_ID')
    
    if tg_token and tg_chat_id:
        print("[*] Отправка анонса и файла в Telegram...")
        tg_text = f"""🚀 <b>Вышел новый релиз Google Antigravity Localizer v{new_tag}!</b>

✨ <b>Что нового в v{new_tag}:</b>
• <b>Антивирусная оптимизация</b>: инсталлятор переведён на доверенный движок Inno Setup + цифровая подпись Authenticode
• <b>Полная русификация всех уголков интерфейса</b>:
  — Настройки: Внешний вид, Команды терминала, Сетевые разрешения, Окно
  — «Горячие клавиши» (Shortcuts): все категории, действия и подсказки
  — «Оставить отзыв» (Feedback): перевод всех категорий, форм и кнопок
  — Статус-бар: «Основной агент», выбор агентов, навыки (Skills)
  — Размышления: «Размышлял 15 с», «Работал 2 мин», счетчики действий
• <b>Потоковый перевод размышлений на лету</b> с тумблером [⚡ Авто] и [🌐 RU / EN]

📦 <b>GitHub Release:</b> <a href="https://github.com/j46871417-ui/Antigravity-Localizer/releases/tag/{new_tag}">v{new_tag}</a>
💾 <b>Подписанный установщик: <code>{installer_exe_name}</code> прикреплён ниже 👇</b>"""

        tg_notifier.send_message(tg_token, tg_chat_id, tg_text, tg_thread_id)
        file_to_send = installer_exe_path if os.path.exists(installer_exe_path) else standalone_exe_path
        if os.path.exists(file_to_send):
            print(f"[*] Загрузка {os.path.basename(file_to_send)} в Telegram...")
            tg_notifier.send_document(
                tg_token,
                tg_chat_id,
                file_to_send,
                caption=f"🚀 <b>{os.path.basename(file_to_send)}</b>\n(Подписанный установщик без ложных срабатываний AV)",
                thread_id=tg_thread_id
            )
            print("[+] Файл и анонс успешно опубликованы в Telegram!")
    else:
        print("[*] Telegram Chat ID пока не настроен.")
except Exception as tg_err:
    print(f"[!] Ошибка отправки в Telegram: {tg_err}")

print(f"Done: Release {new_tag} published successfully!")
