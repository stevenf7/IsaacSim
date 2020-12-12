#!/usr/bin/env bash
set -e

THIS_SCRIPT_LOCATION=$(dirname $(readlink -m $BASH_SOURCE))
TOOLS=$(dirname $(readlink -m $BASH_SOURCE))/tools
PACKMAN=${TOOLS}/packman

cd $THIS_SCRIPT_LOCATION
exec ${PACKMAN}/python.sh $TOOLS/ovat/run_test.py $*
