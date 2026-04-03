#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <package_num>" >&2
    exit 1
fi

ASSET_NUM="$1"
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
ROOT_DIR="$(dirname "$(realpath $SCRIPT_DIR/../../)")"
"$ROOT_DIR/tools/packman/packman" install connect-samples-launcher 1112-linux-x86_64 -l $ROOT_DIR/_build/_omnicli
OMNICLI="$ROOT_DIR/_build/_omnicli/omnicli.sh"
SOURCE_PATH="https://omniverse-content-staging.s3-us-west-2.amazonaws.com/Assets/Isaac"
OUTPUT_PATH="$ROOT_DIR/_assets-${ASSET_NUM}_temp"
VERSION="6.0"
NAME="isaac-sim-assets-${ASSET_NUM}"

echo "Removing $OUTPUT_PATH/..."
rm -rf $OUTPUT_PATH

case "$ASSET_NUM" in
    1)
        echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Robots/..."
        $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Robots $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Robots
        echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Sensors/..."
        $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Sensors $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Sensors
        ;;
    2)
        echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Materials/..."
        $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Materials $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Materials
        echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Props/..."
        $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Props $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Props
        ;;
    3)
        echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Environments/..."
        $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Environments $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Environments
        ;;
    4)
        echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/..."
        $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac
        ;;
    5)
        echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/..."
        $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets
        echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Materials/..."
        $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Materials $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Materials
        ;;
    *)
        echo "Unknown package number: $ASSET_NUM" >&2
        exit 1
        ;;
esac

echo du -h -d 7 $OUTPUT_PATH
du -h -d 7 $OUTPUT_PATH
echo "Packaging $NAME..."
"$ROOT_DIR/repo.sh" package -m $NAME
