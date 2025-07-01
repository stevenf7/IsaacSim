#!/bin/bash
set -e
SCRIPT_DIR=$(realpath $(dirname ${BASH_SOURCE}))
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


find_chained_symlinks(){
    echo "Searching for chained symlinks"
    count=$((0))
    find $1 -type l | while read -r symlink; do
        target="$(dirname "$symlink")/$(readlink "$symlink")"
        if [ -L "$target" ]; then
            target_of_target="$(dirname "$target")/$(readlink "$target")"
            echo "Correcting chained link $(basename "$symlink") -> $(basename "$target") -> $(basename "$target_of_target")"
            ln -sfr "$target_of_target" "$symlink"
            count=$((count + 1))
        fi
    done
    echo "Replaced $count chained symlinks"
}




dedupe_folder(){
    echo "Starting a dedupe of $1" 
    hash=""
    true_path=""
    echo "Searching for duplicates (ignoring paths with spaces)"
    # Use ! -regex to exclude paths containing spaces
    data=$(find $1 -type f ! -regex '.* .*' -exec sh -c 'echo $(md5sum "$1" | cut -f1 -d " ") $(du -h "$1")' _ {} \; | sort | uniq -w32 -dD)
    if [[ -n "$data" ]]; then
        count=$((0))
        dupe_count=$((0))
        while IFS= read -r LINE; do
            new_hash=$(echo "$LINE" | cut -d " " -f1)
            test_path=$(echo "$LINE" | cut -d " " -f3-)
            # new file check
            if [[ ${new_hash} != ${hash} ]]; then
                count=$((count + 1))
                hash=${new_hash}
                true_path="${test_path}"
            else
                dupe_count=$((dupe_count + 1))
                rm "${test_path}"
                ln -sr "${true_path}" "${test_path}"
            fi
        done < <(printf '%s\n' "$data")
        echo "Removed ${dupe_count} duplicates of ${count} files"
        echo "Note: Files with spaces in their paths were skipped"
    else
        echo "No duplicated files found"
    fi
    find_chained_symlinks $1
}





# Pull Artifacts
echo !Start pulling artifacts!
cd "$SCRIPT_DIR/../.."
./tools/packman/packman install "7za" "16.02.4" -l "tools/container/7za"
# ls tools/container/_inputs
rm -rf tools/container/_inputs/*/
cp VERSION tools/container/VERSION.md
# ./tools/packman/packman install isaac-sim-standalone 4.1.0-rc.3+4.0.12843.07053822.gl.linux-x86_64.release -l tools/container/_inputs/isaac-sim
tools/container/7za/linux-x86/64/7za x _build/packages/$APP_NAME-standalone*.7z -otools/container/_inputs/isaac-sim
ls tools/container/_inputs/isaac-sim

dedupe_folder tools/container/_inputs/isaac-sim

# Build Container
echo !Start building container!
cd "$SCRIPT_DIR"
# docker pull gitlab-master.nvidia.com:5005/omniverse/containers/apps/ov-base/ov-base-ubuntu-22:2023.8.0
env BUILD=$APP_NAME ./bin/docker/build.sh -f $FAMILY_NAME
# docker login nvcr.io
docker_image_tag=`cat docker/__most_recent_image_${APP_NAME}`
echo !Built container $docker_image_tag!

if [[ "${CI_COMMIT_BRANCH}" == "local" ]]; then
  exit
fi

# Publish Container
echo !Start publishing container!
echo $docker_image_tag
# ./bin/docker/publish.sh --yes -r nvcr.io/nvidian/isaac-sim $docker_image_tag
echo !Publishing to gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/$APP_NAME:latest-$CI_COMMIT_REF_SLUG!
./bin/docker/publish.sh --yes -r gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim $docker_image_tag -t latest-$CI_COMMIT_REF_SLUG

echo !Publishing to nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_REF_SLUG!
./bin/docker/publish.sh --yes -r nvcr.io/nvidian $docker_image_tag -t latest-$CI_COMMIT_REF_SLUG

docker pull nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_REF_SLUG
docker tag nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_REF_SLUG nvcr.io/nvidian/isaac-sim:latest-${CI_COMMIT_REF_SLUG}-${CI_COMMIT_SHORT_SHA}
docker push nvcr.io/nvidian/isaac-sim:latest-${CI_COMMIT_REF_SLUG}-${CI_COMMIT_SHORT_SHA}
# ./bin/docker/publish.sh --yes -r gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim $docker_image_tag -t latest-$CI_COMMIT_BRANCH
# docker pull nvcr.io/nvidian/isaac-sim/$docker_image_tag

# echo !Publishing to gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim!
# docker tag nvcr.io/nvidian/isaac-sim/$docker_image_tag gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/$APP_NAME:latest-$CI_COMMIT_BRANCH
# docker push gitlab-master.nvidia.com:5005/omniverse/isaac/omni_isaac_sim/$APP_NAME:latest-$CI_COMMIT_BRANCH

# echo !Publishing to nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH!
# docker tag $docker_image_tag nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH
# docker push nvcr.io/nvidian/$APP_NAME:latest-$CI_COMMIT_BRANCH

# # FOR PRODUCTION #
# echo !Publishing to nvcr.io/nvstaging/isaacsim/isaac-sim:5.0.0!
# docker tag $docker_image_tag nvcr.io/nvstaging/isaacsim/isaac-sim:5.0.0
# docker push nvcr.io/nvstaging/isaacsim/isaac-sim:5.0.0

docker images
docker rmi -f $(docker images --filter=reference="$docker_image_tag" -q)
docker images
