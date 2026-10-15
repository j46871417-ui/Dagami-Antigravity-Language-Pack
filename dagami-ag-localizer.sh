#!/usr/bin/env bash
# =============================================================================
# Dagami Antigravity Language Pack — CLI Launcher (Linux & macOS)
# https://github.com/j46871417-ui/Antigravity-Localizer
# Telegram: https://t.me/+8qU7020rMF84OWNi
# Donation: https://pay.cloudtips.ru/p/671fda86
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect Python interpreter
PYTHON_BIN=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Ошибка: Python 3 не найден в системе."
    echo "Пожалуйста, установите Python 3:"
    echo "  - Ubuntu / Debian: sudo apt install python3"
    echo "  - Fedora: sudo dnf install python3"
    echo "  - Arch: sudo pacman -S python"
    echo "  - macOS: brew install python3"
    exit 1
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/dagami_ag_localizer.py" "$@"
