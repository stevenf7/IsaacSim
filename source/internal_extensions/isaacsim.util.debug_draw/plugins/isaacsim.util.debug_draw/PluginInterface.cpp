// SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#define CARB_EXPORTS

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>

#include <isaacsim/util/debug_draw/Curves.h>
#include <isaacsim/util/debug_draw/IDebugDraw.h>
#include <isaacsim/util/debug_draw/PrimitiveDrawingHelper.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>

///
#include <omni/kit/IStageUpdate.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>
///


const struct carb::PluginImplDesc g_kPluginDesc = { "isaacsim.util.debug_draw.plugin", "Isaac Sim debug drawing plugin",
                                                    "NVIDIA", carb::PluginHotReload::eDisabled, "dev" };
CARB_PLUGIN_IMPL(g_kPluginDesc, isaacsim::util::debug_draw::DebugDraw)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IStageUpdate, omni::graph::core::IGraphRegistry, omni::fabric::IToken)
DECLARE_OGN_NODES()


omni::kit::StageUpdatePtr g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
omni::usd::UsdContext* g_usdContext = nullptr;


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


std::unique_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> g_pointDrawing;
std::unique_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> g_lineDrawing;


void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    g_pointDrawing->draw();
    g_lineDrawing->draw();
}

void CARB_ABI drawPoints(const std::vector<carb::Float3>& points,
                         const std::vector<carb::ColorRgba>& colors,
                         const std::vector<float>& size)
{
    for (size_t i = 0; i < points.size(); i++)
    {
        g_pointDrawing->addVertex(points[i], colors[i], size[i]);
    }
}

void CARB_ABI clearPoints()
{
    g_pointDrawing->clear();
}

size_t CARB_ABI getNumPoints()
{
    return g_pointDrawing->size();
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
            g_lineDrawing->addVertex(startPoints[i], colors[i], widths[i]);
            g_lineDrawing->addVertex(endPoints[i], colors[i], widths[i]);
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

    isaacsim::util::debug_draw::curves::BSpline curve(isaacsim::util::debug_draw::curves::BasisCurveWrap::ePinned, 1);

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


            g_lineDrawing->addVertex(carb::Float3({ a1[0], a1[1], a1[2] }), colors, 1.0f);
            g_lineDrawing->addVertex(carb::Float3({ a2[0], a2[1], a2[2] }), colors, 1.0f);

            g_lineDrawing->addVertex(carb::Float3({ b1[0], b1[1], b1[2] }), colors, 1.0f);
            g_lineDrawing->addVertex(carb::Float3({ b2[0], b2[1], b2[2] }), colors, 1.0f);

            g_lineDrawing->addVertex(carb::Float3({ b1[0], b1[1], b1[2] }), colors, 1.0f);
            g_lineDrawing->addVertex(carb::Float3({ a2[0], a2[1], a2[2] }), colors, 1.0f);


            // First line
            if (i == 0)
            {

                g_lineDrawing->addVertex(carb::Float3({ b1[0], b1[1], b1[2] }), colors, 1.0f);
                g_lineDrawing->addVertex(carb::Float3({ a1[0], a1[1], a1[2] }), colors, 1.0f);
            }
            // last line
            if (i == tessellatedPoints.size() - 2)
            {
                g_lineDrawing->addVertex(carb::Float3({ b2[0], b2[1], b2[2] }), colors, 1.0f);
                g_lineDrawing->addVertex(carb::Float3({ a2[0], a2[1], a2[2] }), colors, 1.0f);
            }
        }
    }
    else
    {
        for (uint32_t i = 0; i < tessellatedPoints.size() - 1; ++i)
        {
            const float* pointPtr = tessellatedPoints[i].data();

            g_lineDrawing->addVertex(carb::Float3({ pointPtr[0], pointPtr[1], pointPtr[2] }), colors, width);

            pointPtr = tessellatedPoints[i + 1].data();

            g_lineDrawing->addVertex(carb::Float3({ pointPtr[0], pointPtr[1], pointPtr[2] }), colors, width);
        }
    }
}

void CARB_ABI clearLines()
{
    g_lineDrawing->clear();
}

size_t CARB_ABI getNumLines()
{
    // each line is two points
    return static_cast<size_t>(g_lineDrawing->size() / 2);
}

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    g_usdContext = omni::usd::UsdContext::getContext();
    g_pointDrawing = std::make_unique<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
        g_usdContext, isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::ePoints);
    g_lineDrawing = std::make_unique<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
        g_usdContext, isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);
}

void onDetach(void* data)
{
    g_pointDrawing.reset();
    g_lineDrawing.reset();
}

CARB_EXPORT void carbOnPluginStartup()
{

    INITIALIZE_OGN_NODES()
    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>()->getStageUpdate();

    omni::kit::StageUpdateNodeDesc desc = { nullptr };
    desc.displayName = "Isaac DebugDraw";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    // Create the stage update node and make sure it runs after physx
    size_t index = g_stageUpdate->getStageUpdateNodeCount();
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
    g_stageUpdate->setStageUpdateNodeOrder(index, 75);

    g_pointDrawing = std::make_unique<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
        g_usdContext, isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::ePoints);
    g_lineDrawing = std::make_unique<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
        g_usdContext, isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);
}

CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
    g_pointDrawing.reset();
    g_lineDrawing.reset();
}

void fillInterface(isaacsim::util::debug_draw::DebugDraw& iface)
{
    using namespace isaacsim::util::debug_draw;
    memset(&iface, 0, sizeof(iface));

    iface.clearLines = clearLines;
    iface.clearPoints = clearPoints;
    iface.drawLines = drawLines;
    iface.drawLinesSpline = drawLinesSpline;
    iface.drawPoints = drawPoints;
    iface.getNumLines = getNumLines;
    iface.getNumPoints = getNumPoints;
}
