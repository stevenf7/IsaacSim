#!/usr/bin/env bash

set -e

OMNICLI=~/.local/share/ov/pkg/prod-connectsample-203.0.0/omnicli.sh
SCRIPT_DIR="$(dirname "$(realpath $0)")"/../../_assets


echo Removing $SCRIPT_DIR/Isaac_AMR...
rm -rf $SCRIPT_DIR/Isaac_AMR
echo run $OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Samples/Isaac_AMR/2.1 $SCRIPT_DIR/Isaac_AMR/2.1
$OMNICLI copy omniverse://isaac-dev.ov.nvidia.com/Isaac/Samples/Isaac_AMR/2.1 $SCRIPT_DIR/Isaac_AMR/2.1

echo run aws s3 sync $SCRIPT_DIR/Isaac_AMR s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete
aws s3 sync $SCRIPT_DIR/Isaac_AMR s3://omniverse-content-staging/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete

echo run aws s3 sync $SCRIPT_DIR/Isaac_AMR s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete
aws s3 sync $SCRIPT_DIR/Isaac_AMR s3://omniverse-content-production/Assets/Isaac/2022.2.1/Isaac/Samples/Isaac_AMR --delete
