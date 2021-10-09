// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Interface.h>
#include <carb/Types.h>

#include <cstddef>

namespace omni
{
namespace isaac
{
namespace decals
{
typedef void (*ResponseFn)(bool result, const char* msg, void* userData);

struct Decals
{
    CARB_PLUGIN_INTERFACE("omni::isaac::decals::Decals", 0, 1);

    void(CARB_ABI* setEnbled)(bool enabled);
    void(CARB_ABI* setPickingEnabled)(bool pickingEnabled);
    void(CARB_ABI* setPenColor)(float r, float g, float b);
    void(CARB_ABI* setPenWidth)(float color);
    void(CARB_ABI* setPenOffset)(float offset);
    void(CARB_ABI* setPenThreshold)(float threshold);

    void(CARB_ABI* setPenSurface)(const char* primPath);
    void(CARB_ABI* setPenPosition)(const carb::Float3& worldPosition);
    void(CARB_ABI* setPenDown)(bool penDown);

    bool(CARB_ABI* eraseSurface)(const char* primPath);
    void(CARB_ABI* eraseAllSurfaces)();

    void(CARB_ABI* runTests)();
};

}
}
}
