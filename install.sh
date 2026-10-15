#!/usr/bin/env bash
# =============================================================================
# Dagami Antigravity Language Pack — Universal Installer (Linux & macOS)
# Multi-language localization for Google Antigravity Desktop & IDE
#
# GitHub:   https://github.com/j46871417-ui/Antigravity-Localizer
# Telegram: https://t.me/+8qU7020rMF84OWNi
# Donation: https://pay.cloudtips.ru/p/671fda86
# =============================================================================

set -e

# ANSI Colors
CLR_RESET="\033[0m"
CLR_BOLD="\033[1m"
CLR_CYAN="\033[36m"
CLR_GREEN="\033[32m"
CLR_YELLOW="\033[33m"
CLR_RED="\033[31m"
CLR_WHITE="\033[97m"

print_banner() {
    echo -e "${CLR_CYAN}==========================================================${CLR_RESET}"
    echo -e "${CLR_GREEN}${CLR_BOLD}    🚀 Dagami Antigravity Language Pack (v1.1.0)${CLR_RESET}"
    echo -e "${CLR_WHITE}    Мультиязычная локализация Google Antigravity${CLR_RESET}"
    echo -e "${CLR_CYAN}    GitHub:   https://github.com/j46871417-ui/Antigravity-Localizer${CLR_RESET}"
    echo -e "${CLR_CYAN}    Telegram: https://t.me/+8qU7020rMF84OWNi${CLR_RESET}"
    echo -e "${CLR_YELLOW}    Донат:    https://pay.cloudtips.ru/p/671fda86${CLR_RESET}"
    echo -e "${CLR_CYAN}==========================================================${CLR_RESET}"
    echo ""
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

# Detect OS
OS_TYPE="$(uname -s 2>/dev/null || echo "Unknown")"

# 1. Locate Python 3
PYTHON_BIN=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        # Check that it's Python 3
        VER=$("$candidate" -c "import sys; print(sys.version_info[0])" 2>/dev/null || echo "0")
        if [ "$VER" -ge 3 ]; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    print_banner
    echo -e "${CLR_RED}❌ Ошибка: Python 3 не обнаружен в вашей системе.${CLR_RESET}"
    echo "Для работы установщика необходим Python 3.6+."
    echo ""
    echo "Команды для установки:"
    if [ "$OS_TYPE" = "Darwin" ]; then
        echo "  brew install python3"
    elif command -v apt-get >/dev/null 2>&1; then
        echo "  sudo apt update && sudo apt install -y python3"
    elif command -v dnf >/dev/null 2>&1; then
        echo "  sudo dnf install -y python3"
    elif command -v pacman >/dev/null 2>&1; then
        echo "  sudo pacman -S --noconfirm python"
    else
        echo "  Установите Python 3 через ваш системный пакетный менеджер."
    fi
    exit 1
fi

# 2. Check if running from cloned repository or standalone archive
LOCALIZER_PY=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/dagami_ag_localizer.py" ]; then
    LOCALIZER_PY="$SCRIPT_DIR/dagami_ag_localizer.py"
elif [ -f "./dagami_ag_localizer.py" ]; then
    LOCALIZER_PY="./dagami_ag_localizer.py"
else
    # Remote execution fallback: download repository archive to a temporary directory
    print_banner
    echo -e "${CLR_CYAN}📥 Загрузка последней версии Dagami Antigravity Language Pack...${CLR_RESET}"
    TMP_DIR="$(mktemp -d /tmp/dagami_ag_XXXXXX)"
    trap 'rm -rf "$TMP_DIR"' EXIT
    curl -fsSL "https://github.com/j46871417-ui/Antigravity-Localizer/archive/refs/heads/main.tar.gz" | tar -xz -C "$TMP_DIR"
    LOCALIZER_PY="$TMP_DIR/Antigravity-Localizer-main/dagami_ag_localizer.py"
fi

# 3. Interactive Menu if no arguments passed
if [ $# -eq 0 ]; then
    print_banner
    echo -e "${CLR_BOLD}Выберите действие:${CLR_RESET}"
    echo "  1) Установить русский язык (ru)"
    echo "  2) Установить китайский язык (zh)"
    echo "  3) Установить испанский язык (es)"
    echo "  4) Установить японский язык (ja)"
    echo "  5) Установить немецкий язык (de)"
    echo "  6) Установить французский язык (fr)"
    echo "  7) Показать список всех доступных языков (--list)"
    echo "  8) Обновить языковые пакеты (--update)"
    echo "  9) Восстановить оригинальный английский язык (--restore)"
    echo "  0) Выход"
    echo ""
    read -r -p "Введите номер [1-9, 0]: " CHOICE

    case "$CHOICE" in
        1) "$PYTHON_BIN" "$LOCALIZER_PY" --lang ru ;;
        2) "$PYTHON_BIN" "$LOCALIZER_PY" --lang zh ;;
        3) "$PYTHON_BIN" "$LOCALIZER_PY" --lang es ;;
        4) "$PYTHON_BIN" "$LOCALIZER_PY" --lang ja ;;
        5) "$PYTHON_BIN" "$LOCALIZER_PY" --lang de ;;
        6) "$PYTHON_BIN" "$LOCALIZER_PY" --lang fr ;;
        7) "$PYTHON_BIN" "$LOCALIZER_PY" --list ;;
        8) "$PYTHON_BIN" "$LOCALIZER_PY" --update ;;
        9) "$PYTHON_BIN" "$LOCALIZER_PY" --restore ;;
        *) echo "Отменено."; exit 0 ;;
    esac
else
    # Direct argument pass-through (e.g. ./install.sh --lang ru)
    print_banner
    exec "$PYTHON_BIN" "$LOCALIZER_PY" "$@"
fi
