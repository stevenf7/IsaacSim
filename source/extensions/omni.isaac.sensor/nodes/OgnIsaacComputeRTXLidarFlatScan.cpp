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
    uint32_t emitterToOutput{ 0 };
    int numRaysPerLine{ -1 };
    float startAzimuthDeg;
    float horizontalResolution;
    EmitterProfile* emitterProfile;
    bool mRightHanded = true; // TODO make parameter?
    uint32_t numTicksPerRotation;
    std::vector<uint8_t> intensityBuffer;
    std::vector<float> distanceBuffer;

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
                state.emitterProfile = &state.rotaryProfile.emitterStates[0].emitterProfiles[state.emitterToOutput];
                float minElevation = ::fabs(state.emitterProfile->elevationDeg);
                for (int s = 0; s < (int)state.rotaryProfile.emitterStateCount; s++)
                {
                    for (int i = 0; i < (int)state.rotaryProfile.numberOfEmitters; i++)
                    {
                        float curElevation = ::fabs(state.rotaryProfile.emitterStates[s].emitterProfiles[i].elevationDeg);
                        if (curElevation < minElevation)
                        {
                            minElevation = curElevation;
                            state.emitterToOutput = i;
                            state.emitterProfile = &state.rotaryProfile.emitterStates[s].emitterProfiles[i];
                        }
                    }
                }
                if (minElevation != 0.0f)
                {
                    CARB_LOG_WARN_ONCE("IsaacComputeRTXLidarFlatScan: lowest elevation emitter is %f, not 0.",
                                       state.emitterProfile->elevationDeg);
                }
                // Set useful state variables
                state.numTicksPerRotation = state.rotaryProfile.reportRateBaseHz / state.rotaryProfile.scanRateBaseHz;
                state.horizontalResolution = static_cast<float>(360.0 / state.numTicksPerRotation);
                state.intensityBuffer.resize(state.numTicksPerRotation);
                state.distanceBuffer.resize(state.numTicksPerRotation);
                // Populate config-based outputs
                db.outputs.azimuthRange() = { -180.0f, 180.0f };
                db.outputs.depthRange() = {
                    state.rotaryProfile.nearRangeM,
                    state.rotaryProfile.farRangeM,
                };
                // db.outputs.intensitiesData().resize(state.numTicksPerRotation);
                // db.outputs.linearDepthData().resize(state.numTicksPerRotation);
                db.outputs.horizontalFov() = 360.0;
                db.outputs.horizontalResolution() = state.horizontalResolution;
                db.outputs.rotationRate() = static_cast<float>(state.rotaryProfile.scanRateBaseHz);
            }
            else if (state.scanType == LidarScanType::kSolidState)
            {
                // Find the solid state line with the lowest elevation.
                // gather the start and end Azimuth of the line while at it as well
                float endAzimuthDeg = 361.0;
                float minElevation = 91.0; // 90 is max, so fist emitter state will always at least be picked.
                for (int s = 0; s < (int)state.solidStateProfile.emitterStateCount; s++)
                {
                    int emitterToCheck = 0; // will be adding number of emitters in line as I iterate over the lines.
                    for (int l = 0; l < (int)state.solidStateProfile.numLines; l++)
                    {
                        float curElevation =
                            ::fabs(state.solidStateProfile.emitterStates[s].emitterProfiles[emitterToCheck].elevationDeg);
                        if (curElevation < minElevation)
                        {
                            minElevation = curElevation;
                            state.emitterToOutput = emitterToCheck;
                            state.emitterProfile =
                                &state.solidStateProfile.emitterStates[s].emitterProfiles[emitterToCheck];
                            state.startAzimuthDeg =
                                state.solidStateProfile.emitterStates[s].emitterProfiles[emitterToCheck].azimuthDeg;
                            state.numRaysPerLine = state.solidStateProfile.numRaysPerLine[l];
                            // with one emitter the start and end are the same.
                            state.horizontalResolution =
                                state.numRaysPerLine < 2 ?
                                    0 :
                                    state.solidStateProfile.emitterStates[s].emitterProfiles[emitterToCheck + 1].azimuthDeg -
                                        state.startAzimuthDeg;
                            endAzimuthDeg =
                                state.startAzimuthDeg + state.horizontalResolution * (state.numRaysPerLine - 1);
                        }
                        emitterToCheck += state.solidStateProfile.numRaysPerLine[l];
                    }
                }
                if (minElevation != 0.0f)
                {
                    CARB_LOG_WARN_ONCE("IsaacComputeRTXLidarFlatScan: lowest elevation emitter line is %f, not 0.",
                                       state.emitterProfile->elevationDeg);
                }
                if (state.startAzimuthDeg > endAzimuthDeg)
                {
                    // then it's a solid start that is spinning ccw
                    float tempAzimuth = state.startAzimuthDeg;
                    state.startAzimuthDeg = endAzimuthDeg;
                    endAzimuthDeg = tempAzimuth;
                }
                if (endAzimuthDeg - state.startAzimuthDeg > 360.0f)
                {
                    CARB_LOG_WARN_ONCE(
                        "IsaacComputeRTXLidarFlatScan: %s is not not designed to work with Flat Scan data.  When a Solid State lidar is used with this node, there must be a row of evenly spaced emitters all at the same elevation.",
                        state.config.c_str());
                    endAzimuthDeg = state.startAzimuthDeg + 360.0f;
                }
                db.outputs.azimuthRange() = { state.startAzimuthDeg, endAzimuthDeg };
                db.outputs.depthRange() = {
                    state.solidStateProfile.nearRangeM,
                    state.solidStateProfile.farRangeM,
                };
                float horizontalFov = endAzimuthDeg - state.startAzimuthDeg;
                state.horizontalResolution = horizontalFov / (state.numRaysPerLine - 1);
                state.intensityBuffer.resize(state.numRaysPerLine);
                state.distanceBuffer.resize(state.numRaysPerLine);
                db.outputs.horizontalFov() = horizontalFov;
                db.outputs.horizontalResolution() = state.horizontalResolution;
                db.outputs.rotationRate() = static_cast<float>(state.solidStateProfile.scanRateBaseHz);
                db.outputs.intensitiesData().resize(state.numRaysPerLine);
                db.outputs.linearDepthData().resize(state.numRaysPerLine);
            }
            else
            {
                CARB_LOG_WARN_ONCE("IsaacComputeRTXLidarFlatScan %s is an unknown scanType.", state.config.c_str());
                db.outputs.numCols() = 0;
                return true;
            }
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
                float azimuth = helper.m_gmo.elements.x[pointIdx];
                float distance = helper.m_gmo.elements.z[pointIdx];
                uint8_t intensity = static_cast<uint8_t>(helper.m_gmo.elements.scalar[pointIdx] * 255.0f);
                if (state.emitterProfile->elevationDeg)
                {
                    distance = distance * ::cosf(Deg2Rad(state.emitterProfile->elevationDeg));
                }

                // Azimuth angle of lidar ticks moves CCW from 0 -> -180 -> 180 -> 0
                // Fill buffers by mapping azimuth angle of flat scan between min/max azimuth of lidar.
                size_t outIdx = static_cast<size_t>((azimuth - db.outputs.azimuthRange()[0]) /
                                                    (db.outputs.azimuthRange()[1] - db.outputs.azimuthRange()[0])) *
                                state.intensityBuffer.size();
                if (outIdx < 0)
                {
                    CARB_LOG_WARN("Unexpected azimuth %f < minAzimuth %f; setting azimuth to minAzimuth.", azimuth,
                                  db.outputs.azimuthRange()[0]);
                    outIdx = 0;
                }
                else if (outIdx >= state.intensityBuffer.size())
                {
                    CARB_LOG_WARN("Unexpected azimuth %f > maxAzimuth %f; setting azimuth to maxAzimuth.", azimuth,
                                  db.outputs.azimuthRange()[1]);
                    outIdx = state.intensityBuffer.size() - 1;
                }
                state.intensityBuffer.at(outIdx) = intensity;
                state.distanceBuffer.at(outIdx) = distance;

                // Buffers are considered full when we reach min azimuth, meaning we first issue a partial scan,
                // then subsequently issue full scans.
                if (outIdx == 0)
                {
                    db.outputs.intensitiesData().resize(state.intensityBuffer.size());
                    db.outputs.linearDepthData().resize(state.distanceBuffer.size());
                    db.outputs.numCols() = static_cast<int>(state.intensityBuffer.size());
                    db.outputs.numRows() = 1;
                    // Copy local buffers into output buffers, then reset local buffers
                    for (size_t i = 0; i < state.intensityBuffer.size(); i++)
                    {
                        db.outputs.intensitiesData().at(i) = state.intensityBuffer[i];
                        db.outputs.linearDepthData().at(i) = state.distanceBuffer[i];
                    }
                    std::fill(state.intensityBuffer.begin(), state.intensityBuffer.end(), 0);
                    std::fill(state.distanceBuffer.begin(), state.distanceBuffer.end(), -1.0f);

                    // Enable downstream nodes to execute
                    db.outputs.exec() = kExecutionAttributeStateEnabled;
                }
            }
        }
        return true;
    }
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
