#!/bin/bash

set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

shopt -s globstar
args=""

if ! [[ $EUID -ne 0 ]]; then
    echo "running as root"
    args="$args --allow-root"
fi

if [[ -z "${DISPLAY}" ]]; then
    echo "running headless"
    args="$args --no-window"
fi

pushd $SCRIPT_DIR
for f in tests-*.sh; do
    echo "Executing Test: $f"
    bash "$f" $args $@
done
popd