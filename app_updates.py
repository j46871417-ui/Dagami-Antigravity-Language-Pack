"""GitHub checks and opt-in Windows EXE updates. No tokens or remote scripts."""
from __future__ import annotations
import ctypes
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from app_info import APP_NAME, APP_VERSION, REPOSITORY
from platform_support import update_state_dir, native_asset_name

API = "https://api.github.com/repos/" + REPOSITORY + "/releases?per_page=50"
HOSTS = {"api.github.com", "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}
MAX_FILE = 150 * 1024 * 1024
INTERVAL = 6 * 60 * 60
SEMVER = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")
DIGEST = re.compile(r"^sha256:([a-fA-F0-9]{64})$")

def version_key(text):
    m = SEMVER.fullmatch(text)
    if not m: raise ValueError("Неверный номер версии.")
    pre = m[4]
    if pre and any(not x or (x.isdigit() and len(x) > 1 and x[0] == "0") for x in pre.split(".")):
        raise ValueError("Неверный номер версии.")
    parts = tuple((0, int(x)) if x.isdigit() else (1, x) for x in pre.split(".")) if pre else ()
    return (int(m[1]), int(m[2]), int(m[3]), not bool(pre), parts)

def state_root():
    root = update_state_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()

def atomic(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

def save_json(path, data):
    atomic(path, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

def load_json(path, default):
    try:
        p = Path(path)
        if p.stat().st_size > 4 * 1024 * 1024: return default
        value = json.loads(p.read_text(encoding="utf-8"))
        return value if isinstance(value, type(default)) else default
    except (OSError, ValueError): return default

def settings():
    value = load_json(state_root() / "settings.json", {})
    return {"automatic": value.get("automatic", True) is True, "prereleases": value.get("prereleases", False) is True}

def save_settings(automatic, prereleases):
    save_json(state_root() / "settings.json", {"automatic": bool(automatic), "prereleases": bool(prereleases)})

def due():
    cache = load_json(state_root() / "check.json", {})
    try: checked = float(cache.get("checked", 0))
    except (TypeError, ValueError): checked = 0
    if not math.isfinite(checked): checked = 0
    return settings()["automatic"] and (checked > time.time() + 60 or time.time() - checked >= INTERVAL)

def allowed(url):
    try:
        p = urllib.parse.urlsplit(url)
        return p.scheme == "https" and p.hostname in HOSTS and p.port in (None, 443) and not p.username and not p.password and not p.fragment
    except ValueError: return False

class Redirects(urllib.request.HTTPRedirectHandler):
    max_redirections = 6
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl): raise ValueError("GitHub вернул чужой адрес.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def routes():
    # No global proxy changes. TLS remains end-to-end on every route.
    yield {}
    explicit = os.environ.get("DAGAMI_UPDATE_PROXY")
    if explicit:
        p = urllib.parse.urlsplit(explicit)
        if p.scheme not in ("http", "https") or not p.hostname: raise ValueError("Неверный прокси для GitHub.")
        yield {"https": explicit}
    system = urllib.request.getproxies()
    if system.get("https"): yield {"https": system["https"]}
    # Optional existing Dagami Agent Proxy bridge; no service is started here.
    if os.environ.get("DAGAMI_UPDATE_USE_BRIDGE") == "1":
        yield {"https": "http://127.0.0.1:53200"}

def network(url, limit, destination=None):
    if not allowed(url): raise ValueError("Запрещённый адрес GitHub.")
    for proxy in routes():
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxy), Redirects())
            request = urllib.request.Request(url, headers={"User-Agent": "Dagami-Language-Pack/" + APP_VERSION, "Accept": "application/vnd.github+json"})
            with opener.open(request, timeout=15) as response:
                if not allowed(response.url): raise ValueError("GitHub вернул чужой адрес.")
                size = response.headers.get("Content-Length")
                if size is not None and (int(size) < 0 or int(size) > limit): raise ValueError("Файл слишком велик.")
                result = bytearray(); total = 0; started = time.monotonic()
                stream = open(destination, "wb") if destination else None
                try:
                    while True:
                        chunk = response.read(65536)
                        if not chunk: break
                        total += len(chunk)
                        if total > limit or time.monotonic() - started > 180: raise ValueError("Лимит загрузки GitHub.")
                        if stream: stream.write(chunk)
                        else: result.extend(chunk)
                    if stream: stream.flush(); os.fsync(stream.fileno())
                finally:
                    if stream: stream.close()
                return bytes(result)
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            raise ValueError(f"GitHub HTTP {status}.") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            continue
    # Do not expose proxy URLs, credentials or signed asset URLs in logs.
    raise ConnectionError("Нет связи с GitHub. Проверьте сеть и прокси.")

def asset_name(tag, platform=None):
    return native_asset_name(tag, platform)


def asset_names(tag, platform=None):
    platform = platform or sys.platform
    primary = asset_name(tag, platform)
    if platform == 'win32': return [primary]
    suffix = '-macOS.zip' if platform == 'darwin' else '-Linux.tar.gz'
    return [primary, 'DagamiAntigravityLanguagePack-' + tag + suffix]


def validate_release(value):
    tag = value["tag"]; version_key(tag)
    if value["page"] != "https://github.com/" + REPOSITORY + "/releases/tag/" + urllib.parse.quote(tag, safe=""):
        raise ValueError("Чужой релиз.")
    name = value["name"]
    if name not in {n for p in ("win32", "linux", "darwin") for n in asset_names(tag, p)}:
        raise ValueError("Нет пакета для этой ОС.")
    expected = "https://github.com/" + REPOSITORY + "/releases/download/" + urllib.parse.quote(tag, safe="") + "/" + urllib.parse.quote(name, safe="")
    if value["url"] != expected or not allowed(expected): raise ValueError("Чужой файл релиза.")
    if not isinstance(value["size"], int) or not 512 <= value["size"] <= MAX_FILE: raise ValueError("Неверный размер файла.")
    if not re.fullmatch(r"[a-f0-9]{64}", value["sha256"]): raise ValueError("Нет SHA-256 файла.")

def select_release(data, prereleases=False, platform=None):
    if not isinstance(data, list): raise ValueError("GitHub вернул неверный список.")
    best = None
    for item in data:
        if not isinstance(item, dict) or item.get("draft") or (item.get("prerelease") and not prereleases): continue
        try:
            tag = item["tag_name"]; key = version_key(tag)
            asset = next(a for name in asset_names(tag, platform) for a in item["assets"] if a["name"] == name)
            match = DIGEST.fullmatch(asset.get("digest") or "")
            if not match: continue
            candidate = {"tag": tag, "page": item["html_url"], "name": asset["name"], "url": asset["browser_download_url"],
                         "size": asset["size"], "sha256": match[1].lower(), "notes": str(item.get("body") or "")[:12000]}
            validate_release(candidate)
            if best is None or key > version_key(best["tag"]): best = candidate
        except (ValueError, KeyError, StopIteration, TypeError): continue
    return best

def check(prereleases=None):
    cleanup_history()
    if prereleases is None: prereleases = settings()["prereleases"]
    release = select_release(json.loads(network(API, 4 * 1024 * 1024)), prereleases)
    save_json(state_root() / "check.json", {"checked": time.time(), "release": release})
    return release

def newer(release):
    return bool(release and version_key(release["tag"]) > version_key(APP_VERSION))

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()

def verify_download(release, path):
    validate_release(release)
    if Path(path).stat().st_size != release["size"] or file_hash(path) != release["sha256"]:
        raise ValueError("SHA-256 файла не совпал.")

def cleanup_history(max_age=7 * 86400):
    root = state_root()
    last = load_json(root / "last-result.json", {})
    keep = Path(last["backup"]).parent.resolve() if last.get("backup") else None
    for category in ("staged", "attempts"):
        base = root / category
        if base.is_symlink() or not base.is_dir(): continue
        for folder in base.iterdir():
            if folder.is_symlink() or not folder.is_dir() or not re.fullmatch(r"[a-f0-9]{32}", folder.name): continue
            if folder.resolve() == keep or time.time() - folder.stat().st_mtime < max_age: continue
            # A helper plan can remain live for at most ten minutes. The age
            # margin above is seven days; never remove a newly touched plan.
            plan = folder / "plan.dat"
            if plan.exists() and time.time() - plan.stat().st_mtime < max_age: continue
            try: shutil.rmtree(folder)
            except OSError: pass  # A running helper stays for the next pass.


def download(release):
    cleanup_history()
    validate_release(release)
    folder = state_root() / "staged" / uuid.uuid4().hex
    folder.mkdir(parents=True)
    target = folder / release["name"]
    try:
        network(release["url"], release["size"], target)
        verify_download(release, target)
        if release["name"].endswith(".exe"): validate_exe(target, release["tag"])
        return target
    except Exception:
        if target.exists(): target.unlink()
        folder.rmdir()
        raise

def exe_identity(path):
    if sys.platform != "win32": raise OSError("Установка EXE доступна в Windows.")
    from ctypes import wintypes
    path = str(Path(path).resolve()); version = ctypes.WinDLL("version", use_last_error=True)
    version.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
    version.GetFileVersionInfoSizeW.restype = wintypes.DWORD
    version.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID]
    version.VerQueryValueW.argtypes = [wintypes.LPCVOID, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT)]
    size = version.GetFileVersionInfoSizeW(path, None)
    if not size or size > 1024 * 1024: raise ValueError("В EXE нет версии.")
    data = ctypes.create_string_buffer(size)
    if not version.GetFileVersionInfoW(path, 0, size, data): raise OSError("Не прочитан EXE.")
    pointer = ctypes.c_void_p(); length = wintypes.UINT()
    def query(name):
        if not version.VerQueryValueW(data, name, ctypes.byref(pointer), ctypes.byref(length)): return None
        return pointer.value, length.value
    translations = query(r"\VarFileInfo\Translation")
    if not translations or translations[1] < 4: raise ValueError("В EXE нет свойств.")
    lang, page = struct.unpack("<HH", ctypes.string_at(translations[0], 4))
    values = []
    for key in ("ProductName", "ProductVersion"):
        found = query("\\StringFileInfo\\%04x%04x\\" % (lang, page) + key)
        if not found: raise ValueError("В EXE нет свойств.")
        values.append(ctypes.wstring_at(found[0], found[1]).rstrip("\0"))
    return tuple(values)

