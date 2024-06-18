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
#include "omni/isaac/utils/UsdUtilities.h"

#include <omni/sensors/GenericModelOutput.h>

#include <OgnIsaacComputeRTXLidarFlatScanDatabase.h>
#include <math.h>

namespace omni
{
namespace isaac
{
namespace sensor
{

// a scan buffer that takes only one emitter, as nearest 0 elevation, and has to be from a rotary lidar.
// because it creates laser scan data which assumes 0 elevation emitter with all the same delta for emitter rotation
// and time.
class OgnIsaacComputeRTXLidarFlatScan : public LidarConfigHelper
{
private:
    // ID of emitter at lowest elevation (rotary) or ID of first emitter of lowest-elevation line (solid-state)
    uint32_t emitterToOutput{ 0 };
    // Number of emitters in lowest-elevation line (solid-state only)
    int numRaysPerLine{ -1 };
    float startAzimuthDeg;
    float horizontalResolution;
    float minElevationDeg; // absolute-value of elevation of lowest-elevation emitter
    bool mRightHanded = true; // TODO make parameter?
    std::vector<uint8_t> intensityBuffer;
    std::vector<float> distanceBuffer;
    float prevAzimuth{ FLT_MAX }; // azimuth of previous return incorporated into flat scan
    float minAzimuth{ FLT_MAX }; // minimum azimuth of flat scan
    float maxAzimuth{ -FLT_MAX }; // mazimum azimuth of flat scan

    /**
     * @brief Populates output buffers for node. See compute method for details on when to call.
     *
     * @param db - holds state information
     * @param azimuth - current azimuth
     * @param fwdAzimuth - set to previous azimuth, final azimuth to be written to buffers.
     * @param backAzimuth - set to current azimuth, first azimuth to be written on next call to this method.
     */
    void populateBuffers(OgnIsaacComputeRTXLidarFlatScanDatabase& db,
                         const float azimuth,
                         float& fwdAzimuth,
                         float& backAzimuth)
    {
        auto& state = db.perInstanceState<OgnIsaacComputeRTXLidarFlatScan>();
        fwdAzimuth = state.prevAzimuth;

        size_t bufferSize = state.intensityBuffer.size();
        db.outputs.intensitiesData().resize(bufferSize);
        db.outputs.linearDepthData().resize(bufferSize);
        db.outputs.numCols() = static_cast<int>(bufferSize);
        db.outputs.numRows() = 1;
        db.outputs.azimuthRange() = { state.minAzimuth, state.maxAzimuth };
        // Fill output buffers in in order of increasing azimuth - i.e reverse order if CW, foward order if CCW.
        for (size_t i = 0; i < bufferSize; i++)
        {
            size_t inIdx = state.profile->rotationDirection == LidarRotationDirection::CW ? bufferSize - i - 1 : i;
            db.outputs.intensitiesData().at(i) = state.intensityBuffer[inIdx];
            db.outputs.linearDepthData().at(i) = state.distanceBuffer[inIdx];
        }

        // Reset local buffers
        state.intensityBuffer = std::vector<uint8_t>();
        state.distanceBuffer = std::vector<float>();

        backAzimuth = azimuth;
    }

public:
    static bool compute(OgnIsaacComputeRTXLidarFlatScanDatabase& db)
    {

        db.outputs.numRows() = 1;
        uint8_t* dataPtr = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        // no reason to update the scan buffer if there is no dataHost
        if (!dataPtr)
        {
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
                uint32_t numTicksPerRotation = state.getTicksPerScan();
                state.horizontalResolution = static_cast<float>(360.0 / numTicksPerRotation);
                // Populate config-based outputs
                db.outputs.horizontalFov() = 360.0;
                db.outputs.rotationRate() = static_cast<float>(state.profile->scanRateBaseHz);
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
                db.outputs.horizontalFov() = horizontalFov;
                db.outputs.rotationRate() = static_cast<float>(state.profile->scanRateBaseHz);
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
        for (uint32_t pointIdx = 0; pointIdx < helper.m_gmo.numElements; pointIdx++)
        {
            if (echoIds[pointIdx])
                continue;
            uint32_t emitterId = emitterIds[pointIdx];
            if ((state.scanType == LidarScanType::kRotary && emitterId == state.emitterToOutput) ||
                (state.scanType == LidarScanType::kSolidState && state.emitterToOutput <= emitterId &&
                 emitterId < (state.emitterToOutput + state.numRaysPerLine)))
            {
                // Accumulate depth values until the azimuth value "flips" from -180 deg -> 180 deg (CW) or 180 deg ->
                // -180 deg (CCW), marking a complete rotation, then publish data.
                float azimuth = helper.m_gmo.elements.x[pointIdx];
                if (state.profile->rotationDirection == LidarRotationDirection::CW)
                {
                    if (state.maxAzimuth == -FLT_MAX)
                    {
                        // Azimuth decreases through the rotation, so we set max azimuth to the first azimuth value
                        // we encounter if it's at the sentinel value.
                        state.maxAzimuth = azimuth;
                    }
                    if (azimuth > state.prevAzimuth)
                    {
                        // We've "flipped" azimuth sign, so populate the buffers and enable output.
                        state.populateBuffers(db, azimuth, state.minAzimuth, state.maxAzimuth);
                        db.outputs.exec() = kExecutionAttributeStateEnabled;
                    }
                }
                else
                {
                    if (state.minAzimuth == FLT_MAX)
                    {
                        // Azimuth increases through the rotation, so we set min azimuth to the first azimuth value
                        // we encounter if it's at the sentinel value.
                        state.minAzimuth = azimuth;
                    }
                    if (azimuth < state.prevAzimuth)
                    {
                        // We've "flipped" azimuth sign, so populate the buffers and enable output.
                        state.populateBuffers(db, azimuth, state.maxAzimuth, state.minAzimuth);
                        db.outputs.exec() = kExecutionAttributeStateEnabled;
                    }
                }
                // Push latest depth into distance buffer
                float distance = helper.m_gmo.elements.z[pointIdx];
                if (state.minElevationDeg)
                {
                    distance = distance * ::cosf(Deg2Rad(state.minElevationDeg));
                }
                state.distanceBuffer.push_back(distance);
                // Push latest intensity into intensity buffer
                uint8_t intensity = static_cast<uint8_t>(helper.m_gmo.elements.scalar[pointIdx] * 255.0f);
                state.intensityBuffer.push_back(intensity);
                state.prevAzimuth = azimuth;
            }
        }
        return true;
    }
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
