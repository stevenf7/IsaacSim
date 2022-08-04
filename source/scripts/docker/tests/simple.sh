#!/bin/bash

set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Test apt update
apt update

# Test pip install
cd "$SCRIPT_DIR/.."

./python.sh --version
./python.sh -m pip --version