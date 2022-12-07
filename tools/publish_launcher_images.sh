#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
"$SCRIPT_DIR/../repo.sh" package -m isaac-sim-pipeline-images-beta -c release || exit $?
"$SCRIPT_DIR/../repo.sh" package -m isaac-sim-pipeline-images-rc -c release || exit $?
"$SCRIPT_DIR/../repo.sh" package -m isaac-sim-pipeline-images-assets -c release || exit $?
"$SCRIPT_DIR/../repo.sh" publish_launcher_images $@ || exit $?