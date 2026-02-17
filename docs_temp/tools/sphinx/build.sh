#!/bin/bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

"$SCRIPT_DIR/../packman/packman" link "$SCRIPT_DIR/../../docs/aec/text/docker" ../../main/text/docker

source "$SCRIPT_DIR/../packman/packman" pull "$SCRIPT_DIR/deps.packman.xml" -p linux-x86_64

export PYTHONPATH="$PM_sphinx_PATH"
unset PYTHONHOME

"$PM_PYTHON" -s -S -u "$SCRIPT_DIR/build.py" $@
