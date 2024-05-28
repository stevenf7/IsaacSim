#!/bin/bash

ARTIFACTORY_URL="https://urm.nvidia.com/artifactory/api/storage/sw-isaacsim-pypi-local"
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
    echo -e "Usage:\n\n  $0 version"
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

# set properties
for artifactory_package in $ARTIFACTORY_PYTHON_PACKAGES; do
    echo $ARTIFACTORY_URL/$artifactory_package/$1

    component_name="$artifactory_package"
    component_arch="x86_64"
    component_version=$(echo "$1" | sed 's/+/%2B/g')
    component_branch="develop"
    component_release_approver="aserranomuno"
    component_release_status="not_ready"

    wheel_name=$(echo "$artifactory_package" | sed 's/-/_/g')
    common_properties="component_name=$component_name;arch=$component_arch;version=$component_version;branch=$component_branch;release_approver=$component_release_approver;release_status=$component_release_status"

    # linux
    curl -u $ISAACSIM_ARTIFACTORY_USERNAME:$ISAACSIM_ARTIFACTORY_PASSWORD -X PUT "$ARTIFACTORY_URL/$artifactory_package/$1/$wheel_name-$1-cp310-none-linux_x86_64.whl?properties=os=linux;$common_properties&recursive=0"
    # windows
    curl -u $ISAACSIM_ARTIFACTORY_USERNAME:$ISAACSIM_ARTIFACTORY_PASSWORD -X PUT "$ARTIFACTORY_URL/$artifactory_package/$1/$wheel_name-$1-cp310-none-win_amd64.whl?properties=os=windows;$common_properties&recursive=0"
done
