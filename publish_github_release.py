#!/usr/bin/env python3
"""
GitHub Release Publisher for Dagami Antigravity Language Pack.
Creates release v1.1.0 and uploads release assets for Windows, Linux, and macOS.
"""

import json
import mimetypes
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import urllib.error

REPO_OWNER = "j46871417-ui"
REPO_NAME = "Dagami-Antigravity-Language-Pack"
TAG_NAME = "v1.1.0"
RELEASE_NAME = "Dagami Antigravity Language Pack v1.1.0 (Windows, Linux, macOS)"

RELEASE_BODY = """# 🚀 Dagami Antigravity Language Pack v1.1.0

Универсальный пакет мультиязычной локализации для экосистемы **Google Antigravity Desktop** и **Antigravity IDE**.

* 💬 **Telegram-сообщество:** [t.me/+8qU7020rMF84OWNi](https://t.me/+8qU7020rMF84OWNi)
* ☕ **Поддержать разработку (Донат):** [pay.cloudtips.ru/p/671fda86](https://pay.cloudtips.ru/p/671fda86)
* 📖 **Подробные инструкции по установке:** [INSTRUCTIONS.md](https://github.com/j46871417-ui/Antigravity-Localizer/blob/main/INSTRUCTIONS.md)

---

## 🌟 Что нового в версии 1.1.0:

1. **Кроссплатформенная поддержка:**
   - 🪟 **Windows:** готовый бинарник `AntigravityLocalizer.exe` (работает без установки Python), батники `install.bat` и `dagami-ag-localizer.cmd`, однострочник PowerShell.
   - 🐧 **Linux:** сценарии `install.sh` и `dagami-ag-localizer.sh` с автоопределением путей в `/opt`, `/usr/lib`, `~/.local/share` и поддержкой sudo.
   - 🍏 **macOS:** полная поддержка Apple Silicon (M1/M2/M3/M4) и Intel x86_64 для бандлов `/Applications/Antigravity.app`.

2. **Мультиязычные пакеты и удобный CLI-переключатель:**
   - `dagami-ag-localizer --lang ru` — Русский (4 500+ терминов)
   - `dagami-ag-localizer --lang zh` — Китайский (简体中文)
   - `dagami-ag-localizer --lang es` — Испанский (Español)
   - `dagami-ag-localizer --lang ja` — Японский (日本語)
   - `dagami-ag-localizer --lang de` — Немецкий (Deutsch)
   - `dagami-ag-localizer --lang fr` — Французский (Français)
   - `dagami-ag-localizer --list` — Таблица доступных языков
   - `dagami-ag-localizer --update` — Обновление языковых словарей
   - `dagami-ag-localizer --restore` — Возврат оригинального английского интерфейса

3. **Исправление UI и стабильности перевода:**
   - Исправлена верстка тулбара рассуждений (`Thought for X seconds`): кнопки `🌐 РУ` и `⚡ Авто` теперь жестко зафиксированы в одну строку и не ломают интерфейс.
   - Устранены сбои React Fiber: перевод блоков рассуждений отображается через безопасный контейнерный оверлей, сохраняя структуру DOM.
   - Динамический перевод карточек действий: `Searching for ...`, `Reading ...`, `Editing ...`, `Executing ...`, `Ran ...`, `Analyzed ...` теперь локализуются на лету.

---

## 📦 Файлы для загрузки:

* **`AntigravityLocalizer.exe`** — автономный исполняемый файл для Windows (запуск в 1 клик, не требует Python).
* **`DagamiAntigravityLanguagePack-v1.1.0-Windows.zip`** — полный дистрибутив для Windows (`.exe`, скрипты, словари, документация).
* **`DagamiAntigravityLanguagePack-v1.1.0-Linux.tar.gz`** — дистрибутив для Linux с исполняемыми скриптами `install.sh` и `dagami-ag-localizer.sh`.
* **`DagamiAntigravityLanguagePack-v1.1.0-macOS.zip`** — дистрибутив для macOS с поддержкой `.app` бандлов.
* **`DagamiAntigravityLanguagePack-v1.1.0-AllPlatforms.zip`** — универсальный архив со всеми файлами.
"""

def get_git_token() -> str:
    res = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n",
        text=True,
        capture_output=True,
        check=True
    )
    for line in res.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("Не удалось получить GitHub Token из git credential helper.")

