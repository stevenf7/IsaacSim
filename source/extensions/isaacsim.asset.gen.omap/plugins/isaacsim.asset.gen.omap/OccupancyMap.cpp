// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <isaacsim/asset/gen/omap/MapGenerator.h>
#include <isaacsim/asset/gen/omap/OccupancyMap.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <PrimitiveDrawingHelper.h>
#include <map>
#include <string>
#include <vector>

namespace
{
const carb::PluginImplDesc kPluginImpl = { "isaacsim.asset.gen.omap.plugin", "Isaac Motion Planning", "NVIDIA",
                                           carb::PluginHotReload::eDisabled, "dev" };

pxr::UsdStageWeakPtr g_stage = nullptr;
omni::kit::StageUpdatePtr g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
omni::physx::IPhysx* g_physx = nullptr;
carb::Float3 g_inputOrigin = { 0.0f, 0.0f, 0.0f };
carb::Float3 g_inputMinPoint = { -1.0f, -1.0f, 0.0f };
carb::Float3 g_inputMaxPoint = { 1.0f, 1.0f, 0.0f };
float g_inputCellSize = 0.05f;
float g_metersPerUnit = 1.0f;

std::unique_ptr<isaacsim::asset::gen::omap::MapGenerator> g_generator = nullptr;
std::unique_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> g_lineDrawing;
std::unique_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> g_cellDrawing;
}

CARB_PLUGIN_IMPL(kPluginImpl, isaacsim::asset::gen::omap::OccupancyMap)
CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx, omni::kit::IStageUpdate)

void CARB_ABI generateMap()
{

    g_generator = std::make_unique<isaacsim::asset::gen::omap::MapGenerator>(g_physx, g_stage);

    g_generator->setTransform(g_inputOrigin, g_inputMinPoint, g_inputMaxPoint);
    g_generator->updateSettings(g_inputCellSize, 1.0f, 0.0f, 0.5f);
    g_generator->generate2d();
}

void CARB_ABI setTransform(carb::Float3 origin, carb::Float3 minimum, carb::Float3 maximum)
{
    g_inputOrigin = origin;
    g_inputMinPoint = minimum;
    g_inputMaxPoint = maximum;
}

void CARB_ABI setCellSize(float cellSize)
{
    if (cellSize <= 0)
    {
        cellSize = .01f / g_metersPerUnit;
        CARB_LOG_WARN("Cell size is less than or equal to 0. A value of 0.01 meters will be used instead.");
    }
    g_inputCellSize = cellSize;
}

// Helper function to draw bounding box
void drawBoundingBox(const std::vector<carb::Float3>& corners, const carb::ColorRgba& color, float lineWidth)
{
    // Bottom face
    for (int i = 0; i < 4; i++)
    {
        g_lineDrawing->addVertex(corners[i], color, lineWidth);
        g_lineDrawing->addVertex(corners[(i + 1) % 4], color, lineWidth);
    }

    // Top face
    for (int i = 4; i < 8; i++)
    {
        g_lineDrawing->addVertex(corners[i], color, lineWidth);
        g_lineDrawing->addVertex(corners[(i + 1) % 4 + 4], color, lineWidth);
    }

    // Vertical edges
    for (int i = 0; i < 4; i++)
    {
        g_lineDrawing->addVertex(corners[i], color, lineWidth);
        g_lineDrawing->addVertex(corners[i + 4], color, lineWidth);
    }
}

// Helper function to draw grid
void drawGrid(float lineWidth)
{
    carb::ColorRgba gridColor = { 0.5f, 0.5f, 0.5f, 0.5f };

    // Draw vertical grid lines
    for (float ix = g_inputMinPoint.x; ix <= g_inputMaxPoint.x; ix += g_inputCellSize)
    {
        carb::Float3 p0{ g_inputOrigin.x + ix, g_inputOrigin.y + g_inputMinPoint.y, g_inputOrigin.z };
        carb::Float3 p1{ g_inputOrigin.x + ix, g_inputOrigin.y + g_inputMaxPoint.y, g_inputOrigin.z };

        g_lineDrawing->addVertex(p0, gridColor, lineWidth);
        g_lineDrawing->addVertex(p1, gridColor, lineWidth);
    }

    // Draw horizontal grid lines
    for (float iy = g_inputMinPoint.y; iy <= g_inputMaxPoint.y; iy += g_inputCellSize)
    {
        carb::Float3 p0{ g_inputOrigin.x + g_inputMinPoint.x, g_inputOrigin.y + iy, g_inputOrigin.z };
        carb::Float3 p1{ g_inputOrigin.x + g_inputMaxPoint.x, g_inputOrigin.y + iy, g_inputOrigin.z };

        g_lineDrawing->addVertex(p0, gridColor, lineWidth);
        g_lineDrawing->addVertex(p1, gridColor, lineWidth);
    }
}

