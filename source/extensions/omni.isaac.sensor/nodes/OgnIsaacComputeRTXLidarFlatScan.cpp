// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarReturn.h>
#include <omni/sensors/lidar/LidarReturnTypes.h>

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
class OgnIsaacComputeRTXLidarFlatScan
{
private:
    std::string config;
    LidarScanType scanType{ LidarScanType::kUnknown };
    LidarRotaryProfile rotaryProfile;
    LidarSolidStateProfile solidStateProfile;
    int emitterToOutput{ -1 };
    int numRaysPerLine{ -1 };
    int emitterStateToOutput{ -1 };
    float startAzimuthDeg;
    float horizontalResolution;
    EmitterProfile* emitterProfile;
    bool mRightHanded = true; // TODO make parameter?

public:
    static bool compute(OgnIsaacComputeRTXLidarFlatScanDatabase& db)
    {

        uint8_t* dataHost = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        // no reason to update the scan buffer if there is no dataHost
        if (!dataHost)
        {
            return true;
        }
        auto& state = db.perInstanceState<OgnIsaacComputeRTXLidarFlatScan>();

        // fill the structure of arrays
        LidarTicks lidarTicksHost;
        LidarReturns lidarReturnsHost;
        LidarParameterType* parameterHost = saferFillStructsFromBuffer(dataHost, lidarReturnsHost, lidarTicksHost);
        if (!parameterHost)
            return true;
        const uint32_t numTicks = parameterHost->async.numTicks;
        const uint32_t numChannels = parameterHost->async.numChannels;
        const uint32_t numEchos = parameterHost->async.numEchos;
        const uint32_t startTick = parameterHost->async.startTick;

        if (numTicks == 0 || numChannels * numEchos == 0)
        {
            return true;
        }

        std::string curConfig = "";
        pxr::UsdAttribute configAttr = omni::isaac::utils::getCameraAttributeFromRenderProduct(
            "sensorModelConfig", db.tokenToString(db.inputs.renderProductPath()));
        if (configAttr.IsValid())
        {
            omni::isaac::utils::safeGetAttribute(configAttr, curConfig);
        }
        bool configUpdated =
            updateLidarConfig(curConfig, state.config, state.scanType, state.rotaryProfile, state.solidStateProfile);
        if (configUpdated)
        {
            if (state.scanType == LidarScanType::kRotary)
            {
                state.emitterToOutput = 0;
                state.emitterStateToOutput = 0;
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
                            state.emitterStateToOutput = s;
                            state.emitterProfile = &state.rotaryProfile.emitterStates[s].emitterProfiles[i];
                        }
                    }
                }
                if (minElevation != 0.0f)
                {
                    CARB_LOG_WARN_ONCE("IsaacComputeRTXLidarFlatScan: lowest elevation emitter is %f, not 0.",
                                       state.rotaryProfile.emitterStates[state.emitterStateToOutput]
                                           .emitterProfiles[state.emitterToOutput]
                                           .elevationDeg);
                }
                float startAzimuth = state.emitterProfile->azimuthDeg;
                db.outputs.azimuthRange() = {
                    (state.rotaryProfile.startAzimuthDeg + startAzimuth) * static_cast<float>(M_PI / 180.0f),
                    (state.rotaryProfile.endAzimuthDeg + startAzimuth) * static_cast<float>(M_PI / 180.0f),
                };
                db.outputs.depthRange() = {
                    state.rotaryProfile.nearRangeM,
                    state.rotaryProfile.farRangeM,
                };
                // state.rotaryProfile.reportRateBaseHz; // 3600 for a 10Hz lidar that fires one tick per degree.
                // state.rotaryProfile.scanRateBaseHz; // 10 for a 10Hz lidar
                uint32_t numTicksPerRotation = state.rotaryProfile.reportRateBaseHz / state.rotaryProfile.scanRateBaseHz;
                // state.rotaryProfile.scanRateBaseHz
                //          << " " << numTicksPerRotation << "\n";
                db.outputs.horizontalFov() = 360.0;
                state.horizontalResolution = static_cast<float>(360.0 / numTicksPerRotation);
                db.outputs.horizontalResolution() = state.horizontalResolution;
                db.outputs.numRows() = 1;
                db.outputs.numCols() = numTicksPerRotation;
                db.outputs.rotationRate() = static_cast<float>(state.rotaryProfile.scanRateBaseHz);
                db.outputs.intensitiesData().resize(numTicksPerRotation);
                db.outputs.linearDepthData().resize(numTicksPerRotation);

