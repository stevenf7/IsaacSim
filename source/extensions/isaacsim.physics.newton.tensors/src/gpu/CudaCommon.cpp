// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#include "CudaCommon.h"

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

bool validateCudaContext(int deviceOrdinal)
{
    if (deviceOrdinal < 0)
    {
        return true;
    }

    int deviceCount = 0;
    cudaError_t err = cudaGetDeviceCount(&deviceCount);
    if (err != cudaSuccess)
    {
        (void)cudaGetLastError();
        CARB_LOG_ERROR("Failed to get CUDA device count: %s", cudaGetErrorString(err));
        return false;
    }

    if (deviceOrdinal >= deviceCount)
    {
        CARB_LOG_ERROR("Invalid device ordinal %d (available: %d)", deviceOrdinal, deviceCount);
        return false;
    }

    err = cudaSetDevice(deviceOrdinal);
    if (err != cudaSuccess)
    {
        (void)cudaGetLastError();
        CARB_LOG_ERROR("Failed to set CUDA device %d: %s", deviceOrdinal, cudaGetErrorString(err));
        return false;
    }

    return true;
}

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
