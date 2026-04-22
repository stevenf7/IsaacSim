// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

// CUDA error checking macros and context validation for Newton tensor GPU operations.

#include <carb/logging/Log.h>

#include <cuda_runtime.h>

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

/// Checks a CUDA runtime call, logs the error, and returns false on failure.
#define CHECK_CUDA(call)                                                                                               \
    do                                                                                                                 \
    {                                                                                                                  \
        cudaError_t err = call;                                                                                        \
        if (err != cudaSuccess)                                                                                        \
        {                                                                                                              \
            (void)cudaGetLastError();                                                                                  \
            CARB_LOG_ERROR("CUDA error at %s:%d: %s", __FILE__, __LINE__, cudaGetErrorString(err));                    \
            return false;                                                                                              \
        }                                                                                                              \
    } while (0)

/// Checks for errors after a kernel launch (cudaGetLastError), logs and returns false on failure.
#define CHECK_CUDA_LAUNCH()                                                                                            \
    do                                                                                                                 \
    {                                                                                                                  \
        cudaError_t err = cudaGetLastError();                                                                          \
        if (err != cudaSuccess)                                                                                        \
        {                                                                                                              \
            CARB_LOG_ERROR("CUDA kernel launch error at %s:%d: %s", __FILE__, __LINE__, cudaGetErrorString(err));      \
            return false;                                                                                              \
        }                                                                                                              \
    } while (0)

/// Validates that a CUDA context exists for the given device ordinal, creating one if needed.
bool validateCudaContext(int deviceOrdinal);

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
