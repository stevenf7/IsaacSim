#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
"$SCRIPT_DIR/../../../../repo.sh" build -x -rd
"$SCRIPT_DIR/../../../../repo.sh" publish_exts -c release
"$SCRIPT_DIR/../../../../repo.sh" publish_exts -c debug

# keeping manual command below for reference
# ../build.sh
# ../_build/linux-x86_64/release/isaac-sim.sh --ext-folder exts --ext-folder apps --publish

