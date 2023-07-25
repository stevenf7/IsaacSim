// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

namespace omni
{
namespace sensors
{
namespace nv
{

/*
 * Enable/disable determistic realm for ECU network channels
 *
 * Default: true
 * Examples: --/app/sensors/nv/determisticRealm/enabled=true
 */
constexpr char kSettingDetermisticRealm[] = "/app/sensors/nv/determisticRealm/enabled";

/*
 * Set to true to enable motion BVH for sensor motion effects
 *
 * Default: true
 * Examples: --/renderer/raytracingMotion/enabled=true
 */
constexpr char kSettingMotionBvh[] = "/renderer/raytracingMotion/enabled";


/*
 * Contains the a string with mappings from material name to id of the material.
 *
 * Default: ""
 * Examples:
 * --/rtx/materialDb/rtSensorNameToIdMap="DefaultMaterial:0;AsphaltStandardMaterial:1;AsphaltWeatheredMaterial:2;VegetationGrassMaterial:3;WaterStandardMaterial:4;GlassStandardMaterial:5;FiberGlassMaterial:6;MetalAlloyMaterial:7;MetalAluminumMaterial:8;MetalAluminumOxidizedMaterial:9;PlasticStandardMaterial:10;RetroMarkingsMaterial:11;RetroSignMaterial:12;RubberStandardMaterial:13;SoilClayMaterial:14;ConcreteRoughMaterial:15;ConcreteSmoothMaterial:16;OakTreeBarkMaterial:17;FabricStandardMaterial:18;PlexiGlassStandardMaterial:19;MetalSilverMaterial:20"
 */
constexpr char kSettingMaterialMapping[] = "/rtx/materialDb/rtSensorNameToIdMap";

////// Radar //////

/*
 * Set to true to force radar sensors to run even if motion BVH is disabled, they will run without motion effects
 *
 * Default: false
 * Examples: --/app/sensors/nv/radar/runWithoutMBVH=true
 */
constexpr char kSettingRunRadarWithoutMBVH[] = "/app/sensors/nv/radar/runWithoutMBVH";

/*
 * Set to true to enable ground truth output for radar sensors
 *
 * Default: false
 * Examples: --/app/sensors/nv/radar/enableGT=true
 */
constexpr char kSettingEnableRadarGT[] = "/app/sensors/nv/radar/enableGT";

/*
 * Set to true to skip sorting of detection list produced by radar sensors
 *
 * Default: false
 * Examples: --/app/sensors/nv/radar/skipDetectionsSorting=true
 */
constexpr char kSettingSkipDetectionsSorting[] = "/app/sensors/nv/radar/skipDetectionsSorting";

////// Atmospherics ///////

/*
 * Sets the rain rate [mm/h] for the atmospherics simulation model. 0.0 deactivates rain based atmospheric modeling
 *
 * Examples: --/app/sensors/nv/atmospherics/rainRate=0.05
 */
constexpr char kAtmosRainRateSetting[] = "/app/sensors/nv/atmospherics/rainRate";

/*
 * Sets the threshold for false positive rain drop hits in the atmospherics.
 *
 * Examples: --/app/sensors/nv/atmospherics/rainDropHitThresh=0.015
 */
constexpr char kAtmosRainDropHitSetting[] = "/app/sensors/nv/atmospherics/rainDropHitThresh";

/*
 * Sets value for aerosol model in the atmospherics simulation, while a value of 0 deactivates the aerosolmodel.
 *
 * Examples: --/app/sensors/nv/atmospherics/aerosolModel=2.
 */
constexpr char kAtmosAeroSolModelSetting[] = "/app/sensors/nv/atmospherics/aerosolModel";

/*
 * Sets sun azimuth angle in degrees for aerosolmodel.
 *
 * Examples: --/app/sensors/nv/atmospherics/sunAzimuth=10.
 */
constexpr char kAtmosSunAzimuthSetting[] = "/app/sensors/nv/atmospherics/sunAzimuth";

/*
 * Sets sun elevation angle in degrees for aerosolmodel.
 *
 * Examples: --/app/sensors/nv/atmospherics/sunElevation=10.
 */
constexpr char kAtmosSunElevationSetting[] = "/app/sensors/nv/atmospherics/sunElevation";

/*
 * Sets the fractional amount of direct solar illumination to be applied
 *
 * Examples: --/app/sensors/nv/atmospherics/directSolarFraction=1.
 */
constexpr char kAtmosDirectSolarFractionSetting[] = "/app/sensors/nv/atmospherics/directSolarFraction";

////// LiDAR //////

/*
 * Sets additional base folders where lidar profiles are read from.
 *
 * Examples: --/app/sensors/nv/lidar/profileBaseFolder=["path_to_base_folder"]
 *           --/app/sensors/nv/lidar/profileBaseFolder=["path_to_base_folder","another_base_folder"]
 */
constexpr char kLidarBaseFolderSetting[] = "/app/sensors/nv/lidar/profileBaseFolder";

/*
 * Enables velocity information for lidar point. Default is false for better runtime
 *
 * Examples: --/app/sensors/nv/lidar/enableVelocity=true
 * Default: disabled (setting not defined)
 */
constexpr char kLidarEnableVelocitySetting[] = "/app/sensors/nv/lidar/enableVelocity";


/*
 * Add additional default material variants with corresponding reflectance factors.
 *
 * Examples: --/app/sensors/nv/materials/extraDefaultMaterialFactors=[0.05,0.1,0.84]
 */
constexpr char kDefaultMaterialsFactorsSetting[] = "/app/sensors/nv/materials/extraDefaultMaterialFactors";

/*
 * Adds lobewidth parameter to extra default materials.
 *
 * Examples: --/app/sensors/nv/materials/extraDefaultMaterialLobeWidths=[0.92,0.1,0.4]
 */
constexpr char kDefaultMaterialsLobewidthsSetting[] = "/app/sensors/nv/materials/extraDefaultMaterialLobeWidths";

/*
 * Control setting for back face culling of intersected geometries within the scene.
 *
 * Examples: --/app/sensors/nv/lidar/cullBackFace=true
 */
constexpr char kSettingCullBackFace[] = "/app/sensors/nv/lidar/cullBackFace";

/*
 * Enable viz for lidar rig component sensor as follows
 * --/app/sensors/nv/lidar_#port/vizOnly= [true if no ecu is desired]
 * --/app/sensors/nv/lidar_#port/vizDataId= [-> has to be unique and between 0-10]
 * --/app/sensors/nv/lidar_#port/vizTransformation= [x,y,z,roll,pitch,yaw] [-> if not given then, the sensor mount will
 * be used]
 * --/app/sensors/nv/lidar_#port/colorCode= [0 - constant, 1 - intensity, 2 - height, 3 - range, 4 - objectId, 5 -
 * echoId, 6 - materialId]
 */


////// Ultrasonic //////

/**
 * Set to "<sensor_id>:<error_code>..." to inject errors into USS diagnostic data stream
 *
 * Default: ""
 * Examples: --/app/sensors/nv/ultrasonic/sensor_errors="1:12,4:12"
 */
constexpr char kSettingUltrasonicErrors[] = "/app/sensors/nv/ultrasonic/sensor_errors";

constexpr char kSettingUltrasonicRigVizDataId[] = "/app/sensors/nv/ultrasonic/rigVizDataId";
constexpr char kSettingUltrasonicRigVizAveragePeriod[] = "/app/sensors/nv/ultrasonic/rigVizAveragePeriod";
constexpr char kSettingUltrasonicRigVizOnly[] = "/app/sensors/nv/ultrasonic/rigVizOnly";

////// MemoryHandler FramesInFlight //////

/**
 * That is a constructed setting with the format /app/sensors/nv/<modality>/framesInFlight=<value>
 * modality can be (lidar, radar, ultrasonic, all)
 * value is the number of concurrent frames in flight
 *
 * Sets the frames in flight setting for a specific sensor modality (ex: radar) or for all,
 * if not set the default of the renderer will be used (currently 3), if set to 1 this means the sensor(s)
 * shouldn't multiply their buffers and the old syncWait mechanism will be active
 *
 * Default: "3"
 * Examples: --/app/sensors/nv/all/framesInFlight=3
 *           --/app/sensors/nv/radar/framesInFlight=1
 *
 * the above examples can be concurrent, user can set a setting for all sensors and override only for radar
 */

////// sensors file dump //////

// TODO: rename to match other sensor settings
/**
 * That is a constructed setting with the format /app/sensors/<modality>/<fileFormat>=<path>
 * modality can be (lidar, radar, ultrasonic, camera, all)
 * fileFormat can be (genericFilePath, dwBinFilePath, pcapFilePath, numpyFilePath)
 * path is the path where the file will be dumped
 *
 * enables dumping of sensor streams for a specific sensor modality or for all, the stream format can also
 * be set, there will be a file dump for each "sensor instance"
 *
 * Default: "" (empty = dumping disabled)
 * Examples: --/app/sensors/all/dwBinFilePath="recordings/all"
 *           --/app/sensors/radar/dwBinFilePath="recordings/radar"
 *
 * the above examples can be concurrent, user can set a setting for all sensors and override only for radar
 */

} // namespace nv
} // namespace sensors
} // namespace omni
