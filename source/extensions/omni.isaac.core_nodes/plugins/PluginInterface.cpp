// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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
#include <carb/imaging/IImaging.h>

#include <omni/fabric/FabricUSD.h>
#include <omni/fabric/IToken.h>
#include <omni/fabric/SimStageWithHistory.h>
#include <omni/graph/core/NodeTypeRegistrar.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/kit/IMinimal.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>

#include <CoreNodes.h>
#include <DynamicControl.h>

const struct carb::PluginImplDesc pluginDesc = { "omni.isaac.core_nodes", "Isaac Sim Core OmniGraph Nodes", "NVIDIA",
                                                 carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(pluginDesc, omni::isaac::core_nodes::CoreNodes)
CARB_PLUGIN_IMPL_DEPS(omni::graph::core::IGraphRegistry,
                      omni::kit::IStageUpdate,
                      omni::fabric::IToken,
                      omni::physx::IPhysx,
                      omni::fabric::IStageReaderWriter,
                      omni::fabric::ISimStageWithHistory,
                      omni::fabric::IStageAtTimeInterval,
                      omni::isaac::dynamic_control::DynamicControl)

DECLARE_OGN_NODES()

namespace
{
omni::kit::StageUpdatePtr gStageUpdate = nullptr;
omni::kit::StageUpdateNode* gStageUpdateNode = nullptr;
omni::fabric::ISimStageWithHistory* gSimStageWithHistory = nullptr;
omni::fabric::IStageReaderWriter* gStageReaderWriter = nullptr;
omni::fabric::IStageAtTimeInterval* gStageAtTimeInterval = nullptr;
omni::physx::IPhysx* gPhysXInterface = nullptr;
omni::physx::SubscriptionId gStepSubscription;
pxr::UsdStageWeakPtr gStage = nullptr;
omni::fabric::StageReaderWriterId gStageReaderWriterId;
omni::fabric::SimStageWithHistoryId gSimStageWithHistoryId;
omni::fabric::UsdStageId gStageId;
double gSimTime = 0.0;
double gSimTimeMonotonic = 0.0;
double gSystemTime = 0.0;
size_t gPhysicsNumSteps = 0;
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
    gStageReaderWriterId = gStageReaderWriter->get(gStageId);
    gSimStageWithHistoryId = gSimStageWithHistory->get(gStageId);
    omni::fabric::StageReaderWriter stageReaderWriter = omni::fabric::StageReaderWriter(gStageReaderWriterId);

    stageReaderWriter.createPrim(omni::fabric::Path("/__OgnIsaacSimTime__"));

    const omni::graph::core::Type typeTag(omni::graph::core::BaseDataType::eTag);
    const omni::fabric::Token fc_exportToRingbuffer("fc_exportToRingbuffer");
    stageReaderWriter.createAttribute(omni::fabric::Path("/__OgnIsaacSimTime__"), fc_exportToRingbuffer, typeTag);

    const omni::graph::core::Type typeDouble(omni::graph::core::BaseDataType::eDouble, 1, 0);
    *stageReaderWriter.getOrCreateAttributeWr<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("simTime"), typeDouble) = gSimTime;
    *stageReaderWriter.getOrCreateAttributeWr<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("simTimeMonotonic"), typeDouble) =
        gSimTimeMonotonic;
    *stageReaderWriter.getOrCreateAttributeWr<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("systemTime"), typeDouble) = gSystemTime;
}

// void onPause(void* userData)
// {
// }
void onStop(void* userData)
{
    omni::fabric::StageReaderWriter stageReaderWriter = omni::fabric::StageReaderWriter(gStageReaderWriterId);
    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);
    pxr::UsdStageRefPtr usdStage =
        pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(uint32_t(gStageId.id)));
    if (usdStage->GetPrimAtPath(usdPath))
    {
        stageReaderWriter.destroyPrim(path);
    }
    gSimTime = 0;
    gPhysicsNumSteps = 0;
}

void onPhysicsStep(float timeElapsed, void* userData)
{
    omni::fabric::StageReaderWriter stageReaderWriter = omni::fabric::StageReaderWriter(gStageReaderWriterId);
    gSimTime += timeElapsed;
    gSimTimeMonotonic += timeElapsed;
    gPhysicsNumSteps += 1;
    gSystemTime = std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);
    pxr::UsdStageRefPtr usdStage =
        pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(uint32_t(gStageId.id)));

    gStageReaderWriter->prefetchPrim(gStageId, path);
    // Check if attribute exists:

    if (!usdStage->GetPrimAtPath(usdPath))
    {
        // create prim and attributes if they do not exist, this sets them to the current values as well
        onResume(0, nullptr);
        return;
    }

    double* simTime = stageReaderWriter.getAttributeWr<double>(path, omni::fabric::Token("simTime"));
    double* simTimeMonotonic = stageReaderWriter.getAttributeWr<double>(path, omni::fabric::Token("simTimeMonotonic"));
    double* systemTime = stageReaderWriter.getAttributeWr<double>(path, omni::fabric::Token("systemTime"));
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