                // assert(numTicksPerRotation == parameterHost->async.ticksPerScan);
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
                            state.emitterStateToOutput = s;
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
                                       state.solidStateProfile.emitterStates[state.emitterStateToOutput]
                                           .emitterProfiles[state.emitterToOutput]
                                           .elevationDeg);
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
                db.outputs.azimuthRange() = {
                    state.startAzimuthDeg * static_cast<float>(M_PI / 180.0f),
                    endAzimuthDeg * static_cast<float>(M_PI / 180.0f),
                };
                db.outputs.depthRange() = {
                    state.solidStateProfile.nearRangeM,
                    state.solidStateProfile.farRangeM,
                };
                float horizontalFov = endAzimuthDeg - state.startAzimuthDeg;
                db.outputs.horizontalFov() = horizontalFov;
                state.horizontalResolution = horizontalFov / (state.numRaysPerLine - 1);
                db.outputs.horizontalResolution() = state.horizontalResolution;
                db.outputs.numRows() = 1;
                db.outputs.numCols() = state.numRaysPerLine;
                db.outputs.rotationRate() = static_cast<float>(state.solidStateProfile.scanRateBaseHz);
                db.outputs.intensitiesData().resize(state.numRaysPerLine);
                db.outputs.linearDepthData().resize(state.numRaysPerLine);
                uint8_t* intensitiesData = db.outputs.intensitiesData().data();
                float* linearDepthData = db.outputs.linearDepthData().data();
                // Some solid state configs may not hit all the indices, do get rid of trash data.
                for (int i = 0; i < state.numRaysPerLine; ++i)
                {
                    intensitiesData[i] = 0;
                    linearDepthData[i] = 0.0;
                }
            }
            else
            {

                CARB_LOG_WARN_ONCE("IsaacComputeRTXLidarFlatScan %s is an unknown scanType.", curConfig.c_str());
                return true;
            }
        }

        uint8_t* intensities = db.outputs.intensitiesData().data();
        float* distances = db.outputs.linearDepthData().data();
        if (state.scanType == LidarScanType::kRotary)
        {
            for (uint32_t tick = 0; tick < numTicks; tick++)
            {
                uint32_t channelId = state.emitterToOutput;

                const uint32_t echoId = 0;
                const uint32_t pointIdx{ idxOfReturn(channelId, echoId, numEchos, numChannels, tick) };
                uint8_t intensity{ static_cast<uint8_t>(lidarReturnsHost.intensities[pointIdx] * 255.0f) };
                float distance{ lidarReturnsHost.distances[pointIdx] };
                if (state.emitterProfile->elevationDeg)
                {
                    distance = distance * ::cosf(Deg2Rad(state.emitterProfile->elevationDeg));
                }
                uint32_t outIdx = (startTick + tick) % parameterHost->async.ticksPerScan;
                // reverse output indices if right handed
                if (state.mRightHanded)
                    outIdx = parameterHost->async.ticksPerScan - 1 - outIdx;
                intensities[outIdx] = intensity;
                distances[outIdx] = distance;
            }
        }
        else if (state.scanType == LidarScanType::kSolidState)
        {
            uint32_t maxIndex = static_cast<uint32_t>(360.f / state.horizontalResolution);
            // Solid State is always 1 tick
            for (int i = 0; i < (int)numChannels; i++)
            {
                // returnsIdx is the index into lidarReturnsHost arrays.
                int returnsIdx = i * numEchos;
                int emitterId = static_cast<int>(lidarReturnsHost.emitterIds[returnsIdx]);
                // We only use one line from the solid state emitter
                if (emitterId >= state.emitterToOutput && emitterId < (state.emitterToOutput + state.numRaysPerLine))
                {
                    uint8_t intensity{ static_cast<uint8_t>(lidarReturnsHost.intensities[returnsIdx] * 255.0f) };
                    float distance{ lidarReturnsHost.distances[returnsIdx] };
                    if (state.emitterProfile->elevationDeg)
                    {
                        distance = distance * ::cosf(Deg2Rad(state.emitterProfile->elevationDeg));
                    }
                    // outIdx is the index into intensities and distances arrays, and the 0 entry to that will be at
                    // the azimuthRange()[0]
                    float azimuth = lidarReturnsHost.azimuths[returnsIdx];
                    if (azimuth > 180.0f)
                    {
                        azimuth -= 360.0f;
                    }
                    int outIdx = static_cast<int>(((azimuth - state.startAzimuthDeg) + 0.1 * state.horizontalResolution) /
                                                  state.horizontalResolution);
                    outIdx %= maxIndex;
                    if (outIdx >= 0 && outIdx < state.numRaysPerLine)
                    {
                        if (state.mRightHanded)
                            outIdx = state.numRaysPerLine - 1 - outIdx;
                        intensities[outIdx] = intensity;
                        distances[outIdx] = distance;
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
