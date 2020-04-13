#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

if [ ! -z "$TEAMCITY_VERSION" ]
then
    package="--from-package"
fi

# Startup Test
"$SCRIPT_DIR/../../../../tools/test_runner.sh" --suite startuptest --config release $package -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" $*

# Package shader cache
if [ "$package" == "--from-package" ]
then
    "$SCRIPT_DIR/../../../../tools/packman/python.sh" "$SCRIPT_DIR/../../../../tools/repoman/package_cache.py" --platform linux-x86_64 --config release
fi

