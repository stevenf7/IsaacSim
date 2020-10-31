// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#define CARB_EXPORTS
#include <omni/isaac/dr/DomainRandomizer.h>

#include "DRManager.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/tokens/ITokens.h>

#include <omni/kit/IStageUpdate.h>

#include <inttypes.h> // print 64 bit pointers
#include <random>

#if CARB_PLATFORM_WINDOWS
//#    pragma warning(push)
#    pragma warning(disable : 4244) // = Conversion from double to float / int to float
#    pragma warning(disable : 4267) // conversion from size_t to int
#    pragma warning(disable : 4305) // argument truncation from double to float
#    pragma warning(disable : 4800) // int to bool
#    pragma warning(disable : 4996) // call to std::copy with parameters that may be unsafe
#    define NOMINMAX // Make sure nobody #defines min or max
#endif

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.dr.plugin", "Omni-Kit Domain Randomizer Utilities",
                                                  "NVIDIA", carb::PluginHotReload::eEnabled, "dev" };
CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::dr::DomainRandomizer)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IStageUpdate,
                      carb::tokens::ITokens,
                      carb::datasource::IDataSource,
                      carb::settings::ISettings,
                      carb::filesystem::IFileSystem)

namespace
{
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
carb::tokens::ITokens* g_tokens = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
static pxr::UsdStageWeakPtr g_stage = nullptr;
std::unique_ptr<omni::isaac::dr::DRManager> Manager;
bool manualMode = false;

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    CARB_LOG_INFO("onAttach DR");

    // try and find USD stage from Id
    pxr::UsdStageWeakPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

    if (!stage)
    {
        CARB_LOG_ERROR("Isaac DR could not find USD stage");
        return;
    }

    g_stage = stage;
    g_tokens = carb::getFramework()->acquireInterface<carb::tokens::ITokens>();

    if (!g_tokens)
    {
        CARB_LOG_ERROR("Failed to acquire carb::tokens::ITokens interface");
        return;
    }
    if (Manager)
    {
        Manager->initialize(g_stage, g_tokens);
        Manager->initComponents();
    }
}

void onDetach(void* userData)
{
    CARB_LOG_INFO("onDetach DR");
    if (Manager)
    {
        Manager->deleteAllComponents();
    }
}

bool HasAttribute(const pxr::UsdPrim& prim, const pxr::TfToken& name)
{
    return prim.HasAttribute(name);
}

void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    if (!settings->isPlaying || manualMode)
    {
        return;
    }
    // CARB_LOG_INFO("Tick: %f - %f", currentTime, elapsedSecs);
    if (Manager)
    {
        Manager->tick(elapsedSecs);
    }
}

void onPrimAdd(const pxr::SdfPath& primPath, void* userData)
{
    if (Manager && g_stage)
    {
        Manager->onComponentAdd(g_stage->GetPrimAtPath(primPath));
    }
}

void onPrimOrPropertyChange(const pxr::SdfPath& primOrPropertyPath, void* userData)
{
    if (Manager && g_stage)
    {
        Manager->onComponentChange(g_stage->GetPrimAtPath(primOrPropertyPath));
    }
}

void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    if (Manager && g_stage)
    {
        Manager->onComponentRemove(primPath);
    }
}

} // anonymous namespace

using namespace omni::isaac::dr;

CARB_EXPORT void carbOnPluginStartup()
{
    carb::Framework* framework = carb::getFramework();

    g_stageUpdate = framework->acquireInterface<omni::kit::IStageUpdate>();

    Manager = std::make_unique<omni::isaac::dr::DRManager>();

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "Domain Randomizer";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    desc.onPrimAdd = onPrimAdd;
    desc.onPrimOrPropertyChange = onPrimOrPropertyChange;
    desc.onPrimRemove = onPrimRemove;
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
}

CARB_EXPORT void carbOnPluginShutdown()
{
    if (Manager)
    {
        Manager.reset();
    }
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
}

void randomizeOnce()
{
    if (Manager && manualMode)
    {
        Manager->tickManual();
    }
}

void toggleManualMode()
{
    manualMode = !manualMode;
}

void fillInterface(omni::isaac::dr::DomainRandomizer& iface)
{
    iface.randomizeOnce = randomizeOnce;
    iface.toggleManualMode = toggleManualMode;
}
