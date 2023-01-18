// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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

#    include "omni/isaac/utils/UsdUtilities.h"

// #include <omni/isaac/range_sensor/RangeSensorInterface.h>
#    include <omni/isaac/utils/BaseResetNode.h>
// #include <rangeSensorSchema/lidar.h>
#    include <omni/sensors/lidar/LidarParameterType.h>
#    include <omni/sensors/lidar/LidarReturn.h>
#    include <omni/sensors/lidar/LidarReturnTypes.h>

#    include <OgnIsaacComputeRTXLidarFlatScanDatabase.h>
#    include <fstream>
#    include <math.h>

namespace omni
{
namespace isaac
{
namespace sensor
{

#    define PI 3.141592653589f

inline constexpr float Deg2Rad(float deg)
{
    return (deg / 180.f) * PI;
}

class OgnIsaacComputeRTXLidarFlatScan : public BaseResetNode
{
public:
    static bool compute(OgnIsaacComputeRTXLidarFlatScanDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnIsaacComputeRTXLidarFlatScan>();

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

        // const LidarTick* lidarTicks = reinterpret_cast<const LidarTick*>(input + sizeof(LidarParameterType));
        const LidarReturn* lidarReturns = reinterpret_cast<const LidarReturn*>(
            input + sizeof(LidarParameterType) + sizeof(LidarTick) * parameter->async.numTicks);


        for (uint32_t tick = 0; tick < parameter->async.numTicks; tick++)
        {
            for (uint32_t channelId = 0; channelId < parameter->async.numChannels; ++channelId)
            {
                const uint32_t echoId = 0;
                const uint32_t pointIdx{ idxOfReturn(
                    channelId, echoId, parameter->async.numEchos, parameter->async.numChannels, tick) };
                const LidarReturn& lidarReturn = lidarReturns[pointIdx];

                if (!state.mFoundLevelChannelId)
                {

                    if (abs(lidarReturn.elevationDeg) > abs(state.mElevationDiff))
                    {
                        state.mFoundLevelChannelId = true;
                        return true;
                    }
                    state.mLevelChannelId = channelId;
                    state.mElevationDiff = lidarReturn.elevationDeg;
                }
                else
                {
                    // const float azimuthDeg{ state.mRightHanded ? (360.f - lidarReturn.azimuthDeg) :
                    // lidarReturn.azimuthDeg };

                    if (channelId == state.mLevelChannelId && lidarReturn.elevationDeg == state.mElevationDiff)
                    {

                        if (!state.mFoundStartAzimuth)
                        {
                            if (lidarReturn.azimuthDeg > state.mStartAzimuth)
                            {
                                state.mFoundStartAzimuth = true;

                                state.mRanges.clear();
                                state.mIntensities.clear();

                                state.mRanges.push_back(lidarReturn.distance);
                                state.mIntensities.push_back((uint8_t)(lidarReturn.intensity * 255));
                            }
                            state.mStartAzimuth = lidarReturn.azimuthDeg;
                            state.mPrevAzimuth = state.mStartAzimuth;
                        }
                        else
                        {
                            if (lidarReturn.azimuthDeg < state.mPrevAzimuth)
                            {
                                if (abs(lidarReturn.azimuthDeg - state.mPrevAzimuth) < db.outputs.horizontalFov() * 0.9)
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
                                state.mStartAzimuth = lidarReturn.azimuthDeg;

                                state.mRanges.clear();
                                state.mIntensities.clear();
                            }
                            state.mRanges.push_back(lidarReturn.distance);
                            state.mIntensities.push_back((uint8_t)(lidarReturn.intensity * 255));
                            state.mPrevAzimuth = lidarReturn.azimuthDeg;
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
#endif
