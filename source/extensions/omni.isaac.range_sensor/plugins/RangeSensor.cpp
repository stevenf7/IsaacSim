// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include <pch/UsdPCH.h>
#include <pxr/usd/usd/inherits.h>
#include <omni/usd/UtilsIncludes.h>
// clang-format on

#include "core/RangeSensorManager.h"
#include "generic/GenericSensor.h"
#include "lidar/LidarSensor.h"
#include "ultrasonic/UltrasonicSensor.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/tasking/ITasking.h>

#include <omni/fabric/FabricUSD.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/kit/KitUtils.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/physx/IPhysx.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdUtils.h>

#include <RangeSensorInterface.h>
#include <map>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.range_sensor.plugin", "Isaac Range Sensor", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl,
                 omni::isaac::range_sensor::LidarSensorInterface,
                 omni::isaac::range_sensor::UltrasonicSensorInterface,
                 omni::isaac::range_sensor::GenericSensorInterface)


CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx,
                      omni::kit::IStageUpdate,
                      omni::fabric::IStageReaderWriter,
                      omni::syntheticdata::SyntheticData,
                      carb::tasking::ITasking,
                      omni::graph::core::IGraphRegistry)

DECLARE_OGN_NODES()


// private stuff
namespace
{


omni::kit::StageUpdatePtr g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
omni::physx::IPhysx* g_physx = nullptr;
pxr::UsdStageWeakPtr g_stage = nullptr;
omni::syntheticdata::SyntheticData* g_SyntheticDataInterface = nullptr;
carb::tasking::ITasking* gTasking = nullptr;


std::unique_ptr<omni::isaac::range_sensor::RangeSensorManager> gRangeSensorManager;

} // end of anonymous namespace

namespace lidar
{

int CARB_ABI getNumCols(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getNumCols();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumRows(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getNumRows();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumColsTicked(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getNumColsTicked();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return 0;
    }
}

uint16_t* CARB_ABI getDepthData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getDepthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getLinearDepthData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getLinearDepthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getBeamTimeData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getBeamTimeData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}
uint8_t* CARB_ABI getIntensityData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getIntensityData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getZenithData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getZenithData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getAzimuthData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getAzimuthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}

carb::Float3* CARB_ABI getPointCloud(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getPointCloud().data();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return nullptr;
    }
}

std::vector<std::string> CARB_ABI getPrimData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getPrimData();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return std::vector<std::string>();
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return std::vector<std::string>();
    }
}


bool CARB_ABI isLidarSensor(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return true;
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return false;
    }
}

uint64_t CARB_ABI getSequenceNumber(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getSequenceNumber();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return 0;
    }
}

carb::Float2 CARB_ABI getAzimuthRange(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getAzimuthRange();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return carb::Float2();
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return carb::Float2();
    }
}

carb::Float2 CARB_ABI getZenithRange(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::LidarSensor* sensor =
            gRangeSensorManager->getLidarSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getZenithRange();
        }
        else
        {
            CARB_LOG_ERROR("Lidar Sensor does not exist");
            return carb::Float2();
        }
    }
    else
    {
        CARB_LOG_ERROR("Lidar Sensor Manager does not exist");
        return carb::Float2();
    }
}

}

namespace ultrasonic
{
bool CARB_ABI isUltrasonicSensor(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return true;
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return false;
    }
}

int CARB_ABI getNumBins(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getNumBins();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumRows(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getNumRows();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumEmitters(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getNumEmitters();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return 0;
    }
}

int CARB_ABI getNumCols(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getNumCols();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return 0;
    }
}


uint16_t* CARB_ABI getDepthData(const char* primPath, int emitterIndex)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        // TODO @markb: put sensible indexing guards on this
        if (sensor)
        {

            return sensor->getDepthData(emitterIndex).data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getEnvelope(const char* primPath, int emitterIndex)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getEnvelope(emitterIndex).data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

std::vector<float> CARB_ABI getEnvelopeArrayFlattened(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getEnvelopeArrayFlattened();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return std::vector<float>();
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return std::vector<float>();
    }
}

std::vector<std::vector<float>> CARB_ABI getActiveEnvelopeArray(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getActiveEnvelopeArray();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return std::vector<std::vector<float>>();
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return std::vector<std::vector<float>>();
    }
}

std::vector<carb::Int2> CARB_ABI getEmitterFiringInfo(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getEmitterFiringInfo();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return std::vector<carb::Int2>();
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return std::vector<carb::Int2>();
    }
}


std::vector<carb::Int2> CARB_ABI getReceiverFiringInfo(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getReceiverFiringInfo();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return std::vector<carb::Int2>();
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return std::vector<carb::Int2>();
    }
}

