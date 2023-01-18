#!/bin/bash
# must be run where tools/packman is.
shopt -s extglob
DOV_IN="/home/mcarlson/gitlab-master/drivesim-ov_mcarlson"
CWD=$(pwd)
PACKAGENAME="drivesim_b4050e054e2-kit_104.2+release.39.145ad340-RTXSensor05"
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

cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.beams/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.common/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.ids/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.lidar/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.lidar_tools/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.materials/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.material_tools/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.radar/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.ultrasonic/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.sensors.nv.wpm/ linux-x86_64

# delete configs that are propiatary 
cd linux-x86_64/omni.sensors.nv.radar/data/dmat_approx
rm -v -- !(Example*)
cd -
cd linux-x86_64/omni.sensors.nv.radar/data/wpm_dmat_approx
rm -v -- !(Example*)
cd -
cd linux-x86_64/omni.sensors.nv.ultrasonic/data
rm -v -- !(Example*)
cd -

# get the material files
mkdir data
cp -rflv $DOV_IN/_build/linux-x86_64/release/data/material_files/ data/.

# copy to local repo then package and send out.
cp -rflv $CWD/nvsensor/$PACKAGENAME/ /home/mcarlson/packman-repo/chk/nvsensor

cd $DOV_IN
./tools/packman/packman pack $CWD/nvsensor/$PACKAGENAME/
./tools/packman/packman push -f $CWD/nvsensor/nvsensor@$PACKAGENAME.7z
