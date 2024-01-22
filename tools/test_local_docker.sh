#!/bin/bash

#This script packages isaac sim like normal, extracts it and then mounts it into a container for testing.
rebuild=0
mountpip=0
while getopts x flag
do
    case "${flag}" in
        x) rebuild=1;;
    esac
done

set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

docker pull gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:base
if [ "$rebuild" -eq "1" ]; then
sudo rm -rf $SCRIPT_DIR/../_build/packages
fi


files=( $SCRIPT_DIR/../_build/packages/isaac-sim-standalone*.7z )
if [ ! -f "$files" ]; then
    $SCRIPT_DIR/../build.sh -r
    $SCRIPT_DIR/../repo.sh package --config release -m isaac-sim-standalone
fi

pushd $SCRIPT_DIR/../_build/packages

if [ ! -d "isaac-sim-standalone" ]; then
    7za x isaac-sim-standalone*.7z -oisaac-sim-standalone
fi

nvidia-docker run -it -e OMNI_USER=svc-test -e OMNI_PASS=svc-test --network=host --rm -v "$(pwd)"/isaac-sim-standalone:/isaac-sim gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:base bash

popd
