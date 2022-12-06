#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
"$SCRIPT_DIR/../../../packman/packman" install connect-samples-launcher 445-linux-x86_64 -l $SCRIPT_DIR/../../../../_build/_omnicli
OMNICLI="$SCRIPT_DIR/../../../../_build/_omnicli/omnicli.sh"

echo Removing _assets_temp...
rm -rf $SCRIPT_DIR/../../../../_assets_temp
echo "##teamcity[progressMessage 'Downloading /Isaac/Environments/...']"
$OMNICLI copy omniverse://ov-isaac-dev.nvidia.com/Isaac/Environments $SCRIPT_DIR/../../../../_assets_temp/Isaac/Environments
echo "##teamcity[progressMessage 'Downloading /Isaac/Materials/...']"
$OMNICLI copy omniverse://ov-isaac-dev.nvidia.com/Isaac/Materials $SCRIPT_DIR/../../../../_assets_temp/Isaac/Materials
echo "##teamcity[progressMessage 'Downloading /Isaac/Props/...']"
$OMNICLI copy omniverse://ov-isaac-dev.nvidia.com/Isaac/Props $SCRIPT_DIR/../../../../_assets_temp/Isaac/Props
echo "##teamcity[progressMessage 'Downloading /Isaac/Robots/...']"
$OMNICLI copy omniverse://ov-isaac-dev.nvidia.com/Isaac/Robots $SCRIPT_DIR/../../../../_assets_temp/Isaac/Robots
echo "##teamcity[progressMessage 'Downloading /Isaac/Samples/...']"
$OMNICLI copy omniverse://ov-isaac-dev.nvidia.com/Isaac/Samples $SCRIPT_DIR/../../../../_assets_temp/Isaac/Samples

# Packaging assets
echo "##teamcity[progressMessage 'Packaging isaac-sim-assets...']"
"$SCRIPT_DIR/../../../../repo.sh" package -m isaac-sim-assets

# publish artifacts to teamcity
echo "##teamcity[publishArtifacts '_build/packages']"