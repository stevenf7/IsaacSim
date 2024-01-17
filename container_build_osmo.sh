#!/bin/bash
set -e
SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"
COMMIT=$(git log --pretty=format:'%h' -n 1)
BRANCH=$(git branch --show-current | sed 's|/|_|')

# Copy release folder to resolve symlinks
rm -rf "$SCRIPT_DIR/_build/linux-x86_64/release_container"
cp -r -L "$SCRIPT_DIR/_build/linux-x86_64/release" "$SCRIPT_DIR/_build/linux-x86_64/release_container"

# Build container
docker login nvcr.io
docker build --pull -t \
  nvcr.io/omniverse/isaac-internal/isaac-sim-internal-only:${BRANCH}_${COMMIT} \
  --build-arg ISAACSIM_VERSION=develop \
  --build-arg OMNI_SERVER_ENV=omniverse://isaac-dev.ov.nvidia.com \
  --build-arg ISAACSIM_PATH=_build/linux-x86_64/release_container \
  --file Dockerfile .
