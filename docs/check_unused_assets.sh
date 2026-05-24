#!/bin/bash

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE}")" && pwd)
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

exec "$REPO_ROOT/tools/packman/python.sh" docs/tools/check_unused_assets/check_unused_assets.py "$@"
