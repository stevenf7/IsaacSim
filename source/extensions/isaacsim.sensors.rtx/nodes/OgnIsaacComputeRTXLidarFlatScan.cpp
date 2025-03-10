// Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
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

#include <GenericModelOutput.h>
#include <OgnIsaacComputeRTXLidarFlatScanDatabase.h>
#include <math.h>

namespace isaacsim
{
namespace sensors
{
namespace rtx
{

// a scan buffer that takes only one emitter, as nearest 0 elevation, and has to be from a rotary lidar.
// because it creates laser scan data which assumes 0 elevation emitter with all the same delta for emitter rotation
// and time.
class OgnIsaacComputeRTXLidarFlatScan : public LidarConfigHelper
{
private:
    // ID of emitter at lowest elevation (rotary) or ID of first emitter of lowest-elevation line (solid-state)
    uint32_t m_emitterToOutput{ 0 };
    int m_numRaysPerLine{ -1 }; // Number of emitters in lowest-elevation line (solid-state only)
    float m_startAzimuthDeg; // starting azimuth of emitter in lowest-elevation line (solid-state only)
    float m_horizontalResolution; // angular separation between beams (deg)
    float m_inElevationDeg; // absolute-value of elevation of lowest-elevation emitter
    std::vector<uint8_t> m_intensityBuffer; // buffer containing intensity values from GMO pointer
    std::vector<float> m_distanceBuffer; // buffer containing range measurements from GMO pointer
    std::vector<double> m_timestampBuffer; // buffer containing adjusted timestamps from GMO pointer
    double m_timeOffset{ DBL_MIN }; // offset between render time (from GMO pointer) and simulation time (from input)
    uint32_t m_bufferSize; // size of buffers, based on number of beams as determined from lidar profile
    uint32_t m_prevIdx; // tracks where in the buffers the last measurements were inserted, based on azimuth

public:
    static bool compute(OgnIsaacComputeRTXLidarFlatScanDatabase& db)
    {
        uint8_t* dataPtr = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        // no reason to update the scan buffer if there is no dataHost
        if (!dataPtr)
        {
            db.outputs.numRows() = 1;
            db.outputs.numCols() = 0;
            return true;
        }
        auto& state = db.perInstanceState<OgnIsaacComputeRTXLidarFlatScan>();

        GenericModelOutputHelper helper(dataPtr);
        if (!helper.isValid(OutputType::POINTCLOUD, CoordsType::SPHERICAL, Modality::LIDAR))
        {
            CARB_LOG_WARN(
                "Input to IsaacComputeRTXLidarFlatScan is not a valid LIDAR POINTCLOUD type. Buffer will not be parsed.");
            return true;
        }
        if (helper.mGmo.numElements == 0)
        {
            return true;
        }

        const omni::sensors::LidarAuxiliaryData* auxPoints =
            static_cast<const omni::sensors::LidarAuxiliaryData*>(helper.mGmo.auxiliaryData);
        const uint32_t* tickIds = auxPoints ? auxPoints->tickId : nullptr;
        const uint32_t* emitterIds = auxPoints ? auxPoints->emitterId : nullptr;
        const uint8_t* echoIds = auxPoints ? auxPoints->echoId : nullptr;

        // Find the lowest elevation emitter and update state lidar config variables every time the lidar config
        // changes. This should be infrequent after initialization.
        if (state.updateLidarConfig(db.tokenToString(db.inputs.renderProductPath())))
        {
            if (state.scanType == LidarScanType::kRotary)
            {
                // Find emitter profile for emitter at minimum elevation angle. Ideally this is at 0.0 deg.
                state.m_emitterToOutput = 0;
                state.m_inElevationDeg = 91.0;
                for (size_t s = 0; s < state.profile->emitterStateCount; s++)
                {
                    for (size_t i = 0; i < state.profile->numberOfEmitters; i++)
                    {
                        float curElevation = ::fabs(
                            state.profile->emitterProfileSoA.elevationDeg[s * state.profile->numberOfEmitters + i]);
                        if (curElevation < state.m_inElevationDeg)
                        {
                            state.m_inElevationDeg = curElevation;
                            state.m_emitterToOutput = (uint32_t)i;
                        }
                    }
                }
                // Set useful state variables
                state.m_bufferSize = state.getTicksPerScan();
                state.m_horizontalResolution = static_cast<float>(360.0 / state.m_bufferSize);
                // Populate config-based outputs
                db.outputs.horizontalFov() = 360.0;
                db.outputs.rotationRate() = static_cast<float>(state.profile->scanRateBaseHz);
                db.outputs.azimuthRange() = { -180.0f, 180.0f - state.m_horizontalResolution };
            }
            else if (state.scanType == LidarScanType::kSolidState)
            {
                // Find the solid state line with the lowest elevation, and store its start/end azimuth.
                float endAzimuthDeg = 361.0;
                state.m_inElevationDeg = 91.0; // 90 is max, so fist emitter state will always at least be picked.
                for (int s = 0; s < (int)state.profile->emitterStateCount; s++)
                {
                    int emitterToCheck = 0; // first emitter in line
                    for (int l = 0; l < (int)state.profile->numLines; l++)
                    {
                        float curElevation = ::fabs(state.profile->emitterProfileSoA.elevationDeg[emitterToCheck]);
                        if (curElevation < state.m_inElevationDeg)
                        {
                            state.m_inElevationDeg = curElevation;
                            state.m_emitterToOutput = emitterToCheck;
                            state.m_numRaysPerLine = state.profile->emitterProfileSoA.numRaysPerLine[l];
                            state.m_startAzimuthDeg = state.profile->emitterProfileSoA.azimuthDeg[emitterToCheck];
                            // with one emitter the start and end are the same. otherwise, assume fixed azimuth
                            // difference between emitters in line
                            state.m_horizontalResolution =
                                state.m_numRaysPerLine < 2 ?
                                    0 :
                                    state.profile->emitterProfileSoA.azimuthDeg[emitterToCheck + 1] -
                                        state.m_startAzimuthDeg;
                            endAzimuthDeg =
                                state.m_startAzimuthDeg + state.m_horizontalResolution * (state.m_numRaysPerLine - 1);
                        }
                        // Advance to first emitter in next line
                        emitterToCheck += state.profile->emitterProfileSoA.numRaysPerLine[l];
                    }
                }
                if (state.m_startAzimuthDeg > endAzimuthDeg)
                {
                    // then it's a solid start that is spinning ccw
                    float tempAzimuth = state.m_startAzimuthDeg;
                    state.m_startAzimuthDeg = endAzimuthDeg;
                    endAzimuthDeg = tempAzimuth;
                }
                float horizontalFov = endAzimuthDeg - state.m_startAzimuthDeg;
                if (horizontalFov > 360.0f)
                {
                    CARB_LOG_WARN_ONCE(
                        "IsaacComputeRTXLidarFlatScan: %s is not not designed to work with Flat Scan data.  When a Solid State lidar is used with this node, there must be a row of evenly spaced emitters all at the same elevation.",
                        state.config.c_str());
                    horizontalFov = 360.0f;
                }
                state.m_bufferSize = state.m_numRaysPerLine;
                state.m_prevIdx =
                    state.profile->rotationDirection == LidarRotationDirection::CW ? state.m_bufferSize - 1 : 0;
                db.outputs.horizontalFov() = horizontalFov;
                db.outputs.rotationRate() = static_cast<float>(state.profile->scanRateBaseHz);
                db.outputs.azimuthRange() = { state.m_startAzimuthDeg, endAzimuthDeg };
            }
            else
            {
                CARB_LOG_WARN_ONCE("IsaacComputeRTXLidarFlatScan %s is an unknown scanType.", state.config.c_str());
                db.outputs.numCols() = 0;
                return true;
            }
            if (state.m_inElevationDeg != 0.0f)
            {
                CARB_LOG_WARN_ONCE("IsaacComputeRTXLidarFlatScan: lowest elevation emitter line is %f, not 0.",
                                   state.m_inElevationDeg);
            }
            // Reallocate and fill output buffers
            state.m_distanceBuffer = std::vector<float>(state.m_bufferSize, -1.0);
            state.m_intensityBuffer = std::vector<uint8_t>(state.m_bufferSize, 0);
            state.m_timestampBuffer = std::vector<double>(state.m_bufferSize, DBL_MIN);
            // Set outputs common to solid-state and rotary lidars
            db.outputs.depthRange() = { state.profile->nearRangeM, state.profile->farRangeM };
            db.outputs.horizontalResolution() = state.m_horizontalResolution;
        }

        if ((state.scanType == LidarScanType::kRotary && (!echoIds || !emitterIds || !tickIds)) ||
            (state.scanType == LidarScanType::kSolidState && (!echoIds || !emitterIds)))
        {
            return true;
        }

        db.outputs.exec() = kExecutionAttributeStateDisabled;
        if (state.m_timeOffset == DBL_MIN)
        {
            state.m_timeOffset = db.inputs.timeStamp() - helper.mGmo.timestampNs / 1e9;
        }
        for (uint32_t pointIdx = 0; pointIdx < helper.mGmo.numElements; pointIdx++)
        {
            if (echoIds[pointIdx])
                continue;
            uint32_t emitterId = emitterIds[pointIdx];
            if ((state.scanType == LidarScanType::kRotary && emitterId == state.m_emitterToOutput) ||
                (state.scanType == LidarScanType::kSolidState && state.m_emitterToOutput <= emitterId &&
                 emitterId < (state.m_emitterToOutput + state.m_numRaysPerLine)))
            {
                float azimuth = helper.mGmo.elements.x[pointIdx];
                // Compute index of buffer in which measurements will be placed, based on beam azimuth
                uint32_t idx =
                    static_cast<uint32_t>((azimuth - db.outputs.azimuthRange()[0]) / state.m_horizontalResolution);
                if (idx >= state.m_bufferSize)
                {
                    idx = state.m_bufferSize - 1;
                }
                if (state.m_prevIdx - idx > state.m_intensityBuffer.size() / 2)
                {
                    db.outputs.intensitiesData().resize(state.m_bufferSize);
                    db.outputs.linearDepthData().resize(state.m_bufferSize);
                    db.outputs.numCols() = static_cast<int>(state.m_bufferSize);
                    db.outputs.numRows() = 1;
                    db.outputs.timeStamp() = DBL_MIN;
                    for (size_t i = 0; i < state.m_bufferSize; i++)
                    {
                        db.outputs.intensitiesData().at(i) = state.m_intensityBuffer[i];
                        db.outputs.linearDepthData().at(i) = state.m_distanceBuffer[i];
                        size_t inIdx = state.profile->rotationDirection == LidarRotationDirection::CW ?
                                           state.m_bufferSize - i - 1 :
                                           i;
                        if (db.outputs.timeStamp() == DBL_MIN && state.m_timestampBuffer[inIdx] != DBL_MIN)
                        {
                            // Set timestamp to first timestamp that's not a sentinel value
                            db.outputs.timeStamp() = state.m_timestampBuffer[inIdx];
                        }
                    }
                    // Reset local buffers
                    std::fill(state.m_intensityBuffer.begin(), state.m_intensityBuffer.end(), 0);
                    std::fill(state.m_distanceBuffer.begin(), state.m_distanceBuffer.end(), -1.0);
                    std::fill(state.m_timestampBuffer.begin(), state.m_timestampBuffer.end(), DBL_MIN);
                    db.outputs.exec() = kExecutionAttributeStateEnabled;
                }
                // Push latest depth into distance buffer
                float distance = helper.mGmo.elements.z[pointIdx];
                if (state.m_inElevationDeg)
                {
                    distance = distance * ::cosf(deg2Rad(state.m_inElevationDeg));
                }
                state.m_distanceBuffer[idx] = distance;
                // Push latest intensity into intensity buffer
                state.m_intensityBuffer[idx] = static_cast<uint8_t>(helper.mGmo.elements.scalar[pointIdx] * 255.0f);
                state.m_timestampBuffer[idx] = helper.mGmo.timestampNs / 1e9 +
                                               helper.mGmo.elements.timeOffsetNs[pointIdx] / 1e9 + state.m_timeOffset;
                state.m_prevIdx = idx;
            }
        }
        return true;
    }
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
