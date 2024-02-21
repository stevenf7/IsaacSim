// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "LidarNodeUtils.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/InterfaceUtils.h>

#include <internal/omni/sensors/lidar/LidarReturnHelper.h>
#include <internal/omni/sensors/lidar/LidarSettings.h>
#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarReturn.h>
#include <omni/sensors/lidar/LidarReturnTypes.h>

#include <OgnIsaacReadRTXLidarDataDatabase.h>

namespace omni
{
namespace isaac
{
namespace sensor
{

class OgnIsaacReadRTXLidarData
{
private:
    std::string config;
    LidarScanType scanType{ LidarScanType::kUnknown };
    LidarRotaryProfile rotaryProfile;
    LidarSolidStateProfile solidStateProfile;

public:
    static bool compute(OgnIsaacReadRTXLidarDataDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Read RTX Lidar Data");

        uint8_t* input = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        if (!input)
        {
            return true;
        }
        auto& state = db.perInstanceState<OgnIsaacReadRTXLidarData>();

        // fill the structure of arrays
        LidarTicks lidarTicks;
        LidarReturns lidarReturns;
        LidarParameterType* parameter = omni::sensors::nv::lidar::fillStructsFromBuffer(input, lidarReturns, lidarTicks);
        const uint32_t numTicks = parameter->async.numTicks;
        const uint32_t numChannels = parameter->async.numChannels;
        const uint32_t numEchos = parameter->async.numEchos;
        db.outputs.numTicks() = numTicks;
        db.outputs.numChannels() = numChannels;
        db.outputs.numEchos() = numEchos;

        if (numTicks == 0 || numChannels * numEchos == 0)
        {
            return true;
        }

        const size_t maxSize = numChannels * numEchos * numTicks;

        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        size_t outSize = maxSize;
        if (keepOnlyPositiveDistance)
        {
            outSize = 0;
            for (size_t i = 0; i < maxSize; ++i)
            {
                if (lidarReturns.distances[i] > 0.f)
                {
                    ++outSize;
                }
            }
        }
        std::string curConfig = "";
        pxr::UsdAttribute configAttr = omni::isaac::utils::getCameraAttributeFromRenderProduct(
            "sensorModelConfig", db.tokenToString(db.inputs.renderProductPath()));
        if (configAttr.IsValid())
        {
            omni::isaac::utils::safeGetAttribute(configAttr, curConfig);
        }
        updateLidarConfig(curConfig, state.config, state.scanType, state.rotaryProfile, state.solidStateProfile);

        db.outputs.depthRange() = {
            state.scanType == LidarScanType::kSolidState ? state.solidStateProfile.nearRangeM :
                                                           state.rotaryProfile.nearRangeM,
            state.scanType == LidarScanType::kSolidState ? state.solidStateProfile.farRangeM :
                                                           state.rotaryProfile.farRangeM,
        };
        // state.rotaryProfile.reportRateBaseHz; // 3600 for a 10Hz lidar that fires one tick per degree.
        // state.rotaryProfile.scanRateBaseHz; // 10 for a 10Hz lidar
        db.outputs.numBeams() = outSize;

#define _DEF_OUT_VAR(outName, outSz)                                                                                   \
    auto& outName = db.outputs.outName();                                                                              \
    outName.resize(outSz)

        _DEF_OUT_VAR(tickAzimuths, numTicks);
        _DEF_OUT_VAR(tickStates, numTicks);
        _DEF_OUT_VAR(tickTimestamps, numTicks);

        _DEF_OUT_VAR(azimuths, outSize);
        _DEF_OUT_VAR(elevations, outSize);
        _DEF_OUT_VAR(distances, outSize);
        _DEF_OUT_VAR(intensities, outSize);
        _DEF_OUT_VAR(velocities, outSize);
        _DEF_OUT_VAR(hitPointNormals, outSize);
        _DEF_OUT_VAR(deltaTimes, outSize);
        _DEF_OUT_VAR(emitterIds, outSize);
        _DEF_OUT_VAR(beamIds, outSize);
        _DEF_OUT_VAR(materialIds, outSize);
        _DEF_OUT_VAR(objectIds, outSize);
        _DEF_OUT_VAR(ticks, outSize);
        _DEF_OUT_VAR(channels, outSize);
        _DEF_OUT_VAR(echos, outSize);
#undef _DEFINE_OUTPUT_VARS

        // One tick fires every channel an echo number of times.
        memcpy(tickAzimuths.data(), lidarTicks.azimuths, numTicks * sizeof(float));
        memcpy(tickStates.data(), lidarTicks.states, numTicks * sizeof(uint32_t));
        memcpy(tickTimestamps.data(), lidarTicks.timestamps, numTicks * sizeof(uint64_t));

        if (!keepOnlyPositiveDistance)
        {
            memcpy(azimuths.data(), lidarReturns.azimuths, maxSize * sizeof(float));
            memcpy(elevations.data(), lidarReturns.elevations, maxSize * sizeof(float));
            memcpy(distances.data(), lidarReturns.distances, maxSize * sizeof(float));
            memcpy(intensities.data(), lidarReturns.intensities, maxSize * sizeof(float));
            memcpy(velocities.data(), lidarReturns.velocities, 3 * maxSize * sizeof(float));
            memcpy(hitPointNormals.data(), lidarReturns.hitPointNormals, 3 * maxSize * sizeof(float));
            memcpy(deltaTimes.data(), lidarReturns.deltaTimes, maxSize * sizeof(uint32_t));
            memcpy(emitterIds.data(), lidarReturns.emitterIds, maxSize * sizeof(uint32_t));
            memcpy(beamIds.data(), lidarReturns.beamIds, maxSize * sizeof(uint32_t));
            memcpy(materialIds.data(), lidarReturns.materialIds, maxSize * sizeof(uint32_t));
            memcpy(objectIds.data(), lidarReturns.objectIds, maxSize * sizeof(uint32_t));
            unsigned int i = 0;

            for (uint32_t tick = 0; tick < numTicks; tick++)
            {
                for (uint32_t channelId = 0; channelId < numChannels; ++channelId)
                {
                    for (uint32_t echoId = 0; echoId < numEchos; ++echoId)
                    {
                        ticks[i] = tick;
                        channels[i] = channelId;
                        echos[i] = echoId;
                        i += 1;
                    }
                }
            }
        }
        else
        {
            uint32_t i = 0;
            uint32_t idx = 0;
            for (uint32_t tick = 0; tick < numTicks; tick++)
            {
                for (uint32_t channelId = 0; channelId < numChannels; ++channelId)
                {
                    for (uint32_t echoId = 0; echoId < numEchos; ++echoId)
                    {
                        if (lidarReturns.distances[idx] > 0.f)
                        {
                            azimuths[i] = lidarReturns.azimuths[idx];
                            elevations[i] = lidarReturns.elevations[idx];
                            distances[i] = lidarReturns.distances[idx];
                            intensities[i] = lidarReturns.intensities[idx];
                            velocities[i][0] = lidarReturns.velocities[idx * 3 + 0];
                            velocities[i][1] = lidarReturns.velocities[idx * 3 + 1];
                            velocities[i][2] = lidarReturns.velocities[idx * 3 + 2];
                            hitPointNormals[i][0] = lidarReturns.hitPointNormals[idx * 3 + 0];
                            hitPointNormals[i][1] = lidarReturns.hitPointNormals[idx * 3 + 1];
                            hitPointNormals[i][2] = lidarReturns.hitPointNormals[idx * 3 + 2];
                            deltaTimes[i] = lidarReturns.deltaTimes[idx];
                            emitterIds[i] = lidarReturns.emitterIds[idx];
                            beamIds[i] = lidarReturns.beamIds[idx];
                            materialIds[i] = lidarReturns.materialIds[idx];
                            objectIds[i] = lidarReturns.objectIds[idx];
                            ticks[i] = tick;
                            channels[i] = channelId;
                            echos[i] = echoId;
                            i++;
                        }
                        idx++;
                    }
                }
            }
        }

        db.outputs.exec() = kExecutionAttributeStateEnabled;

        return true;
    }
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
