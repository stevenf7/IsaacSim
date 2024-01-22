#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

while (( "$#" )); do
     case $1 in
          release)
               CONFIG=release
               shift
               ;;
          debug)
               CONFIG=debug
               shift
               ;;
          package)
               # Use package in _build/packages
               USE_PACKAGE="--from-package"
               shift
               ;;
          *)
               PARAMS="$PARAMS $1"
               shift
               ;;
     esac
done

if [ "$CONFIG" == "" ]
then
    CONFIG="release"
fi

# Nucleus server credentials
# export OMNI_USER=svc-test
# export OMNI_PASS=svc-test

cd "$SCRIPT_DIR/../../../../tools"
./test.sh --suite internaldockertests --config $CONFIG $USE_PACKAGE $PARAMS

# cd "$SCRIPT_DIR/../../../.."
# docker run --name isaac-sim --entrypoint bash -it --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
# -v $SCRIPT_DIR/../../../../_build/linux-x86_64/release:/isaac-sim:rw \
# gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:latest-develop
# gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:latest-develop ./tests/tests-docker-simple.sh
# ./test.sh --suite jupytertests --config $CONFIG $USE_PACKAGE $PARAMS
