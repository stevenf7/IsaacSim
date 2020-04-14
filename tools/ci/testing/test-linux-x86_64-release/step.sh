#!/usr/bin/env bash

set -e


SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
"$SCRIPT_DIR/../../../test_runner.sh" --suite unittests --config release -e ~[teamcityjob1] $*

# needs to be added to the command above when the tests are fixed
# -e ~[teamcityjob2] -e ~[teamcityjob3]
