#!/usr/bin/env bash

set -e


SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
"$SCRIPT_DIR/../../../test_runner.sh" --suite pythontests --config release $*

# needs to be added to the command above when the tests are fixed
# -e ~[teamcityjob1] -e ~[teamcityjob2] -e ~[teamcityjob3]
