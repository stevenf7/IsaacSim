#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

# Verify formatting
"$SCRIPT_DIR/../../../../format_code.sh" --verify

# Full rebuild
"$SCRIPT_DIR/../../../../build.sh" -x -d
"$SCRIPT_DIR/../../../../build.sh" -x -r

# Package
"$SCRIPT_DIR/../../../../repo.sh" package -c release

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"


