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
#include <carb/filesystem/IFileSystem.h>
#include <carb/imaging/IImaging.h>

#include <isaacsim/core/nodes/ICoreNodes.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/fabric/IToken.h>
#include <omni/fabric/SimStageWithHistory.h>
#include <omni/graph/core/NodeTypeRegistrar.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/kit/IMinimal.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>


const struct carb::PluginImplDesc g_kPluginDesc = { "isaacsim.core.nodes", "Isaac Sim Core OmniGraph Nodes", "NVIDIA",
                                                    carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(g_kPluginDesc, isaacsim::core::nodes::CoreNodes)
CARB_PLUGIN_IMPL_DEPS(omni::graph::core::IGraphRegistry,
                      omni::kit::IStageUpdate,
                      omni::fabric::IToken,
                      omni::physx::IPhysx,
                      omni::fabric::IStageReaderWriter,
                      omni::fabric::ISimStageWithHistory,
                      omni::fabric::IStageAtTimeInterval)

DECLARE_OGN_NODES()

namespace
{
omni::kit::StageUpdatePtr g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
omni::fabric::ISimStageWithHistory* g_simStageWithHistory = nullptr;
omni::fabric::IStageReaderWriter* g_stageReaderWriter = nullptr;
omni::fabric::IStageAtTimeInterval* g_stageAtTimeInterval = nullptr;
omni::physx::IPhysx* g_physXInterface = nullptr;
omni::physx::SubscriptionId g_stepSubscription;
pxr::UsdStageWeakPtr g_stage = nullptr;
omni::fabric::StageReaderWriterId g_stageReaderWriterId;
omni::fabric::SimStageWithHistoryId g_simStageWithHistoryId;
omni::fabric::UsdStageId g_stageId;
double g_simTime = 0.0;
double g_simTimeMonotonic = 0.0;
double g_systemTime = 0.0;
size_t g_physicsNumSteps = 0;
std::map<uint64_t, void*> g_handleMap;
std::mutex g_handleMutex;
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

    g_stage = stage;
    g_stageId.id = stageId;
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
    g_stageReaderWriterId = g_stageReaderWriter->get(g_stageId);
    g_simStageWithHistoryId = g_simStageWithHistory->get(g_stageId);
    omni::fabric::StageReaderWriter stageReaderWriter = omni::fabric::StageReaderWriter(g_stageReaderWriterId);

    stageReaderWriter.createPrim(omni::fabric::Path("/__OgnIsaacSimTime__"));

    const omni::graph::core::Type typeTag(omni::graph::core::BaseDataType::eTag);
    const omni::fabric::Token fcExportToRingbuffer("fcExportToRingbuffer");
    stageReaderWriter.createAttribute(omni::fabric::Path("/__OgnIsaacSimTime__"), fcExportToRingbuffer, typeTag);

    const omni::graph::core::Type typeDouble(omni::graph::core::BaseDataType::eDouble, 1, 0);
    *stageReaderWriter.getOrCreateAttributeWr<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("simTime"), typeDouble) = g_simTime;
    *stageReaderWriter.getOrCreateAttributeWr<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("simTimeMonotonic"), typeDouble) =
        g_simTimeMonotonic;
    *stageReaderWriter.getOrCreateAttributeWr<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("systemTime"), typeDouble) = g_systemTime;
}

// void onPause(void* userData)
// {
// }
void onStop(void* userData)
{
    omni::fabric::StageReaderWriter stageReaderWriter = omni::fabric::StageReaderWriter(g_stageReaderWriterId);
    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);
    pxr::UsdStageRefPtr usdStage =
        pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(uint32_t(g_stageId.id)));
    if (usdStage->GetPrimAtPath(usdPath))
    {
        stageReaderWriter.destroyPrim(path);
    }
    g_simTime = 0;
    g_physicsNumSteps = 0;
}

void onPhysicsStep(float timeElapsed, void* userData)
{
    CARB_PROFILE_ZONE(0, "isaacsim.code.nodes.plugin::onPhysicsStep");
    omni::fabric::StageReaderWriter stageReaderWriter = omni::fabric::StageReaderWriter(g_stageReaderWriterId);
    g_simTime += timeElapsed;
    g_simTimeMonotonic += timeElapsed;
    g_physicsNumSteps += 1;
    g_systemTime = std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);
    pxr::UsdStageRefPtr usdStage =
        pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(uint32_t(g_stageId.id)));

    g_stageReaderWriter->prefetchPrim(g_stageId, path);
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
        *simTime = g_simTime;
        *simTimeMonotonic = g_simTimeMonotonic;
        *systemTime = g_systemTime;
    }
    else
    {
        CARB_LOG_ERROR("Could not read or create sim time attributes");
    }
}


double getSimulationTime()
{
    return g_simTime;
}


double getSimulationTimeMonotonic()
{
    return g_simTimeMonotonic;
}

double getSystemTime()
{
    return g_systemTime;
}

size_t getPhysicsNumSteps()
{
    return g_physicsNumSteps;
}

