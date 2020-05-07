#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

if [ ! -z "$TEAMCITY_VERSION" ]
then
    package="--from-package"
fi

# Startup Test
"$SCRIPT_DIR/../../../test_runner.sh" --suite startuptest --config release $package -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" $*

# Package shader cache
if [ "$package" == "--from-package" ]
then
    "$SCRIPT_DIR/../../../packman/python.sh" "$SCRIPT_DIR/../../../repoman/package_cache.py" --platform linux-x86_64 --config release
fi

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_builtpackages/*']"



if [ ! -z "$TEAMCITY_VERSION" ]
then
    package="--from-package"
    ARCHIVE_PATTERN="_builtpackages/omniverse-kit-robotics*.7z"

    # Startup Test
    "$SCRIPT_DIR/../../../test_runner.sh" --suite startuptest --config release $package -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" $*

    # Package shader cache
    if [ "$package" == "--from-package" ]
    then
        "$SCRIPT_DIR/../../../packman/python.sh" "$SCRIPT_DIR/../../../repoman/package_cache.py" --platform linux-x86_64 --config release
    fi

    # publish artifacts to teamcity
    echo "##teamcity[publishArtifacts '_builtpackages/*']"
fi
