#!/bin/bash

SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Check EULA acceptance first
"${SCRIPT_DIR}/eula_check.sh"
EULA_STATUS=$?

if [ $EULA_STATUS -ne 0 ]; then
    echo "Error: NVIDIA Software License Agreement and Product-Specific Terms for NVIDIA Omniverse must be accepted to proceed."
    exit 1
fi

set -e
source "$SCRIPT_DIR/repo.sh" build $@ || exit $?
