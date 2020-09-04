#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

if [ -n "$TEAMCITY_VERSION" ]
then
    package="--from-package --clean"
fi


echo "##teamcity[testSuiteStarted name='isaac-sim-pythontests-release']"
"$SCRIPT_DIR/../../../test_runner.sh" --suite pythontests --config release $package $*
echo "##teamcity[testSuiteFinished name='isaac-sim-pythontests-release']"

# if [ ! -z "$TEAMCITY_VERSION" ]
# then
#     export ARCHIVE_PATTERN="_builtpackages/omniverse-kit-robotics*.7z"
#     echo "##teamcity[testSuiteStarted name='omniverse-kit-robotics-pythontests-release']"
#     "$SCRIPT_DIR/../../../test_runner.sh" --suite pythontests --config release $package $*
#     echo "##teamcity[testSuiteFinished name='omniverse-kit-robotics-pythontests-release']"
# fi
