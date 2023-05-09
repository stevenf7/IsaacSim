#!/bin/bash
set -e
SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
VERSION=$(cat VERSION)

# Build release
# "$SCRIPT_DIR/build.sh" --release

# Copy release folder to resolve symlinks
rm -rf "$SCRIPT_DIR/_build/linux-x86_64/release_container"
cp -r -L "$SCRIPT_DIR/_build/linux-x86_64/release" "$SCRIPT_DIR/_build/linux-x86_64/release_container"

# Build container
docker login nvcr.io
docker build --pull -t \
  isaac-sim:${VERSION} \
  --build-arg ISAACSIM_VERSION=2022.2.1 \
  --build-arg BASE_DIST=ubuntu20.04 \
  --build-arg CUDA_VERSION=11.4.2 \
  --build-arg VULKAN_SDK_VERSION=1.3.224.1 \
  --build-arg OMNI_SERVER_ENV=http://omniverse-content-staging.s3-us-west-2.amazonaws.com/Assets/Isaac/2023.1.0 \
  --build-arg ISAACSIM_PATH=_build/linux-x86_64/release_container \
  --file Dockerfile .
