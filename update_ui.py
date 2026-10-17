"""Small Tk update window; all Tk calls stay on the GUI thread."""
import queue
import sys
import threading
from pathlib import Path
import app_updates as updates
from app_info import APP_VERSION

class UpdatePanel:
    def __init__(self, owner, links):
        self.owner = owner; self.root = owner.root; self.events = queue.Queue()
        self.release = None; self.dialog = None; self.running = False; self.closed = False
        self.status = owner.tk.StringVar(value="Версия " + APP_VERSION)
        self.button = owner.ttk.Button(links, text="Обновления", command=self.open)
        self.button.pack(side=owner.tk.RIGHT)
        self.root.after(100, self.poll)
        self.root.after(1800, self.automatic)

    def automatic(self):
        if not self.running and updates.due(): self.check()
        self.root.after(updates.INTERVAL * 1000, self.automatic)

    def poll(self):
        if self.closed: return
        try:
            while not self.closed: self.events.get_nowait()()
        except queue.Empty: pass
        if not self.closed and self.root.winfo_exists(): self.root.after(100, self.poll)

    def submit(self, work, done, installing=False):
        if self.running: return
        self.running = True
        if installing: self.owner._update_busy = True; self.owner._set_actions(False)
        self.refresh()
        def worker():
            try:
                result = work()
                self.events.put(lambda result=result: finish(result, None))
            except Exception as error:
                # Network errors are sanitized by the update engine.
                text = str(error) if isinstance(error, (ValueError, ConnectionError, TimeoutError)) else "Сбой операции. Проверьте права записи и занятые файлы."
                self.events.put(lambda text=text: finish(None, text))
        def finish(result, error):
            self.running = False
            if installing: self.owner._update_busy = False; self.owner._set_actions(not self.owner._busy)
            if error: self.status.set(error)
            else: done(result)
            self.refresh()
        threading.Thread(target=worker, daemon=True).start()

    def check(self):
        self.status.set("Проверка GitHub…")
        def done(release):
            self.release = release
            self.status.set(("Есть версия " + release["tag"]) if updates.newer(release) else "У вас свежая версия.")
            self.button.config(text="Обновить" if updates.newer(release) else "Обновления")
        self.submit(lambda: updates.check(), done)

    def open(self):
        if self.dialog and self.dialog.winfo_exists(): self.dialog.lift(); return
        tk, ttk = self.owner.tk, self.owner.ttk
        self.dialog = tk.Toplevel(self.root); self.dialog.title("Обновления")
        self.dialog.geometry("620x440"); self.dialog.minsize(520, 360)
        self.dialog.transient(self.root)
        box = ttk.Frame(self.dialog, padding=12); box.pack(fill=tk.BOTH, expand=True)
        ttk.Label(box, text="Версия " + APP_VERSION).pack(anchor="w")
        ttk.Label(box, textvariable=self.status, wraplength=570).pack(anchor="w", pady=6)
        prefs = updates.settings()
        self.automatic_var = tk.BooleanVar(value=prefs["automatic"])
        self.pre_var = tk.BooleanVar(value=prefs["prereleases"])
        def save(): updates.save_settings(self.automatic_var.get(), self.pre_var.get())
        ttk.Checkbutton(box, text="Проверять при запуске и раз в 6 часов", variable=self.automatic_var, command=save).pack(anchor="w")
        ttk.Checkbutton(box, text="Искать тестовые версии", variable=self.pre_var, command=save).pack(anchor="w")
        self.notes = tk.Text(box, height=8, wrap=tk.WORD, font=("Segoe UI", 9))
        self.notes.pack(fill=tk.BOTH, expand=True, pady=8)
        row = ttk.Frame(box); row.pack(fill=tk.X)
        self.check_button = ttk.Button(row, text="Проверить", command=self.check); self.check_button.pack(side=tk.LEFT)
        self.install_button = ttk.Button(row, text="Скачать и установить" if updates.supports_install(self.release) else "Скачать", command=self.install)
        self.install_button.pack(side=tk.RIGHT)
        ttk.Label(box, text="Установка — лишь по кнопке. Старый EXE будет сохранён.", wraplength=570).pack(anchor="w", pady=(8, 0))
        result = updates.load_json(updates.state_root() / "last-result.json", {})
        if result.get("message") and not updates.newer(self.release): self.status.set(result["message"])
        self.refresh()

    def refresh(self):
        if self.closed: return
        if not self.dialog or not self.dialog.winfo_exists(): return
        self.check_button.config(state="disabled" if self.running else "normal")
        can_install = updates.newer(self.release) and not self.running and not self.owner._busy
        self.install_button.config(state="normal" if can_install else "disabled", text="Скачать и установить" if updates.supports_install(self.release) else "Скачать")
        text = self.release["notes"] if self.release else "Нажмите «Проверить». Скачивание и установка сами не начнутся."
        self.notes.config(state="normal"); self.notes.delete("1.0", "end"); self.notes.insert("1.0", text); self.notes.config(state="disabled")

    def install(self):
        if self.owner._busy or self.running or not updates.newer(self.release): return
        release = dict(self.release); frozen = updates.supports_install(release)
        self.status.set("Загрузка и проверка SHA-256…")
        def work():
            payload = updates.download(release)
            if frozen: return updates.start_install(release, payload)
            return payload
        def done(path):
            if frozen:
                self.owner._exit_for_update = True
                self.closed = True
                self.owner.close()
            else: self.status.set("Файл скачан и проверен: " + str(path))
        self.submit(work, done, installing=True)
