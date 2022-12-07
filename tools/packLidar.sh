#!/bin/bash
# must be run where tools/packman is.
shopt -s extglob
DOV_IN="/home/mcarlson/gitlab-master/drivesim-ov_mcarlson"
CWD=$(pwd)
PACKAGENAME="drivesim_d67a50de13-kit_104.1+release.328.d5a5ff0c-RTXSensor05"
echo $PACKAGENAME
mkdir -p $CWD/nvsensor
mkdir -p $CWD/nvsensor/$PACKAGENAME
cd $CWD/nvsensor/$PACKAGENAME
mkdir include
mkdir include/internal
mkdir include/internal/omni
mkdir include/internal/omni/drivesim
mkdir include/internal/omni/drivesim/sensors
mkdir include/internal/omni/drivesim/sensors/common
mkdir include/internal/omni/drivesim/sensors/lidar
mkdir include/omni
mkdir include/omni/sensors
mkdir include/omni/drivesim
mkdir include/omni/drivesim/sensors
mkdir include/omni/drivesim/utils
mkdir include/omni/drivesim/utils/cuda
mkdir linux-x86_64

cp -vf $DOV_IN/source/include/internal/omni/drivesim/sensors/lidar/LidarSettings.h include/internal/omni/drivesim/sensors/lidar/.
cp -vf $DOV_IN/include/omni/sensors/settings.h include/omni/sensors/.
cp -vf $DOV_IN/source/include/internal/omni/drivesim/sensors/common/Utils.h include/internal/omni/drivesim/sensors/common/.
cp -vf $DOV_IN/source/extensions/omni.drivesim.sensors.nv.lidar_tools/plugins/converter/LidarPointsConvert.h include/omni/sensors/.
cp -vf $DOV_IN/include/omni/drivesim/utils/cuda/CudaHelperMath.h include/omni/drivesim/utils/cuda/.
cp -vf $DOV_IN/include/omni/drivesim/utils/cuda/CudaHelperDecl.h include/omni/drivesim/utils/cuda/.

cp -rflv $DOV_IN/include/omni/drivesim/sensors/ include/omni/drivesim/.
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.buffer/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.beams/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.common/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.ids/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.lidar/ linux-x86_64
cd linux-x86_64/omni.drivesim.sensors.nv.lidar/data
rm -v -- !(Example*)
cd -
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.lidar_tools/ linux-x86_64
cd linux-x86_64/omni.drivesim.sensors.nv.lidar_tools/data
rm -v -- !(Example*)
cd -
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.materials/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.material_tools/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.radar/ linux-x86_64
cd linux-x86_64/omni.drivesim.sensors.nv.radar/data/dmat_approx
rm -v -- !(Example*)
cd -
cd linux-x86_64/omni.drivesim.sensors.nv.radar/data/wpm_dmat_approx
rm -v -- !(Example*)
cd -
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.radar_tools/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.samples/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.ultrasonic/ linux-x86_64
cd linux-x86_64/omni.drivesim.sensors.nv.ultrasonic/data
rm -v -- !(Example*)
cd -
cp -rflv $DOV_IN/_build/linux-x86_64/release/exts/omni.drivesim.sensors.nv.wpm/ linux-x86_64
cp -rflv $DOV_IN/_build/linux-x86_64/release/data/material_files/ .

# copy to local repo then package and send out.
cp -rflv $CWD/nvsensor/$PACKAGENAME/ /home/mcarlson/packman-repo/chk/nvsensor

cd $DOV_IN
./tools/packman/packman pack $CWD/nvsensor/$PACKAGENAME/
./tools/packman/packman push -f $CWD/nvsensor/nvsensor@$PACKAGENAME.7z
