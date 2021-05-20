#!/bin/bash

set -e

shopt -s globstar

for f in tests-*.sh; do
    echo "executing $f"
    bash "$f"
done
