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

#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <MapGenerator.h>
#include <OccupancyMap.h>
#include <PrimitiveDrawingHelper.h>
#include <map>
#include <string>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "isaacsim.asset.gen.omap.plugin", "Isaac Motion Planning", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, isaacsim::asset::gen::omap::OccupancyMap)
CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx, omni::kit::IStageUpdate)

// private stuff
namespace
{
pxr::UsdStageWeakPtr gStage = nullptr;
omni::kit::StageUpdatePtr gStageUpdate = nullptr;
omni::kit::StageUpdateNode* gStageUpdateNode = nullptr;
omni::physx::IPhysx* gPhysx = nullptr;
carb::Float3 inputOrigin = { 0, 0, 0 };
carb::Float3 inputMinPoint = { -1.00f, -1.00f, 0.0f };
carb::Float3 inputMaxPoint = { 1.00f, 1.00f, 0.0f };
float inputCellSize = .05f;
std::unique_ptr<isaacsim::asset::gen::omap::MapGenerator> gGenerator = nullptr;
std::unique_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> gLineDrawing;
std::unique_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> gCellDrawing;
float gMetersPerUnit = 1.0f;
}


void CARB_ABI GenerateMap()
{

    gGenerator = std::make_unique<isaacsim::asset::gen::omap::MapGenerator>(gPhysx, gStage);

    gGenerator->setTransform(inputOrigin, inputMinPoint, inputMaxPoint);
    gGenerator->updateSettings(inputCellSize, 1.0f, 0.0f, 0.5f);
    gGenerator->generate2d();

    // gCellDrawing->clear();

    // std::vector<carb::Float3> occ_pos = gGenerator->getOccupiedPositions();
    // // std::vector<carb::Float2> unocc_pos = gGenerator->getFreePositions();
    // // pos = gGenerator->getOccupiedPositions();
    // carb::ColorRgba occupied = { 1, 1, 1, 1 };
    // // carb::ColorRgba unoccupied = { 1, 1, 1, 1 };
    // float step = inputCellSize / 10.0f;
    // for (size_t i = 0; i < occ_pos.size(); i++)
    // {
    //     for (float ix = -inputCellSize / 2.0f + step; ix <= inputCellSize / 2.0f - step; ix += step)
    //     {
    //         carb::Float3 p0{ occ_pos[i].x + ix, occ_pos[i].y - inputCellSize / 2.0f, inputOrigin.z };
    //         carb::Float3 p1{ occ_pos[i].x + ix, occ_pos[i].y + inputCellSize / 2.0f, inputOrigin.z };

    //         gCellDrawing->addVertex(p0, occupied, 0.02f/ gMetersPerUnit);
    //         gCellDrawing->addVertex(p1, occupied, 0.02f/ gMetersPerUnit);
    //     }

    //     for (float iy = -inputCellSize / 2.0f + step; iy <= inputCellSize / 2.0f - step; iy += step)
    //     {
    //         carb::Float3 p0{ occ_pos[i].x - inputCellSize / 2.0f, occ_pos[i].y + iy, inputOrigin.z };
    //         carb::Float3 p1{ occ_pos[i].x + inputCellSize / 2.0f, occ_pos[i].y + iy, inputOrigin.z };

    //         gCellDrawing->addVertex(p0, occupied, step);
    //         gCellDrawing->addVertex(p1, occupied, step);
    //     }

    //     // gCellDrawing->addVertex(carb::Float3({ occ_pos[i].x, occ_pos[i].y, inputOrigin.z }), occupied,
    //     // inputCellSize); gCellDrawing->addVertex(carb::Float3({ occ_pos[i].x, occ_pos[i].y, inputOrigin.z }),
    //     // occupied, inputCellSize);
    // }
    // // for (size_t i = 0; i < unocc_pos.size(); i++)
    // // {
    // //     gCellDrawing->addVertex(
    // //         carb::Float3({ unocc_pos[i].x, unocc_pos[i].y, inputOrigin.z }), unoccupied, inputCellSize);
    // // }
    // gCellDrawing->draw();
}

void CARB_ABI SetTransform(carb::Float3 origin, carb::Float3 minimum, carb::Float3 maximum)
{
    inputOrigin = origin;
    inputMinPoint = minimum;
    inputMaxPoint = maximum;
}

void CARB_ABI SetCellSize(float cellSize)
{
    if (cellSize <= 0)
    {
        cellSize = .01f / gMetersPerUnit;
        CARB_LOG_WARN("Cell size is less than or equal to 0. A value of 0.01 meters will be used instead.");
    }
    inputCellSize = cellSize;
}

