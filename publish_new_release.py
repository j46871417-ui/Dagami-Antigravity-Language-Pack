import os
import sys
import subprocess
import urllib.request
import json
import re

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
        new_tag = "0.0.5"

print(f"Target release tag: {new_tag}")

# 3. Create and push git tag
print(f"Creating git tag {new_tag}...")
subprocess.run(["git", "tag", "-a", new_tag, "-m", f"Release {new_tag}"], cwd=repo_root, check=False)
subprocess.run(["git", "push", "origin", new_tag], cwd=repo_root, check=False)

# 4. Release title and body
release_title = f"Google Antigravity Localizer v{new_tag}"
release_body = f"""# Google Antigravity Localizer v{new_tag}

Автономный русификатор для экосистемы **Google Antigravity**:
- **Antigravity 2.0 Desktop** (950+ элементов интерфейса, все 187 параметров настроек, меню окна, системный трей, экран загрузки)
- **Antigravity IDE (VS Code Edition)** (15 000+ строк интерфейса)
- **Перевод размышлений агента (Thinking Translation) на лету** с тумблером `[⚡ Авто]` и кнопками `[🌐 RU / EN]` прямо в блоке мыслей

---

## 💬 Сообщество и группа в Telegram
Обсуждение программ автора и сообщества:  
👉 **[Вступить в Telegram-группу](https://t.me/+8qU7020rMF84OWNi)**

---

## ⚡ Способы установки:

### 1. Автономный `.exe` (Рекомендуется)
Скачайте **`AntigravityLocalizer.exe`** ниже и нажмите **«Установить русификатор»**.

### 2. Через консоль PowerShell:
```powershell
irm https://raw.githubusercontent.com/j46871417-ui/Antigravity-Localizer/main/install.ps1 | iex
```

### 3. Через `install.bat`:
Скачайте `install.bat` и запустите двойным кликом.
"""

# 5. Create new GitHub Release
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

# 6. Upload AntigravityLocalizer.exe
exe_path = os.path.join(repo_root, "AntigravityLocalizer.exe")
if os.path.exists(exe_path):
    print("Uploading AntigravityLocalizer.exe...")
    with open(exe_path, "rb") as f:
        exe_bytes = f.read()
    upload_url = f"https://uploads.github.com/repos/j46871417-ui/Antigravity-Localizer/releases/{release_id}/assets?name=AntigravityLocalizer.exe"
    req_upload = urllib.request.Request(
        upload_url,
        data=exe_bytes,
        headers={
            'Authorization': f'token {token}',
            'User-Agent': 'Python',
            'Content-Type': 'application/octet-stream',
            'Content-Length': str(len(exe_bytes))
        },
        method='POST'
    )
    res_up = json.loads(urllib.request.urlopen(req_upload).read().decode('utf-8'))
    print("Uploaded AntigravityLocalizer.exe successfully! Size:", res_up.get("size"))

# 7. Upload install.bat
bat_path = os.path.join(repo_root, "install.bat")
if os.path.exists(bat_path):
    print("Uploading install.bat...")
    with open(bat_path, "rb") as f:
        bat_bytes = f.read()
    upload_url = f"https://uploads.github.com/repos/j46871417-ui/Antigravity-Localizer/releases/{release_id}/assets?name=install.bat"
    req_upload = urllib.request.Request(
        upload_url,
        data=bat_bytes,
        headers={
            'Authorization': f'token {token}',
            'User-Agent': 'Python',
            'Content-Type': 'application/x-bat',
            'Content-Length': str(len(bat_bytes))
        },
        method='POST'
    )
    res_up = json.loads(urllib.request.urlopen(req_upload).read().decode('utf-8'))
    print("Uploaded install.bat successfully! Size:", res_up.get("size"))

print(f"Done: Release {new_tag} published successfully!")
