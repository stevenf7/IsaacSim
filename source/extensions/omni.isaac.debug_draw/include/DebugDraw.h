// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <vector>

namespace omni
{
namespace isaac
{
namespace debug_draw
{


struct DebugDraw
{


    CARB_PLUGIN_INTERFACE("omni::isaac::debug_draw::DebugDraw", 0, 1);

    void(CARB_ABI* drawPoints)(const std::vector<carb::Float3>& points,
                               const std::vector<carb::ColorRgba>& color,
                               const std::vector<float>& size);
    void(CARB_ABI* clearPoints)();
    size_t(CARB_ABI* getNumPoints)();
    void(CARB_ABI* drawLines)(const std::vector<carb::Float3>& startLines,
                              const std::vector<carb::Float3>& endLines,
                              const std::vector<carb::ColorRgba>& colors,
                              const std::vector<float>& widths);
    void(CARB_ABI* drawLinesSpline)(const std::vector<carb::Float3>& points,
                                    const carb::ColorRgba& colors,
                                    const float& widths,
                                    bool filled);
    void(CARB_ABI* clearLines)();
    size_t(CARB_ABI* getNumLines)();
};
}
}
}
