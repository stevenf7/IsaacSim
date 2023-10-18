#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

# Publish docs
"$SCRIPT_DIR/../../../../repo.sh" docs --config release --stage publish --edition production


