// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/math/linalg/matrix.h>
#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>
#include <omni/sensors/lidar/LidarReturnTypes.h>

namespace omni
{
namespace isaac
{
namespace sensor
{

inline constexpr float Deg2Rad(float deg)
{
    return (deg / 180.f) * 3.141592653589f;
}
inline uint32_t idxOfReturn(const uint32_t beamId,
                            const uint32_t echoId,
                            const uint32_t numEchos,
                            const uint32_t numBeams = 0,
                            const uint32_t tick = 0)
{
    return beamId * numEchos + echoId + tick * numEchos * numBeams;
}


void getTransformFromLidarAsyncParameter(const LidarAsyncParameter& parm, omni::math::linalg::matrix4d& matrixOutput);
bool updateLidarConfig(std::string inConfig,
                       std::string& config,
                       LidarScanType& scanType,
                       LidarRotaryProfile& rotaryProfile,
                       LidarSolidStateProfile& solidStateProfile);
inline LidarParameterType* saferFillStructsFromBuffer(uint8_t* buffer, LidarReturns& returns, LidarTicks& ticks)
{
    ticks.azimuths = nullptr;
    ticks.states = nullptr;
    ticks.timestamps = nullptr;
    returns.azimuths = nullptr;
    returns.elevations = nullptr;
    returns.distances = nullptr;
    returns.intensities = nullptr;
    returns.velocities = nullptr;
    returns.hitPointNormals = nullptr;
    returns.deltaTimes = nullptr;
    returns.emitterIds = nullptr;
    returns.beamIds = nullptr;
    returns.materialIds = nullptr;
    returns.objectIds = nullptr;
    LidarParameterType* parameter = reinterpret_cast<LidarParameterType*>(buffer);
    if (!parameter || parameter->sync.numTicks != parameter->async.numTicks)
        return nullptr;

    const size_t numTicks{ static_cast<size_t>(parameter->sync.numTicks) };
    const size_t numReturns{ static_cast<size_t>(parameter->async.numEchos * parameter->async.numChannels *
                                                 parameter->async.numTicks) };
    if (!numReturns || !numTicks)
        return parameter;

    size_t offset = sizeof(LidarParameterType);

    ticks.azimuths = reinterpret_cast<float*>(buffer + offset);
    offset += sizeof(float) * numTicks;
    ticks.states = reinterpret_cast<uint32_t*>(buffer + offset);
    offset += sizeof(uint32_t) * numTicks;
    ticks.timestamps = reinterpret_cast<uint64_t*>(buffer + offset);
    offset += sizeof(uint64_t) * numTicks;
    // Returns
    returns.azimuths = reinterpret_cast<float*>(buffer + offset);
    offset += sizeof(float) * numReturns;
    returns.elevations = reinterpret_cast<float*>(buffer + offset);
    offset += sizeof(float) * numReturns;
    returns.distances = reinterpret_cast<float*>(buffer + offset);
    offset += sizeof(float) * numReturns;
    returns.intensities = reinterpret_cast<float*>(buffer + offset);
    offset += sizeof(float) * numReturns;
    returns.velocities = reinterpret_cast<float*>(buffer + offset);
    offset += sizeof(float) * numReturns * 3;
    returns.hitPointNormals = reinterpret_cast<float*>(buffer + offset);
    offset += sizeof(float) * numReturns * 3;
    returns.deltaTimes = reinterpret_cast<uint32_t*>(buffer + offset);
    offset += sizeof(uint32_t) * numReturns;
    returns.emitterIds = reinterpret_cast<uint32_t*>(buffer + offset);
    offset += sizeof(uint32_t) * numReturns;
    returns.beamIds = reinterpret_cast<uint32_t*>(buffer + offset);
    offset += sizeof(uint32_t) * numReturns;
    returns.materialIds = reinterpret_cast<uint32_t*>(buffer + offset);
    offset += sizeof(uint32_t) * numReturns;
    returns.objectIds = reinterpret_cast<uint32_t*>(buffer + offset);
    return parameter;
}
}
}
}