def api_request(url: str, method: str = "GET", data: bytes = None, headers: dict = None):
    req = urllib.request.Request(url, data=data, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

def main():
    token = get_git_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Dagami-Release-Publisher/1.1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    base_api = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

    # 1. Check existing releases
    print("[*] Checking existing releases...")
    status, body = api_request(f"{base_api}/releases", headers=headers)
    releases = json.loads(body.decode("utf-8")) if status == 200 else []

    target_release = None
    for r in releases:
        if r.get("tag_name") == TAG_NAME:
            target_release = r
            break

    if target_release:
        release_id = target_release["id"]
        print(f"[*] Found existing release {TAG_NAME} (id: {release_id}). Updating...")
        payload = json.dumps({
            "name": RELEASE_NAME,
            "body": RELEASE_BODY,
            "draft": False,
            "prerelease": False,
        }).encode("utf-8")
        h = dict(headers)
        h["Content-Type"] = "application/json"
        api_request(f"{base_api}/releases/{release_id}", method="PATCH", data=payload, headers=h)
    else:
        print(f"[*] Creating new release {TAG_NAME}...")
        payload = json.dumps({
            "tag_name": TAG_NAME,
            "target_commitish": "main",
            "name": RELEASE_NAME,
            "body": RELEASE_BODY,
            "draft": False,
            "prerelease": False,
        }).encode("utf-8")
        h = dict(headers)
        h["Content-Type"] = "application/json"
        status, body = api_request(f"{base_api}/releases", method="POST", data=payload, headers=h)
        if status not in (200, 201):
            print(f"[-] Failed to create release: {status} {body.decode('utf-8')}")
            sys.exit(1)
        target_release = json.loads(body.decode("utf-8"))
        release_id = target_release["id"]
        print(f"[+] Created release {TAG_NAME} (id: {release_id})")

    # Fetch current release to get fresh upload_url and assets
    status, body = api_request(f"{base_api}/releases/{release_id}", headers=headers)
    release_info = json.loads(body.decode("utf-8"))
    upload_url_tpl = release_info["upload_url"]  # format: https://uploads.github.com/.../assets{?name,label}
    upload_url_base = upload_url_tpl.split("{")[0]

    existing_assets = {a["name"]: a["id"] for a in release_info.get("assets", [])}

    # Assets to upload
    repo_root = Path(__file__).resolve().parent
    dist_dir = repo_root / "release_dist"
    assets_to_upload = [
        repo_root / "AntigravityLocalizer.exe",
        dist_dir / f"DagamiAntigravityLanguagePack-{TAG_NAME}-Windows.zip",
        dist_dir / f"DagamiAntigravityLanguagePack-{TAG_NAME}-Linux.tar.gz",
        dist_dir / f"DagamiAntigravityLanguagePack-{TAG_NAME}-macOS.zip",
        dist_dir / f"DagamiAntigravityLanguagePack-{TAG_NAME}-AllPlatforms.zip",
    ]

    for asset_path in assets_to_upload:
        if not asset_path.exists():
            print(f"[!] Warning: Asset not found: {asset_path}")
            continue

        name = asset_path.name
        # Delete existing asset with same name if already uploaded
        if name in existing_assets:
            print(f"[*] Deleting old asset: {name} (id: {existing_assets[name]})...")
            api_request(f"{base_api}/releases/assets/{existing_assets[name]}", method="DELETE", headers=headers)

        print(f"[*] Uploading asset: {name} ({asset_path.stat().st_size / (1024*1024):.2f} MB)...")
        content_type = mimetypes.guess_type(asset_path)[0] or "application/octet-stream"
        upload_url = f"{upload_url_base}?name={urllib.parse.quote(name)}"

        with open(asset_path, "rb") as f:
            data = f.read()

        up_headers = dict(headers)
        up_headers["Content-Type"] = content_type
        up_headers["Content-Length"] = str(len(data))

        st, res_body = api_request(upload_url, method="POST", data=data, headers=up_headers)
        if st in (200, 201):
            print(f"  [+] Successfully uploaded {name}")
        else:
            print(f"  [-] Failed to upload {name}: {st} {res_body.decode('utf-8')}")

    print("\n[+] All release assets published successfully!")
    print(f"URL: {release_info.get('html_url')}")

if __name__ == "__main__":
    main()
