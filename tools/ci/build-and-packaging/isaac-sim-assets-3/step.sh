#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
ROOT_DIR="$(dirname "$(realpath $SCRIPT_DIR/../../../)")"
"$ROOT_DIR/tools/packman/packman" install connect-samples-launcher 1112-linux-x86_64 -l $ROOT_DIR/_build/_omnicli
OMNICLI="$ROOT_DIR/_build/_omnicli/omnicli.sh"
SOURCE_PATH="https://omniverse-content-staging.s3-us-west-2.amazonaws.com/Assets/Isaac"
OUTPUT_PATH="$ROOT_DIR/_assets-3_temp"
VERSION="4.0"
NAME="isaac-sim-assets-3"


echo Removing $OUTPUT_PATH/...
rm -rf $OUTPUT_PATH

# # Pack 1 (19.4GB)
# # echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/...']"
# # $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac

# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Environments/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Environments $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Environments


# # Pack 2 (23.5GB)
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/IsaacLab/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/IsaacLab $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/IsaacLab
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Materials/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Materials $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Materials
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/People/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/People $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/People
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Props/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Props $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Props
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Robots/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Robots $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Robots
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Samples/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Samples $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Samples
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Sensors/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/Isaac/Sensors $OUTPUT_PATH/Assets/Isaac/$VERSION/Isaac/Sensors

# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Commercial/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/ArchVis/Commercial $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Commercial
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Industrial/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/ArchVis/Industrial $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Industrial


# Pack 3 (26.5GB)
echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Residential/...']"
$OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/ArchVis/Residential $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Residential


# # Pack 4 (22.3GB)
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Materials/Base/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Materials/Base $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Materials/Base
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/vMaterials_2/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Materials/vMaterials_2 $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Materials/vMaterials_2

# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/AnimGraph/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/AnimGraph $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/AnimGraph
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Audio2Face/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Audio2Face $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Audio2Face
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Characters/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Characters $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Characters
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Particles/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Particles $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Particles
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Scenes/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Particles $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Scenes
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Skies/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Skies $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Skies
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Vegetation/...']"
# $OMNICLI copy $SOURCE_PATH/$VERSION/NVIDIA/Assets/Vegetation $OUTPUT_PATH/Assets/Isaac/$VERSION/NVIDIA/Assets/Vegetation


# Packaging assets
echo du -h -d 7 $OUTPUT_PATH
du -h -d 7 $OUTPUT_PATH
echo "##teamcity[progressMessage 'Packaging $NAME...']"
"$ROOT_DIR/repo.sh" package -m $NAME
