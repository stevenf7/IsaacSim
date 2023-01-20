// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdContext.h>

#include <vector>

namespace omni
{
namespace isaac
{
namespace debug_draw
{
namespace drawing
{

class PrimitiveDrawingHelper
{
public:
    enum RenderingMode
    {
        ePoints = 0,
        eLines = 1

    };
    PrimitiveDrawingHelper(omni::usd::UsdContext* usdContext,
                           omni::renderer::IDebugDraw* debugDrawPtr,
                           RenderingMode renderingMode,
                           bool worldSpace = false,
                           bool depthTest = true);
    ~PrimitiveDrawingHelper();

    // Add a single vertex
    void addVertex(const carb::Float3& position, const carb::ColorRgba& color, const float width);
    void addVertex(const carb::scenerenderer::PrimitiveVertex& vertex);
    // Add a list of vertices
    void addVertices(const std::vector<carb::Float3>& positions,
                     const std::vector<carb::ColorRgba>& colors,
                     const std::vector<float> sizes);
    // Add a list of vertices with constant color and width
    void addVertices(const std::vector<carb::Float3>& positions, const carb::ColorRgba& color, float width);
    // set a list of vertices
    void setVertices(const carb::Float3* p, size_t numPositions);
    // transform the positions of vertices
    void transformVertices(const double m[]);
    // set a constant color
    void setColor(const carb::ColorRgba& color);
    // set a constant width
    void setWidth(float width);
    // add a list of primitive vertices directly
    void addVertices(const std::vector<carb::scenerenderer::PrimitiveVertex>& vertices);
    // Sets the vertex data directly, clearing what was there previously
    void setVertices(const std::vector<carb::scenerenderer::PrimitiveVertex>& vertices);

    // render current vertices
    void draw();

    // clear data
    void clear();

    size_t size();


private:
    void createList();
    void releaseList();
    bool isValid();

    omni::usd::UsdContext* mUsdContext;

    omni::renderer::IDebugDraw* mDebugDrawPtr;
    RenderingMode mRenderingMode;
    bool mWorldSpace;
    bool mDepthTest;
    carb::scenerenderer::PrimitiveList* mPrimitiveList;
    bool mDirty;
    std::vector<carb::scenerenderer::PrimitiveVertex> mVertices;
};
}
}
}
}
