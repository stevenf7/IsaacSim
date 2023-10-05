# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Reference:
# https://gitlab.com/nvidia/container-images/vulkan/-/blob/master/docker/Dockerfile.ubuntu
# https://github.com/NVIDIA-Omniverse/IsaacSim-dockerfiles
#
# Build the image:
# docker login nvcr.io
# docker build --pull -t \
#   isaac-sim:local \
#   --build-arg ISAACSIM_VERSION=develop \
#   --file Dockerfile .
#
# Run container:
# docker run --name isaac-sim --entrypoint bash -it --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
#   -v ~/docker/isaac-sim/cache/kit:/isaac-sim/kit/cache:rw \
#   -v ~/docker/isaac-sim/cache/ov:/root/.cache/ov:rw \
#   -v ~/docker/isaac-sim/cache/pip:/root/.cache/pip:rw \
#   -v ~/docker/isaac-sim/cache/glcache:/root/.cache/nvidia/GLCache:rw \
#   -v ~/docker/isaac-sim/cache/computecache:/root/.nv/ComputeCache:rw \
#   -v ~/docker/isaac-sim/logs:/root/.nvidia-omniverse/logs:rw \
#   -v ~/docker/isaac-sim/data:/root/.local/share/ov/data:rw \
#   -v ~/docker/isaac-sim/documents:/root/Documents:rw \
# 	isaac-sim:local \
# 	./isaac-sim.headless.native.sh --allow-root
#
# More info:
# https://developer.nvidia.com/isaac-sim
#
ARG DEBIAN_FRONTEND=noninteractive
ARG ISAACSIM_VERSION=develop

FROM gitlab-master.nvidia.com:5005/isaac/omni_isaac_sim/isaac-sim:latest-${ISAACSIM_VERSION} as isaac-sim

# ENV OMNI_SERVER http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/2023.1.0
ARG OMNI_SERVER_ENV omniverse://isaac-dev.ov.nvidia.com
ENV OMNI_SERVER omniverse://isaac-dev.ov.nvidia.com
# ENV OMNI_USER admin
# ENV OMNI_PASS admin
ENV MIN_DRIVER_VERSION 525.60.11

# Copy dev Isaac Sim files
RUN rm -rf /isaac-sim
ARG ISAACSIM_PATH=_build/linux-x86_64/release_container
COPY ${ISAACSIM_PATH} /isaac-sim


WORKDIR /isaac-sim

# Add symlink
RUN ln -s exts/omni.isaac.examples/omni/isaac/examples extension_examples

# Default entrypoint to launch headless with streaming
ENTRYPOINT ./isaac-sim.headless.native.sh --/persistent/isaac/asset_root/default="${OMNI_SERVER_ENV}" --allow-root
