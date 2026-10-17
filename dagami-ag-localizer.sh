#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
        exec "$candidate" "$SCRIPT_DIR/launch.py" "$@"
    fi
done
printf '%s\n' 'Нужен Python 3.10 или новее. Для GUI нужен Tk.' >&2
exit 1
