#!/usr/bin/env bash

set -e

OMNICLI=~/.local/share/ov/pkg/prod-connectsample-203.0.0/omnicli.sh
TEMP_DIR="$(dirname "$(realpath $0)")"/../../_assets
ISAAC_VER=2023.1.0

#echo run $OMNICLI copy omniverse://ov-isaac-dev/Isaac/Samples $TEMP_DIR/Isaac/Samples
#$OMNICLI copy omniverse://ov-isaac-dev/Isaac/Samples $TEMP_DIR/Isaac/Samples
#7z x Isaac.zip -oIsaac
#pause


echo !! Pulling /Isaac... /Need VPN

echo Removing $TEMP_DIR/nv-staging/Isaac...
rm -rf $TEMP_DIR/nv-staging/Isaac

echo run $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac $TEMP_DIR/nv-staging/Isaac
echo copy /Isaac/Environments/...
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Environments $TEMP_DIR/nv-staging/Isaac/Environments
echo copy /Isaac/People/...
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/People $TEMP_DIR/nv-staging/Isaac/People
echo copy /Isaac/Materials/...
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Materials $TEMP_DIR/nv-staging/Isaac/Materials
echo copy /Isaac/Props/...
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Props $TEMP_DIR/nv-staging/Isaac/Props
echo copy /Isaac/Robots/...
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots $TEMP_DIR/nv-staging/Isaac/Robots
echo copy /Isaac/Samples/...
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Samples $TEMP_DIR/nv-staging/Isaac/Samples
echo copy /Isaac/Sensors/...
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Sensors $TEMP_DIR/nv-staging/Isaac/Sensors


echo !! Staging /Isaac... /VPN not needed from here
echo run aws s3 sync $TEMP_DIR/nv-staging/Isaac s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/Isaac --delete
aws s3 sync $TEMP_DIR/nv-staging/Isaac s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/Isaac --delete

echo Copying latest /NVIDIA assets to local
aws s3 sync s3://omniverse-content-production/Materials $TEMP_DIR/nv-staging/NVIDIA/Materials --delete
aws s3 sync s3://omniverse-content-production/Assets/AnimGraph $TEMP_DIR/nv-staging/NVIDIA/Assets/AnimGraph --delete
aws s3 sync s3://omniverse-content-production/Assets/ArchVis $TEMP_DIR/nv-staging/NVIDIA/Assets/ArchVis --delete
aws s3 sync s3://omniverse-content-production/Assets/Audio2Face $TEMP_DIR/nv-staging/NVIDIA/Assets/Audio2Face --delete
aws s3 sync s3://omniverse-content-production/Assets/Characters $TEMP_DIR/nv-staging/NVIDIA/Assets/Characters --delete
aws s3 sync s3://omniverse-content-production/Assets/Particles $TEMP_DIR/nv-staging/NVIDIA/Assets/Particles --delete
aws s3 sync s3://omniverse-content-production/Assets/Scenes $TEMP_DIR/nv-staging/NVIDIA/Assets/Scenes --delete
aws s3 sync s3://omniverse-content-production/Assets/Skies $TEMP_DIR/nv-staging/NVIDIA/Assets/Skies --delete
aws s3 sync s3://omniverse-content-production/Assets/Vegetation $TEMP_DIR/nv-staging/NVIDIA/Assets/Vegetation --delete

echo !! Staging /NVIDIA...
echo Copying local /NVIDIA assets to staging
aws s3 sync $TEMP_DIR/nv-staging/NVIDIA/Materials s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Materials --delete
aws s3 sync $TEMP_DIR/nv-staging/NVIDIA/Assets/AnimGraph s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/AnimGraph --delete
aws s3 sync $TEMP_DIR/nv-staging/NVIDIA/Assets/ArchVis s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/ArchVis --delete
aws s3 sync $TEMP_DIR/nv-staging/NVIDIA/Assets/Audio2Face s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Audio2Face --delete
aws s3 sync $TEMP_DIR/nv-staging/NVIDIA/Assets/Characters s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Characters --delete
aws s3 sync $TEMP_DIR/nv-staging/NVIDIA/Assets/Particles s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Particles --delete
aws s3 sync $TEMP_DIR/nv-staging/NVIDIA/Assets/Scenes s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Scenes --delete
aws s3 sync $TEMP_DIR/nv-staging/NVIDIA/Assets/Skies s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Skies --delete
aws s3 sync $TEMP_DIR/nv-staging/NVIDIA/Assets/Vegetation s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Vegetation --delete


echo !! Sync Staging to Production...

echo run aws s3 sync s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER s3://omniverse-content-production/Assets/Isaac/$ISAAC_VER --delete
aws s3 sync s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER s3://omniverse-content-production/Assets/Isaac/$ISAAC_VER --delete

echo !! Completed!
