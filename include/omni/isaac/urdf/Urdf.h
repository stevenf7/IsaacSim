// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/Defines.h>

#include <stdint.h>

namespace omni
{
namespace isaac
{
namespace urdf
{

struct ImportConfig
{
    bool mergeFixedJoints = false;
    bool enableConvexDecomp = false;
    bool forceZUp = true;
    bool addDebugInfo = false;
    float distanceScale = 100.0;
    bool importInertiaTensor = false;
};


struct Urdf
{
    CARB_PLUGIN_INTERFACE("omni::isaac::urdf::Urdf", 0, 1);
    void(CARB_ABI* importUrdf)(std::string asset_path, const ImportConfig& importConfig);
};
}
}
}
