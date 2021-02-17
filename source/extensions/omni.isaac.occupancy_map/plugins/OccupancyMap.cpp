// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include <omni/isaac/occupancy_map/OccupancyMap.h>
#include <omni/isaac/occupancy_map/MapGenerator.h>

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <omni/physx/IPhysx.h>

#include <omni/kit/IStageUpdate.h>
#include <omni/renderer/IDebugDraw.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

#include <map>
#include <string>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.occupancy_map.plugin", "Isaac Motion Planning", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::occupancy_map::OccupancyMap)
CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx, omni::kit::IStageUpdate, omni::renderer::IDebugDraw)

// private stuff
namespace
{
pxr::UsdStageWeakPtr gStage = nullptr;
carb::Framework* gFramework = nullptr;
omni::kit::IStageUpdate* gStageUpdate = nullptr;
omni::kit::StageUpdateNode* gStageUpdateNode = nullptr;
omni::physx::IPhysx* gPhysx = nullptr;
carb::Float3 inputOrigin = { 0, 0, 0 };
carb::Float2 inputMinPoint = { -100, -100 };
carb::Float2 inputMaxPoint = { 100, 100 };
std::unique_ptr<omni::isaac::occupancy_map::MapGenerator> gGenerator = nullptr;

}


void CARB_ABI
GenerateMap(float gridResolution, float rayResolution, float minSearchDistance, float occupancyThreshold, size_t maxRays)
{

    gGenerator = std::make_unique<omni::isaac::occupancy_map::MapGenerator>(gPhysx, gStage);

    gGenerator->setTransform(inputOrigin, inputMinPoint, inputMaxPoint);
    gGenerator->updateSettings(
        gridResolution, occupancyThreshold, minSearchDistance, rayResolution, maxRays, 1.0f, 0.0f, 0.5f);
    gGenerator->generate();
}

void CARB_ABI SetTransform(carb::Float3 origin, carb::Float2 minimum, carb::Float2 maximum)
{

    inputOrigin = origin;
    inputMinPoint = minimum;
    inputMaxPoint = maximum;

    // printf("[%f %f %f], [%f %f], [%f %f]\n", origin.x, origin.y, origin.z, minimum.x, minimum.y, maximum.x,
    // maximum.y);
}


omni::renderer::IDebugDraw* g_debugDraw = nullptr;
omni::renderer::LineBuffer mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
omni::renderer::RenderInstanceBuffer mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
void createDebugLineList(size_t size)
{
    if (mShapeDebugLineBuffer == omni::renderer::IDebugDraw::eInvalidBuffer)
    {
        mShapeDebugLineBuffer = g_debugDraw->allocateLineBuffer(size);
        mShapeDebugRenderInstanceBuffer = g_debugDraw->allocateRenderInstanceBuffer(mShapeDebugLineBuffer, 1);
        float transform[16] = {};
        transform[0] = 1.f;
        transform[1 + 4] = 1.f;
        transform[2 + 8] = 1.f;
        transform[3 + 12] = 1.f;

        g_debugDraw->setRenderInstance(mShapeDebugRenderInstanceBuffer, 0, &transform[0], 0);
    }
}

void releaseDebugLineList()
{
    if (mShapeDebugLineBuffer != omni::renderer::IDebugDraw::eInvalidBuffer)
    {
        g_debugDraw->deallocateLineBuffer(mShapeDebugLineBuffer);
        g_debugDraw->deallocateRenderInstanceBuffer(mShapeDebugRenderInstanceBuffer);
        mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
        mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    }
}

void CARB_ABI Update()
{
    releaseDebugLineList();
    createDebugLineList(4);
    uint32_t color = 255 + (255 << 8) + (255 << 16) + (255 << 24);
    g_debugDraw->setLine(mShapeDebugLineBuffer, 0,
                         { inputOrigin.x + inputMinPoint.x, inputOrigin.y + inputMinPoint.y, inputOrigin.z }, color,
                         { inputOrigin.x + inputMaxPoint.x, inputOrigin.y + inputMinPoint.y, inputOrigin.z }, color);
    g_debugDraw->setLine(mShapeDebugLineBuffer, 1,
                         { inputOrigin.x + inputMinPoint.x, inputOrigin.y + inputMinPoint.y, inputOrigin.z }, color,
                         { inputOrigin.x + inputMinPoint.x, inputOrigin.y + inputMaxPoint.y, inputOrigin.z }, color);
    g_debugDraw->setLine(mShapeDebugLineBuffer, 2,
                         { inputOrigin.x + inputMaxPoint.x, inputOrigin.y + inputMinPoint.y, inputOrigin.z }, color,
                         { inputOrigin.x + inputMaxPoint.x, inputOrigin.y + inputMaxPoint.y, inputOrigin.z }, color);
    g_debugDraw->setLine(mShapeDebugLineBuffer, 3,
                         { inputOrigin.x + inputMinPoint.x, inputOrigin.y + inputMaxPoint.y, inputOrigin.z }, color,
                         { inputOrigin.x + inputMaxPoint.x, inputOrigin.y + inputMaxPoint.y, inputOrigin.z }, color);
}
std::vector<carb::Float2> GetOccupiedPositions()
{
    std::vector<carb::Float2> pos;
    if (gGenerator)
    {
        pos = gGenerator->getOccupiedPositions();
    }
    return pos;
}
std::vector<carb::Float2> GetFreePositions()
{
    std::vector<carb::Float2> pos;
    if (gGenerator)
    {
        pos = gGenerator->getFreePositions();
    }
    return pos;
}
carb::Float2 GetMinBound()
{
    carb::Float2 bounds = { 0, 0 };
    if (gGenerator)
    {
        bounds = gGenerator->getMinBound();
    }
    return bounds;
}
carb::Float2 GetMaxBound()
{
    carb::Float2 bounds = { 0, 0 };
    if (gGenerator)
    {
        bounds = gGenerator->getMaxBound();
    }
    return bounds;
}

carb::Int2 GetDimensions()
{
    carb::Int2 bounds = { 0, 0 };
    if (gGenerator)
    {
        bounds = gGenerator->getDimensions();
    }
    return bounds;
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
    gFramework = carb::getFramework();
    gStageUpdate = gFramework->acquireInterface<omni::kit::IStageUpdate>();

    gPhysx = gFramework->acquireInterface<omni::physx::IPhysx>();
    if (!gPhysx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }
    g_debugDraw = gFramework->acquireInterface<omni::renderer::IDebugDraw>();
    if (!g_debugDraw)
    {
        CARB_LOG_ERROR("*** Failed to acquire debugdraw interface\n");
        return;
    }
    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "OccupancyMap";
    desc.onAttach = onAttach;
    // Create the stage update node and make sure it runs after physx
    size_t index = gStageUpdate->getStageUpdateNodeCount();
    gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);
    gStageUpdate->setStageUpdateNodeOrder(index, 75);
}

CARB_EXPORT void carbOnPluginShutdown()
{
    releaseDebugLineList();
    gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
}

void fillInterface(omni::isaac::occupancy_map::OccupancyMap& iface)
{
    using namespace omni::isaac::occupancy_map;

    memset(&iface, 0, sizeof(iface));

    iface.generateMap = GenerateMap;
    iface.update = Update;
    iface.setTransform = SetTransform;
    iface.getOccupiedPositions = GetOccupiedPositions;
    iface.getFreePositions = GetFreePositions;
    iface.getMinBound = GetMinBound;
    iface.getMaxBound = GetMaxBound;
    iface.getDimensions = GetDimensions;
    iface.getBuffer = GetBuffer;
    iface.getColoredByteBuffer = GetColoredByteBuffer;
}
