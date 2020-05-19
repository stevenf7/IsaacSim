#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

if [ ! -z "$TEAMCITY_VERSION" ]
then
    package="--from-package --clean"
fi

# Startup Test
echo "##teamcity[testSuiteStarted name='isaac-sim']"
"$SCRIPT_DIR/../../../test_runner.sh" --suite startuptest --config release $package -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" $*

# Package shader cache
if [ ! -z "$TEAMCITY_VERSION" ]
then
    "$SCRIPT_DIR/../../../packman/python.sh" "$SCRIPT_DIR/../../../repoman/package_cache.py" --platform linux-x86_64 --config release
fi

echo "##teamcity[testSuiteFinished name='isaac-sim']"

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_builtpackages/isaac-sim*.7z']"



if [ ! -z "$TEAMCITY_VERSION" ]
then
    export ARCHIVE_PATTERN="_builtpackages/omniverse-kit-robotics*.7z"

    # Startup Test
    echo "##teamcity[testSuiteStarted name='omniverse-kit-robotics']"
    "$SCRIPT_DIR/../../../test_runner.sh" --suite startuptest --config release $package -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" $*

    # Package shader cache
    "$SCRIPT_DIR/../../../packman/python.sh" "$SCRIPT_DIR/../../../repoman/package_cache.py" --platform linux-x86_64 --config release

    echo "##teamcity[testSuiteFinished name='omniverse-kit-robotics']"
    
    # publish artifacts to teamcity
    echo "##teamcity[publishArtifacts '_builtpackages/omniverse-kit-robotics*.7z']"
fi
