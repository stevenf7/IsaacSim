#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

# Build release
"$SCRIPT_DIR/../../../../build.sh" --release

# Package
"$SCRIPT_DIR/../../../package_launcher.sh"

# Packaging test_runner
"$SCRIPT_DIR/../../../package.sh" --mode test_runner

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"


