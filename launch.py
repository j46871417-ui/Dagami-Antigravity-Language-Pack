"""Source-port launcher. The native builds do not use system Python."""
import os
import sys


def main():
    if sys.version_info < (3,10):
        print('Нужен Python 3.10 или новее.',file=sys.stderr);return 1
    if '--gui' in sys.argv or len(sys.argv)==1:
        try: import tkinter
        except ImportError:
            message='Нужен Tk для Python. Linux: пакет python3-tk. macOS: Python с Tcl/Tk.'
            print(message,file=sys.stderr);return 1
        if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
            print('Для GUI нужен X11 или XWayland с DISPLAY. CLI доступен с --list или --lang.',file=sys.stderr);return 1
    if len(sys.argv)==1: sys.argv.append('--gui')
    from language_pack import main as application
    return application()

if __name__ == '__main__': sys.exit(main())
