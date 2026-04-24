#!/usr/bin/env bash
set -euo pipefail

# Required env vars: B2_ACCOUNT_ID, B2_ACCOUNT_KEY, RESTIC_PASSWORD, RESTIC_REPOSITORY
# RESTIC_REPOSITORY should be: b2:bucketname:/path

export B2_ACCOUNT_ID="${B2_ACCOUNT_ID:?B2_ACCOUNT_ID not set}"
export B2_ACCOUNT_KEY="${B2_ACCOUNT_KEY:?B2_ACCOUNT_KEY not set}"
export RESTIC_PASSWORD="${RESTIC_PASSWORD:?RESTIC_PASSWORD not set}"
export RESTIC_REPOSITORY="${RESTIC_REPOSITORY:?RESTIC_REPOSITORY not set}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(dirname "$SCRIPT_DIR")/data"

echo "Starting backup of $DATA_DIR..."
restic backup "$DATA_DIR" --tag "cz-dev-rag" --verbose
restic forget --keep-daily 7 --keep-weekly 4 --prune
echo "Backup complete."
