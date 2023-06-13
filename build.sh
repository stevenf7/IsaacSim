#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
# Build Isaac Sim
source "$SCRIPT_DIR/repo.sh" build $@ || exit $?
