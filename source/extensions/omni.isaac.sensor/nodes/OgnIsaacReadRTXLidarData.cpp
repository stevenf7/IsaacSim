// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#ifndef _WIN32

// clang-format off
#include <UsdPCH.h>
// clang-format on

#    include <carb/InterfaceUtils.h>

#    include <internal/omni/sensors/lidar/LidarSettings.h>
#    include <omni/isaac/utils/BaseResetNode.h>
#    include <omni/sensors/lidar/LidarParameterType.h>
#    include <omni/sensors/lidar/LidarReturn.h>
#    include <omni/sensors/lidar/LidarReturnTypes.h>

#    include <OgnIsaacReadRTXLidarDataDatabase.h>

namespace omni
{
namespace isaac
{
namespace sensor
{

class OgnIsaacReadRTXLidarData : public BaseResetNode
{

public:
    static bool compute(OgnIsaacReadRTXLidarDataDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Read RTX Lidar Data");

        const uint8_t* input = reinterpret_cast<const uint8_t*>(db.inputs.cpuPointer());
        if (!input)
        {
            return true;
        }

        const LidarParameterType* parameter{ reinterpret_cast<const LidarParameterType*>(input) };

        if (parameter->async.numTicks == 0 || parameter->async.numChannels * parameter->async.numEchos == 0)
        {
            return true;
        }

        const LidarTick* lidarTicks = reinterpret_cast<const LidarTick*>(input + sizeof(LidarParameterType));
        const LidarReturn* lidarReturns = reinterpret_cast<const LidarReturn*>(
            input + sizeof(LidarParameterType) + sizeof(LidarTick) * parameter->async.numTicks);

        auto& nodeObj = db.abi_node();
        const size_t maxSize = parameter->async.numChannels * parameter->async.numEchos * parameter->async.numTicks;

        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        size_t outSize = 0;
        if (keepOnlyPositiveDistance)
        {
            for (size_t i = 0; i < maxSize; ++i)
            {
                if (lidarReturns[i].distance > 0.f)
                {
                    outSize++;
                }
            }
        }
        else
        {
            outSize = maxSize;
        }

#    define _DEF_OUT_VAR(outName)                                                                                      \
        auto& db_outputs_##outName = db.outputs.outName();                                                             \
        db_outputs_##outName.resize(outSize)
        _DEF_OUT_VAR(intensity);
        _DEF_OUT_VAR(distance);
        _DEF_OUT_VAR(azimuth);
        _DEF_OUT_VAR(elevation);
        _DEF_OUT_VAR(velocityMs);
        _DEF_OUT_VAR(echoId);
        _DEF_OUT_VAR(emitterId);
        _DEF_OUT_VAR(beamId);
        _DEF_OUT_VAR(materialId);
        _DEF_OUT_VAR(hitPointNormal);
        _DEF_OUT_VAR(tick);
        _DEF_OUT_VAR(objectId);
        _DEF_OUT_VAR(timeStampNs);
#    undef _DEFINE_OUTPUT_VARS

        uint32_t atomicOutIdx = 0;
        for (uint32_t tick = 0; tick < parameter->async.numTicks; tick++)
        {
            const LidarTick& lidarTick = lidarTicks[tick];
            for (uint32_t channelId = 0; channelId < parameter->async.numChannels; ++channelId)
            {
                for (uint32_t echoId = 0; echoId < parameter->async.numEchos; ++echoId)
                {
                    const uint32_t pointIdx{ idxOfReturn(
                        channelId, echoId, parameter->async.numEchos, parameter->async.numChannels, tick) };
                    const LidarReturn& lidarReturn = lidarReturns[pointIdx];

                    // This is just for runtime efficiency
                    if (!keepOnlyPositiveDistance || lidarReturn.distance > 0.f)
                    {
                        const uint32_t outIdx = keepOnlyPositiveDistance ? atomicOutIdx++ : pointIdx;

#    define _ASSIGN_OUT(outputName, index, comp, src) db_outputs_##outputName[index] comp = src

                        _ASSIGN_OUT(intensity, outIdx, , lidarReturn.intensity);
                        _ASSIGN_OUT(distance, outIdx, , lidarReturn.distance);
                        _ASSIGN_OUT(azimuth, outIdx, , lidarReturn.azimuthDeg);
                        _ASSIGN_OUT(elevation, outIdx, , lidarReturn.elevationDeg);
                        _ASSIGN_OUT(velocityMs, outIdx, [0], lidarReturn.velocityMs[0]);
                        _ASSIGN_OUT(velocityMs, outIdx, [1], lidarReturn.velocityMs[1]);
                        _ASSIGN_OUT(velocityMs, outIdx, [2], lidarReturn.velocityMs[2]);
                        _ASSIGN_OUT(echoId, outIdx, , echoId);
                        _ASSIGN_OUT(emitterId, outIdx, , lidarReturn.emitterId);
                        _ASSIGN_OUT(beamId, outIdx, , lidarReturn.beamId);
                        _ASSIGN_OUT(materialId, outIdx, , lidarReturn.materialId);
                        _ASSIGN_OUT(hitPointNormal, outIdx, [0], lidarReturn.hitPointNormal[0]);
                        _ASSIGN_OUT(hitPointNormal, outIdx, [1], lidarReturn.hitPointNormal[1]);
                        _ASSIGN_OUT(hitPointNormal, outIdx, [2], lidarReturn.hitPointNormal[2]);
                        _ASSIGN_OUT(tick, outIdx, , tick + parameter->async.startTick);
                        _ASSIGN_OUT(objectId, outIdx, , lidarReturn.objectId);
                        _ASSIGN_OUT(timeStampNs, outIdx, , lidarTick.timeStampNs + lidarReturn.deltaTimeNs);

#    undef _ASSIGN_IF_NEEDED
                    }
                }
            }
        }

        db.outputs.execOut() = kExecutionAttributeStateEnabled;

        return true;
    }
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
#endif
