#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

if [ -n "$TEAMCITY_VERSION" ]
then
    package="--from-package --clean"
fi

# Startup Test
echo "##teamcity[testSuiteStarted name='isaac-sim-startuptests']"
"$SCRIPT_DIR/../../../test_runner.sh" --suite startuptest --config release $package -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" $*
echo "##teamcity[testSuiteFinished name='isaac-sim-startuptests']"


if [ -n "$TEAMCITY_VERSION" ]
then
    # Package shader cache
    echo "##teamcity[testSuiteStarted name='Packaging the shader cache...']"
    "$SCRIPT_DIR/../../../packman/python.sh" "$SCRIPT_DIR/../../../repoman/package_cache.py" --platform linux-x86_64 --config release --experience isaac-sim
    echo "##teamcity[testSuiteFinished name='Packaging the shader cache...']"
    
    # publish artifacts to teamcity
    echo "##teamcity[publishArtifacts '_builtpackages/isaac-sim*.7z']"
fi

# if [ -n "$TEAMCITY_VERSION" ]
# then
#     export ARCHIVE_PATTERN="_builtpackages/omniverse-kit-robotics*.7z"

#     # Startup Test
#     echo "##teamcity[testSuiteStarted name='omniverse-kit-robotics-startuptests']"
#     "$SCRIPT_DIR/../../../test_runner.sh" --suite startuptest --config release $package -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" $*
#     echo "##teamcity[testSuiteFinished name='omniverse-kit-robotics-startuptests']"

#     # Package shader cache
#     echo "##teamcity[testSuiteStarted name='Packaging the shader cache...']"
#     "$SCRIPT_DIR/../../../packman/python.sh" "$SCRIPT_DIR/../../../repoman/package_cache.py" --platform linux-x86_64 --config release --experience omniverse-kit-robotics
#     echo "##teamcity[testSuiteFinished name='Packaging the shader cache...']"
    
#     # publish artifacts to teamcity
#     echo "##teamcity[publishArtifacts '_builtpackages/omniverse-kit-robotics*.7z']"
# fi
