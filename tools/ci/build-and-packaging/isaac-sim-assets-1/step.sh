#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
"$SCRIPT_DIR/../../../packman/packman" install connect-samples-launcher 643-linux-x86_64 -l $SCRIPT_DIR/../../../../_build/_omnicli
OMNICLI="$SCRIPT_DIR/../../../../_build/_omnicli/omnicli.sh"
ROOT_PATH="omniverse://isaac-dev.ov.nvidia.com/NVIDIA-Staging/Assets/Isaac"
OUTPUT_PATH="_assets-1_temp"
VERSION="2023.1.0"
NAME="isaac-sim-assets-1"

echo Removing %OUTPUT_PATH...
rm -rf $SCRIPT_DIR/../../../../$OUTPUT_PATH

# Pack 1 (19.9GB)
echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Environments/...']"
$OMNICLI copy $ROOT_PATH/$VERSION/Isaac/Environments $SCRIPT_DIR/../../../../$OUTPUT_PATH/Isaac/Environments
echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Materials/...']"
$OMNICLI copy $ROOT_PATH/$VERSION/Isaac/Materials $SCRIPT_DIR/../../../../$OUTPUT_PATH/Isaac/Materials
echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/People/...']"
$OMNICLI copy $ROOT_PATH/$VERSION/Isaac/People $SCRIPT_DIR/../../../../$OUTPUT_PATH/Isaac/People
echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Props/...']"
$OMNICLI copy $ROOT_PATH/$VERSION/Isaac/Props $SCRIPT_DIR/../../../../$OUTPUT_PATH/Isaac/Props
echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Robots/...']"
$OMNICLI copy $ROOT_PATH/$VERSION/Isaac/Robots $SCRIPT_DIR/../../../../$OUTPUT_PATH/Isaac/Robots
echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Samples/...']"
$OMNICLI copy $ROOT_PATH/$VERSION/Isaac/Samples $SCRIPT_DIR/../../../../$OUTPUT_PATH/Isaac/Samples
echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/Isaac/Sensors/...']"
$OMNICLI copy $ROOT_PATH/$VERSION/Isaac/Sensors $SCRIPT_DIR/../../../../$OUTPUT_PATH/Isaac/Sensors

echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Materials/Base/...']"
$OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Materials/Base $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Materials/Base
echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/vMaterials_2/...']"
$OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Materials/vMaterials_2 $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Materials/vMaterials_2

# # Pack 2 (27.8GB)
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/AnimGraph/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/AnimGraph $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/AnimGraph
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Audio2Face/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/Audio2Face $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/Audio2Face
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Characters/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/Characters $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/Characters
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Particles/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/Particles $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/Particles
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Scenes/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/Scenes $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/Scenes
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Skies/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/Skies $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/Skies
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/Vegetation/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/Vegetation $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/Vegetation
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Commercial/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/ArchVis $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/ArchVis/Commercial
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Industrial/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/ArchVis $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/ArchVis/Industrial

# # Pack 3 (28.4GB)
# echo "##teamcity[progressMessage 'Downloading /NVIDIA-Staging/Assets/Isaac/$VERSION/NVIDIA/Assets/ArchVis/Residential/...']"
# $OMNICLI copy $ROOT_PATH/$VERSION/NVIDIA/Assets/ArchVis $SCRIPT_DIR/../../../../$OUTPUT_PATH/NVIDIA/Assets/ArchVis/Residential

# Packaging assets
echo "##teamcity[progressMessage 'Packaging $NAME...']"
"$SCRIPT_DIR/../../../../repo.sh" package -m $NAME

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"
