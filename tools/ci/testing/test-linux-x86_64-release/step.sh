#!/usr/bin/env bash

set -e

if [ ! -z "$TEAMCITY_VERSION" ]
then
    package="--from-package"
fi

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
"$SCRIPT_DIR/../../../test_runner.sh" --suite unittests --config release $package -e ~[teamcityjob1] $*

# needs to be added to the command above when the tests are fixed
# -e ~[teamcityjob2] -e ~[teamcityjob3]
