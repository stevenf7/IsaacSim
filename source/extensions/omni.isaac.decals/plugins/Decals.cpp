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


// Disable "unsafe/insecure" warning for sprintf
#if CARB_PLATFORM_WINDOWS
#    pragma warning(disable : 4996) // Disable "unsafe/insecure" warning
#endif


#include "Manager.h"

#include <carb/PluginUtils.h>
#include <carb/dictionary/IDictionary.h>
#include <carb/input/IInput.h>

#include <omni/isaac/decals/Decals.h>
#include <omni/kit/IEditor.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/usd/UsdContext.h>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.decals.Decals.plugin", "OV Kit Decal Manager", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };
CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::decals::Decals)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IEditor, omni::kit::IStageUpdate, carb::input::IInput, carb::dictionary::IDictionary)


namespace omni
{
extern int runConvexPolygonIntersectTests();

namespace isaac
{
namespace decals
{

extern void testClipping();

static Manager* gDecals = nullptr;
static kit::IStageUpdate* gStageUpdate = nullptr;
static kit::StageUpdateNode* gStageUpdateNode = nullptr;

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    CARB_UNUSED(metersPerUnit);

    Manager& decals = *reinterpret_cast<Manager*>(userData);

    pxr::UsdStageWeakPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!stage)
    {
        CARB_LOG_ERROR("omni::isaac::decals::Decals could not find USD stage");
        decals.term();
        return;
    }

    decals.init(stage);
}

static void onDetach(void* userData)
{
    Manager& decals = *reinterpret_cast<Manager*>(userData);

    decals.term();
}

static void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    reinterpret_cast<Manager*>(userData)->onPrimRemove(primPath);
}

static void onRaycast(const float* orig, const float* dir, bool input, void* userData)
{
    reinterpret_cast<Manager*>(userData)->onRaycast(orig, dir, input);
}


// Interface

static void setEnabled(bool enabled)
{
    carb::Framework* framework = carb::getFramework();

    if (enabled && gDecals == nullptr)
    {
        omni::kit::IEditor* editor = framework->acquireInterface<omni::kit::IEditor>();

        pxr::UsdStageWeakPtr stage = pxr::UsdUtilsStageCache::Get().Find(
            pxr::UsdStageCache::Id::FromLongInt(omni::usd::UsdContext::getContext()->getStageId()));

        // Create decal manager
        gDecals = new Manager;
        gDecals->init(stage);
        gDecals->setPenColor(1.0f, 0.0f, 0.0f);
        gDecals->setPenWidth(5.0f);
        gDecals->setPenThreshold(10.0f);

        // Create stage update node for stage attach/detach events
        if (gStageUpdate == nullptr)
        {
            gStageUpdate = framework->acquireInterface<omni::kit::IStageUpdate>();
            if (gStageUpdate != nullptr)
            {
                omni::kit::StageUpdateNodeDesc desc = { 0 };
                desc.displayName = "Decals";
                desc.userData = gDecals;
                desc.onAttach = onAttach;
                desc.onDetach = onDetach;
                desc.onPrimRemove = onPrimRemove;
                desc.onRaycast = onRaycast; // Only using this for the "manip" modifier (shift key)!

                gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);
                if (gStageUpdateNode == nullptr)
                {
                    framework->releaseInterface(gStageUpdate);
                    gStageUpdate = nullptr;
                }
            }
        }
    }
    else if (!enabled && gDecals != nullptr)
    {
        if (gStageUpdate != nullptr)
        {
            if (gStageUpdateNode != nullptr)
            {
                gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
                gStageUpdateNode = nullptr;
            }
            framework->releaseInterface(gStageUpdate);
            gStageUpdate = nullptr;
        }

        delete gDecals;
        gDecals = nullptr;
    }
}

static void setPickingEnabled(bool pickingEnabled)
{
    if (gDecals != nullptr)
        gDecals->setPickingEnabled(pickingEnabled);
}

static void setPenColor(float r, float g, float b)
{
    if (gDecals != nullptr)
        gDecals->setPenColor(r, g, b);
}

static void setPenWidth(float width)
{
    if (gDecals != nullptr)
        gDecals->setPenWidth(width);
}

static void setPenOffset(float offset)
{
    if (gDecals != nullptr)
        gDecals->setPenOffset(offset);
}

static void setPenThreshold(float threshold)
{
    if (gDecals != nullptr)
        gDecals->setPenThreshold(threshold);
}

static void setPenSurface(const char* primPath)
{
    if (gDecals != nullptr)
        gDecals->setPenSurface(primPath);
}

static void setPenPosition(const carb::Float3& worldPosition)
{
    if (gDecals != nullptr)
        gDecals->setPenPosition(worldPosition);
}

static void setPenDown(bool penDown)
{
    if (gDecals != nullptr)
        gDecals->setPenDown(penDown);
}

static bool eraseSurface(const char* primPath)
{
    if (gDecals != nullptr)
        return gDecals->eraseSurface(primPath);

    return false;
}

static void eraseAllSurfaces()
{
    if (gDecals != nullptr)
        gDecals->eraseAllSurfaces();
}

static void runTests()
{
    runConvexPolygonIntersectTests();
    testClipping();
}

CARB_EXPORT void carbOnPluginStartup()
{
}

CARB_EXPORT void carbOnPluginShutdown()
{
    setEnabled(false);
}

}
}
}


using namespace omni::isaac::decals;

void fillInterface(Decals& iface)
{
    // clang-format off
    iface =
    {
        setEnabled,
        setPickingEnabled,
        setPenColor,
        setPenWidth,
        setPenOffset,
        setPenThreshold,
        setPenSurface,
        setPenPosition,
        setPenDown,
        eraseSurface,
        eraseAllSurfaces,
        runTests,
    };
    // clang-format on
}
