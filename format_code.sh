#!/bin/bash
set -e

# fix issue with user python packages getting used by packman
export PYTHONNOUSERSITE=" "

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
source "$SCRIPT_DIR/tools/packman/python.sh" "$SCRIPT_DIR/tools/repoman/format.py" $@ || exit $?
