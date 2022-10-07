// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/renderer/Renderer.h>
#include <carb/scenerenderer/SceneRenderer.h>

#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/isaac/debug_draw/Curves.h>
#include <omni/isaac/debug_draw/DebugDraw.h>
#include <omni/isaac/debug_draw/PrimitiveDrawingHelper.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdContextIncludes.h>

///
#include <omni/usd/UsdContext.h>
///


const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.debug_draw.plugin", "Isaac Sim debug drawing plugin",
                                                  "NVIDIA", carb::PluginHotReload::eDisabled, "dev" };
CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::debug_draw::DebugDraw)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IStageUpdate,
                      omni::renderer::IDebugDraw,
                      omni::graph::core::IGraphRegistry,
                      carb::flatcache::IToken)
DECLARE_OGN_NODES()

using namespace carb::scenerenderer;

omni::renderer::IDebugDraw* gDebugDraw = nullptr;
omni::kit::IStageUpdate* gStageUpdate = nullptr;
omni::kit::StageUpdateNode* gStageUpdateNode = nullptr;
// // Points
// carb::scenerenderer::PrimitiveList* gDebugPointList;
// std::vector<carb::scenerenderer::PrimitiveVertex> gDebugPointVector;

// // Lines
// std::vector<carb::scenerenderer::PrimitiveVertex> gDebugLineVector;
// carb::scenerenderer::PrimitiveList* gDebugLineList;

omni::usd::UsdContext* gUsdContext = nullptr;


void convertColor(uint32_t inColor, carb::ColorRgba& outColor)
{
    outColor.a = ((inColor & 0xFF000000) >> 24) / 255.0f;
    outColor.r = ((inColor & 0xFF0000) >> 16) / 255.0f;
    outColor.g = ((inColor & 0xFF00) >> 8) / 255.0f;
    outColor.b = (inColor & 0xFF) / 255.0f;
}


pxr::GfVec3f getOrientation(pxr::GfVec3f& normal, pxr::GfVec3f& tangent)
{
    pxr::GfVec3f binormal = pxr::GfCross(tangent.GetNormalized(), normal);
    return binormal.GetNormalized();
}


std::unique_ptr<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper> gPointDrawing;
std::unique_ptr<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper> gLineDrawing;


void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    gPointDrawing->draw();
    gLineDrawing->draw();
}

void CARB_ABI drawPoints(const std::vector<carb::Float3>& points,
                         const std::vector<carb::ColorRgba>& colors,
                         const std::vector<float>& size)
{
    for (size_t i = 0; i < points.size(); i++)
    {
        gPointDrawing->addVertex(points[i], colors[i], size[i]);
    }
}

void CARB_ABI clearPoints()
{
    gPointDrawing->clear();
}

size_t CARB_ABI getNumPoints()
{
    return gPointDrawing->size();
}


void CARB_ABI drawLines(const std::vector<carb::Float3>& startPoints,
                        const std::vector<carb::Float3>& endPoints,
                        const std::vector<carb::ColorRgba>& colors,
                        const std::vector<float>& widths)
{

    if (startPoints.size() == endPoints.size() && endPoints.size() == colors.size() && colors.size() == widths.size())
    {
        for (size_t i = 0; i < startPoints.size(); i++)
        {
            gLineDrawing->addVertex(startPoints[i], colors[i], widths[i]);
            gLineDrawing->addVertex(endPoints[i], colors[i], widths[i]);
        }
    }
    else
    {
        CARB_LOG_ERROR("start points %zu, end points %zu, colors %zu, and widths %zu not the same size",
                       startPoints.size(), endPoints.size(), colors.size(), widths.size());
    }
}


