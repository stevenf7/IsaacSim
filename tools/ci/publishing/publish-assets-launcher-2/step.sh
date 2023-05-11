#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
source "$SCRIPT_DIR/../../../../repo.sh" publish_assets_launcher_2 $@ || exit $?
