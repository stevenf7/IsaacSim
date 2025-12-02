// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <vector>

namespace isaacsim
{
namespace util
{
namespace debug_draw
{

/**
 * @brief Interface for debug drawing functionality
 * @details Provides methods for drawing debug visualization elements like points and lines
 *          in 3D space. This is useful for debugging spatial relationships and visualizing
 *          geometric data.
 */
struct DebugDraw
{
    CARB_PLUGIN_INTERFACE("isaacsim::util::debug_draw::DebugDraw", 0, 1);

    /**
     * @brief Draws a collection of points in 3D space
     * @param[in] points Vector of 3D point positions to draw
     * @param[in] color Vector of colors for each point
     * @param[in] size Vector of sizes for each point
     */
    void(CARB_ABI* drawPoints)(const std::vector<carb::Float3>& points,
                               const std::vector<carb::ColorRgba>& color,
                               const std::vector<float>& size);

    /**
     * @brief Clears all drawn points from the visualization
     */
    void(CARB_ABI* clearPoints)();

    /**
     * @brief Gets the number of points currently being drawn
     * @return Number of points in the visualization
     */
    size_t(CARB_ABI* getNumPoints)();

    /**
     * @brief Draws a collection of lines in 3D space
     * @param[in] startLines Vector of start points for each line
     * @param[in] endLines Vector of end points for each line
     * @param[in] colors Vector of colors for each line
     * @param[in] widths Vector of line widths for each line
     */
    void(CARB_ABI* drawLines)(const std::vector<carb::Float3>& startLines,
                              const std::vector<carb::Float3>& endLines,
                              const std::vector<carb::ColorRgba>& colors,
                              const std::vector<float>& widths);

    /**
     * @brief Draws a spline curve through a set of points
     * @param[in] points Vector of control points defining the spline
     * @param[in] colors Color of the spline
     * @param[in] widths Width of the spline
     * @param[in] filled Whether to draw the spline as a filled curve
     */
    void(CARB_ABI* drawLinesSpline)(const std::vector<carb::Float3>& points,
                                    const carb::ColorRgba& colors,
                                    const float& widths,
                                    bool filled);

    /**
     * @brief Clears all drawn lines from the visualization
     */
    void(CARB_ABI* clearLines)();

    /**
     * @brief Gets the number of lines currently being drawn
     * @return Number of lines in the visualization
     */
    size_t(CARB_ABI* getNumLines)();
};
}
}
}
