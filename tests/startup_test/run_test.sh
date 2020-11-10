#!/usr/bin/env bash
set -e

TOOLS=$(dirname $(readlink -m $BASH_SOURCE))/../../../tools


exec $TOOLS/packman/python.sh $TOOLS/ovat/run_test.py $*
