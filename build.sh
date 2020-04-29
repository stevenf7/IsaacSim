#!/bin/bash

set -e

# fix issue with user python packages getting used by packman
export PYTHONNOUSERSITE=" "

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
cd "$SCRIPT_DIR"
exec "tools/packman/python.sh" tools/repoman/build.py $@

