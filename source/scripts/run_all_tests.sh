#!/bin/bash

set -e

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

for f in tests-*.sh; do
    echo "executing $f"
    bash "$f" $args $@
done