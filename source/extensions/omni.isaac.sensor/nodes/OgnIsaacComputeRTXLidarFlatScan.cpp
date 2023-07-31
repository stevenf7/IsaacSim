// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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

#include "omni/isaac/utils/UsdUtilities.h"

#include <internal/omni/sensors/lidar/LidarReturnHelper.h>
#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarReturn.h>
#include <omni/sensors/lidar/LidarReturnTypes.h>

#include <OgnIsaacComputeRTXLidarFlatScanDatabase.h>
#include <fstream>
#include <math.h>

namespace omni
{
namespace isaac
{
namespace sensor
{

#define PI 3.141592653589f

inline constexpr float Deg2Rad(float deg)
{
    return (deg / 180.f) * PI;
}

class OgnIsaacComputeRTXLidarFlatScan : public BaseResetNode
{
public:
    static bool compute(OgnIsaacComputeRTXLidarFlatScanDatabase& db)
    {

        auto& state = db.internalState<OgnIsaacComputeRTXLidarFlatScan>();

        uint8_t* input = reinterpret_cast<uint8_t*>(db.inputs.cpuPointer());
        if (!input)
        {
            return true;
        }

        // fill the structure of arrays
        LidarTicks lidarTicks;
        LidarReturns lidarReturns;
        LidarParameterType* parameter = omni::sensors::nv::lidar::fillStructsFromBuffer(input, lidarReturns, lidarTicks);
        const uint32_t numTicks = parameter->async.numTicks;
        const uint32_t numChannels = parameter->async.numChannels;
        const uint32_t numEchos = parameter->async.numEchos;

        if (numTicks == 0 || numChannels * numEchos == 0)
        {
            return true;
        }


        for (uint32_t tick = 0; tick < numTicks; tick++)
        {
            for (uint32_t channelId = 0; channelId < numChannels; ++channelId)
            {
                const uint32_t echoId = 0;
                const uint32_t pointIdx{ idxOfReturn(channelId, echoId, numEchos, numChannels, tick) };

                if (!state.mFoundLevelChannelId)
                {

                    if (abs(lidarReturns.elevations[pointIdx]) > abs(state.mElevationDiff))
                    {
                        state.mFoundLevelChannelId = true;
                        return true;
                    }
                    state.mLevelChannelId = channelId;
                    state.mElevationDiff = lidarReturns.elevations[pointIdx];
                }
                else
                {

                    if (channelId == state.mLevelChannelId && lidarReturns.elevations[pointIdx] == state.mElevationDiff)
                    {

                        if (!state.mFoundStartAzimuth)
                        {
                            if (lidarReturns.azimuths[pointIdx] > state.mStartAzimuth)
                            {
                                state.mFoundStartAzimuth = true;

                                state.mRanges.clear();
                                state.mIntensities.clear();

                                state.mRanges.push_back(lidarReturns.distances[pointIdx]);
                                state.mIntensities.push_back((uint8_t)(lidarReturns.intensities[pointIdx] * 255));
                            }
                            state.mStartAzimuth = lidarReturns.azimuths[pointIdx];
                            state.mPrevAzimuth = state.mStartAzimuth;
                        }
                        else
                        {
                            if (lidarReturns.azimuths[pointIdx] < state.mPrevAzimuth)
                            {
                                if (abs(lidarReturns.azimuths[pointIdx] - state.mPrevAzimuth) <
                                    db.outputs.horizontalFov() * 0.9)
                                {
                                    state.mFoundStartAzimuth = false;
                                    state.mStartAzimuth = FLT_MAX;
                                    state.mPrevAzimuth = FLT_MIN;
                                    return true;
                                }
                                float startAzimuth = state.mStartAzimuth;
                                float endAzimuth = state.mPrevAzimuth;

                                size_t numPoints = state.mRanges.size();

                                db.outputs.horizontalFov() = endAzimuth - startAzimuth;
                                db.outputs.horizontalResolution() =
                                    (endAzimuth - startAzimuth) / static_cast<float>(numPoints);

                                db.outputs.depthRange() = { 0, 200 };
                                db.outputs.rotationRate() = parameter->async.scanFrequency;


                                db.outputs.linearDepthData.resize(numPoints);
                                db.outputs.intensitiesData.resize(numPoints);

                                // Reverse copy when right handed lidar
                                if (state.mRightHanded)
                                {
                                    std::reverse_copy(std::begin(state.mRanges), std::end(state.mRanges),
                                                      std::begin(db.outputs.linearDepthData()));
                                    std::reverse_copy(std::begin(state.mIntensities), std::end(state.mIntensities),
                                                      std::begin(db.outputs.intensitiesData()));
                                }
                                else
                                {
                                    std::memcpy(db.outputs.linearDepthData().data(), &state.mRanges[0],
                                                state.mRanges.size() * sizeof(float));
                                    std::memcpy(db.outputs.intensitiesData().data(), &state.mIntensities[0],
                                                state.mIntensities.size() * sizeof(uint8_t));
                                }


                                db.outputs.numRows() = 1;
                                db.outputs.numCols() = static_cast<int>(numPoints);

                                db.outputs.azimuthRange() = { Deg2Rad(startAzimuth), Deg2Rad(endAzimuth) };

                                db.outputs.execOut() = kExecutionAttributeStateEnabled;


                                // Reset start Azimuth
                                state.mStartAzimuth = lidarReturns.azimuths[pointIdx];

                                state.mRanges.clear();
                                state.mIntensities.clear();
                            }
                            state.mRanges.push_back(lidarReturns.distances[pointIdx]);
                            state.mIntensities.push_back((uint8_t)(lidarReturns.intensities[pointIdx] * 255));
                            state.mPrevAzimuth = lidarReturns.azimuths[pointIdx];
                        }
                    }
                }
            }
        }

        return true;
    }

    virtual void reset()
    {
        mFoundLevelChannelId = false;
        mLevelChannelId = 0;
        mElevationDiff = FLT_MAX;

        mFoundStartAzimuth = false;
        mStartAzimuth = FLT_MAX;
        mPrevAzimuth = FLT_MIN;
    }


private:
    std::vector<float> mRanges;
    std::vector<uint8_t> mIntensities;

    bool mFoundLevelChannelId = false;
    uint32_t mLevelChannelId = 0;
    float mElevationDiff = FLT_MAX;

    bool mFoundStartAzimuth = false;
    float mStartAzimuth = FLT_MAX;
    float mPrevAzimuth = FLT_MIN;

    bool mRightHanded = true;
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
