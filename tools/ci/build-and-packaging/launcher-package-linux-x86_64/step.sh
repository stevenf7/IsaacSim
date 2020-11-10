#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

# Package
"$SCRIPT_DIR/../../../package_launcher.sh"

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages/*.release.zip']"


