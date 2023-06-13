#!/bin/bash
# must be run where tools/packman is.
# 1) ./build.sh -r
# 2) ./build.sh -d

shopt -s extglob
DOV_IN="/home/mcarlson/gitlab-master/drivesim-ov_mcarlson"
BUILD_TYPE="debug"
CWD=$(pwd)
PACKAGENAME="nvsensors105-dev6.$BUILD_TYPE"
# dev 6 based on ce1fdff41003c91c321255848aaee474e1f60d03  (no changes from 5)
#"nvsensors105-dev2" based on 14214b7866d2af14807939f482c74830d0da48d8
# PACKAGENAME="nvsensors105-dev1" based on aeabc8a02dd266af066a186b2bdcd6761854b0a4
echo $PACKAGENAME
mkdir -p $CWD/nvsensor
mkdir -p $CWD/nvsensor/$PACKAGENAME
cd $CWD/nvsensor/$PACKAGENAME
mkdir include
mkdir include/omni
mkdir include/omni/sensors
cp -rflv $DOV_IN/include/omni/sensors/ include/omni/.
cp -vf $DOV_IN/source/extensions/omni.sensors.nv.lidar/plugins/converter/LidarPointsConvert.h include/omni/sensors/.

mkdir include/internal
mkdir include/internal/omni
mkdir include/internal/omni/sensors
cp -rflv $DOV_IN/source/include/internal/omni/sensors/ include/internal/omni/.

# kill any header with a brand
rm -rfv ./include/internal/omni/sensors/radar/encoders/ContiARS430RDI
rm -v ./include/internal/omni/sensors/lidar/HesaiPacketTypes.h
rm -rfv ./include/internal/omni/sensors/lidar/encoders/Luminar
rm -rfv ./include/internal/omni/sensors/lidar/encoders/Velodyne
rm -rfv ./include/internal/omni/sensors/lidar/encoders/Hesai
rm -v ./include/internal/omni/sensors/lidar/decoders/LuminarDecoder.h
rm -v ./include/internal/omni/sensors/lidar/decoders/HesaiDecoder.h
rm -v ./include/internal/omni/sensors/lidar/LuminarNCDTypeHelper.h
rm -v ./include/internal/omni/sensors/lidar/HesaiBackChannel.h
rm -v ./include/internal/omni/sensors/lidar/Luminar*

mkdir linux-x86_64
mkdir linux-x86_64/$BUILD_TYPE

cp -rflv $DOV_IN/_build/linux-x86_64/$BUILD_TYPE/exts/ linux-x86_64/$BUILD_TYPE

# delete configs that are propiatary 
rm -rfv linux-x86_64/$BUILD_TYPE/exts/omni.sensors.nv.radar/data
rm -rfv linux-x86_64/$BUILD_TYPE/exts/omni.sensors.nv.lidar/data
rm -rfv linux-x86_64/$BUILD_TYPE/exts/omni.sensors.nv.lidar_tools/data

# get the material files
# must be data/material_files path or won't find the material.
mkdir data
cp -rflv $DOV_IN/_build/linux-x86_64/$BUILD_TYPE/data/material_files/ data/.
# get the example configuration files.
mkdir data/lidar
cp -vf $DOV_IN/data/sensors/lidar/Example*.json data/lidar/.
mkdir data/radar
mkdir data/radar/wpm_dmat_approx
cp -vf $DOV_IN/data/sensors/radar/wpm_dmat_approx/Example.json data/radar/wpm_dmat_approx/.
mkdir data/radar/dmat_approx
cp -vf $DOV_IN/data/sensors/radar/dmat_approx/Example.json data/radar/dmat_approx/.
mkdir data/ultrasonic
cp -vf $DOV_IN/data/sensors/ultrasonic/Example.json data/ultrasonic/.

# copy to local repo then package and send out.
#cp -rflv $CWD/nvsensor/$PACKAGENAME/ /home/mcarlson/packman-repo/chk/nvsensor

cd $DOV_IN
./tools/packman/packman pack $CWD/nvsensor/$PACKAGENAME/
./tools/packman/packman push -f $CWD/nvsensor/nvsensor@$PACKAGENAME.7z
