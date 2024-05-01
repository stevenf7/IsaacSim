#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
# APP_NAME="isaac-sim"
# CI_COMMIT_BRANCH=local

if [[ -z "${APP_NAME}" ]]; then
  APP_NAME="isaac-sim"
fi

if [[ -z "${CI_COMMIT_BRANCH}" ]]; then
  CI_COMMIT_BRANCH="local"
fi

if [[ -z "${FAMILY_NAME}" ]]; then
  FAMILY_NAME="local"
fi


# Pull Artifacts
echo !Start pulling artifacts!
cd "$SCRIPT_DIR/../.."
./tools/packman/packman install "7za" "16.02.4" -l "tools/container/7za"
# ls tools/container/_inputs
rm -rf tools/container/_inputs/*/
cp VERSION tools/container/VERSION.md
# ./tools/packman/packman install isaac-sim-standalone 4.0.0-rc.3+4.0.12843.07053822.gl.linux-x86_64.release -l tools/container/_inputs/isaac-sim
tools/container/7za/linux-x86/64/7za x _build/packages/$APP_NAME-standalone*.7z -otools/container/_inputs/isaac-sim
ls tools/container/_inputs/isaac-sim

# Build Container
echo !Start building container!
cd "$SCRIPT_DIR"
# docker pull gitlab-master.nvidia.com:5005/omniverse/containers/apps/ov-base/ov-base-ubuntu-22:2023.8.0
env BUILD=$APP_NAME ./bin/docker/build.sh -f $FAMILY_NAME
# docker login nvcr.io
docker_image_tag=`cat docker/__most_recent_image_${APP_NAME}`

# Publish Container
echo !Start publishing container!
echo $docker_image_tag
# ./bin/docker/publish.sh --yes -r nvcr.io/nvidian/isaac-sim $docker_image_tag
echo !Publishing to nvcr.io/nvidian/isaac-sim!
./bin/docker/publish.sh --yes -r nvcr.io/nvidian/isaac-sim $docker_image_tag -t latest-$CI_COMMIT_BRANCH
# ./bin/docker/publish.sh --yes -r nvcr.io/nvidian $docker_image_tag -t latest-$CI_COMMIT_BRANCH
# ./bin/docker/publish.sh --yes -r gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim $docker_image_tag -t latest-$CI_COMMIT_BRANCH
docker pull nvcr.io/nvidian/isaac-sim/$docker_image_tag

echo !Publishing to gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim!
docker tag nvcr.io/nvidian/isaac-sim/$docker_image_tag gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/$APP_NAME:latest-$CI_COMMIT_BRANCH
docker push gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/$APP_NAME:latest-$CI_COMMIT_BRANCH

echo !Publishing to nvcr.io/nvidian!
docker tag nvcr.io/nvidian/isaac-sim/$docker_image_tag nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH
docker push nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH

docker images
docker rmi -f $(docker images --filter=reference="$docker_image_tag" -q)
docker images