size_t getPhysicsNumSteps()
{
    return gPhysicsNumSteps;
}

double getSimulationTimeAtTime(const omni::fabric::RationalTime& rtime)
{
    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);

    if (!gStage->GetPrimAtPath(usdPath) || !gSimStageWithHistoryId.id || !gStageId.id)
    {
        return gSimTime;
    }
    else
    {
        CARB_LOG_ERROR("getSimulationTimeAtTime , returning default sim time %d %d %d", !gStage->GetPrimAtPath(usdPath),
                       !gSimStageWithHistoryId.id, !gStageId.id);
    }
    omni::fabric::StageAtTime stageAtTime(gSimStageWithHistoryId, rtime);
    auto simTime =
        stageAtTime.getAttributeRd<double>(omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("simTime"));
    return simTime ? simTime.value() : gSimTime;
}


double getSimulationTimeMonotonicAtTime(const omni::fabric::RationalTime& rtime)
{
    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);

    if (!gStage->GetPrimAtPath(usdPath) || !gSimStageWithHistoryId.id || !gStageId.id)
    {
        return gSimTimeMonotonic;
    }
    else
    {
        CARB_LOG_ERROR("getSimulationTimeMonotonicAtTime, returning default monotonic sim time %d %d %d",
                       !gStage->GetPrimAtPath(usdPath), !gSimStageWithHistoryId.id, !gStageId.id);
    }
    omni::fabric::StageAtTime stageAtTime(gSimStageWithHistoryId, rtime);
    auto simTimeMonotonic = stageAtTime.getAttributeRd<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("simTimeMonotonic"));
    return simTimeMonotonic ? simTimeMonotonic.value() : gSimTimeMonotonic;
}

double getSystemTimeAtTime(const omni::fabric::RationalTime& rtime)
{

    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);

    if (!gStage->GetPrimAtPath(usdPath) || !gSimStageWithHistoryId.id || !gStageId.id)
    {
        return gSystemTime;
    }
    else
    {
        CARB_LOG_ERROR("getSystemTimeAtTime, returning default system time %d %d %d", !gStage->GetPrimAtPath(usdPath),
                       !gSimStageWithHistoryId.id, !gStageId.id);
    }
    omni::fabric::StageAtTime stageAtTime(gSimStageWithHistoryId, rtime);
    auto systemTime = stageAtTime.getAttributeRd<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("systemTime"));
    return systemTime ? systemTime.value() : gSystemTime;
}
// TODO105 Depricate next 3 functions.
double getSimulationTimeAtSwhFrame(const int64_t swhFrame)
{
    return gSimStageWithHistory ? getSimulationTimeAtTime(gSimStageWithHistory->getSimPeriod(gStageId) * swhFrame) :
                                  gSimTime;
}


double getSimulationTimeMonotonicAtSwhFrame(const int64_t swhFrame)
{
    return gSimStageWithHistory ?
               getSimulationTimeMonotonicAtTime(gSimStageWithHistory->getSimPeriod(gStageId) * swhFrame) :
               gSimTimeMonotonic;
}

double getSystemTimeAtSwhFrame(const int64_t swhFrame)
{
    return gSimStageWithHistory ? getSystemTimeAtTime(gSimStageWithHistory->getSimPeriod(gStageId) * swhFrame) :
                                  gSystemTime;
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
    gStageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>()->getStageUpdate();
    gStageReaderWriter = carb::getCachedInterface<omni::fabric::IStageReaderWriter>();
    gPhysXInterface = carb::getCachedInterface<omni::physx::IPhysx>();
    gSimStageWithHistory = carb::getCachedInterface<omni::fabric::ISimStageWithHistory>();
    gStageAtTimeInterval = carb::getCachedInterface<omni::fabric::IStageAtTimeInterval>();
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
    gPhysicsNumSteps = 0;
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
    iface.getPhysicsNumSteps = getPhysicsNumSteps;

    iface.getSimTimeAtSwhFrame = getSimulationTimeAtSwhFrame;
    iface.getSimTimeMonotonicAtSwhFrame = getSimulationTimeMonotonicAtSwhFrame;
    iface.getSystemTimeAtSwhFrame = getSystemTimeAtSwhFrame;

    iface.addHandle = addHandle;
    iface.getHandle = getHandle;
    iface.removeHandle = removeHandle;

    iface.getSimTimeAtTime = getSimulationTimeAtTime;
    iface.getSimTimeMonotonicAtTime = getSimulationTimeMonotonicAtTime;
    iface.getSystemTimeAtTime = getSystemTimeAtTime;
}
