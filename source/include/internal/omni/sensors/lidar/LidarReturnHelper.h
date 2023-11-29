// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <omni/sensors/cuda/CudaHelperDecl.h>
#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarReturnTypes.h>

namespace omni
{
namespace sensors
{
namespace nv
{
namespace lidar
{

// Helper Functions
inline void cpyToBuffer(uint8_t* buffer,
                        const LidarParameterType* parameter,
                        const LidarReturns& returns,
                        const LidarTicks& ticks,
                        const cudaMemcpyKind& kind,
                        const cudaStream_t& stream = nullptr)
{

    // Parameter already on host
    {
        LidarParameterType* bufferParam = reinterpret_cast<LidarParameterType*>(buffer);
        memcpy(&bufferParam->sync, &parameter->sync, sizeof(LidarSyncParameter));
        CUDA_CALL(cudaMemcpyAsync(
            &bufferParam->async, &parameter->async, sizeof(LidarAsyncParameter), cudaMemcpyHostToHost, stream));
    }

    const size_t numTicks{ static_cast<size_t>(parameter->async.numTicks) };
    const size_t numReturns{ static_cast<size_t>(parameter->async.numEchos * parameter->async.numChannels *
                                                 parameter->async.numTicks) };

    size_t offset = sizeof(LidarParameterType);
    // Ticks
    size_t sizeInBytes = sizeof(float) * numTicks;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, ticks.azimuths, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    sizeInBytes = sizeof(uint32_t) * numTicks;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, ticks.states, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    sizeInBytes = sizeof(uint64_t) * numTicks;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, ticks.timestamps, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    // Returns
    sizeInBytes = sizeof(float) * numReturns;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.azimuths, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.elevations, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.distances, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.intensities, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    sizeInBytes = sizeof(float) * numReturns * 3;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.velocities, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.hitPointNormals, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    sizeInBytes = sizeof(uint32_t) * numReturns;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.deltaTimes, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.emitterIds, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.beamIds, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.materialIds, sizeInBytes, kind, stream));
    offset += sizeInBytes;
    CUDA_CALL(cudaMemcpyAsync(buffer + offset, returns.objectIds, sizeInBytes, kind, stream));
}

inline void fillTicksFromBuffer(uint8_t* buffer, const uint32_t numTicks, LidarTicks& ticks)
{
    size_t offset = sizeof(LidarParameterType);
    ticks.azimuths = reinterpret_cast<float*>(buffer + offset);
    offset += sizeof(float) * numTicks;
    ticks.states = reinterpret_cast<uint32_t*>(buffer + offset);
    offset += sizeof(uint32_t) * numTicks;
    ticks.timestamps = reinterpret_cast<uint64_t*>(buffer + offset);
    offset += sizeof(uint64_t) * numTicks;
}

NV_HOSTDEVICE
inline LidarParameterType* fillStructsFromBuffer(uint8_t* buffer, LidarReturns& returns, LidarTicks& ticks)
{
    LidarParameterType* parameter = reinterpret_cast<LidarParameterType*>(buffer);
    const size_t numTicks{ static_cast<size_t>(parameter->async.numTicks) };
    const size_t numReturns{ static_cast<size_t>(parameter->async.numEchos * parameter->async.numChannels *
                                                 parameter->async.numTicks) };

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

inline void reInitReturns(LidarReturns& returns, LidarParameterType* parameter, cudaStream_t stream)
{
    const uint32_t numReturns{ parameter->async.numTicks * parameter->async.numEchos * parameter->async.numChannels };
    CUDA_CALL(cudaMemsetAsync(returns.azimuths, 0, sizeof(float) * numReturns, stream));
    CUDA_CALL(cudaMemsetAsync(returns.elevations, 0, sizeof(float) * numReturns, stream));
    CUDA_CALL(cudaMemsetAsync(returns.distances, 0, sizeof(float) * numReturns, stream));
    CUDA_CALL(cudaMemsetAsync(returns.intensities, 0, sizeof(float) * numReturns, stream));
    CUDA_CALL(cudaMemsetAsync(returns.velocities, 0, sizeof(float) * numReturns * 3, stream));
    CUDA_CALL(cudaMemsetAsync(returns.hitPointNormals, 0, sizeof(float) * numReturns * 3, stream));
    CUDA_CALL(cudaMemsetAsync(returns.deltaTimes, 0, sizeof(uint32_t) * numReturns, stream));
    CUDA_CALL(cudaMemsetAsync(returns.emitterIds, 0, sizeof(uint32_t) * numReturns, stream));
    CUDA_CALL(cudaMemsetAsync(returns.beamIds, 0, sizeof(uint32_t) * numReturns, stream));
    CUDA_CALL(cudaMemsetAsync(returns.materialIds, 0, sizeof(uint32_t) * numReturns, stream));
    CUDA_CALL(cudaMemsetAsync(returns.objectIds, 0, sizeof(uint32_t) * numReturns, stream));
}


} // namespace lidar
} // namespace nv
} // namespace sensors
} // namespace omni
