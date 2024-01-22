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
./test.sh --suite dockertests --config $CONFIG $USE_PACKAGE $PARAMS

# cd "$SCRIPT_DIR/../../../../source/scripts"

# echo "##teamcity[testStarted name='isaac-sim.docker-1']"
# docker ps -q --filter "name=isaac-sim" | grep -q . && docker kill isaac-sim
# ./isaac-sim.docker.sh "nvidia-smi && ls"
# echo "##teamcity[testFinished name='isaac-sim.docker-1']"

# echo "##teamcity[testStarted name='isaac-sim.docker-2']"
# docker ps -q --filter "name=isaac-sim" | grep -q . && docker kill isaac-sim
# ./isaac-sim.docker.sh "apt update"
# echo "##teamcity[testFinished name='isaac-sim.docker-2']"

# echo "##teamcity[testStarted name='isaac-sim.docker-3']"
# docker ps -q --filter "name=isaac-sim" | grep -q . && docker kill isaac-sim
# ./isaac-sim.docker.sh "./isaac-sim.headless.native.sh --allow-root --/app/quitAfter=500"
# echo "##teamcity[testFinished name='isaac-sim.docker-3']"



# nvidia-smi && ls && ./isaac-sim.headless.native.sh --allow-root --/app/quitAfter=500
# docker run --name isaac-sim --entrypoint bash -it --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
# -v $SCRIPT_DIR/../../../../_build/linux-x86_64/release:/isaac-sim:rw \
# gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:latest-develop
# gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:latest-develop ./tests/tests-docker-simple.sh
# ./test.sh --suite jupytertests --config $CONFIG $USE_PACKAGE $PARAMS
