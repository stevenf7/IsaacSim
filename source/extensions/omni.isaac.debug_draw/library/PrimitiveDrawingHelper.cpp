// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on
#include <carb/scenerenderer/SceneRenderer.h>

#include <omni/isaac/debug_draw/PrimitiveDrawingHelper.h>
// #include <tbb/parallel_for.h>

using namespace carb::scenerenderer;

namespace omni
{
namespace isaac
{
namespace debug_draw
{
namespace drawing
{
PrimitiveDrawingHelper::PrimitiveDrawingHelper(omni::usd::UsdContext* usdContext,
                                               omni::renderer::IDebugDraw* debugDrawPtr,
                                               RenderingMode renderingMode,
                                               bool worldSpace,
                                               bool depthTest)
    : mUsdContext(usdContext),
      mDebugDrawPtr(debugDrawPtr),
      mRenderingMode(renderingMode),
      mWorldSpace(worldSpace),
      mDepthTest(depthTest),
      mPrimitiveList(nullptr),
      mDirty(false)
{
}
PrimitiveDrawingHelper::~PrimitiveDrawingHelper()
{
    clear();
    releaseList();
}

// Add a single vertex
void PrimitiveDrawingHelper::addVertex(const carb::Float3& position, const carb::ColorRgba& color, const float width)
{
    mDirty = true;
    carb::scenerenderer::PrimitiveVertex point;
    point.position = position;
    point.width = width;
    point.color = color;
    mVertices.push_back(point);
}
void PrimitiveDrawingHelper::addVertex(const carb::scenerenderer::PrimitiveVertex& vertex)
{
    mDirty = true;
    mVertices.push_back(vertex);
}
// Add a list of vertices
void PrimitiveDrawingHelper::addVertices(const std::vector<carb::Float3>& positions,
                                         const std::vector<carb::ColorRgba>& colors,
                                         const std::vector<float> widths)
{
    mDirty = true;
    carb::scenerenderer::PrimitiveVertex point;

    for (size_t i = 0; i < positions.size(); i++)
    {
        point.position = positions[i];
        point.width = widths[i];
        point.color = colors[i];
        mVertices.push_back(point);
    }
}
// Add a list of vertices with constant color and width
void PrimitiveDrawingHelper::addVertices(const std::vector<carb::Float3>& positions,
                                         const carb::ColorRgba& color,
                                         float width)
{
    mDirty = true;
    carb::scenerenderer::PrimitiveVertex point;
    size_t first_index = size();
    mVertices.resize(first_index + positions.size());
    for (size_t i = 0; i < positions.size(); i++)
    {
        point.position = positions[i];
        point.width = width;
        point.color = color;
        mVertices[first_index + i] = point;
    }
}

// set a list of vertices with constant color and width
void PrimitiveDrawingHelper::setVertices(const carb::Float3* positions,
                                         size_t numPositions,
                                         const carb::ColorRgba& color,
                                         float width)
{
    if (mVertices.size() != numPositions)
    {
        mDirty = true;
    }
    mVertices.resize(numPositions);
    for (int i = 0; i < (int)numPositions; ++i)
    {
        mVertices[i].position = positions[i];
        mVertices[i].color = color;
        mVertices[i].width = width;
    }

    /*tbb::parallel_for(tbb::blocked_range<int>(0, numPositions),
                      [&](tbb::blocked_range<int> r)
                      {
                          for (int i = r.begin(); i < r.end(); ++i)
                          {
                              mVertices[i].position = positions[i];
                              mVertices[i].color = color;
                              mVertices[i].width = width;
                          }
                      });*/
}
void PrimitiveDrawingHelper::addVertices(const std::vector<carb::scenerenderer::PrimitiveVertex>& vertices)
{
    mDirty = true;

    mVertices.insert(mVertices.end(), vertices.begin(), vertices.end());
}

void PrimitiveDrawingHelper::setVertices(const std::vector<carb::scenerenderer::PrimitiveVertex>& vertices)
{
    // avoid release/create of the primitive instance if the size is the same
    if (mVertices.size() != vertices.size())
    {
        mDirty = true;
    }
    mVertices = vertices;
}

// render current vertices
void PrimitiveDrawingHelper::draw()
{
    if (mDirty)
    {
        releaseList();
        createList();
    }
    if (!mVertices.empty())
    {

        carb::scenerenderer::PrimitiveListSettings settings = {};
        settings.width = 1.0f;
        settings.antialiasingWidth = 0;
        settings.fadeOutStartDistance = 1e10f;
        settings.fadeOutEndDistance = 1e10f;

        carb::scenerenderer::PrimitiveListInstance inst = {};
        inst.transform.m[0] = 1.f;
        inst.transform.m[1 + 4] = 1.f;
        inst.transform.m[2 + 8] = 1.f;
        inst.transform.m[3 + 12] = 1.f;

        mUsdContext->getSceneRenderer()->updatePrimitiveListSettings(
            mUsdContext->getSceneRendererContext(), mPrimitiveList, settings);
        mUsdContext->getSceneRenderer()->updatePrimitiveListInstances(
            mUsdContext->getSceneRendererContext(), mPrimitiveList, &inst, 0, 1, 1);
        mUsdContext->getSceneRenderer()->updatePrimitiveListVertices(mUsdContext->getSceneRendererContext(),
                                                                     mPrimitiveList, mVertices.data(), 0,
                                                                     mVertices.size(), mVertices.size());
    }
    else
    {
        releaseList();
    }
}
// clear data
void PrimitiveDrawingHelper::clear()
{
    mVertices.clear();
}
size_t PrimitiveDrawingHelper::size()
{
    return mVertices.size();
}

void PrimitiveDrawingHelper::createList()
{
    SceneId id = mUsdContext->getRendererScene();
    if (!mPrimitiveList && id)
    {

        PrimitiveKind kind = mRenderingMode == RenderingMode::ePoints ? PrimitiveKind::ePoint : PrimitiveKind::eLine;
        carb::scenerenderer::PrimitiveListFlags flags = carb::scenerenderer::kPrimitiveListFlagNone;
        if (mDepthTest)
        {
            flags |= carb::scenerenderer::kPrimitiveListFlagDepthTest |
                     carb::scenerenderer::kPrimitiveListFlagDepthTestWrite;
        }
        if (mWorldSpace)
        {
            flags |= carb::scenerenderer::kPrimitiveListFlagWorldSpaceWidth;
        }
        mPrimitiveList = mUsdContext->getSceneRenderer()->createPrimitiveList(
            mUsdContext->getSceneRendererContext(), id, kind, flags);
    }
}
void PrimitiveDrawingHelper::releaseList()
{
    if (mPrimitiveList && mUsdContext && mUsdContext->getSceneRenderer() && mUsdContext->getSceneRendererContext() &&
        mUsdContext->getRendererScene())
    {
        mUsdContext->getSceneRenderer()->destroyPrimitiveList(mUsdContext->getSceneRendererContext(), mPrimitiveList);
        mPrimitiveList = nullptr;
    }
}
}
}
}
}