float* CARB_ABI getLinearDepthData(const char* primPath, int emitterIndex)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getLinearDepthData(emitterIndex).data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}
uint8_t* CARB_ABI getIntensityData(const char* primPath, int emitterIndex)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getIntensityData(emitterIndex).data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getZenithData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getZenithData().data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getAzimuthData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getAzimuthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

carb::Float3* CARB_ABI getPointCloud(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::UltrasonicSensor* sensor =
            gRangeSensorManager->getUltrasonicSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getPointCloud().data();
        }
        else
        {
            CARB_LOG_ERROR("Ultrasonic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Ultrasonic Sensor Manager does not exist");
        return nullptr;
    }
}

}

namespace generic
{
bool CARB_ABI isGenericSensor(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return true;
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
        return false;
    }
}

bool CARB_ABI sendNextBatch(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->sendNextBatch();
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
            return false;
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
        return false;
    }
}


void CARB_ABI setNextBatchRays(const char* primPath,
                               const float* azimuth_angles,
                               const float* zenith_angles,
                               const int sample_length)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            sensor->setNextBatchRays(azimuth_angles, zenith_angles, sample_length);
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
    }
}

void CARB_ABI setNextBatchOffsets(const char* primPath, const float* origin_offsets, const int sample_length)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            sensor->setNextBatchOffsets(origin_offsets, sample_length);
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
    }
}


int CARB_ABI getNumSamplesTicked(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getNumSamplesTicked();
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
            return 0;
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
        return 0;
    }
}

uint16_t* CARB_ABI getDepthData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getDepthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getLinearDepthData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getLinearDepthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
        return nullptr;
    }
}
uint8_t* CARB_ABI getIntensityData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getIntensityData().data();
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getZenithData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getZenithData().data();
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
        return nullptr;
    }
}

float* CARB_ABI getAzimuthData(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {

            return sensor->getAzimuthData().data();
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
        return nullptr;
    }
}

carb::Float3* CARB_ABI getPointCloud(const char* primPath)
{
    if (g_stage && gRangeSensorManager)
    {
        omni::isaac::range_sensor::GenericSensor* sensor =
            gRangeSensorManager->getGenericSensor(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
        if (sensor)
        {
            return sensor->getPointCloud().data();
        }
        else
        {
            CARB_LOG_ERROR("Generic Sensor does not exist");
            return nullptr;
        }
    }
    else
    {
        CARB_LOG_ERROR("Generic Sensor Manager does not exist");
        return nullptr;
    }
}

}


void onAttach(long stageId, double metersPerUnit, void* data)
{
    g_stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!g_stage)
    {
        CARB_LOG_ERROR("PhysX could not find USD stage");
        return;
    }

    if (gRangeSensorManager)
    {
        gRangeSensorManager->initialize(g_stage);
        gRangeSensorManager->initComponents();
    }
}

void onDetach(void* data)
{
    if (gRangeSensorManager)
    {
        gRangeSensorManager->deleteAllComponents();
    }
}

// TODO @markb: add this to ultrasonic!!!
void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    if (!settings->isPlaying)
    {
        return;
    }

    if (gRangeSensorManager)
    {
        gRangeSensorManager->tick(elapsedSecs);
    }
}
void onStop(void* userData)
{
    if (gRangeSensorManager)
    {
        gRangeSensorManager->onStop();
    }
}

void onPrimAdd(const pxr::SdfPath& primPath, void* userData)
{
    // CARB_LOG_INFO("++ Lidar: Prim Add: %s of type %s\n", primPath,
    //    g_stage->GetPrimAtPath(pxr::SdfPath(primPath)).GetTypeName().GetString().c_str());

    if (g_stage && gRangeSensorManager)
    {
        pxr::UsdPrim addedPrim = g_stage->GetPrimAtPath(primPath);
        if (!addedPrim)
        {
            return;
        }
        // Add the root prim
        gRangeSensorManager->onComponentAdd(addedPrim);

        // Check if it has any descendants that need to be added
        pxr::UsdPrimSubtreeRange range = addedPrim.GetDescendants();
        for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        {
            pxr::UsdPrim prim = *iter;
            gRangeSensorManager->onComponentAdd(prim);
        }
    }
}
void onComponentChange(const pxr::SdfPath& primOrPropertyPath, void* userData)
{
    // CARB_LOG_INFO("++ Lidar: Prim Change: %s of type %s\n", primPath,
    //    g_stage->GetPrimAtPath(pxr::SdfPath(primPath)).GetTypeName().GetString().c_str());
    if (g_stage && gRangeSensorManager)
    {
        gRangeSensorManager->onComponentChange(g_stage->GetPrimAtPath(primOrPropertyPath));
    }
}

void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    // CARB_LOG_INFO("++ Lidar: Prim Remove: %s\n", primPath);
    if (gRangeSensorManager)
    {
        gRangeSensorManager->onComponentRemove(primPath);
    }
}


