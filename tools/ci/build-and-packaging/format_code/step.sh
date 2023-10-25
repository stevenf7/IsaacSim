#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

# Verify formatting
"$SCRIPT_DIR/../../../../format_code.sh" --verify



