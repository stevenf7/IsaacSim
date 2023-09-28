#!/usr/bin/env bash

set -e

OMNICLI=~/.local/share/ov/pkg/prod-connectsample-203.0.0/omnicli.sh
SCRIPT_DIR="$(dirname "$(realpath $0)")"/../../_assets
ISAAC_VER=2023.1.0

#echo run $OMNICLI copy omniverse://ov-isaac-dev/Isaac/Samples $SCRIPT_DIR/Isaac/Samples
#$OMNICLI copy omniverse://ov-isaac-dev/Isaac/Samples $SCRIPT_DIR/Isaac/Samples
#7z x Isaac.zip -oIsaac
#pause



echo Copying latest /NVIDIA assets to local
aws s3 sync s3://omniverse-content-production/Materials $SCRIPT_DIR/nv-staging/NVIDIA/Materials --delete
aws s3 sync s3://omniverse-content-production/Assets/AnimGraph $SCRIPT_DIR/nv-staging/NVIDIA/Assets/AnimGraph --delete
aws s3 sync s3://omniverse-content-production/Assets/ArchVis $SCRIPT_DIR/nv-staging/NVIDIA/Assets/ArchVis --delete
aws s3 sync s3://omniverse-content-production/Assets/Audio2Face $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Audio2Face --delete
aws s3 sync s3://omniverse-content-production/Assets/Characters $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Characters --delete
aws s3 sync s3://omniverse-content-production/Assets/Particles $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Particles --delete
aws s3 sync s3://omniverse-content-production/Assets/Scenes $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Scenes --delete
aws s3 sync s3://omniverse-content-production/Assets/Skies $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Skies --delete
aws s3 sync s3://omniverse-content-production/Assets/Vegetation $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Vegetation --delete

echo Copying local /NVIDIA assets to staging
aws s3 sync $SCRIPT_DIR/nv-staging/NVIDIA/Materials s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Materials --delete
aws s3 sync $SCRIPT_DIR/nv-staging/NVIDIA/Assets/AnimGraph s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/AnimGraph --delete
aws s3 sync $SCRIPT_DIR/nv-staging/NVIDIA/Assets/ArchVis s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/ArchVis --delete
aws s3 sync $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Audio2Face s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Audio2Face --delete
aws s3 sync $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Characters s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Characters --delete
aws s3 sync $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Particles s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Particles --delete
aws s3 sync $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Scenes s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Scenes --delete
aws s3 sync $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Skies s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Skies --delete
aws s3 sync $SCRIPT_DIR/nv-staging/NVIDIA/Assets/Vegetation s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/NVIDIA/Assets/Vegetation --delete

echo Removing $SCRIPT_DIR/nv-staging/Isaac...
rm -rf $SCRIPT_DIR/nv-staging/Isaac

echo run $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac $SCRIPT_DIR/nv-staging/Isaac
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Environments $SCRIPT_DIR/nv-staging/Isaac/Environments
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/People $SCRIPT_DIR/nv-staging/Isaac/People
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Materials $SCRIPT_DIR/nv-staging/Isaac/Materials
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Props $SCRIPT_DIR/nv-staging/Isaac/Props
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots $SCRIPT_DIR/nv-staging/Isaac/Robots
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Samples $SCRIPT_DIR/nv-staging/Isaac/Samples
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Sensors $SCRIPT_DIR/nv-staging/Isaac/Sensors

echo run aws s3 sync $SCRIPT_DIR/nv-staging/Isaac s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/Isaac --delete
aws s3 sync $SCRIPT_DIR/nv-staging/Isaac s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER/Isaac --delete

echo run aws s3 sync s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER s3://omniverse-content-production/Assets/Isaac/$ISAAC_VER --delete
aws s3 sync s3://omniverse-content-staging/Assets/Isaac/$ISAAC_VER s3://omniverse-content-production/Assets/Isaac/$ISAAC_VER --delete
