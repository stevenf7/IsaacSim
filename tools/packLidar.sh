#!/bin/bash
# must be run where tools/packman is.
DOV_IN="/home/mcarlson/gitlab-master/drivesim-ov"
CWD=$(pwd)
PACKAGENAME="0596cfe606_kitfdbc4586_RTXSensor05"
echo $PACKAGENAME
mkdir -p $CWD/nvlidar
mkdir -p $CWD/nvlidar/$PACKAGENAME
cd $CWD/nvlidar/$PACKAGENAME
mkdir include
mkdir include/common
mkdir include/lidar
mkdir linux-x86_64
cp -v $DOV_IN/include/omni/drivesim/sensors/lidar/LidarParameterType.h include/lidar/.
cp -v $DOV_IN/include/omni/drivesim/sensors/lidar/LidarReturnTypes.h include/lidar/.
cp -v $DOV_IN/include/omni/drivesim/sensors/common/SyncData.h include/common/.
cp -rlv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.common/ linux-x86_64
cp -rlv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.lidar/ linux-x86_64
cp -rlv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.materials/ linux-x86_64
cp -rlv $DOV_IN/_build/linux-x86_64/release/data/material_files/ .
cd linux-x86_64/omni.drivesim.sensors.nv.lidar/data
shopt -s extglob
rm -v -- !(Example*)
cd $DOV_IN
./tools/packman/packman pack $CWD/nvlidar/$PACKAGENAME/
./tools/packman/packman push $CWD/nvlidar/nvlidar@$PACKAGENAME.7z
