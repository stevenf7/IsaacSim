#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

if [ ! -z "$TEAMCITY_VERSION" ]
then
    package="--from-package"
fi

"$SCRIPT_DIR/../../../test_runner.sh" --suite pythontests --config release $package $*

if [ ! -z "$TEAMCITY_VERSION" ]
then
    export ARCHIVE_PATTERN="_builtpackages/omniverse-kit-robotics*.7z"
    "$SCRIPT_DIR/../../../test_runner.sh" --suite pythontests --config release $package $*
fi

# needs to be added to the command above when the tests are fixed
# -e ~[teamcityjob1] -e ~[teamcityjob2] -e ~[teamcityjob3]
