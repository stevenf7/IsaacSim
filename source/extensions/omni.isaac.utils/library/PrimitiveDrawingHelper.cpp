
// clang-format off
#include "UsdPCH.h"
// clang-format on
#include <omni/isaac/utils/PrimitiveDrawingHelper.h>
#include <carb/scenerenderer/SceneRenderer.h>


using namespace carb::scenerenderer;

namespace omni
{
namespace isaac
{
namespace utils
{
namespace drawing
{
PrimitiveDrawingHelper::PrimitiveDrawingHelper(omni::usd::UsdContext* usdContext,
                                               omni::renderer::IDebugDraw* debugDrawPtr,
                                               RenderingMode renderingMode)
    : mUsdContext(usdContext),
      mDebugDrawPtr(debugDrawPtr),
      mRenderingMode(renderingMode),
      mPrimitiveList(nullptr),
      mDirty(false)
{
}
PrimitiveDrawingHelper::~PrimitiveDrawingHelper()
{
    releaseList();
}

// Add a single vertex
void PrimitiveDrawingHelper::addVertex(const carb::Float3& position, const carb::ColorRgba& color, const float size)
{
    mDirty = true;
    carb::scenerenderer::PrimitiveVertex point;
    point.position = position;
    point.width = size;
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
                                         const std::vector<float> sizes)
{
    mDirty = true;
    carb::scenerenderer::PrimitiveVertex point;

    for (size_t i = 0; i < positions.size(); i++)
    {
        point.position = positions[i];
        point.width = sizes[i];
        point.color = colors[i];
        mVertices.push_back(point);
    }
}
// Add a list of vertices with constant color and width
void PrimitiveDrawingHelper::addVertices(const std::vector<carb::Float3>& positions,
                                         const carb::ColorRgba& color,
                                         float size)
{
    mDirty = true;
    carb::scenerenderer::PrimitiveVertex point;

    for (size_t i = 0; i < positions.size(); i++)
    {
        point.position = positions[i];
        point.width = size;
        point.color = color;
        mVertices.push_back(point);
    }
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
        settings.antialiasingWidth = -1;
        settings.fadeOutStartDistance = 1e5f;
        settings.fadeOutEndDistance = 1e9f;

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
    if (!mPrimitiveList)
    {
        SceneId id = mUsdContext->getRendererScene();
        PrimitiveKind kind = mRenderingMode == RenderingMode::ePoints ? PrimitiveKind::ePoint : PrimitiveKind::eLine;

        mPrimitiveList = mUsdContext->getSceneRenderer()->createPrimitiveList(
            mUsdContext->getSceneRendererContext(), id, kind,
            carb::scenerenderer::kPrimitiveListFlagDepthTest | carb::scenerenderer::kPrimitiveListFlagDepthTestWrite);
    }
}
void PrimitiveDrawingHelper::releaseList()
{
    if (mPrimitiveList)
    {
        mUsdContext->getSceneRenderer()->destroyPrimitiveList(mUsdContext->getSceneRendererContext(), mPrimitiveList);
        mPrimitiveList = nullptr;
    }
}
}
}
}
}
