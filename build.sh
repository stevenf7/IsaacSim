#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
# Generate USD Schemas
"$SCRIPT_DIR/schemas/repo.sh" usdgenschema
"$SCRIPT_DIR/schemas/repo.sh" build
# Build Isaac Sim
source "$SCRIPT_DIR/repo.sh" build $@ || exit $?
