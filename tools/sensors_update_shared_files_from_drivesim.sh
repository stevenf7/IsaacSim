#!/bin/bash
# This script grabs the headers from a drivesim repo that isaac-sim depends on.  Use it when upgrading the 
# omni.sensor extensions.
# This file is used for the released branches of isaac-sim.
# If you want to build the new versions of omni.sensors then you are looking for the sensors_prep_build.sh
# script, which is used to build the omni.sensors extensions in isaac-sim.
# using drivesim-ov hash: 066b16db966ffa9e1cc4fbe4e17fa47dde6d2e3c
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
mkdir -p data/sensors/materials
cp -rflv $OMNI_SENSORS_FOLDER/data/sensors/materials/material_files data/sensors/materials/.
mkdir -p data/sensors/lidar
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/lidar/Example*.json data/sensors/lidar/.
mkdir -p data/sensors/radar/wpm_dmat_approx
mkdir -p data/sensors/radar/dmat_approx
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/radar/wpm_dmat_approx/Example.json data/sensors/radar/wpm_dmat_approx/.
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/radar/dmat_approx/Example.json data/sensors/radar/dmat_approx/.
mkdir -p data/sensors/ultrasonic/wpm_ultrasonic_interference
mkdir -p data/sensors/ultrasonic/wpm_ultrasonic
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/ultrasonic/wpm_ultrasonic_interference/Example.json data/sensors/ultrasonic/wpm_ultrasonic_interference/.
cp -flv $OMNI_SENSORS_FOLDER/data/sensors/ultrasonic/wpm_ultrasonic/Example.json data/sensors/ultrasonic/wpm_ultrasonic/.

