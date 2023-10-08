#!/usr/bin/env bash

set -e

OMNICLI=~/.local/share/ov/pkg/prod-connectsample-203.0.0/omnicli.sh
TEMP_DIR="$(dirname "$(realpath $0)")"/../../_assets


echo Removing $TEMP_DIR/amr-2022.2.1/Isaac_AMR...
rm -rf $TEMP_DIR/amr-2022.2.1/Isaac_AMR

echo run $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Projects/isaac_amr_envoy/Staging_2.1/ $TEMP_DIR/amr-2022.2.1/Isaac_AMR/
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Projects/isaac_amr_envoy/Staging_2.1/ $TEMP_DIR/amr-2022.2.1/Isaac_AMR/

echo run aws s3 sync $TEMP_DIR/amr-2022.2.1/Isaac_AMR s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete
aws s3 sync $TEMP_DIR/amr-2022.2.1/Isaac_AMR s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete

echo run aws s3 sync s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR  s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete
aws s3 sync s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR  s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete


echo Removing $TEMP_DIR/amr-2022.2.1/carter_v2_4.usd...
if [ -f "TEMP_DIR/amr-2022.2.1/carter_v2_4.usd" ]; then
    rm $TEMP_DIR/amr-2022.2.1/carter_v2_4.usd
fi
echo run $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots/Carter/carter_v2_4.usd $TEMP_DIR/amr-2022.2.1/carter_v2_4.usd
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots/Carter/carter_v2_4.usd $TEMP_DIR/amr-2022.2.1/carter_v2_4.usd

echo run aws s3 cp $TEMP_DIR/amr-2022.2.1/carter_v2_4.usd s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd
aws s3 cp $TEMP_DIR/amr-2022.2.1/carter_v2_4.usd s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd

echo run aws s3 cp s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd
aws s3 cp s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd


echo Removing $TEMP_DIR/amr-2022.2.1/Carter_V2_4/
rm -rf $TEMP_DIR/amr-2022.2.1/Carter_V2_4/
echo run $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots/Carter/Carter_V2_4/ $TEMP_DIR/amr-2022.2.1/Carter_V2_4/
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots/Carter/Carter_V2_4/ $TEMP_DIR/amr-2022.2.1/Carter_V2_4/

echo run aws s3 sync $TEMP_DIR/amr-2022.2.1/Carter_V2_4/ s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/ --delete
aws s3 sync $TEMP_DIR/amr-2022.2.1/Carter_V2_4/ s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/ --delete

echo run aws s3 sync s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/ s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/ --delete
aws s3 sync s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/ s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/ --delete

echo !! Completed!

