#!/usr/bin/env bash

set -e

OMNICLI=~/.local/share/ov/pkg/prod-connectsample-203.0.0/omnicli.sh
TEMP_DIR="$(dirname "$(realpath $0)")"/../../_assets


echo Removing $TEMP_DIR/nvblox-2022.2.1/NvBlox...
rm -rf $TEMP_DIR/nvblox-2022.2.1/NvBlox

echo run $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Samples/NvBlox/ $TEMP_DIR/nvblox-2022.2.1/NvBlox/
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Samples/NvBlox/ $TEMP_DIR/nvblox-2022.2.1/NvBlox/

echo run aws s3 sync $TEMP_DIR/nvblox-2022.2.1/Isaac_AMR s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/NvBlox --delete
aws s3 sync $TEMP_DIR/nvblox-2022.2.1/Isaac_AMR s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/NvBlox --delete

echo run aws s3 sync s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/NvBlox  s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Samples/NvBlox --delete
aws s3 sync s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/NvBlox  s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Samples/NvBlox --delete
