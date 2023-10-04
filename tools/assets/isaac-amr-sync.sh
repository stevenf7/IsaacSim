#!/usr/bin/env bash

set -e

OMNICLI=~/.local/share/ov/pkg/prod-connectsample-203.0.0/omnicli.sh
SCRIPT_DIR="$(dirname "$(realpath $0)")"/../../_assets


echo Removing $SCRIPT_DIR/Isaac_AMR...
rm -rf $SCRIPT_DIR/Isaac_AMR

echo run $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Projects/isaac_amr_envoy/Staging_2.1/ $SCRIPT_DIR/Isaac_AMR/
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Projects/isaac_amr_envoy/Staging_2.1/ $SCRIPT_DIR/Isaac_AMR/

echo run aws s3 sync $SCRIPT_DIR/Isaac_AMR s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete
aws s3 sync $SCRIPT_DIR/Isaac_AMR s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete

echo run aws s3 sync $SCRIPT_DIR/Isaac_AMR s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete
aws s3 sync $SCRIPT_DIR/Isaac_AMR s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete

echo Removing $SCRIPT_DIR/carter_v2_4.usd...
rm $SCRIPT_DIR/carter_v2_4.usd
echo run $OMNICLI cp omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots/Carter/carter_v2_4.usd $SCRIPT_DIR/carter_v2_4.usd
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots/Carter/carter_v2_4.usd $SCRIPT_DIR/carter_v2_4.usd

echo run aws s3 cp $SCRIPT_DIR/carter_v2_4.usd s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd
aws s3 cp $SCRIPT_DIR/carter_v2_4.usd s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd

echo run aws s3 cp $SCRIPT_DIR/carter_v2_4.usd s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd
aws s3 cp $SCRIPT_DIR/carter_v2_4.usd s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/carter_v2_4.usd

echo Removing $SCRIPT_DIR/Carter_V2_4/
rm $SCRIPT_DIR/Carter_V2_4/
echo run $OMNICLI cp omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots/Carter/Carter_V2_4/ $SCRIPT_DIR/Carter_V2_4/
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots/Carter/Carter_V2_4/ $SCRIPT_DIR/Carter_V2_4/

echo run aws s3 cp $SCRIPT_DIR/carter_v2_4.usd s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/
aws s3 cp $SCRIPT_DIR/carter_v2_4.usd s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/

echo run aws s3 cp $SCRIPT_DIR/carter_v2_4.usd s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/
aws s3 cp $SCRIPT_DIR/carter_v2_4.usd s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Robots/Carter/Carter_V2_4/