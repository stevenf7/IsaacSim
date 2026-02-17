#!/bin/bash

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE}")" && pwd)
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

exec "$REPO_ROOT/tools/packman/python.sh" tools/validate_filenames/validate_filenames.py "$@"