def validate_exe(path, tag):
    with open(path, "rb") as f:
        if f.read(2) != b"MZ": raise ValueError("Файл не является EXE.")
        f.seek(0x3c); offset = struct.unpack("<I", f.read(4))[0]
        if offset > 1024 * 1024: raise ValueError("Неверный EXE.")
        f.seek(offset)
        if f.read(4) != b"PE\0\0": raise ValueError("Неверный EXE.")
        machine = struct.unpack("<H", f.read(2))[0]
    current = os.environ.get("PROCESSOR_ARCHITEW6432", os.environ.get("PROCESSOR_ARCHITECTURE", "")).upper()
    supported = (0xaa64, 0x8664, 0x14c) if current == "ARM64" else ((0x14c,) if current == "X86" else (0x8664, 0x14c))
    if machine not in supported:
        raise ValueError("EXE для другой ОС.")
    name, version = exe_identity(path)
    if name != APP_NAME or version_key(version) != version_key(tag): raise ValueError("Версия EXE не совпала с релизом.")

def protect(data, decrypt=False):
    if sys.platform != "win32": raise OSError("Установка доступна в Windows EXE.")
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]
    raw = ctypes.create_string_buffer(data); blob = Blob(len(data), ctypes.cast(raw, ctypes.POINTER(ctypes.c_ubyte))); out = Blob()
    entropy_raw = ctypes.create_string_buffer(b"Dagami-Language-Pack-Update-v1")
    entropy = Blob(len(entropy_raw.raw), ctypes.cast(entropy_raw, ctypes.POINTER(ctypes.c_ubyte)))
    dll = ctypes.WinDLL("crypt32", use_last_error=True)
    function = dll.CryptUnprotectData if decrypt else dll.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    if not function(ctypes.byref(blob), None, ctypes.byref(entropy), None, None, 1, ctypes.byref(out)): raise OSError(ctypes.get_last_error(), "Не прочитан план установки.")
    kernel = ctypes.WinDLL("kernel32"); kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    try: return ctypes.string_at(out.data, out.size)
    finally: kernel.LocalFree(out.data)

