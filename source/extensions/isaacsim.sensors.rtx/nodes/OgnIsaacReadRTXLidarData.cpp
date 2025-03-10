// Copyright (c) 2022-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "SensorNodeUtils.h"
#include "isaacsim/core/includes/UsdUtilities.h"

#include <carb/InterfaceUtils.h>

#include <GenericModelOutput.h>
#include <OgnIsaacReadRTXLidarDataDatabase.h>


namespace isaacsim
{
namespace sensors
{
namespace rtx
{
using namespace omni::sensors;

class OgnIsaacReadRTXLidarData : public LidarConfigHelper
{
    // m_buffer used to copy data from the gpu if needed.
    std::vector<uint8_t> m_buffer;

public:
    static bool compute(OgnIsaacReadRTXLidarDataDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Read RTX Lidar Data");

        db.outputs.numBeams() = 0;
        auto& transformStart = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.transformStart());
        transformStart.SetIdentity();
        auto& transform = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.transform());
        transform.SetIdentity();

        uint8_t* dataPtr = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        if (!dataPtr)
        {
            return true;
        }
        auto& state = db.perInstanceState<OgnIsaacReadRTXLidarData>();

        if (db.inputs.cudaDeviceIndex() != -1)
        {
            CARB_PROFILE_ZONE(0, "Copy Read RTX Lidar Data");
            if (state.m_buffer.size() < db.inputs.bufferSize())
            {
                state.m_buffer.resize(db.inputs.bufferSize());
            }
            // omni::sensors::cpygmoToBuffer(&state.m_buffer[0], (const omni::sensors::GenericPointCloud*)(dataPtr),
            // true, false, db.inputs.cudaDeviceIndex(), (cudaStream_t)db.inputs.cudaStream());
            cudaMemcpyAsync(&state.m_buffer[0], dataPtr, db.inputs.bufferSize(), cudaMemcpyDeviceToHost);
            dataPtr = state.m_buffer.data();
        }
        GenericModelOutputHelper helper(dataPtr);
        if (!helper.isValid(OutputType::POINTCLOUD, CoordsType::SPHERICAL, Modality::LIDAR))
        {
            CARB_LOG_WARN(
                "Input to IsaacReadRTXLidarData is not a valid LIDAR POINTCLOUD type. Buffer will not be parsed.");
            return true;
        }
        if (helper.mGmo.numElements == 0)
        {
            return true;
        }

        const size_t maxSize = helper.mGmo.numElements;
        const float* azimuths = helper.mGmo.elements.x;
        const float* elevations = helper.mGmo.elements.y;
        const float* distances = helper.mGmo.elements.z;
        const float* intensities = helper.mGmo.elements.scalar;

        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        size_t outSize = maxSize;
        {
            CARB_PROFILE_ZONE(0, "Read RTX Lidar Data keepOnlyPositiveDistance");
            if (keepOnlyPositiveDistance)
            {
                outSize = 0;
                for (size_t i = 0; i < maxSize; ++i)
                {
                    if (distances[i] > 0.f)
                    {
                        ++outSize;
                    }
                }
            }
        }
        state.updateLidarConfig(db.tokenToString(db.inputs.renderProductPath()));

        db.outputs.depthRange() = { state.getNearRange(), state.getFarRange() };
        db.outputs.numBeams() = outSize;
        db.outputs.frameId() = helper.mGmo.frameId;
        db.outputs.timestampNs() = helper.mGmo.timestampNs;

        getTransformFromSensorPose(helper.mGmo.frameStart, transformStart);
        getTransformFromSensorPose(helper.mGmo.frameEnd, transform);

        const omni::sensors::LidarAuxiliaryData* auxPoints =
            static_cast<const omni::sensors::LidarAuxiliaryData*>(helper.mGmo.auxiliaryData);
        uint32_t hasAux = auxPoints ? (uint32_t)auxPoints->filledAuxMembers : 0x0000;

#define DEF_OUT_VAR(outName, outSz)                                                                                    \
    auto& db_outputs_##outName = db.outputs.outName();                                                                 \
    db_outputs_##outName.resize(outSz)

