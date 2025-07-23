#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
ROOT_DIR="$(dirname "$(realpath $SCRIPT_DIR/../../../)")"
"$ROOT_DIR/tools/packman/packman" install connect-samples-launcher 1112-linux-x86_64 -l $ROOT_DIR/_build/_omnicli
OMNICLI="$ROOT_DIR/_build/_omnicli/omnicli.sh"
SOURCE_PATH="https://omniverse-content-staging.s3-us-west-2.amazonaws.com/Assets/Isaac"
OUTPUT_PATH="$ROOT_DIR/_assets-4_temp"
VERSION="5.0"
NAME="isaac-sim-assets-4"


echo Removing $OUTPUT_PATH/...
rm -rf $OUTPUT_PATH

echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/..."
$OMNICLI copy $SOURCE_PATH/$VERSION/Isaac $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac

# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Environments/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Environments $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Environments
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/IsaacLab/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/IsaacLab $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/IsaacLab
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Materials/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Materials $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Materials
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/People/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/People $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/People
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Props/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Props $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Props
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Robots/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Robots $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Robots
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Samples/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Samples $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Samples
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Sensors/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Sensors $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Sensors


# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Commercial/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/ArchVis/Commercial $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Commercial
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Industrial/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/ArchVis/Industrial $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Industrial
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Residential/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/ArchVis/Residential $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Residential


# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Materials/Base/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Materials/Base $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Materials/Base
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/vMaterials_2/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Materials/vMaterials_2 $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Materials/vMaterials_2
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/AnimGraph/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/AnimGraph $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/AnimGraph
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Audio2Face/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Audio2Face $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Audio2Face
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Characters/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Characters $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Characters
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Particles/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Particles $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Particles
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Scenes/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Particles $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Scenes
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Skies/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Skies $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Skies
# echo "Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Vegetation/..."
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Vegetation $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Vegetation


# Packaging assets
echo du -h -d 7 $OUTPUT_PATH
du -h -d 7 $OUTPUT_PATH
echo "Packaging $NAME..."
"$ROOT_DIR/repo.sh" package -m $NAME
