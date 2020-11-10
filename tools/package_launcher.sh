#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
source "$SCRIPT_DIR/packman/packman" pull "$SCRIPT_DIR/../deps/kit-sdk.packman.xml" -i release -p linux-x86_64 || exit $?
source "$SCRIPT_DIR/../repo.sh" package -m create-launcher $@ || exit $?