        DEF_OUT_VAR(deltaTimes, outSize);
        DEF_OUT_VAR(azimuths, outSize);
        DEF_OUT_VAR(elevations, outSize);
        DEF_OUT_VAR(distances, outSize);
        DEF_OUT_VAR(intensities, outSize);
        DEF_OUT_VAR(flags, outSize);
        DEF_OUT_VAR(velocities, auxPoints && hasAux & (uint32_t)LidarAuxHas::VELOCITIES ? outSize : 0);
        DEF_OUT_VAR(hitPointNormals, auxPoints && hasAux & (uint32_t)LidarAuxHas::HIT_NORMALS ? outSize : 0);
        DEF_OUT_VAR(emitterIds, auxPoints && hasAux & (uint32_t)LidarAuxHas::ECHO_ID ? outSize : 0);
        DEF_OUT_VAR(materialIds, auxPoints && hasAux & (uint32_t)LidarAuxHas::MAT_ID ? outSize : 0);
        DEF_OUT_VAR(objectIds, auxPoints && hasAux & (uint32_t)LidarAuxHas::OBJ_ID ? outSize : 0);
        DEF_OUT_VAR(ticks, auxPoints && hasAux & (uint32_t)LidarAuxHas::TICK_ID ? outSize : 0);
        DEF_OUT_VAR(tickStates, auxPoints && hasAux & (uint32_t)LidarAuxHas::TICK_STATES ? outSize : 0);
        DEF_OUT_VAR(channels, auxPoints && hasAux & (uint32_t)LidarAuxHas::CHANNEL_ID ? outSize : 0);
        DEF_OUT_VAR(echos, auxPoints && hasAux & (uint32_t)LidarAuxHas::ECHO_ID ? outSize : 0);

#undef _DEFINE_OUTPUT_VARS

        if (!keepOnlyPositiveDistance)
        {
            memcpy(db_outputs_deltaTimes.data(), helper.mGmo.elements.timeOffsetNs, maxSize * sizeof(uint32_t));
            memcpy(db_outputs_azimuths.data(), azimuths, maxSize * sizeof(float));
            memcpy(db_outputs_elevations.data(), elevations, maxSize * sizeof(float));
            memcpy(db_outputs_distances.data(), distances, maxSize * sizeof(float));
            memcpy(db_outputs_intensities.data(), intensities, maxSize * sizeof(float));
            memcpy(db_outputs_flags.data(), helper.mGmo.elements.flags, maxSize * sizeof(uint8_t));
            if (db_outputs_velocities.size())
            {
                memcpy(db_outputs_velocities.data(), auxPoints->velocities, 3 * maxSize * sizeof(float));
            }
            if (db_outputs_hitPointNormals.size())
            {
                memcpy(db_outputs_hitPointNormals.data(), auxPoints->hitNormals, 3 * maxSize * sizeof(float));
            }
            if (db_outputs_emitterIds.size())
            {
                memcpy(db_outputs_emitterIds.data(), auxPoints->emitterId, maxSize * sizeof(uint32_t));
            }
            if (db_outputs_materialIds.size())
            {
                memcpy(db_outputs_materialIds.data(), auxPoints->matId, maxSize * sizeof(uint32_t));
            }
            if (db_outputs_objectIds.size())
            {
                memcpy(db_outputs_objectIds.data(), auxPoints->objId, maxSize * sizeof(uint32_t));
            }
            if (db_outputs_ticks.size())
            {
                memcpy(db_outputs_ticks.data(), auxPoints->tickId, maxSize * sizeof(uint32_t));
            }
            if (db_outputs_tickStates.size())
            {
                memcpy(db_outputs_tickStates.data(), auxPoints->tickStates, maxSize * sizeof(uint8_t));
            }
            if (db_outputs_channels.size())
            {
                memcpy(db_outputs_channels.data(), auxPoints->channelId, maxSize * sizeof(uint32_t));
            }
            if (db_outputs_echos.size())
            {
                memcpy(db_outputs_echos.data(), auxPoints->echoId, maxSize * sizeof(uint8_t));
            }
        }
        else
        {
            uint32_t i = 0;
            for (uint32_t idx = 0; idx < helper.mGmo.numElements; idx++)
            {
                if (distances[idx] > 0.f)
                {
                    db_outputs_deltaTimes[i] = helper.mGmo.elements.timeOffsetNs[idx];
                    db_outputs_azimuths[i] = azimuths[idx];
                    db_outputs_elevations[i] = elevations[idx];
                    db_outputs_distances[i] = distances[idx];
                    db_outputs_intensities[i] = intensities[idx];
                    db_outputs_flags[i] = helper.mGmo.elements.flags[idx];
                    db_outputs_velocities[i][0] = auxPoints->velocities[idx * 3 + 0];
                    db_outputs_velocities[i][1] = auxPoints->velocities[idx * 3 + 1];
                    db_outputs_velocities[i][2] = auxPoints->velocities[idx * 3 + 2];
                    db_outputs_hitPointNormals[i][0] = auxPoints->hitNormals[idx * 3 + 0];
                    db_outputs_hitPointNormals[i][1] = auxPoints->hitNormals[idx * 3 + 1];
                    db_outputs_hitPointNormals[i][2] = auxPoints->hitNormals[idx * 3 + 2];
                    db_outputs_emitterIds[i] = auxPoints->emitterId[idx];
                    db_outputs_materialIds[i] = auxPoints->matId[idx];
                    db_outputs_objectIds[i] = auxPoints->objId[idx];
                    db_outputs_ticks[i] = auxPoints->tickId[idx];
                    db_outputs_tickStates[i] = auxPoints->tickStates[idx];
                    db_outputs_channels[i] = auxPoints->channelId[idx];
                    db_outputs_echos[i] = auxPoints->echoId[idx];
                    i++;
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
