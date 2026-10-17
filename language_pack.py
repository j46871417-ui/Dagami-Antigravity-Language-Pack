"""Frozen entry point with a private startup error report, never a silent modal."""
import os
import sys

def main():
    try:
        from dagami_ag_localizer import main as application
        # Windowed builds have no streams when no console can be attached.
        if sys.stdout is None: sys.stdout = open(os.devnull, "w", encoding="utf-8")
        if sys.stderr is None: sys.stderr = open(os.devnull, "w", encoding="utf-8")
        return application()
    except Exception:
        import traceback
        from platform_support import update_state_dir
        root = update_state_dir()
        try:
            os.makedirs(root, exist_ok=True)
            with open(os.path.join(root, "startup-error.log"), "w", encoding="utf-8") as log: traceback.print_exc(file=log)
        except OSError: pass
        if sys.stderr is not None: traceback.print_exc(file=sys.stderr)
        if sys.platform == "win32" and (len(sys.argv) == 1 or sys.argv[1:] == ["--gui"]):
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, "Не удалось запустить. См. startup-error.log в папке updates.", "Dagami Language Pack", 0x10)
        return 1

if __name__ == "__main__": sys.exit(main())
