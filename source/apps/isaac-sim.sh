#!/bin/bash
set -e
SCRIPT_DIR=$(readlink -e $(dirname ${BASH_SOURCE}))
"$SCRIPT_DIR/_build/$PLATFORM/$CONFIG/isaac-sim.sh $@