void CARB_ABI Update()
{
    g_lineDrawing->clear();
    g_cellDrawing->clear();
    float lineWidth = 2.0f;

    // Calculate corners
    std::vector<carb::Float3> corners(8);
    corners[0] = carb::Float3({ g_inputOrigin.x + g_inputMinPoint.x, g_inputOrigin.y + g_inputMinPoint.y,
                                g_inputOrigin.z + g_inputMinPoint.z });
    corners[1] = carb::Float3({ g_inputOrigin.x + g_inputMaxPoint.x, g_inputOrigin.y + g_inputMinPoint.y,
                                g_inputOrigin.z + g_inputMinPoint.z });
    corners[2] = carb::Float3({ g_inputOrigin.x + g_inputMaxPoint.x, g_inputOrigin.y + g_inputMaxPoint.y,
                                g_inputOrigin.z + g_inputMinPoint.z });
    corners[3] = carb::Float3({ g_inputOrigin.x + g_inputMinPoint.x, g_inputOrigin.y + g_inputMaxPoint.y,
                                g_inputOrigin.z + g_inputMinPoint.z });
    corners[4] = carb::Float3({ g_inputOrigin.x + g_inputMinPoint.x, g_inputOrigin.y + g_inputMinPoint.y,
                                g_inputOrigin.z + g_inputMaxPoint.z });
    corners[5] = carb::Float3({ g_inputOrigin.x + g_inputMaxPoint.x, g_inputOrigin.y + g_inputMinPoint.y,
                                g_inputOrigin.z + g_inputMaxPoint.z });
    corners[6] = carb::Float3({ g_inputOrigin.x + g_inputMaxPoint.x, g_inputOrigin.y + g_inputMaxPoint.y,
                                g_inputOrigin.z + g_inputMaxPoint.z });
    corners[7] = carb::Float3({ g_inputOrigin.x + g_inputMinPoint.x, g_inputOrigin.y + g_inputMaxPoint.y,
                                g_inputOrigin.z + g_inputMaxPoint.z });

    // Draw bounding box
    drawBoundingBox(corners, { 1, 1, 1, 1 }, lineWidth);

    // Draw grid
    drawGrid(lineWidth);

    // Draw coordinate axes
    carb::Float3 scaleMin = g_inputMinPoint;
    carb::Float3 scaleMax = g_inputMaxPoint;

    // Ensure minimum axis size
    float minSize = 0.1f / g_metersPerUnit;

    // Check and adjust X dimension
    if (scaleMax.x - scaleMin.x < minSize)
    {
        scaleMin.x -= minSize;
        scaleMax.x += minSize;
    }

    // Check and adjust Y dimension
    if (scaleMax.y - scaleMin.y < minSize)
    {
        scaleMin.y -= minSize;
        scaleMax.y += minSize;
    }

    // Check and adjust Z dimension
    if (scaleMax.z - scaleMin.z < minSize)
    {
        scaleMin.z -= minSize;
        scaleMax.z += minSize;
    }

    // Draw X axis (red)
    g_lineDrawing->addVertex(carb::Float3({ g_inputOrigin.x + scaleMin.x, g_inputOrigin.y, g_inputOrigin.z }),
                             { 1, 0, 0, 1 }, lineWidth * 2);
    g_lineDrawing->addVertex(carb::Float3({ g_inputOrigin.x + scaleMax.x, g_inputOrigin.y, g_inputOrigin.z }),
                             { 1, 0, 0, 1 }, lineWidth * 2);

    // Draw Y axis (green)
    g_lineDrawing->addVertex(carb::Float3({ g_inputOrigin.x, g_inputOrigin.y + scaleMin.y, g_inputOrigin.z }),
                             { 0, 1, 0, 1 }, lineWidth * 2);
    g_lineDrawing->addVertex(carb::Float3({ g_inputOrigin.x, g_inputOrigin.y + scaleMax.y, g_inputOrigin.z }),
                             { 0, 1, 0, 1 }, lineWidth * 2);

    // Draw Z axis (blue)
    g_lineDrawing->addVertex(carb::Float3({ g_inputOrigin.x, g_inputOrigin.y, g_inputOrigin.z + scaleMin.z }),
                             { 0, 0, 1, 1 }, lineWidth * 2);
    g_lineDrawing->addVertex(carb::Float3({ g_inputOrigin.x, g_inputOrigin.y, g_inputOrigin.z + scaleMax.z }),
                             { 0, 0, 1, 1 }, lineWidth * 2);

    g_lineDrawing->draw();
}