CARB_EXPORT void carbOnPluginStartup()
{


    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>()->getStageUpdate();
    if (!g_stageUpdate)
    {
        CARB_LOG_ERROR("*** Failed to acquire stage update interface\n");
        return;
    }


    g_physx = carb::getCachedInterface<omni::physx::IPhysx>();
    if (!g_physx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }

    g_SyntheticDataInterface = carb::getCachedInterface<omni::syntheticdata::SyntheticData>();
    if (!g_SyntheticDataInterface)
    {
        CARB_LOG_ERROR("Failed to acquire carb::sensors::syntheticdata::SyntheticData interface");
        return;
    }
    gTasking = carb::getCachedInterface<carb::tasking::ITasking>();


    gRangeSensorManager =
        std::make_unique<omni::isaac::range_sensor::RangeSensorManager>(g_physx, g_SyntheticDataInterface, gTasking);

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "Range Sensor Interface";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    desc.onStop = onStop;
    desc.onPrimAdd = onPrimAdd;
    desc.onPrimOrPropertyChange = onComponentChange;
    desc.onPrimRemove = onPrimRemove;
    desc.order = 50; // happens after physx, dc, but before robot engine bridge

    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
    if (!g_stageUpdateNode)
    {
        CARB_LOG_ERROR("*** Failed to create stage update node\n");
        return;
    }

    INITIALIZE_OGN_NODES()
}


CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()

    gRangeSensorManager.reset();
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);

    g_physx = nullptr;
    g_stage = nullptr;
}


void fillInterface(omni::isaac::range_sensor::LidarSensorInterface& iface)
{
    using namespace omni::isaac::range_sensor;

    memset(&iface, 0, sizeof(iface));
    iface.getNumCols = lidar::getNumCols;
    iface.getNumRows = lidar::getNumRows;
    iface.getNumColsTicked = lidar::getNumColsTicked;
    iface.getDepthData = lidar::getDepthData;
    iface.getLinearDepthData = lidar::getLinearDepthData;
    iface.getIntensityData = lidar::getIntensityData;
    iface.getZenithData = lidar::getZenithData;
    iface.getAzimuthData = lidar::getAzimuthData;
    iface.getBeamTimeData = lidar::getBeamTimeData;
    iface.getPointCloud = lidar::getPointCloud;
    iface.getPrimData = lidar::getPrimData;
    iface.isLidarSensor = lidar::isLidarSensor;
    iface.getSequenceNumber = lidar::getSequenceNumber;
    iface.getAzimuthRange = lidar::getAzimuthRange;
    iface.getZenithRange = lidar::getZenithRange;
}


void fillInterface(omni::isaac::range_sensor::UltrasonicSensorInterface& iface)
{
    using namespace omni::isaac::range_sensor;
    memset(&iface, 0, sizeof(iface));
    iface.getNumCols = ultrasonic::getNumCols;
    iface.getNumRows = ultrasonic::getNumRows;
    iface.getDepthData = ultrasonic::getDepthData;
    iface.getLinearDepthData = ultrasonic::getLinearDepthData;
    iface.getIntensityData = ultrasonic::getIntensityData;
    iface.getZenithData = ultrasonic::getZenithData;
    iface.getAzimuthData = ultrasonic::getAzimuthData;
    iface.getNumBins = ultrasonic::getNumBins;
    iface.getNumEmitters = ultrasonic::getNumEmitters;
    iface.getPointCloud = ultrasonic::getPointCloud;
    iface.getEnvelope = ultrasonic::getEnvelope;
    iface.getActiveEnvelopeArray = ultrasonic::getActiveEnvelopeArray;
    iface.getEnvelopeArrayFlattened = ultrasonic::getEnvelopeArrayFlattened;
    iface.getEmitterFiringInfo = ultrasonic::getEmitterFiringInfo;
    iface.getReceiverFiringInfo = ultrasonic::getReceiverFiringInfo;
    iface.isUSS = ultrasonic::isUltrasonicSensor;
}


void fillInterface(omni::isaac::range_sensor::GenericSensorInterface& iface)
{
    using namespace omni::isaac::range_sensor;
    memset(&iface, 0, sizeof(iface));
    iface.getNumSamplesTicked = generic::getNumSamplesTicked;
    iface.getDepthData = generic::getDepthData;
    iface.getLinearDepthData = generic::getLinearDepthData;
    iface.getIntensityData = generic::getIntensityData;
    iface.getZenithData = generic::getZenithData;
    iface.getAzimuthData = generic::getAzimuthData;
    iface.getPointCloud = generic::getPointCloud;
    iface.isGenericSensor = generic::isGenericSensor;
    iface.sendNextBatch = generic::sendNextBatch;
    iface.setNextBatchRays = generic::setNextBatchRays;
    iface.setNextBatchOffsets = generic::setNextBatchOffsets;
}