void CARB_ABI drawLinesSpline(const std::vector<carb::Float3>& points,
                              const carb::ColorRgba& colors,
                              const float& width,
                              bool filled)
{

    pxr::VtArray<pxr::GfVec4f> tessellatedPoints;
    pxr::VtArray<pxr::GfVec4f> tessellatedTangents;

    omni::isaac::debug_draw::curves::BSpline curve(omni::isaac::debug_draw::curves::eBasisCurveWrap::Pinned, 1);

    pxr::VtArray<pxr::GfVec3f> ctrlPoints;
    for (size_t i = 0; i < points.size(); i++)
    {
        ctrlPoints.push_back(pxr::GfVec3f(points[i].x, points[i].y, points[i].z));
    }
    curve.tessellate(ctrlPoints, tessellatedPoints, tessellatedTangents);
    if (tessellatedPoints.size() < 2 || tessellatedPoints.size() != tessellatedTangents.size())
    {
        return;
    }
    PrimitiveVertex point;
    if (filled)
    {


        for (uint32_t i = 0; i < tessellatedPoints.size() - 1; ++i)
        {
            const float* pointPtr = tessellatedPoints[i].data();
            const float* tangentPtr = tessellatedTangents[i].data();
            pxr::GfVec3f normal(0, 0, 1);
            pxr::GfVec3f cpi = { pointPtr[0], pointPtr[1], pointPtr[2] };
            pxr::GfVec3f tangent = { tangentPtr[0], tangentPtr[1], tangentPtr[2] };
            pxr::GfVec3f binormal = getOrientation(normal, tangent);
            pxr::GfVec3f offset = binormal * width;
            pxr::GfVec3f a1 = cpi - offset;
            pxr::GfVec3f b1 = cpi + offset;


            pointPtr = tessellatedPoints[i + 1].data();
            tangentPtr = tessellatedTangents[i + 1].data();
            cpi = { pointPtr[0], pointPtr[1], pointPtr[2] };
            tangent = { tangentPtr[0], tangentPtr[1], tangentPtr[2] };
            binormal = getOrientation(normal, tangent);
            offset = binormal * width;
            pxr::GfVec3f a2 = cpi - offset;
            pxr::GfVec3f b2 = cpi + offset;


            point.position = carb::Float3({ a1[0], a1[1], a1[2] });
            point.width = 1.0;
            point.color = colors;
            gLineDrawing->addVertex(point);
            point.position = carb::Float3({ a2[0], a2[1], a2[2] });
            point.width = 1.0;
            point.color = colors;
            gLineDrawing->addVertex(point);

            point.position = carb::Float3({ b1[0], b1[1], b1[2] });
            point.width = 1.0;
            point.color = colors;
            gLineDrawing->addVertex(point);
            point.position = carb::Float3({ b2[0], b2[1], b2[2] });
            point.width = 1.0;
            point.color = colors;
            gLineDrawing->addVertex(point);

            point.position = carb::Float3({ b1[0], b1[1], b1[2] });
            point.width = 1.0;
            point.color = colors;
            gLineDrawing->addVertex(point);
            point.position = carb::Float3({ a2[0], a2[1], a2[2] });
            point.width = 1.0;
            point.color = colors;
            gLineDrawing->addVertex(point);


            // First line
            if (i == 0)
            {

                point.position = carb::Float3({ b1[0], b1[1], b1[2] });
                point.width = 1.0;
                point.color = colors;
                gLineDrawing->addVertex(point);
                point.position = carb::Float3({ a1[0], a1[1], a1[2] });
                point.width = 1.0;
                point.color = colors;
                gLineDrawing->addVertex(point);
            }
            // last line
            if (i == tessellatedPoints.size() - 2)
            {
                point.position = carb::Float3({ b2[0], b2[1], b2[2] });
                point.width = 1.0;
                point.color = colors;
                gLineDrawing->addVertex(point);
                point.position = carb::Float3({ a2[0], a2[1], a2[2] });
                point.width = 1.0;
                point.color = colors;
                gLineDrawing->addVertex(point);
            }
        }
    }
    else
    {
        for (uint32_t i = 0; i < tessellatedPoints.size() - 1; ++i)
        {
            const float* pointPtr = tessellatedPoints[i].data();

            point.position = carb::Float3({ pointPtr[0], pointPtr[1], pointPtr[2] });
            point.width = width;
            point.color = colors;
            gLineDrawing->addVertex(point);

            pointPtr = tessellatedPoints[i + 1].data();

            point.position = carb::Float3({ pointPtr[0], pointPtr[1], pointPtr[2] });
            point.width = width;
            point.color = colors;
            gLineDrawing->addVertex(point);
        }
    }
}

void CARB_ABI clearLines()
{
    gLineDrawing->clear();
}

size_t CARB_ABI getNumLines()
{
    // each line is two points
    return static_cast<size_t>(gLineDrawing->size() / 2);
}

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    gUsdContext = omni::usd::UsdContext::getContext();
    gPointDrawing = std::make_unique<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
        gUsdContext, gDebugDraw, omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::ePoints);
    gLineDrawing = std::make_unique<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
        gUsdContext, gDebugDraw, omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);
}

void onDetach(void* data)
{
    gPointDrawing.reset();
    gLineDrawing.reset();
}

CARB_EXPORT void carbOnPluginStartup()
{

    INITIALIZE_OGN_NODES()
    gStageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>();

    gDebugDraw = carb::getCachedInterface<omni::renderer::IDebugDraw>();
    if (!gDebugDraw)
    {
        CARB_LOG_ERROR("*** Failed to acquire debugdraw interface\n");
        return;
    }
    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "Isaac DebugDraw";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    // Create the stage update node and make sure it runs after physx
    size_t index = gStageUpdate->getStageUpdateNodeCount();
    gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);
    gStageUpdate->setStageUpdateNodeOrder(index, 75);

    gPointDrawing = std::make_unique<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
        gUsdContext, gDebugDraw, omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::ePoints);
    gLineDrawing = std::make_unique<omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper>(
        gUsdContext, gDebugDraw, omni::isaac::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);
}

CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()
    gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
    gPointDrawing.reset();
    gLineDrawing.reset();
}

void fillInterface(omni::isaac::debug_draw::DebugDraw& iface)
{
    using namespace omni::isaac::debug_draw;
    memset(&iface, 0, sizeof(iface));

    iface.clearLines = clearLines;
    iface.clearPoints = clearPoints;
    iface.drawLines = drawLines;
    iface.drawLinesSpline = drawLinesSpline;
    iface.drawPoints = drawPoints;
    iface.getNumLines = getNumLines;
    iface.getNumPoints = getNumPoints;
}