std::vector<carb::Float3> getOccupiedPositions()
{
    std::vector<carb::Float3> pos;
    if (g_generator)
    {
        pos = g_generator->getOccupiedPositions();
    }
    return pos;
}

std::vector<carb::Float3> getFreePositions()
{
    std::vector<carb::Float3> pos;
    if (g_generator)
    {
        pos = g_generator->getFreePositions();
    }
    return pos;
}

carb::Float3 getMinBound()
{
    carb::Float3 bounds = { 0, 0, 0 };
    if (g_generator)
    {
        bounds = g_generator->getMinBound();
    }
    return bounds;
}

carb::Float3 getMaxBound()
{
    carb::Float3 bounds = { 0, 0, 0 };
    if (g_generator)
    {
        bounds = g_generator->getMaxBound();
    }
    return bounds;
}

carb::Int3 getDimensions()
{
    carb::Int3 dims = { 0, 0, 0 };
    if (g_generator)
    {
        dims = g_generator->getDimensions();
    }
    return dims;
}

std::vector<float> getBuffer()
{
    if (g_generator)
    {
        return g_generator->getBuffer();
    }
    return std::vector<float>();
}

std::vector<char> getColoredByteBuffer(const carb::Int4& occupied, const carb::Int4& unoccupied, const carb::Int4& unknown)
{
    if (g_generator)
    {
        return g_generator->getColoredByteBuffer(occupied, unoccupied, unknown);
    }
    return std::vector<char>();
}

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    // try and find USD stage from Id
    pxr::UsdStageWeakPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

    if (!stage)
    {
        CARB_LOG_ERROR("Isaac OccupancyMap could not find USD stage");
        return;
    }

    g_stage = stage;
    g_metersPerUnit = static_cast<float>(metersPerUnit);
    g_lineDrawing = std::make_unique<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
        omni::usd::UsdContext::getContext(), isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::eLines);

    g_cellDrawing = std::make_unique<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
        omni::usd::UsdContext::getContext(), isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::eLines, true);
}

static void onDetach(void* data)
{

    g_lineDrawing.reset();
    g_cellDrawing.reset();
}

void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{

    if (!settings->isPlaying)
    {
        return;
    }
}


CARB_EXPORT void carbOnPluginStartup()
{
    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>()->getStageUpdate();

    g_physx = carb::getCachedInterface<omni::physx::IPhysx>();
    if (!g_physx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "OccupancyMap";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    // Create the stage update node and make sure it runs after physx
    size_t index = g_stageUpdate->getStageUpdateNodeCount();
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
    g_stageUpdate->setStageUpdateNodeOrder(index, 75);
}

CARB_EXPORT void carbOnPluginShutdown()
{
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
    g_lineDrawing.reset();
    g_cellDrawing.reset();
}

void fillInterface(isaacsim::asset::gen::omap::OccupancyMap& iface)
{
    iface.generateMap = generateMap;
    iface.update = Update;
    iface.setTransform = setTransform;
    iface.setCellSize = setCellSize;
    iface.getOccupiedPositions = getOccupiedPositions;
    iface.getFreePositions = getFreePositions;
    iface.getMinBound = getMinBound;
    iface.getMaxBound = getMaxBound;
    iface.getDimensions = getDimensions;
    iface.getBuffer = getBuffer;
    iface.getColoredByteBuffer = getColoredByteBuffer;
}