def process_identity(pid):
    if sys.platform != "win32": return None
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]; kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    handle = kernel.OpenProcess(0x101000, False, pid)
    if not handle:
        if ctypes.get_last_error() in (87,): return None
        raise OSError("Не удалось проверить процесс.")
    try:
        # A terminated process can still have a PID while its parent's handle
        # remains open. QueryFullProcessImageName then fails; it is already gone.
        state = kernel.WaitForSingleObject(handle, 0)
        if state == 0: return None
        if state != 258: raise OSError("Не удалось проверить выход процесса.")
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(x) for x in times)): raise OSError("Нет времени старта процесса.")
        buf = ctypes.create_unicode_buffer(32768); count = wintypes.DWORD(len(buf))
        if not kernel.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(count)): raise OSError("Не прочитан путь процесса.")
        return {"path": str(Path(buf.value).resolve()), "start": times[0].dwLowDateTime | times[0].dwHighDateTime << 32}
    finally: kernel.CloseHandle(handle)

def supports_install():
    if not getattr(sys, "frozen", False) or sys.platform != "win32": return False
    bundle = getattr(sys, "_MEIPASS", None)
    return not bundle or not Path(bundle).resolve().is_relative_to(Path(sys.executable).resolve().parent)


def create_plan(release, payload, target=None, parent_pid=None, helper=None):
    validate_release(release)
    if not newer(release): raise ValueError("Уже стоит эта версия или новее.")
    if sys.platform != "win32": raise OSError("Установка доступна в Windows EXE.")
    if not supports_install(): raise OSError("Для сборки из папки нужен полный пакет.")
    payload = Path(payload).resolve(); verify_download(release, payload); validate_exe(payload, release["tag"])
    target = Path(target or sys.executable).resolve()
    parent_pid = parent_pid or os.getpid()
    identity = process_identity(parent_pid)
    if not identity or Path(identity["path"]) != target: raise ValueError("Путь процесса не совпал.")
    folder = state_root() / "attempts" / uuid.uuid4().hex; folder.mkdir(parents=True)
    # Probe access without truncating or renaming an installed file.
    fd, probe = tempfile.mkstemp(prefix=".update-access-", dir=target.parent); os.close(fd); os.unlink(probe)
    helper_path = folder / "helper.exe"; shutil.copy2(helper or sys.executable, helper_path)
    plan = {"release": release, "payload": str(payload), "target": str(target),
            "old_sha256": file_hash(target), "helper_sha256": file_hash(helper_path),
            "parent_pid": parent_pid, "parent": identity, "created": time.time()}
    plan_path = folder / "plan.dat"; atomic(plan_path, protect(json.dumps(plan).encode("utf-8")))
    return plan_path, helper_path

