// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <carb/flatcache/FlatCache.h>
#include <carb/flatcache/IToken.h>
#include <carb/flatcache/StageWithHistory.h>
#include <carb/imaging/IImaging.h>

#include <omni/graph/core/NodeTypeRegistrar.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/isaac/core_nodes/CoreNodes.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/kit/IMinimal.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>

const struct carb::PluginImplDesc pluginDesc = { "omni.isaac.core_nodes", "Isaac Sim Core OmniGraph Nodes", "NVIDIA",
                                                 carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(pluginDesc, omni::isaac::core_nodes::CoreNodes)
CARB_PLUGIN_IMPL_DEPS(omni::graph::core::IGraphRegistry,
                      omni::kit::IStageUpdate,
                      carb::flatcache::IToken,
                      omni::physx::IPhysx,
                      carb::flatcache::IStageInProgress,
                      carb::flatcache::IStageWithHistory,
                      carb::flatcache::IStageAtTimeInterval,
                      omni::isaac::dynamic_control::DynamicControl)

DECLARE_OGN_NODES()

namespace
{
omni::kit::IStageUpdate* gStageUpdate = nullptr;
omni::kit::StageUpdateNode* gStageUpdateNode = nullptr;
carb::flatcache::IStageWithHistory* gStageWithHistory = nullptr;
carb::flatcache::IStageInProgress* gStageInProgress = nullptr;
carb::flatcache::IStageAtTimeInterval* gStageAtTimeInterval = nullptr;
omni::physx::IPhysx* gPhysXInterface = nullptr;
omni::physx::SubscriptionId gStepSubscription;
pxr::UsdStageWeakPtr gStage = nullptr;
carb::flatcache::StageInProgressId gStageInProgressId;
carb::flatcache::StageWithHistoryId gStageWithHistoryId;
carb::flatcache::UsdStageId gStageId = { 0 };
double gSimTime = 0.0;
double gSimTimeMonotonic = 0.0;
double gSystemTime = 0.0;
std::map<uint64_t, void*> gHandleMap;
std::mutex gHandleMutex;
}


static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    // try and find USD stage from Id
    pxr::UsdStageWeakPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

    if (!stage)
    {
        CARB_LOG_ERROR("Isaac Core Nodes could not find USD stage");
        return;
    }

    gStage = stage;
    gStageId.id = stageId;
}

void onDetach(void* userData)
{
}

// void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
// {
//     if (!settings->isPlaying)
//     {
//         return;
//     }
// }

void onResume(float currentTime, void* userData)
{
    gStageInProgressId = gStageInProgress->get(gStageId);
    gStageWithHistoryId = gStageWithHistory->get(gStageId);
    carb::flatcache::StageInProgress stageinProgress = carb::flatcache::StageInProgress(gStageInProgressId);

    stageinProgress.createPrim(carb::flatcache::Path("/__OgnIsaacSimTime__"));

    const omni::graph::core::Type typeTag(omni::graph::core::BaseDataType::eTag);
    const carb::flatcache::Token fc_exportToRingbuffer("fc_exportToRingbuffer");
    stageinProgress.createAttribute(carb::flatcache::Path("/__OgnIsaacSimTime__"), fc_exportToRingbuffer, typeTag);

    const omni::graph::core::Type typeDouble(omni::graph::core::BaseDataType::eDouble, 1, 0);
    stageinProgress.getOrCreateAttributeWr<double>(
        carb::flatcache::Path("/__OgnIsaacSimTime__"), carb::flatcache::Token("simTime"), typeDouble) = gSimTime;
    stageinProgress.getOrCreateAttributeWr<double>(
        carb::flatcache::Path("/__OgnIsaacSimTime__"), carb::flatcache::Token("simTimeMonotonic"), typeDouble) =
        gSimTimeMonotonic;
    stageinProgress.getOrCreateAttributeWr<double>(
        carb::flatcache::Path("/__OgnIsaacSimTime__"), carb::flatcache::Token("systemTime"), typeDouble) = gSystemTime;
}

