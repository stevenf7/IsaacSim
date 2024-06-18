#!/bin/bash

ARTIFACTORY_URL="https://urm.nvidia.com/artifactory/sw-isaacsim-pypi-local"
ARTIFACTORY_PYTHON_PACKAGES="
isaacsim
isaacsim-app
isaacsim-asset
isaacsim-benchmark
isaacsim-code-editor
isaacsim-core
isaacsim-cortex
isaacsim-example
isaacsim-extscache-kit
isaacsim-extscache-kit-sdk
isaacsim-extscache-physics
isaacsim-gui
isaacsim-kernel
isaacsim-replicator
isaacsim-rl
isaacsim-robot
isaacsim-robot-motion
isaacsim-robot-setup
isaacsim-ros1
isaacsim-ros2
isaacsim-sensor
isaacsim-storage
isaacsim-template
isaacsim-test
isaacsim-utils
"

if [ "$#" -ne 1 ]; then
    echo -e "Usage:\n\n  $0 --all|version"
    exit
fi

# check credentials
if [ -z "$ISAACSIM_ARTIFACTORY_USERNAME" ]; then
    echo "Credential not defined: ISAACSIM_ARTIFACTORY_USERNAME"
    exit
fi
if [ -z "$ISAACSIM_ARTIFACTORY_PASSWORD" ]; then
    echo "Credential not defined: ISAACSIM_ARTIFACTORY_PASSWORD"
    exit
fi

# delete packages
for artifactory_package in $ARTIFACTORY_PYTHON_PACKAGES; do
    if [ "$1" == "--all" ]; then
        echo $ARTIFACTORY_URL/$artifactory_package
        curl -u $ISAACSIM_ARTIFACTORY_USERNAME:$ISAACSIM_ARTIFACTORY_PASSWORD -X DELETE "$ARTIFACTORY_URL/$artifactory_package"
    else
        echo $ARTIFACTORY_URL/$artifactory_package/$1
        curl -u $ISAACSIM_ARTIFACTORY_USERNAME:$ISAACSIM_ARTIFACTORY_PASSWORD -X DELETE "$ARTIFACTORY_URL/$artifactory_package/$1"
    fi
done
