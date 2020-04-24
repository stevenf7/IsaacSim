#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

# Startup Test
#"$SCRIPT_DIR/../../../test_runner.sh" --suite startuptest --config release -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" $*

# Package shader cache
#if [ ! -z "$TEAMCITY_VERSION" ]
#then
#    "$SCRIPT_DIR/../../../packman/python.sh" "$SCRIPT_DIR/../../../repoman/package_cache.py" --platform linux-x86_64 --config release
#fi

