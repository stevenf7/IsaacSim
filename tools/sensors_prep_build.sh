#!/bin/bash
#   The drivesim codebase holds the omni.sensors extensions.  Normal workflow is to build those extensions there, but
# in order to share those extensions with isaac-sim, it is necessary to build with the same kit version as isaac-sim.
#   This script copies over all the omni.sensors extensions from a drivesim repo to the isaac-sim one.  In the 
# premake5.lua file, you will want to set build_with_omni_sensors=true.
# branch git checkout mcarlson/build_omni_sensors_1000.1.0-isaacsim.2024.1.0
# using drivesim-ov hash: c5ef2973b27adc0ea9f2a73dff0860d8dd43e1fc
# ./repo.sh publish_exts -c release

shopt -s extglob
OMNI_SENSORS_FOLDER="/home/mcarlson/gitlab-master/drivesim-ov_autosimulator"

# uncomment to reset
rm -rf data
rm -rf source/include
rm -rf include/omni/sensors
rm -rf include/omni/drivesim
rm -rf source/extensions/omni.sensors.fov_preview_visualization
rm -rf source/extensions/omni.sensors.nv.beams
rm -rf source/extensions/omni.sensors.nv.camera
rm -rf source/extensions/omni.sensors.nv.common
rm -rf source/extensions/omni.sensors.nv.ids
rm -rf source/extensions/omni.sensors.nv.lidar
rm -rf source/extensions/omni.sensors.nv.lidar_tools
rm -rf source/extensions/omni.sensors.nv.materials
rm -rf source/extensions/omni.sensors.nv.material_tools
rm -rf source/extensions/omni.sensors.nv.radar
rm -rf source/extensions/omni.sensors.nv.radar_tools
rm -rf source/extensions/omni.sensors.nv.ultrasonic
rm -rf source/extensions/omni.sensors.nv.wpm

# extensions we want to build.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.fov_preview_visualization source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.beams source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.camera source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.common source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.ids source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.lidar source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.lidar_tools source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.materials source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.material_tools source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.radar source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.radar_tools source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.ultrasonic source/extensions/.
cp -rflv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.wpm source/extensions/.

# headers
mkdir -p source/include/internal/omni/drivesim
cp -rflv $OMNI_SENSORS_FOLDER/source/include/internal/omni/sensors source/include/internal/omni/.
cp -rflv $OMNI_SENSORS_FOLDER/source/include/internal/omni/drivesim/sensors source/include/internal/omni/drivesim/.
cp -rflv $OMNI_SENSORS_FOLDER/source/include/internal/omni/drivesim/net source/include/internal/omni/drivesim/.

cp -rflv $OMNI_SENSORS_FOLDER/include/omni/sensors include/omni/.
cp -rflv $OMNI_SENSORS_FOLDER/include/omni/drivesim include/omni/.

cp -flv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.lidar/plugins/converter/LidarPointsConvert.h include/omni/sensors/.

#data 
mkdir -p data/sensors/materials
cp -rflv $OMNI_SENSORS_FOLDER/data/sensors/lidar data/sensors/.
cp -rflv $OMNI_SENSORS_FOLDER/data/sensors/radar data/sensors/.
cp -rflv $OMNI_SENSORS_FOLDER/data/sensors/ultrasonic data/sensors/.
cp -rflv $OMNI_SENSORS_FOLDER/data/sensors/materials/material_files data/sensors/materials/.

# remove ip
rm -rfv source/include/internal/omni/sensors/radar/encoders/SOMEIPNCD
# too big
rm -fv source/extensions/omni.sensors.nv.wpm/docs/images/EmPulse.apng 

echo "Remove the pip_prebundle from common extension.toml file."
echo "fix path in source/extensions/omni.sensors.nv.material_tools/python/nodes/MaterialAnalyzer.py"