def start_install(release, payload):
    if not supports_install(): raise OSError("Эта сборка может лишь скачать EXE. Полный пакет меняется вручную.")
    plan, helper = create_plan(release, payload)
    env = dict(os.environ); env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    process = subprocess.Popen([str(helper), "--apply-update", str(plan)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000, env=env)
    start = time.monotonic()
    while time.monotonic() - start < 40:
        if (plan.parent / "ready").exists(): return plan
        if process.poll() is not None: raise OSError("Помощник закрылся до старта установки.")
        if (plan.parent / "error.json").exists(): raise OSError("Не удалось начать установку. См. итог в окне обновлений.")
        time.sleep(.1)
    atomic(plan.parent / "cancel", b"cancel")
    raise TimeoutError("Не дождались старта установки.")

def replace_file(source, target):
    end = time.monotonic() + 8
    while True:
        try: os.replace(source, target); return
        except PermissionError:
            if time.monotonic() >= end: raise
            time.sleep(.2)

def install_files(plan, folder, replace=replace_file):
    release = plan["release"]; target = Path(plan["target"]); payload = Path(plan["payload"])
    verify_download(release, payload); validate_exe(payload, release["tag"])
    if file_hash(target) != plan["old_sha256"]: raise ValueError("Исходный EXE уже изменён.")
    backup = folder / "previous.exe"; shutil.copy2(target, backup)
    if file_hash(backup) != plan["old_sha256"]: raise ValueError("Не совпал хеш копии.")
    pending = target.parent / (".dagami-update-" + uuid.uuid4().hex + ".exe")
    changed = False
    try:
        shutil.copy2(payload, pending)
        verify_download(release, pending)
        if file_hash(target) != plan["old_sha256"]: raise ValueError("Исходный EXE уже изменён.")
        replace(pending, target); changed = True
        verify_download(release, target); validate_exe(target, release["tag"])
        return backup
    except Exception:
        if changed and target.exists() and file_hash(target) == release["sha256"]:
            shutil.copy2(backup, pending); replace(pending, target)
            if file_hash(target) != plan["old_sha256"]: raise OSError("Не удался откат. Старая копия: " + str(backup))
        raise
    finally:
        if pending.exists(): pending.unlink()

def run_helper(path):
    folder = Path(path).resolve().parent
    result = {"ok": False, "message": "Сбой установки. Старый EXE сохранён.", "at": time.time(), "backup": str(folder / "previous.exe")}
    valid_plan = False; approved_folder = False; phase = "validate-plan"
    try:
        base = state_root() / "attempts"
        if folder.parent != base or not re.fullmatch("[a-f0-9]{32}", folder.name) or Path(path).name != "plan.dat":
            raise ValueError("Чужой путь плана.")
        approved_folder = True
        data = Path(path).read_bytes()
        if len(data) > 128 * 1024: raise ValueError("План слишком велик.")
        plan = json.loads(protect(data, True)); release = plan["release"]; validate_release(release)
        if time.time() - plan["created"] > 600 or plan["created"] > time.time() + 30: raise ValueError("План устарел.")
        if not newer(release) or file_hash(sys.executable) != plan["helper_sha256"]: raise ValueError("Чужой помощник.")
        payload = Path(plan["payload"]).resolve()
        if payload.parent.parent != state_root() / "staged" or payload.name != release["name"]: raise ValueError("Чужой файл.")
        target = Path(plan["target"]).resolve()
        if not target.is_file() or target == Path(sys.executable).resolve() or file_hash(target) != plan["old_sha256"]: raise ValueError("Чужой EXE.")
        if Path(plan["parent"]["path"]) != target or process_identity(plan["parent_pid"]) != plan["parent"]: raise ValueError("Чужой процесс.")
        verify_download(release, payload); validate_exe(payload, release["tag"]); valid_plan = True
        atomic(folder / "ready", b"ready")
        phase = "wait-parent"
        deadline = time.monotonic() + 90
        while True:
            if (folder / "cancel").exists(): raise ValueError("Установка отменена.")
            current = process_identity(plan["parent_pid"])
            if current != plan["parent"]: break
            if time.monotonic() > deadline: raise TimeoutError("Программа ещё открыта.")
            time.sleep(.15)
        # Refuse competing helpers. File stays open exclusively until the swap ends.
        phase = "swap"
        lock_path = state_root() / "install.lock"
        with open(lock_path, "a+b") as lock:
            import msvcrt
            lock.seek(0)
            if not lock.read(1): lock.write(b"0"); lock.flush()
            lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                backup = install_files(plan, folder)
                result = {"ok": True, "message": "Новая версия установлена.", "at": time.time(), "tag": release["tag"], "backup": str(backup)}
            finally: lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        env = dict(os.environ); env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        try:
            subprocess.Popen([str(target), "--gui"], cwd=target.parent, close_fds=True, env=env)
            result["restart_ok"] = True
        except OSError:
            result["restart_ok"] = False
            result["message"] = "Новая версия установлена. Запустите EXE вручную."
        save_json(state_root() / "last-result.json", result)
        return 0
    except Exception as error:
        result.update(phase=phase, error_type=type(error).__name__, error_code=getattr(error, "winerror", None))
        # Fixed text avoids accidental disclosure of signed URLs or proxy data.
        if isinstance(error, PermissionError): result["message"] = "Нет прав записи или EXE занят. Старая копия сохранена."
        if approved_folder: save_json(folder / "error.json", result)
        if valid_plan: save_json(state_root() / "last-result.json", result)
        return 1