// void onPause(void* userData)
// {
// }
void onStop(void* userData)
{
    carb::flatcache::StageInProgress stageinProgress = carb::flatcache::StageInProgress(gStageInProgressId);
    auto path = carb::flatcache::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = carb::flatcache::intToPath(path);
    pxr::UsdStageRefPtr usdStage =
        pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(uint32_t(gStageId.id)));
    if (usdStage->GetPrimAtPath(usdPath))
    {
        stageinProgress.destroyPrim(path);
    }
    gSimTime = 0;
}

void onPhysicsStep(float timeElapsed, void* userData)
{
    carb::flatcache::StageInProgress stageinProgress = carb::flatcache::StageInProgress(gStageInProgressId);
    gSimTime += timeElapsed;
    gSimTimeMonotonic += timeElapsed;
    gSystemTime = std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
    auto path = carb::flatcache::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = carb::flatcache::intToPath(path);
    pxr::UsdStageRefPtr usdStage =
        pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(uint32_t(gStageId.id)));

    gStageInProgress->prefetchPrim(gStageId, path);
    // Check if attribute exists:

    if (!usdStage->GetPrimAtPath(usdPath))
    {
        // create prim and attributes if they do not exist, this sets them to the current values as well
        onResume(0, nullptr);
        return;
    }

    double* simTime = stageinProgress.getAttributeWr<double>(path, carb::flatcache::Token("simTime"));
    double* simTimeMonotonic = stageinProgress.getAttributeWr<double>(path, carb::flatcache::Token("simTimeMonotonic"));
    double* systemTime = stageinProgress.getAttributeWr<double>(path, carb::flatcache::Token("systemTime"));
    // Check if the attributes exist
    if (simTime && simTimeMonotonic && systemTime)
    {
        *simTime = gSimTime;
        *simTimeMonotonic = gSimTimeMonotonic;
        *systemTime = gSystemTime;
    }
    else
    {
        CARB_LOG_ERROR("Could not read or create sim time attributes");
    }
}


double getSimulationTime()
{
    return gSimTime;
}


double getSimulationTimeMonotonic()
{
    return gSimTimeMonotonic;
}

double getSystemTime()
{
    return gSystemTime;
}

double getSimulationTimeAtSwhFrame(const int64_t swhFrame)
{
    auto path = carb::flatcache::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = carb::flatcache::intToPath(path);

    if (!gStage->GetPrimAtPath(usdPath) || !gStageWithHistoryId.id || !gStageId.id)
    {
        return gSimTime;
    }
    else
    {
        CARB_LOG_ERROR("getSimulationTimeAtSwhFrame , returning default sim time %d %d %d",
                       !gStage->GetPrimAtPath(usdPath), !gStageWithHistoryId.id, !gStageId.id);
    }
    carb::flatcache::RationalTime simPeriod = gStageWithHistory->getSimPeriod(gStageId);
    carb::flatcache::RationalTime rtime = simPeriod * swhFrame;
    carb::flatcache::StageAtTimeInterval stageAtTimeInterval(gStageWithHistoryId, rtime, rtime, true);
    auto simTime = stageAtTimeInterval.getAttributeRd<double>(
        carb::flatcache::Path("/__OgnIsaacSimTime__"), carb::flatcache::Token("simTime"));
    if (!simTime.empty() && simTime[0])
    {
        return *simTime[0];
    }
    else
    {
        return gSimTime;
    }
}


double getSimulationTimeMonotonicAtSwhFrame(const int64_t swhFrame)
{
    auto path = carb::flatcache::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = carb::flatcache::intToPath(path);

    if (!gStage->GetPrimAtPath(usdPath) || !gStageWithHistoryId.id || !gStageId.id)
    {
        return gSimTimeMonotonic;
    }
    else
    {
        CARB_LOG_ERROR("getSimulationTimeMonotonicAtSwhFrame, returning default monotonic sim time %d %d %d",
                       !gStage->GetPrimAtPath(usdPath), !gStageWithHistoryId.id, !gStageId.id);
    }
    carb::flatcache::RationalTime simPeriod = gStageWithHistory->getSimPeriod(gStageId);
    carb::flatcache::RationalTime rtime = simPeriod * swhFrame;
    carb::flatcache::StageAtTimeInterval stageAtTimeInterval(gStageWithHistoryId, rtime, rtime, true);
    auto simTimeMonotonic = stageAtTimeInterval.getAttributeRd<double>(
        carb::flatcache::Path("/__OgnIsaacSimTime__"), carb::flatcache::Token("simTimeMonotonic"));
    if (!simTimeMonotonic.empty() && simTimeMonotonic[0])
    {
        return *simTimeMonotonic[0];
    }
    else
    {
        return gSimTimeMonotonic;
    }
}

