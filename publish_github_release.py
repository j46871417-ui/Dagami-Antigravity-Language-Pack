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
from app_info import APP_VERSION
from app_updates import validate_exe, file_hash

REPO_OWNER = "j46871417-ui"
REPO_NAME = "Dagami-Antigravity-Language-Pack"
TAG_NAME = "v" + APP_VERSION
RELEASE_NAME = "Dagami Antigravity Language Pack " + TAG_NAME

RELEASE_BODY = (Path(__file__).resolve().parent / "CHANGES_1.2.0.md").read_text(encoding="utf-8")


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

def api_request(url: str, method: str = "GET", data: bytes = None, headers: dict = None, max_retries: int = 5):
    import time
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(url, data=data, method=method)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except Exception as e:
            if attempt < max_retries:
                print(f"  [!] Transient error on attempt {attempt}/{max_retries}: {e}. Retrying in 5s...")
                time.sleep(5)
            else:
                raise

def main():
    # Preflight precedes credentials and all API writes.
    root = Path(__file__).resolve().parent
    validate_exe(root / "AntigravityLocalizer.exe", APP_VERSION)
    sums = {}
    for line in (root / "release_dist" / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ", 1)
        path = (root if name == "AntigravityLocalizer.exe" else root / "release_dist") / name
        if file_hash(path) != digest:
            raise ValueError("Stale release asset: " + name)
        sums[name] = digest

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
    if status != 200: raise RuntimeError("Could not read releases")
    releases = json.loads(body.decode("utf-8"))

    target_release = None
    for r in releases:
        if r.get("tag_name") == TAG_NAME:
            target_release = r
            break

    if target_release:
        release_id = target_release["id"]
        if not target_release.get("draft"):
            raise ValueError("Release already published; refusing to alter it")
        payload = json.dumps({
            "name": RELEASE_NAME,
            "body": RELEASE_BODY,
            "draft": True,
            "prerelease": False,
        }).encode("utf-8")
        h = dict(headers)
        h["Content-Type"] = "application/json"
        status, _ = api_request(f"{base_api}/releases/{release_id}", method="PATCH", data=payload, headers=h)
        if status != 200: raise RuntimeError("Could not update draft")
    else:
        print(f"[*] Creating new release {TAG_NAME}...")
        payload = json.dumps({
            "tag_name": TAG_NAME,
            "target_commitish": "main",
            "name": RELEASE_NAME,
            "body": RELEASE_BODY,
            "draft": True,
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
    if status != 200: raise RuntimeError("Could not read draft")
    release_info = json.loads(body.decode("utf-8"))
    upload_url_tpl = release_info["upload_url"]  # format: https://uploads.github.com/.../assets{?name,label}
    upload_url_base = upload_url_tpl.split("{")[0]

    existing_assets = {a["name"]: a for a in release_info.get("assets", [])}

    # Assets to upload
    repo_root = Path(__file__).resolve().parent
    dist_dir = repo_root / "release_dist"
    assets_to_upload = [
        repo_root / "AntigravityLocalizer.exe",
        dist_dir / f"DagamiAntigravityLanguagePack-{TAG_NAME}-Windows.zip",
        dist_dir / f"DagamiAntigravityLanguagePack-{TAG_NAME}-Linux.tar.gz",
        dist_dir / f"DagamiAntigravityLanguagePack-{TAG_NAME}-macOS.zip",
        dist_dir / f"DagamiAntigravityLanguagePack-{TAG_NAME}-AllPlatforms.zip",
        dist_dir / "SHA256SUMS.txt",
    ]

    for asset_path in assets_to_upload:
        if not asset_path.exists():
            raise FileNotFoundError(asset_path)

        name = asset_path.name
        if name in existing_assets:
            item = existing_assets[name]
            if item.get("digest") == "sha256:" + file_hash(asset_path) and item.get("size") == asset_path.stat().st_size and item.get("state") == "uploaded":
                continue
            status, _ = api_request(f"{base_api}/releases/assets/{item['id']}", method="DELETE", headers=headers)
            if status != 204: raise RuntimeError("Could not replace stale draft asset")

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
            raise RuntimeError(f"Upload failed: {name} (HTTP {st})")

    status, body = api_request(f"{base_api}/releases/{release_id}/assets", headers=headers)
    if status != 200: raise RuntimeError("Could not read draft assets")
    uploaded = {a["name"]: a for a in json.loads(body)}
    if set(uploaded) != {p.name for p in assets_to_upload}:
        raise ValueError("Incomplete draft assets")
    for path in assets_to_upload:
        item = uploaded[path.name]
        digest = file_hash(path)
        if item.get("digest") != "sha256:" + digest or item["size"] != path.stat().st_size or item["state"] != "uploaded":
            raise ValueError("Bad uploaded digest: " + path.name)
    payload = json.dumps({"draft": False}).encode()
    publish_headers = dict(headers, **{"Content-Type": "application/json"})
    st, res = api_request(f"{base_api}/releases/{release_id}", method="PATCH", data=payload, headers=publish_headers)
    if st != 200:
        raise RuntimeError("Draft was not published")
    print("\n[+] All release assets published successfully!")
    print(f"URL: {release_info.get('html_url')}")

if __name__ == "__main__":
    main()
