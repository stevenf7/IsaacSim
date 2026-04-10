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

#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/usd/UsdContext.h>

#include <memory>
#include <vector>

// Forward declarations
namespace carb
{
struct Float3;
struct ColorRgba;

namespace scenerenderer
{
struct PrimitiveList;
typedef PrimitiveList* PrimitiveListId;
}
}

namespace isaacsim
{
namespace util
{
namespace debug_draw
{
namespace drawing
{

// Forward declaration for private implementation class
class PrimitiveDrawingHelperImpl;

/**
 * @brief Helper class for drawing primitive shapes in 3D space
 * @details Provides functionality for drawing points and lines with various attributes
 *          like color, width, and transformation. Supports both immediate and batch
 *          rendering modes.
 */
class PrimitiveDrawingHelper
{
public:
    /**
     * @brief Enumeration of supported rendering modes
     */
    enum class RenderingMode
    {
        /**
         * @brief Render vertices as points
         */
        ePoints = 0,

        /**
         * @brief Render vertices as lines
         */
        eLines = 1
    };

    /**
     * @brief Constructs a PrimitiveDrawingHelper
     * @param[in] usdContext USD context for rendering
     * @param[in] renderingMode Mode to render primitives (points or lines)
     * @param[in] worldSpace Whether to render in world space coordinates
     * @param[in] depthTest Whether to perform depth testing during rendering
     */
    PrimitiveDrawingHelper(omni::usd::UsdContext* usdContext,
                           RenderingMode renderingMode,
                           bool worldSpace = false,
                           bool depthTest = true);
    ~PrimitiveDrawingHelper();

    /**
     * @brief Adds a single vertex with position, color, and width
     * @param[in] position 3D position of the vertex
     * @param[in] color Color of the vertex
     * @param[in] width Width of the point or line
     */
    void addVertex(const carb::Float3& position, const carb::ColorRgba& color, const float width);

    /**
     * @brief Adds multiple vertices with individual attributes
     * @param[in] positions Vector of 3D positions
     * @param[in] colors Vector of colors for each position
     * @param[in] sizes Vector of sizes for each position
     */
    void addVertices(const std::vector<carb::Float3>& positions,
                     const std::vector<carb::ColorRgba>& colors,
                     const std::vector<float>& sizes);

    /**
     * @brief Adds multiple vertices with constant color and width
     * @param[in] positions Vector of 3D positions
     * @param[in] color Color to apply to all vertices
     * @param[in] width Width to apply to all vertices
     */
    void addVertices(const std::vector<carb::Float3>& positions, const carb::ColorRgba& color, float width);

    /**
     * @brief Sets vertex positions directly from an array
     * @param[in] p Pointer to array of positions
     * @param[in] numPositions Number of positions in the array
     */
    void setVertices(const carb::Float3* p, size_t numPositions);

    /**
     * @brief Transforms all vertex positions using a transformation matrix
     * @param[in] m Array of 16 doubles representing a 4x4 transformation matrix
     */
    void transformVertices(const double m[]);

    /**
     * @brief Sets a constant color for all vertices
     * @param[in] color Color to apply to all vertices
     */
    void setColor(const carb::ColorRgba& color);

    /**
     * @brief Sets a constant width for all vertices
     * @param[in] width Width to apply to all vertices
     */
    void setWidth(float width);

    /**
     * @brief Renders all currently stored vertices
     */
    void draw();

    /**
     * @brief Clears all stored vertex data
     */
    void clear();

    /**
     * @brief Gets the number of vertices currently stored
     * @return Number of vertices
     */
    size_t size();

private:
    /**
     * @brief Creates a new primitive list for rendering
     */
    void _createList();

    /**
     * @brief Releases the current primitive list
     */
    void _releaseList();

    /**
     * @brief Checks if the primitive list is valid
     * @return True if the list is valid, false otherwise
     */
    bool _isValid();

    // Basic members
    omni::usd::UsdContext* m_usdContext;
    RenderingMode m_renderingMode;
    bool m_worldSpace;
    bool m_depthTest;
    bool m_dirty;

    // Opaque pointer to implementation details
    struct VertexData;
    std::unique_ptr<VertexData> m_vertexData;
    carb::scenerenderer::PrimitiveListId m_primitiveList;
};
}
}
}
}