double getSystemTimeAtSwhFrame(const int64_t swhFrame)
{

    auto path = carb::flatcache::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = carb::flatcache::intToPath(path);

    if (!gStage->GetPrimAtPath(usdPath) || !gStageWithHistoryId.id || !gStageId.id)
    {
        return gSystemTime;
    }
    else
    {
        CARB_LOG_ERROR("getSystemTimeAtSwhFrame, returning default system time %d %d %d",
                       !gStage->GetPrimAtPath(usdPath), !gStageWithHistoryId.id, !gStageId.id);
    }
    carb::flatcache::RationalTime simPeriod = gStageWithHistory->getSimPeriod(gStageId);
    carb::flatcache::RationalTime rtime = simPeriod * swhFrame;
    carb::flatcache::StageAtTimeInterval stageAtTimeInterval(gStageWithHistoryId, rtime, rtime, true);
    auto systemTime = stageAtTimeInterval.getAttributeRd<double>(
        carb::flatcache::Path("/__OgnIsaacSimTime__"), carb::flatcache::Token("systemTime"));
    if (!systemTime.empty() && systemTime[0])
    {
        return *systemTime[0];
    }
    else
    {
        return gSystemTime;
    }
}

uint64_t addHandle(void* handle)
{
    uint64_t handleId = reinterpret_cast<uint64_t>(handle);
    std::lock_guard<std::mutex> guard(gHandleMutex);
    gHandleMap[handleId] = handle;
    return handleId;
}

void* getHandle(const uint64_t handleId)
{
    std::lock_guard<std::mutex> guard(gHandleMutex);
    auto it = gHandleMap.find(handleId);
    if (it == gHandleMap.end())
    {
        return nullptr;
    }
    else
    {
        return it->second;
    }
}

bool removeHandle(const uint64_t handleId)
{
    std::lock_guard<std::mutex> guard(gHandleMutex);
    return gHandleMap.erase(handleId);
}

CARB_EXPORT void carbOnPluginStartup()
{
    gStageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>();
    gStageInProgress = carb::getCachedInterface<carb::flatcache::IStageInProgress>();
    gPhysXInterface = carb::getCachedInterface<omni::physx::IPhysx>();
    gStageWithHistory = carb::getCachedInterface<carb::flatcache::IStageWithHistory>();
    gStageAtTimeInterval = carb::getCachedInterface<carb::flatcache::IStageAtTimeInterval>();
    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "Isaac Core Nodes";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    // desc.onUpdate = onUpdate;
    desc.onResume = onResume;
    // desc.onPause = onPause;
    desc.onStop = onStop;
    desc.order = 20; // should run after physics
    gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);

    gStepSubscription = gPhysXInterface->subscribePhysicsStepEvents(onPhysicsStep, nullptr);


    // This increases forever until we stop sim.
    gSimTimeMonotonic = 0.0;
    gSystemTime = std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();

    INITIALIZE_OGN_NODES()
}

CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()

    gPhysXInterface->unsubscribePhysicsStepEvents(gStepSubscription);
    gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
}

// carbonite interface for this plugin (may contain multiple compute nodes)
void fillInterface(omni::isaac::core_nodes::CoreNodes& iface)
{

    using namespace omni::isaac::core_nodes;

    memset(&iface, 0, sizeof(iface));

    iface.getSimTime = getSimulationTime;
    iface.getSimTimeMonotonic = getSimulationTimeMonotonic;
    iface.getSystemTime = getSystemTime;

    iface.getSimTimeAtSwhFrame = getSimulationTimeAtSwhFrame;
    iface.getSimTimeMonotonicAtSwhFrame = getSimulationTimeMonotonicAtSwhFrame;
    iface.getSystemTimeAtSwhFrame = getSystemTimeAtSwhFrame;

    iface.addHandle = addHandle;
    iface.getHandle = getHandle;
    iface.removeHandle = removeHandle;
}
