// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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
#include "isaacsim/core/utils/UsdUtilities.h"

#include <omni/sensors/GenericModelOutput.h>

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
    uint32_t emitterToOutput{ 0 };
    int numRaysPerLine{ -1 }; // Number of emitters in lowest-elevation line (solid-state only)
    float startAzimuthDeg; // starting azimuth of emitter in lowest-elevation line (solid-state only)
    float horizontalResolution; // angular separation between beams (deg)
    float minElevationDeg; // absolute-value of elevation of lowest-elevation emitter
    std::vector<uint8_t> intensityBuffer; // buffer containing intensity values from GMO pointer
    std::vector<float> distanceBuffer; // buffer containing range measurements from GMO pointer
    std::vector<double> timestampBuffer; // buffer containing adjusted timestamps from GMO pointer
    double timeOffset{ DBL_MIN }; // offset between render time (from GMO pointer) and simulation time (from input)
    uint32_t bufferSize; // size of buffers, based on number of beams as determined from lidar profile
    uint32_t prevIdx; // tracks where in the buffers the last measurements were inserted, based on azimuth

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
        if (!helper.isValid(OutputType::POINTCLOUD, CoordsType::SPHERICAL, AuxType::LIDAR))
        {
            CARB_LOG_WARN(
                "Input to IsaacComputeRTXLidarFlatScan is not a valid LIDAR POINTCLOUD type. Buffer will not be parsed.");
            return true;
        }
        if (helper.m_gmo.numElements == 0)
        {
            return true;
        }

        const omni::sensors::LidarAuxiliaryData* auxPoints =
            static_cast<const omni::sensors::LidarAuxiliaryData*>(helper.m_gmo.auxiliaryData);
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
                state.emitterToOutput = 0;
                state.minElevationDeg = 91.0;
                for (size_t s = 0; s < state.profile->emitterStateCount; s++)
                {
                    for (size_t i = 0; i < state.profile->numberOfEmitters; i++)
                    {
                        float curElevation = ::fabs(
                            state.profile->emitterProfileSoA.elevationDeg[s * state.profile->numberOfEmitters + i]);
                        if (curElevation < state.minElevationDeg)
                        {
                            state.minElevationDeg = curElevation;
                            state.emitterToOutput = (uint32_t)i;
                        }
                    }
                }
                // Set useful state variables
                state.bufferSize = state.getTicksPerScan();
                state.horizontalResolution = static_cast<float>(360.0 / state.bufferSize);
                // Populate config-based outputs
                db.outputs.horizontalFov() = 360.0;
                db.outputs.rotationRate() = static_cast<float>(state.profile->scanRateBaseHz);
                db.outputs.azimuthRange() = { -180.0f, 180.0f - state.horizontalResolution };
            }
            else if (state.scanType == LidarScanType::kSolidState)
            {
                // Find the solid state line with the lowest elevation, and store its start/end azimuth.
                float endAzimuthDeg = 361.0;
                state.minElevationDeg = 91.0; // 90 is max, so fist emitter state will always at least be picked.
                for (int s = 0; s < (int)state.profile->emitterStateCount; s++)
                {
                    int emitterToCheck = 0; // first emitter in line
                    for (int l = 0; l < (int)state.profile->numLines; l++)
                    {
                        float curElevation = ::fabs(state.profile->emitterProfileSoA.elevationDeg[emitterToCheck]);
                        if (curElevation < state.minElevationDeg)
                        {
                            state.minElevationDeg = curElevation;
                            state.emitterToOutput = emitterToCheck;
                            state.numRaysPerLine = state.profile->emitterProfileSoA.numRaysPerLine[l];
                            state.startAzimuthDeg = state.profile->emitterProfileSoA.azimuthDeg[emitterToCheck];
                            // with one emitter the start and end are the same. otherwise, assume fixed azimuth
                            // difference between emitters in line
                            state.horizontalResolution =
                                state.numRaysPerLine < 2 ?
                                    0 :
                                    state.profile->emitterProfileSoA.azimuthDeg[emitterToCheck + 1] -
                                        state.startAzimuthDeg;
                            endAzimuthDeg =
                                state.startAzimuthDeg + state.horizontalResolution * (state.numRaysPerLine - 1);
                        }
                        // Advance to first emitter in next line
                        emitterToCheck += state.profile->emitterProfileSoA.numRaysPerLine[l];
                    }
                }
                if (state.startAzimuthDeg > endAzimuthDeg)
                {
                    // then it's a solid start that is spinning ccw
                    float tempAzimuth = state.startAzimuthDeg;
                    state.startAzimuthDeg = endAzimuthDeg;
                    endAzimuthDeg = tempAzimuth;
                }
                float horizontalFov = endAzimuthDeg - state.startAzimuthDeg;
                if (horizontalFov > 360.0f)
                {
                    CARB_LOG_WARN_ONCE(
                        "IsaacComputeRTXLidarFlatScan: %s is not not designed to work with Flat Scan data.  When a Solid State lidar is used with this node, there must be a row of evenly spaced emitters all at the same elevation.",
                        state.config.c_str());
                    horizontalFov = 360.0f;
                }
                state.bufferSize = state.numRaysPerLine;
                state.prevIdx = state.profile->rotationDirection == LidarRotationDirection::CW ? state.bufferSize - 1 : 0;
                db.outputs.horizontalFov() = horizontalFov;
                db.outputs.rotationRate() = static_cast<float>(state.profile->scanRateBaseHz);
                db.outputs.azimuthRange() = { state.startAzimuthDeg, endAzimuthDeg };
            }
            else
            {
                CARB_LOG_WARN_ONCE("IsaacComputeRTXLidarFlatScan %s is an unknown scanType.", state.config.c_str());
                db.outputs.numCols() = 0;
                return true;
            }
            if (state.minElevationDeg != 0.0f)
            {
                CARB_LOG_WARN_ONCE(
                    "IsaacComputeRTXLidarFlatScan: lowest elevation emitter line is %f, not 0.", state.minElevationDeg);
            }
            // Reallocate and fill output buffers
            state.distanceBuffer = std::vector<float>(state.bufferSize, -1.0);
            state.intensityBuffer = std::vector<uint8_t>(state.bufferSize, 0);
            state.timestampBuffer = std::vector<double>(state.bufferSize, DBL_MIN);
            // Set outputs common to solid-state and rotary lidars
            db.outputs.depthRange() = { state.profile->nearRangeM, state.profile->farRangeM };
            db.outputs.horizontalResolution() = state.horizontalResolution;
        }

        if ((state.scanType == LidarScanType::kRotary && (!echoIds || !emitterIds || !tickIds)) ||
            (state.scanType == LidarScanType::kSolidState && (!echoIds || !emitterIds)))
        {
            return true;
        }

        db.outputs.exec() = kExecutionAttributeStateDisabled;
        if (state.timeOffset == DBL_MIN)
        {
            state.timeOffset = db.inputs.timeStamp() - helper.m_gmo.timestampNs / 1e9;
        }
        for (uint32_t pointIdx = 0; pointIdx < helper.m_gmo.numElements; pointIdx++)
        {
            if (echoIds[pointIdx])
                continue;
            uint32_t emitterId = emitterIds[pointIdx];
            if ((state.scanType == LidarScanType::kRotary && emitterId == state.emitterToOutput) ||
                (state.scanType == LidarScanType::kSolidState && state.emitterToOutput <= emitterId &&
                 emitterId < (state.emitterToOutput + state.numRaysPerLine)))
            {
                float azimuth = helper.m_gmo.elements.x[pointIdx];
                // Compute index of buffer in which measurements will be placed, based on beam azimuth
                uint32_t idx =
                    static_cast<uint32_t>((azimuth - db.outputs.azimuthRange()[0]) / state.horizontalResolution);
                if (idx >= state.bufferSize)
                {
                    idx = state.bufferSize - 1;
                }
                if (state.prevIdx - idx > state.intensityBuffer.size() / 2)
                {
                    db.outputs.intensitiesData().resize(state.bufferSize);
                    db.outputs.linearDepthData().resize(state.bufferSize);
                    db.outputs.numCols() = static_cast<int>(state.bufferSize);
                    db.outputs.numRows() = 1;
                    db.outputs.timeStamp() = DBL_MIN;
                    for (size_t i = 0; i < state.bufferSize; i++)
                    {
                        db.outputs.intensitiesData().at(i) = state.intensityBuffer[i];
                        db.outputs.linearDepthData().at(i) = state.distanceBuffer[i];
                        size_t inIdx = state.profile->rotationDirection == LidarRotationDirection::CW ?
                                           state.bufferSize - i - 1 :
                                           i;
                        if (db.outputs.timeStamp() == DBL_MIN && state.timestampBuffer[inIdx] != DBL_MIN)
                        {
                            // Set timestamp to first timestamp that's not a sentinel value
                            db.outputs.timeStamp() = state.timestampBuffer[inIdx];
                        }
                    }
                    // Reset local buffers
                    std::fill(state.intensityBuffer.begin(), state.intensityBuffer.end(), 0);
                    std::fill(state.distanceBuffer.begin(), state.distanceBuffer.end(), -1.0);
                    std::fill(state.timestampBuffer.begin(), state.timestampBuffer.end(), DBL_MIN);
                    db.outputs.exec() = kExecutionAttributeStateEnabled;
                }
                // Push latest depth into distance buffer
                float distance = helper.m_gmo.elements.z[pointIdx];
                if (state.minElevationDeg)
                {
                    distance = distance * ::cosf(Deg2Rad(state.minElevationDeg));
                }
                state.distanceBuffer[idx] = distance;
                // Push latest intensity into intensity buffer
                state.intensityBuffer[idx] = static_cast<uint8_t>(helper.m_gmo.elements.scalar[pointIdx] * 255.0f);
                state.timestampBuffer[idx] = helper.m_gmo.timestampNs / 1e9 +
                                             helper.m_gmo.elements.timeOffsetNs[pointIdx] / 1e9 + state.timeOffset;
                state.prevIdx = idx;
            }
        }
        return true;
    }
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
