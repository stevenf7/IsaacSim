#!/bin/bash

set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

docker pull gitlab-master.nvidia.com:5005/isaac/omni_isaac_sim/isaac-sim:base

# 

files=( $SCRIPT_DIR/../_build/packages/isaac-sim-standalone*.7z )
if [ ! -f "$files" ]; then
    $SCRIPT_DIR/../repo.sh package --config release -m isaac-sim-standalone
fi

pushd $SCRIPT_DIR/../_build/packages

if [ ! -d "isaac-sim-standalone" ]; then
    7za x isaac-sim-standalone*.7z -oisaac-sim-standalone
fi

nvidia-docker run -it -e OMNI_USER=svc-test -e OMNI_PASS=svc-test --network=host --rm -v "$(pwd)"/isaac-sim-standalone:/isaac-sim gitlab-master.nvidia.com:5005/isaac/omni_isaac_sim/isaac-sim:base bash

popd