#!/bin/bash
# This script grabs the headers from a drivesim repo that isaac-sim depends on.  Use it when upgrading the 
# omni.sensor extensions.
# This file is used for the released branches of isaac-sim.
# If you want to build the new versions of omni.sensors then you are looking for the sensors_prep_build.sh
# script, which is used to build the omni.sensors extensions in isaac-sim.
# branch mcarlson/omni.sensors-1000.1-0-isaacsim.2024.1.0
# using drivesim-ov hash: c5ef2973b27adc0ea9f2a73dff0860d8dd43e1fc
shopt -s extglob
OMNI_SENSORS_FOLDER="/home/mcarlson/gitlab-master/drivesim-ov_autosimulator"

# headers
mkdir -p include/omni/sensors
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/Settings.h include/omni/sensors/Settings.h
# note where this one comes from.  If we could build with extscache deps then we may be able to put the header in the extension.
cp -flv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.lidar/plugins/converter/LidarPointsConvert.h include/omni/sensors/.

mkdir -p include/omni/sensors/cuda
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/cuda/CudaHelperMath.h include/omni/sensors/cuda/CudaHelperMath.h
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/cuda/CudaHelperDecl.h include/omni/sensors/cuda/CudaHelperDecl.h

mkdir -p include/omni/sensors/lidar
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/lidar/LidarReturnTypes.h include/omni/sensors/lidar/LidarReturnTypes.h
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/lidar/LidarReturn.h include/omni/sensors/lidar/LidarReturn.h
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/lidar/LidarProfileTypes.h include/omni/sensors/lidar/LidarProfileTypes.h
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/lidar/LidarPoint.h include/omni/sensors/lidar/LidarPoint.h
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/lidar/LidarParameterType.h include/omni/sensors/lidar/LidarParameterType.h
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/lidar/ILidarProfileReaderFactory.h include/omni/sensors/lidar/ILidarProfileReaderFactory.h
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/lidar/ILidarProfileReader.h include/omni/sensors/lidar/ILidarProfileReader.h
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/lidar/ILidarPCConverter.h include/omni/sensors/lidar/ILidarPCConverter.h

mkdir -p include/omni/sensors/materials
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/materials/MaterialProperties.h include/omni/sensors/materials/MaterialProperties.h

mkdir -p include/omni/sensors/radar
cp -flv $OMNI_SENSORS_FOLDER/include/omni/sensors/radar/IRadarPCConverter.h include/omni/sensors/radar/IRadarPCConverter.h

mkdir -p source/include/internal/omni/sensors
cp -flv $OMNI_SENSORS_FOLDER/source/include/internal/omni/sensors/Utils.h source/include/internal/omni/sensors/Utils.h

mkdir -p source/include/internal/omni/sensors/lidar
cp -flv $OMNI_SENSORS_FOLDER/source/include/internal/omni/sensors/lidar/LidarIntensityMapping.h source/include/internal/omni/sensors/lidar/LidarIntensityMapping.h
cp -flv $OMNI_SENSORS_FOLDER/source/include/internal/omni/sensors/lidar/LidarReturnHelper.h source/include/internal/omni/sensors/lidar/LidarReturnHelper.h
cp -flv $OMNI_SENSORS_FOLDER/source/include/internal/omni/sensors/lidar/LidarSettings.h source/include/internal/omni/sensors/lidar/LidarSettings.h

#data 
mkdir -p data/sensors/ids
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/ids/*.json data/sensors/ids/.
mkdir -p data/sensors/materials
cp -rflv $OMNI_SENSORS_FOLDER/data/sensors/materials/material_files data/sensors/materials/.
mkdir -p data/sensors/lidar
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/lidar/Example*.json data/sensors/lidar/.
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/lidar/Velodyne_VLS128.json source/extensions/omni.isaac.sensor/data/lidar_configs/Velodyne/.
mkdir -p data/sensors/radar/wpm_dmat_approx
mkdir -p data/sensors/radar/dmat_approx
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/radar/wpm_dmat_approx/Example.json data/sensors/radar/wpm_dmat_approx/.
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/radar/dmat_approx/Example.json data/sensors/radar/dmat_approx/.
mkdir -p data/sensors/ultrasonic/wpm_ultrasonic_interference
mkdir -p data/sensors/ultrasonic/wpm_ultrasonic
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/ultrasonic/wpm_ultrasonic_interference/Example.json data/sensors/ultrasonic/wpm_ultrasonic_interference/.
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/ultrasonic/wpm_ultrasonic/Example.json data/sensors/ultrasonic/wpm_ultrasonic/.
mkdir -p data/sensors/material_tools/configuration
#note folder change
cp -flv $OMNI_SENSORS_FOLDER/source/extensions/omni.sensors.nv.material_tools/configuration/parameters.json data/sensors/material_tools/configuration/.

