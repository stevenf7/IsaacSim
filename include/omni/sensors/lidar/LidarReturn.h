// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
//! @file
//!
//! @brief LidarReturn Helper functions: This file specifies the data struct of the lidar data stream

#pragma once

#include "LidarParameterType.h"
#include "LidarReturnTypes.h"

#include <omni/sensors/cuda/CudaHelperDecl.h>


/**
 * Calculates the index inside the lidarReturn data array
 *
 * @param beamId [in] id of beam/emitter
 * @param echoId [in] id of echo/return per beam
 * @param numEchos [in] number of echos per beam
 * @param numBeams [in] number of beams per tick, optional
 * @param tick [in] tick index of trace, optional
 * @return uint32_t index inside lidarReturn data array
 */
/// \cond DO_NOT_DOCUMENT
NV_HOSTDEVICE
/// \endcond
static inline uint32_t idxOfReturn(const uint32_t beamId,
                                   const uint32_t echoId,
                                   const uint32_t numEchos,
                                   const uint32_t numBeams = 0,
                                   const uint32_t tick = 0)
{
    return beamId * numEchos + echoId + tick * numEchos * numBeams;
}

/**
 * Calculates data size in bytes for one tick
 * @param numEchos [in] number of echos per beam/emitter
 * @param numEmitter [in] number of emitters per tick
 * @return uint32_t size of one tick in bytes
 */
/// \cond DO_NOT_DOCUMENT
NV_HOSTDEVICE
/// \endcond
static inline uint32_t sizeOneTick(const uint32_t numEchos, const uint32_t numEmitter)
{
    const uint32_t sizeOfTickStruct{ sizeof(float) + sizeof(uint32_t) + sizeof(uint64_t) };
    const uint32_t sizeOfReturnStruct{ sizeof(float) * 4 + sizeof(float) * 3 + sizeof(float) * 3 + sizeof(uint32_t) * 5 };
    return sizeOfTickStruct + sizeOfReturnStruct * numEchos * numEmitter;
}
