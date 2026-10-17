#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
exec /bin/sh "$SCRIPT_DIR/dagami-ag-localizer.sh" --gui "$@"
