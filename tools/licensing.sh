#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

if [ ! -d "$SCRIPT_DIR/../PACKAGE-LICENSES" ]
then
    mkdir "$SCRIPT_DIR/../PACKAGE-LICENSES"
fi

source "$SCRIPT_DIR/packman/python.sh" "$SCRIPT_DIR/repoman/licensing.py" $@ || exit $?
