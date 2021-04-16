#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

# Build release
"$SCRIPT_DIR/../../../../build.sh" --release

# Package launcher
"$SCRIPT_DIR/../../../../repo.sh" package -m isaac-sim-standalone -c release

# Packaging test_runner
"$SCRIPT_DIR/../../../../repo.sh" package -m test_runner

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"


