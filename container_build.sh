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
  --build-arg ISAACSIM_VERSION=develop \
  --build-arg OMNI_SERVER_ENV=omniverse://isaac-dev.ov.nvidia.com \
  --build-arg ISAACSIM_PATH=_build/linux-x86_64/release_container \
  --file Dockerfile .
