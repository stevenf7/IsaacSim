#!/bin/bash
docker login gitlab-master.nvidia.com:5005
docker pull gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:latest-develop
# the following will dump you into the docker with a bash terminal and not run anything
# useful for testing in a clean environment
nvidia-docker run -it --entrypoint bash --gpus all -e "ACCEPT_EULA=Y" --rm --network=host -v /tmp/.X11-unix:/tmp/.X11-unix -v /etc/localtime:/etc/localtime:ro -e DISPLAY=unix${DISPLAY} gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/isaac-sim:latest-develop
