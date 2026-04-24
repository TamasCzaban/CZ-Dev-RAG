#!/usr/bin/env bash
set -euo pipefail

# Required env vars: B2_ACCOUNT_ID, B2_ACCOUNT_KEY, RESTIC_PASSWORD, RESTIC_REPOSITORY
# RESTIC_REPOSITORY should be: b2:bucketname:/path

export B2_ACCOUNT_ID="${B2_ACCOUNT_ID:?B2_ACCOUNT_ID not set}"
export B2_ACCOUNT_KEY="${B2_ACCOUNT_KEY:?B2_ACCOUNT_KEY not set}"
export RESTIC_PASSWORD="${RESTIC_PASSWORD:?RESTIC_PASSWORD not set}"
export RESTIC_REPOSITORY="${RESTIC_REPOSITORY:?RESTIC_REPOSITORY not set}"

# Locate restic: prefer PATH, fall back to winget install location
if command -v restic &>/dev/null; then
    RESTIC=restic
else
    RESTIC_WINGET="/c/Users/Toma/AppData/Local/Microsoft/WinGet/Packages/restic.restic_Microsoft.Winget.Source_8wekyb3d8bbwe/restic_0.18.1_windows_amd64.exe"
    if [[ -f "$RESTIC_WINGET" ]]; then
        RESTIC="$RESTIC_WINGET"
    else
        echo "ERROR: restic not found. Add it to PATH or install via: winget install restic" >&2
        exit 1
    fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(dirname "$SCRIPT_DIR")/data"

echo "Starting backup of $DATA_DIR..."
"$RESTIC" backup "$DATA_DIR" --tag "cz-dev-rag" --verbose
"$RESTIC" forget --keep-daily 7 --keep-weekly 4 --prune
echo "Backup complete."