// Helper function to draw bounding box
void drawBoundingBox(const std::vector<carb::Float3>& corners, const carb::ColorRgba& color, float lineWidth)
{
    // Bottom face
    for (int i = 0; i < 4; i++)
    {
        gLineDrawing->addVertex(corners[i], color, lineWidth);
        gLineDrawing->addVertex(corners[(i + 1) % 4], color, lineWidth);
    }

    // Top face
    for (int i = 4; i < 8; i++)
    {
        gLineDrawing->addVertex(corners[i], color, lineWidth);
        gLineDrawing->addVertex(corners[(i + 1) % 4 + 4], color, lineWidth);
    }

    // Vertical edges
    for (int i = 0; i < 4; i++)
    {
        gLineDrawing->addVertex(corners[i], color, lineWidth);
        gLineDrawing->addVertex(corners[i + 4], color, lineWidth);
    }
}

// Helper function to draw grid
void drawGrid(float lineWidth)
{
    carb::ColorRgba gridColor = { 0.5f, 0.5f, 0.5f, 0.5f };

    // Draw vertical grid lines
    for (float ix = inputMinPoint.x; ix <= inputMaxPoint.x; ix += inputCellSize)
    {
        carb::Float3 p0{ inputOrigin.x + ix, inputOrigin.y + inputMinPoint.y, inputOrigin.z };
        carb::Float3 p1{ inputOrigin.x + ix, inputOrigin.y + inputMaxPoint.y, inputOrigin.z };

        gLineDrawing->addVertex(p0, gridColor, lineWidth);
        gLineDrawing->addVertex(p1, gridColor, lineWidth);
    }

    // Draw horizontal grid lines
    for (float iy = inputMinPoint.y; iy <= inputMaxPoint.y; iy += inputCellSize)
    {
        carb::Float3 p0{ inputOrigin.x + inputMinPoint.x, inputOrigin.y + iy, inputOrigin.z };
        carb::Float3 p1{ inputOrigin.x + inputMaxPoint.x, inputOrigin.y + iy, inputOrigin.z };

        gLineDrawing->addVertex(p0, gridColor, lineWidth);
        gLineDrawing->addVertex(p1, gridColor, lineWidth);
    }
}

void CARB_ABI Update()
{
    gLineDrawing->clear();
    gCellDrawing->clear();
    float lineWidth = 2.0f;

    // Calculate corners
    std::vector<carb::Float3> corners(8);
    corners[0] = carb::Float3(
        { inputOrigin.x + inputMinPoint.x, inputOrigin.y + inputMinPoint.y, inputOrigin.z + inputMinPoint.z });
    corners[1] = carb::Float3(
        { inputOrigin.x + inputMaxPoint.x, inputOrigin.y + inputMinPoint.y, inputOrigin.z + inputMinPoint.z });
    corners[2] = carb::Float3(
        { inputOrigin.x + inputMaxPoint.x, inputOrigin.y + inputMaxPoint.y, inputOrigin.z + inputMinPoint.z });
    corners[3] = carb::Float3(
        { inputOrigin.x + inputMinPoint.x, inputOrigin.y + inputMaxPoint.y, inputOrigin.z + inputMinPoint.z });
    corners[4] = carb::Float3(
        { inputOrigin.x + inputMinPoint.x, inputOrigin.y + inputMinPoint.y, inputOrigin.z + inputMaxPoint.z });
    corners[5] = carb::Float3(
        { inputOrigin.x + inputMaxPoint.x, inputOrigin.y + inputMinPoint.y, inputOrigin.z + inputMaxPoint.z });
    corners[6] = carb::Float3(
        { inputOrigin.x + inputMaxPoint.x, inputOrigin.y + inputMaxPoint.y, inputOrigin.z + inputMaxPoint.z });
    corners[7] = carb::Float3(
        { inputOrigin.x + inputMinPoint.x, inputOrigin.y + inputMaxPoint.y, inputOrigin.z + inputMaxPoint.z });

    // Draw bounding box
    drawBoundingBox(corners, { 1, 1, 1, 1 }, lineWidth);

    // Draw grid
    drawGrid(lineWidth);

    // Draw coordinate axes
    carb::Float3 scaleMin = inputMinPoint;
    carb::Float3 scaleMax = inputMaxPoint;

    // Ensure minimum axis size
    float minSize = 0.1f / gMetersPerUnit;

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
    gLineDrawing->addVertex(
        carb::Float3({ inputOrigin.x + scaleMin.x, inputOrigin.y, inputOrigin.z }), { 1, 0, 0, 1 }, lineWidth * 2);
    gLineDrawing->addVertex(
        carb::Float3({ inputOrigin.x + scaleMax.x, inputOrigin.y, inputOrigin.z }), { 1, 0, 0, 1 }, lineWidth * 2);

    // Draw Y axis (green)
    gLineDrawing->addVertex(
        carb::Float3({ inputOrigin.x, inputOrigin.y + scaleMin.y, inputOrigin.z }), { 0, 1, 0, 1 }, lineWidth * 2);
    gLineDrawing->addVertex(
        carb::Float3({ inputOrigin.x, inputOrigin.y + scaleMax.y, inputOrigin.z }), { 0, 1, 0, 1 }, lineWidth * 2);

    // Draw Z axis (blue)
    gLineDrawing->addVertex(
        carb::Float3({ inputOrigin.x, inputOrigin.y, inputOrigin.z + scaleMin.z }), { 0, 0, 1, 1 }, lineWidth * 2);
    gLineDrawing->addVertex(
        carb::Float3({ inputOrigin.x, inputOrigin.y, inputOrigin.z + scaleMax.z }), { 0, 0, 1, 1 }, lineWidth * 2);

    gLineDrawing->draw();
}

