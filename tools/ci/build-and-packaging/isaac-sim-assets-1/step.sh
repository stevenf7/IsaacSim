#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
"$SCRIPT_DIR/../../../packman/packman" install connect-samples-launcher 643-linux-x86_64 -l $SCRIPT_DIR/../../../../_build/_omnicli
OMNICLI="$SCRIPT_DIR/../../../../_build/_omnicli/omnicli.sh"

echo Removing _assets-1_temp...
rm -rf $SCRIPT_DIR/../../../../_assets-1_temp

# FOR PRODUCTION #
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Materials/Base/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Materials/Base $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Materials/Base
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Materials/vMaterials_2/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Materials/vMaterials_2 $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Materials/vMaterials_2
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/AnimGraph/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/AnimGraph $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/AnimGraph
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/ArchVis/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/ArchVis $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/ArchVis
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Audio2Face/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Audio2Face $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Audio2Face
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Characters/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Characters $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Characters
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Particles/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Particles $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Particles
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Scenes/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Scenes $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Scenes
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Skies/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Skies $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Skies
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Vegetation/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/NVIDIA/Assets/Vegetation $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Vegetation

echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/Isaac/Environments/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/Isaac/Environments $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Environments
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/Isaac/Materials/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/Isaac/Materials $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Materials
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/Isaac/People/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/Isaac/People $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/People
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/Isaac/Props/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/Isaac/Props $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Props
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/Isaac/Robots/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/Isaac/Robots $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Robots
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/Isaac/Samples/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/Isaac/Samples $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Samples
echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Isaac/2022.2.1/Isaac/Sensors/...']"
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Isaac/2022.2.1/Isaac/Sensors $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Sensors

# # FOR DEVELOPMENT #
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Materials/Base/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Materials/Base $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Materials/Base
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Materials/vMaterials_2/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Materials/vMaterials_2 $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Materials/vMaterials_2
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/AnimGraph/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/AnimGraph $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/AnimGraph
# # echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/ArchVis/...']"
# # $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/ArchVis $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/ArchVis
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Audio2Face/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Audio2Face $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Audio2Face
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Characters/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Characters $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Characters
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Particles/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Particles $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Particles
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Scenes/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Scenes $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Scenes
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Skies/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Skies $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Skies
# echo "##teamcity[progressMessage 'Downloading /NVIDIA/Assets/Vegetation/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/NVIDIA/Assets/Vegetation $SCRIPT_DIR/../../../../_assets-1_temp/NVIDIA/Assets/Vegetation

# echo "##teamcity[progressMessage 'Downloading /Isaac/Environments/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Environments $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Environments
# echo "##teamcity[progressMessage 'Downloading /Isaac/Materials/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Materials $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Materials
# echo "##teamcity[progressMessage 'Downloading /Isaac/People/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/People $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/People
# echo "##teamcity[progressMessage 'Downloading /Isaac/Props/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Props $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Props
# echo "##teamcity[progressMessage 'Downloading /Isaac/Robots/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Robots
# echo "##teamcity[progressMessage 'Downloading /Isaac/Samples/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Samples $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Samples
# echo "##teamcity[progressMessage 'Downloading /Isaac/Sensors/...']"
# $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Sensors $SCRIPT_DIR/../../../../_assets-1_temp/Isaac/Sensors

# Packaging assets
echo "##teamcity[progressMessage 'Packaging isaac-sim-assets-1...']"
"$SCRIPT_DIR/../../../../repo.sh" package -m isaac-sim-assets-1

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"