double getSimulationTimeAtTime(const omni::fabric::RationalTime& rtime)
{
    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);

    if (!g_stage->GetPrimAtPath(usdPath) || !g_simStageWithHistoryId.id || !g_stageId.id)
    {
        return g_simTime;
    }
    else
    {
        CARB_LOG_ERROR("getSimulationTimeAtTime , returning default sim time %d %d %d",
                       !g_stage->GetPrimAtPath(usdPath), !g_simStageWithHistoryId.id, !g_stageId.id);
    }
    omni::fabric::StageAtTime stageAtTime(g_simStageWithHistoryId, rtime);
    auto simTime =
        stageAtTime.getAttributeRd<double>(omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("simTime"));
    return simTime ? simTime.value() : g_simTime;
}


double getSimulationTimeMonotonicAtTime(const omni::fabric::RationalTime& rtime)
{
    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);

    if (!g_stage->GetPrimAtPath(usdPath) || !g_simStageWithHistoryId.id || !g_stageId.id)
    {
        return g_simTimeMonotonic;
    }
    else
    {
        CARB_LOG_ERROR("getSimulationTimeMonotonicAtTime, returning default monotonic sim time %d %d %d",
                       !g_stage->GetPrimAtPath(usdPath), !g_simStageWithHistoryId.id, !g_stageId.id);
    }
    omni::fabric::StageAtTime stageAtTime(g_simStageWithHistoryId, rtime);
    auto simTimeMonotonic = stageAtTime.getAttributeRd<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("simTimeMonotonic"));
    return simTimeMonotonic ? simTimeMonotonic.value() : g_simTimeMonotonic;
}

double getSystemTimeAtTime(const omni::fabric::RationalTime& rtime)
{

    auto path = omni::fabric::Path("/__OgnIsaacSimTime__");
    pxr::SdfPath usdPath = omni::fabric::toSdfPath(path);

    if (!g_stage->GetPrimAtPath(usdPath) || !g_simStageWithHistoryId.id || !g_stageId.id)
    {
        return g_systemTime;
    }
    else
    {
        CARB_LOG_ERROR("getSystemTimeAtTime, returning default system time %d %d %d", !g_stage->GetPrimAtPath(usdPath),
                       !g_simStageWithHistoryId.id, !g_stageId.id);
    }
    omni::fabric::StageAtTime stageAtTime(g_simStageWithHistoryId, rtime);
    auto systemTime = stageAtTime.getAttributeRd<double>(
        omni::fabric::Path("/__OgnIsaacSimTime__"), omni::fabric::Token("systemTime"));
    return systemTime ? systemTime.value() : g_systemTime;
}
// TODO105 Depricate next 3 functions.
double getSimulationTimeAtSwhFrame(const int64_t swhFrame)
{
    return g_simStageWithHistory ?
               getSimulationTimeAtTime(g_simStageWithHistory->getSimPeriod(g_stageId).asRationalTime() * swhFrame) :
               g_simTime;
}


double getSimulationTimeMonotonicAtSwhFrame(const int64_t swhFrame)
{
    return g_simStageWithHistory ? getSimulationTimeMonotonicAtTime(
                                       g_simStageWithHistory->getSimPeriod(g_stageId).asRationalTime() * swhFrame) :
                                   g_simTimeMonotonic;
}

double getSystemTimeAtSwhFrame(const int64_t swhFrame)
{
    return g_simStageWithHistory ?
               getSystemTimeAtTime(g_simStageWithHistory->getSimPeriod(g_stageId).asRationalTime() * swhFrame) :
               g_systemTime;
}

uint64_t addHandle(void* handle)
{
    uint64_t handleId = reinterpret_cast<uint64_t>(handle);
    std::lock_guard<std::mutex> guard(g_handleMutex);
    g_handleMap[handleId] = handle;
    return handleId;
}

void* getHandle(const uint64_t handleId)
{
    std::lock_guard<std::mutex> guard(g_handleMutex);
    auto it = g_handleMap.find(handleId);
    if (it == g_handleMap.end())
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
    std::lock_guard<std::mutex> guard(g_handleMutex);
    return g_handleMap.erase(handleId);
}

CARB_EXPORT void carbOnPluginStartup()
{
    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>()->getStageUpdate();
    g_stageReaderWriter = carb::getCachedInterface<omni::fabric::IStageReaderWriter>();
    g_physXInterface = carb::getCachedInterface<omni::physx::IPhysx>();
    g_simStageWithHistory = carb::getCachedInterface<omni::fabric::ISimStageWithHistory>();
    g_stageAtTimeInterval = carb::getCachedInterface<omni::fabric::IStageAtTimeInterval>();
    omni::kit::StageUpdateNodeDesc desc = { nullptr };
    desc.displayName = "Isaac Core Nodes";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    // desc.onUpdate = onUpdate;
    desc.onResume = onResume;
    // desc.onPause = onPause;
    desc.onStop = onStop;
    desc.order = 20; // should run after physics
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);

    g_stepSubscription = g_physXInterface->subscribePhysicsOnStepEvents(false, 0, onPhysicsStep, nullptr);


    // This increases forever until we stop sim.
    g_simTimeMonotonic = 0.0;
    g_systemTime = std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
    g_physicsNumSteps = 0;
    INITIALIZE_OGN_NODES()
}

CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()

    g_physXInterface->unsubscribePhysicsOnStepEvents(g_stepSubscription);
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
}

// carbonite interface for this plugin (may contain multiple compute nodes)
void fillInterface(isaacsim::core::nodes::CoreNodes& iface)
{

    using namespace isaacsim::core::nodes;

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
