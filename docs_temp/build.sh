#!/bin/bash

set -e

# Navigate to the repo root (one level up from docs_temp/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Building docs from $SCRIPT_DIR using repo root at $REPO_ROOT"
"$REPO_ROOT/repo.sh" docs
