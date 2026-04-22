// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

// Template helper for GPU getter methods.
// Encapsulates the common pattern: launch CUDA gather kernel into staging buffer,
// then cudaMemcpy D2H into the caller's output tensor if it resides on the host.

#include <carb/logging/Log.h>

#include <omni/physics/tensors/ISimulationView.h>

#include <cuda_runtime.h>

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

using omni::physics::tensors::TensorDesc;

/// Launches a CUDA gather kernel and stages the result to dstTensor.
/// @param launch      Callable(float* gpuDst, int count) → bool, launches the CUDA kernel.
/// @param dstTensor   Caller's output tensor (may be CPU or GPU).
/// @param n           Number of elements to gather.
/// @param elemFloats  Number of float components per element (for byte size computation).
/// @param stagingBuffer  Pre-allocated device buffer, used when dstTensor is on CPU.
template <typename LaunchFn>
bool gpuGather(LaunchFn&& launch, const TensorDesc* dstTensor, int n, size_t elemFloats, float* stagingBuffer)
{
    if (n == 0)
        return true;
    float* gpuDst = (dstTensor->device >= 0) ? static_cast<float*>(dstTensor->data) : stagingBuffer;
    if (!gpuDst)
    {
        CARB_LOG_ERROR("gpuGather: null GPU destination buffer");
        return false;
    }
    bool ok = launch(gpuDst, n);
    if (ok && dstTensor->device < 0)
    {
        cudaError_t err = cudaMemcpy(dstTensor->data, stagingBuffer,
                                     static_cast<size_t>(n) * elemFloats * sizeof(float), cudaMemcpyDeviceToHost);
        if (err != cudaSuccess)
        {
            (void)cudaGetLastError();
            CARB_LOG_ERROR("gpuGather D2H cudaMemcpy failed: %s", cudaGetErrorString(err));
            return false;
        }
    }
    return ok;
}

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
