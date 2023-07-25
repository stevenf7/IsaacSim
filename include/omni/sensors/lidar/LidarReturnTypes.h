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
//! @brief LidarReturn: This file specifies the data structs of the lidar data stream

#pragma once

#include <cstdint>

// The basic data structure is as follows:
// LidarParameter      +
// LidarTickMember1,LidarTickMember1,...,LidarTickMember1,...,LidarTickMemberN,LidarReturnMember1,...,LidarReturnMember1,LidarReturnMember1,...,LidarReturnMemberN
// (see LidarParameterType.h) ------------------|-------------- -------------|-------------,                -----|-----
// (basic parameters of lidar device)      x numTicks                  x numReturns per Tick
//                                                              ------------------------------|----------------------------------------------------------------------------------------------
//                                                                                          x numTicks

#pragma pack(push, 1) // Make sure we have consistent structure packing

struct LidarReturns
{
    float* azimuths;
    float* elevations;
    float* distances;
    float* intensities;
    float* velocities; // Stride 3
    float* hitPointNormals; // Stride 3
    uint32_t* deltaTimes;
    uint32_t* emitterIds;
    uint32_t* beamIds;
    uint32_t* materialIds;
    uint32_t* objectIds;
};

// Defines sensor head positions
struct LidarTicks
{
    float* azimuths;
    uint32_t* states;
    uint64_t* timestamps;
};

#pragma pack(pop)
