#!/usr/bin/env bash

set -e

if [ ! -z "$TEAMCITY_VERSION" ]
then
    package="--from-package"
fi

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
"$SCRIPT_DIR/../../../../tools/test_runner.sh" --suite unittests --config release $package -e ~[teamcityjob1] --linbuild-profile=u18-$(arch)-x11 $*

# needs to be added to the command above when the tests are fixed
# -e ~[teamcityjob2] -e ~[teamcityjob3]
