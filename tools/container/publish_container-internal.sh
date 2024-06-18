#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
APP_NAME="isaac-sim-internal"
# CI_COMMIT_BRANCH=local


# Pull Artifacts
# cd "$SCRIPT_DIR/../.."
# ./tools/packman/packman install "7za" "16.02.4" -l "tools/container/7za"
# rm -rf tools/container/_inputs/*/
# cp VERSION tools/container/VERSION.md
# # ./tools/packman/packman install isaac-sim-pipeline-images-rc 2023.1.0-alpha.7+develop.47.63cd61b8.tc.windows-x86_64 -l tools/container/_inputs/isaac-sim
# tools/container/7za/linux-x86/64/7za x _build/packages/isaac-sim-internal*.7z -otools/container/_inputs/isaac-sim

# Build Container
cd "$SCRIPT_DIR"
# docker pull gitlab-master.nvidia.com:5005/omniverse/containers/apps/ov-base/ov-base-ubuntu-22:2023.8.0
env BUILD=$APP_NAME ./bin/docker/build.sh -f "gl"
# docker login nvcr.io
docker_image_tag=`cat docker/__most_recent_image_${APP_NAME}`

# Publish Container
echo !Start publishing container!
echo $docker_image_tag
# ./bin/docker/publish.sh --yes -r nvcr.io/nvidian/isaac-sim $docker_image_tag
echo !Publishing to gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim!
./bin/docker/publish.sh --yes -r gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim $docker_image_tag -t latest-$CI_COMMIT_BRANCH
# ./bin/docker/publish.sh --yes -r nvcr.io/nvidian $docker_image_tag -t latest-$CI_COMMIT_BRANCH
# ./bin/docker/publish.sh --yes -r gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim $docker_image_tag -t latest-$CI_COMMIT_BRANCH
# docker pull nvcr.io/nvidian/isaac-sim/$docker_image_tag

# docker tag nvcr.io/nvidian/isaac-sim/$docker_image_tag gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/$APP_NAME:latest-$CI_COMMIT_BRANCH
# docker push gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/$APP_NAME:latest-$CI_COMMIT_BRANCH

# docker tag nvcr.io/nvidian/isaac-sim/$docker_image_tag nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH
# docker push nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH

echo !Publishing to nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH!
docker tag $docker_image_tag nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH
docker push nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH

echo !Publishing to nvcr.io/nvidian/isaac-sim/$APP_NAME:latest-$CI_COMMIT_BRANCH!
docker tag $docker_image_tag nvcr.io/nvidian/isaac-sim/$APP_NAME:latest-$CI_COMMIT_BRANCH
docker push nvcr.io/nvidian/isaac-sim/$APP_NAME:latest-$CI_COMMIT_BRANCH

# docker images
# docker rmi -f $(docker images --filter=reference="$docker_image_tag" -q)
# docker images