std::vector<carb::Float3> GetOccupiedPositions()
{
    std::vector<carb::Float3> pos;
    if (gGenerator)
    {
        pos = gGenerator->getOccupiedPositions();
    }
    return pos;
}

std::vector<carb::Float3> GetFreePositions()
{
    std::vector<carb::Float3> pos;
    if (gGenerator)
    {
        pos = gGenerator->getFreePositions();
    }
    return pos;
}

carb::Float3 GetMinBound()
{
    carb::Float3 bounds = { 0, 0, 0 };
    if (gGenerator)
    {
        bounds = gGenerator->getMinBound();
    }
    return bounds;
}

carb::Float3 GetMaxBound()
{
    carb::Float3 bounds = { 0, 0, 0 };
    if (gGenerator)
    {
        bounds = gGenerator->getMaxBound();
    }
    return bounds;
}

carb::Int3 GetDimensions()
{
    carb::Int3 dims = { 0, 0, 0 };
    if (gGenerator)
    {
        dims = gGenerator->getDimensions();
    }
    return dims;
}

std::vector<float> GetBuffer()
{
    if (gGenerator)
    {
        return gGenerator->getBuffer();
    }
    return std::vector<float>();
}

std::vector<char> GetColoredByteBuffer(const carb::Int4& occupied, const carb::Int4& unoccupied, const carb::Int4& unknown)
{
    if (gGenerator)
    {
        return gGenerator->getColoredByteBuffer(occupied, unoccupied, unknown);
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

    gStage = stage;
    gMetersPerUnit = static_cast<float>(metersPerUnit);
    gLineDrawing = std::make_unique<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
        omni::usd::UsdContext::getContext(), isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::eLines);

    gCellDrawing = std::make_unique<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
        omni::usd::UsdContext::getContext(), isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::eLines, true);
}

static void onDetach(void* data)
{

    gLineDrawing.reset();
    gCellDrawing.reset();
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
    gStageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>()->getStageUpdate();

    gPhysx = carb::getCachedInterface<omni::physx::IPhysx>();
    if (!gPhysx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "OccupancyMap";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    // Create the stage update node and make sure it runs after physx
    size_t index = gStageUpdate->getStageUpdateNodeCount();
    gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);
    gStageUpdate->setStageUpdateNodeOrder(index, 75);
}

CARB_EXPORT void carbOnPluginShutdown()
{
    gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
    gLineDrawing.reset();
    gCellDrawing.reset();
}

void fillInterface(isaacsim::asset::gen::omap::OccupancyMap& iface)
{
    using namespace isaacsim::asset::gen::omap;

    memset(&iface, 0, sizeof(iface));

    iface.generateMap = GenerateMap;
    iface.update = Update;
    iface.setTransform = SetTransform;
    iface.setCellSize = SetCellSize;
    iface.getOccupiedPositions = GetOccupiedPositions;
    iface.getFreePositions = GetFreePositions;
    iface.getMinBound = GetMinBound;
    iface.getMaxBound = GetMaxBound;
    iface.getDimensions = GetDimensions;
    iface.getBuffer = GetBuffer;
    iface.getColoredByteBuffer = GetColoredByteBuffer;
}
