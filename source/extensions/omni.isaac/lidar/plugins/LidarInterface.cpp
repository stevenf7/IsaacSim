// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include <omni/kit/IStageUpdate.h>
#include <omni/isaac/lidar/LidarInterface.h>

#include "Lidar.h"
#include <LidarSchema/lidar.h>

#include <carb/physx/physx.h>

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/fastcache/FastCache.h>

#include <map>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.lidar.plugin", "Isaac Lidar", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::lidar::LidarInterface)
CARB_PLUGIN_IMPL_DEPS(carb::physics::PhysX,
                      omni::kit::IStageUpdate,
                      carb::fastcache::FastCache,
                      omni::isaac::dynamic_control::DynamicControl)

using namespace physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace lidar
{
// private stuff
namespace
{


// Eek global state
omni::kit::IStageUpdate* g_su = nullptr;
omni::kit::StageUpdateNode* g_suNode = nullptr;

carb::fastcache::FastCache* g_FastCache = nullptr;

carb::physics::PhysX* g_physx = nullptr;

UsdStageRefPtr g_stage = nullptr;
float g_metersPerUnit = 1.0f;

std::map<LidarHandle, Lidar> g_lidars;
std::map<SdfPath, LidarHandle> g_lidarMap;

LidarHandle g_nextLidarHandle = 0;

} // end of anonymous namespace


void removeLidar(const SdfPath& path)
{
    if (g_lidarMap.count(path) == 0)
        return;

    LidarHandle handle = g_lidarMap[path];

    g_lidars.erase(handle);
    g_lidarMap.erase(path);
}


void addLidar(const LidarSchemaLidar& prim)
{
    SdfPath path = prim.GetPath();

    // Already here, re-initialize
    if (g_lidarMap.count(path))
    {
        g_lidars[g_lidarMap[path]].init(LidarSchemaLidar(prim));
        return;
    }

    LidarHandle handle = ++g_nextLidarHandle;
    g_lidarMap[path] = handle;
    g_lidars[handle] = Lidar(prim);
}


struct UsdNoticeListener : public pxr::TfWeakBase
{
    UsdNoticeListener() = default;

    void Handle(const class pxr::UsdNotice::ObjectsChanged& objectsChanged);
    void RemovePrim(const SdfPath& primPath);
};


void UsdNoticeListener::RemovePrim(const SdfPath& primPath)
{
    size_t size = g_FastCache->getPrimRangePathCount(primPath);
    std::vector<SdfPath> pathRange(size);
    g_FastCache->getPrimRangePaths(primPath, pathRange.data(), size);

    // cleanup from physics plugins
    for (const SdfPath& path : pathRange)
    {
        // CARB_LOG_WARN("REMOVE %s", path.GetText());

        if (g_lidarMap.count(path))
            removeLidar(path);
    }
}

void UsdNoticeListener::Handle(const class pxr::UsdNotice::ObjectsChanged& objectsChanged)
{

    // This is an old callback, ignore it
    if (g_stage != objectsChanged.GetStage())
    {
        return;
    }

    for (auto& path : objectsChanged.GetResyncedPaths())
    {
        if (path.IsAbsoluteRootOrPrimPath())
        {
            // CARB_LOG_WARN("ResyncedPaths: %s", path.GetText());
            auto primPath =
                g_stage->GetPseudoRoot().GetPath() == path ? g_stage->GetPseudoRoot().GetPath() : path.GetPrimPath();

            // If prim is removed, remove it and its descendants from selection.
            UsdPrim prim = g_stage->GetPrimAtPath(primPath);

            // CARB_LOG_WARN("Prim valid %d", prim.IsValid());
            if (prim.IsValid() == false) // remove prim
            {
                RemovePrim(primPath);
            }
            else // resync prim
            {
                UsdPrim prim = g_stage->GetPrimAtPath(primPath);

                if (prim.IsA<LidarSchemaLidar>())
                {
                    // UsdGeomPrimvarsAPI blah(prim);
                    std::vector<UsdAttribute> attributes = prim.GetAttributes();
                    std::vector<UsdAttribute> authored = prim.GetAuthoredAttributes();

                    addLidar(LidarSchemaLidar(prim));
                }
            }
        }
        else if (path.IsPropertyPath())
        {
            const SdfPath& primPath = path.GetParentPath();
            // CARB_LOG_WARN("Property Path parent: %s", primPath.GetText());
            auto prim = g_stage->GetPrimAtPath(primPath);
        }
    }

    for (auto& path : objectsChanged.GetChangedInfoOnlyPaths())
    {
        auto primPath = g_stage->GetPseudoRoot().GetPath() == path ? path : path.GetPrimPath();

        // CARB_LOG_WARN("GetChangedInfoOnlyPaths %s", primPath.GetText());

        UsdPrim prim = g_stage->GetPrimAtPath(primPath);

        if (prim.IsA<LidarSchemaLidar>())
        {
            g_lidars[g_lidarMap[primPath]].init(LidarSchemaLidar(prim));
        }
    }
}


UsdNoticeListener* g_usdNoticeListener = nullptr;
pxr::TfNotice::Key g_usdNoticeListenerKey;


LidarHandle CARB_ABI getLidarHandle(const char* usdPath)
{
    if (!usdPath)
        return kLidarInvalidHandle;

    SdfPath path = pxr::SdfPath(usdPath);

    if (g_lidarMap.count(path) == 0)
        return kLidarInvalidHandle;

    return g_lidarMap[path];
}


float CARB_ABI getHorizontalFov(LidarHandle handle)
{
    return g_lidars[handle].getHorizontalFov();
}


float CARB_ABI getVerticalFov(LidarHandle handle)
{
    return g_lidars[handle].getVerticalFov();
}


float CARB_ABI getRotationRate(LidarHandle handle)
{
    return g_lidars[handle].getRotationRate();
}


float CARB_ABI getHorizontalResolution(LidarHandle handle)
{
    return g_lidars[handle].getHorizontalResolution();
}


float CARB_ABI getVerticalResolution(LidarHandle handle)
{
    return g_lidars[handle].getVerticalResolution();
}


float CARB_ABI getMinRange(LidarHandle handle)
{
    return g_lidars[handle].getMinRange();
}


float CARB_ABI getMaxRange(LidarHandle handle)
{
    return g_lidars[handle].getMaxRange();
}


bool CARB_ABI getHighLod(LidarHandle handle)
{
    return g_lidars[handle].getHighLod();
}


bool CARB_ABI getDrawLidarPoints(LidarHandle handle)
{
    return g_lidars[handle].getDrawLidarPoints();
}


void CARB_ABI setHorizontalFov(LidarHandle handle, const float& horizontalFov)
{
    UsdPrim prim = g_stage->GetPrimAtPath(g_lidars[handle].getPath());

    if (prim.IsA<LidarSchemaLidar>())
    {
        LidarSchemaLidar lidarPrim(prim);

        lidarPrim.CreateHorizontalFovAttr(VtValue(horizontalFov));
    }
}


void CARB_ABI setVerticalFov(LidarHandle handle, const float& verticalFov)
{
    UsdPrim prim = g_stage->GetPrimAtPath(g_lidars[handle].getPath());

    if (prim.IsA<LidarSchemaLidar>())
    {
        LidarSchemaLidar lidarPrim(prim);

        lidarPrim.CreateVerticalFovAttr(VtValue(verticalFov));
    }
}


void CARB_ABI setRotationRate(LidarHandle handle, const float& rotationRate)
{
    UsdPrim prim = g_stage->GetPrimAtPath(g_lidars[handle].getPath());

    if (prim.IsA<LidarSchemaLidar>())
    {
        LidarSchemaLidar lidarPrim(prim);

        lidarPrim.CreateRotationRateAttr(VtValue(rotationRate));
    }
}


void CARB_ABI setHorizontalResolution(LidarHandle handle, const float& horizontalResolution)
{
    UsdPrim prim = g_stage->GetPrimAtPath(g_lidars[handle].getPath());

    if (prim.IsA<LidarSchemaLidar>())
    {
        LidarSchemaLidar lidarPrim(prim);

        lidarPrim.CreateHorizontalResolutionAttr(VtValue(horizontalResolution));
    }
}


void CARB_ABI setVerticalResolution(LidarHandle handle, const float& verticalResolution)
{
    UsdPrim prim = g_stage->GetPrimAtPath(g_lidars[handle].getPath());

    if (prim.IsA<LidarSchemaLidar>())
    {
        LidarSchemaLidar lidarPrim(prim);

        lidarPrim.CreateVerticalResolutionAttr(VtValue(verticalResolution));
    }
}


void CARB_ABI setMinRange(LidarHandle handle, const float& minRange)
{
    UsdPrim prim = g_stage->GetPrimAtPath(g_lidars[handle].getPath());

    if (prim.IsA<LidarSchemaLidar>())
    {
        LidarSchemaLidar lidarPrim(prim);

        lidarPrim.CreateMinRangeAttr(VtValue(minRange));
    }
}


void CARB_ABI setMaxRange(LidarHandle handle, const float& maxRange)
{
    UsdPrim prim = g_stage->GetPrimAtPath(g_lidars[handle].getPath());

    if (prim.IsA<LidarSchemaLidar>())
    {
        LidarSchemaLidar lidarPrim(prim);

        lidarPrim.CreateMaxRangeAttr(VtValue(maxRange));
    }
}


void CARB_ABI setHighLod(LidarHandle handle, const bool& highLod)
{
    UsdPrim prim = g_stage->GetPrimAtPath(g_lidars[handle].getPath());
    if (prim.IsA<LidarSchemaLidar>())
    {
        LidarSchemaLidar lidarPrim(prim);
        lidarPrim.CreateHighLodAttr(VtValue(highLod));
    }
}


void CARB_ABI setDrawLidarPoints(LidarHandle handle, const bool& drawLidarPoints)
{
    UsdPrim prim = g_stage->GetPrimAtPath(g_lidars[handle].getPath());
    if (prim.IsA<LidarSchemaLidar>())
    {
        LidarSchemaLidar lidarPrim(prim);
        lidarPrim.CreateDrawLidarPointsAttr(VtValue(drawLidarPoints));
    }
}


int CARB_ABI getNumCols(LidarHandle handle)
{
    return g_lidars[handle].getNumCols();
}

int CARB_ABI getNumRows(LidarHandle handle)
{
    return g_lidars[handle].getNumRows();
}

int CARB_ABI getNumColsTicked(LidarHandle handle)
{
    return g_lidars[handle].getLastNumColsTicked();
}

uint16_t* CARB_ABI getDepthData(LidarHandle handle)
{
    return g_lidars[handle].getLastDepthData().data();
}

uint8_t* CARB_ABI getIntensityData(LidarHandle handle)
{
    return g_lidars[handle].getLastIntensityData().data();
}

float* CARB_ABI getZenithData(LidarHandle handle)
{
    return g_lidars[handle].getLastZenithData().data();
}

float* CARB_ABI getAzimuthData(LidarHandle handle)
{
    return g_lidars[handle].getLastAzimuthData().data();
}


// stage update
void SuAttach(long stageId, double metersPerUnit, void* data)
{
    UsdStageRefPtr stage = UsdUtilsStageCache::Get().Find(UsdStageCache::Id::FromLongInt(stageId));
    if (!stage)
    {
        CARB_LOG_ERROR("PhysX could not find USD stage");
        return;
    }

    g_stage = stage;
    Lidar::stage = stage;

    g_metersPerUnit = float(metersPerUnit);
    Lidar::metersPerUnit = float(metersPerUnit);


    UsdPrimRange range = g_stage->Traverse();

    for (auto iter = range.begin(); iter != range.end(); iter++)
    {

        const UsdPrim& prim = *iter;

        if (prim.IsA<LidarSchemaLidar>())
        {
            SdfPath path = prim.GetPath();
            // printf("%s\n", path.GetText());

            addLidar(LidarSchemaLidar(prim));
        }
    }

    // printf("++ LidarInterface: Stage Attach: stageId %ld\n", stageId);
}

void SuDetach(void* data)
{
    g_stage = nullptr;
    Lidar::stage = nullptr;

    for (const auto& path : g_lidarMap)
    {
        removeLidar(path.first);
    }

    // printf("++ LidarInterface: Stage Detach\n");
}

void SuPause(void* data)
{
    // printf("++ LidarInterface: Stage Pause\n");
}

void SuResume(float currentTime, void* data)
{
    // printf("++ LidarInterface: Stage Resume\n");
}

void SuUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{

    if (!settings->isPlaying)
    {
        return;
    }
    // printf("++ LidarInterface: Stage Update %f\n", elapsedSecs);

    for (auto it = g_lidars.begin(); it != g_lidars.end(); it++)
    {
        it->second.update(elapsedSecs);
    }

    // printf("++ LidarInterface: Stage Update %f\n", elapsedSecs);
}


}
}
}

CARB_EXPORT void carbOnPluginStartup()
{
    using namespace omni::isaac::lidar;

    carb::Framework* framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
        return;
    }

    g_su = framework->acquireInterface<omni::kit::IStageUpdate>();
    if (!g_su)
    {
        CARB_LOG_ERROR("*** Failed to acquire stage update interface\n");
        return;
    }

    g_FastCache = framework->acquireInterface<carb::fastcache::FastCache>();
    if (!g_FastCache)
    {
        CARB_LOG_ERROR("*** Failed to acquire FastCache interface\n");
        return;
    }


    omni::isaac::lidar::g_usdNoticeListener = new omni::isaac::lidar::UsdNoticeListener();
    omni::isaac::lidar::g_usdNoticeListenerKey = pxr::TfNotice::Register(
        pxr::TfCreateWeakPtr(omni::isaac::lidar::g_usdNoticeListener), &omni::isaac::lidar::UsdNoticeListener::Handle);


    g_physx = framework->acquireInterface<carb::physics::PhysX>();
    if (!g_physx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }
    Lidar::physx = g_physx;

    omni::kit::StageUpdateNodeDesc suDesc = { 0 };
    suDesc.displayName = "Lidar Interface";
    suDesc.onAttach = SuAttach;
    suDesc.onDetach = SuDetach;
    suDesc.onUpdate = SuUpdate;
    suDesc.onResume = SuResume;
    suDesc.onPause = SuPause;

    g_suNode = g_su->createStageUpdateNode(suDesc);
    if (!g_suNode)
    {
        CARB_LOG_ERROR("*** Failed to create stage update node\n");
        return;
    }
}


CARB_EXPORT void carbOnPluginShutdown()
{
    using namespace omni::isaac::lidar;

    if (g_suNode)
    {
        g_su->destroyStageUpdateNode(g_suNode);
        g_suNode = nullptr;
    }

    g_physx = nullptr;
    Lidar::physx = nullptr;
    g_stage = nullptr;
    Lidar::stage = nullptr;

    g_FastCache = nullptr;

    g_lidars.clear();
    g_lidarMap.clear();

    pxr::TfNotice::Revoke(omni::isaac::lidar::g_usdNoticeListenerKey);
    delete omni::isaac::lidar::g_usdNoticeListener;
    omni::isaac::lidar::g_usdNoticeListener = nullptr;
}


void fillInterface(omni::isaac::lidar::LidarInterface& iface)
{
    using namespace omni::isaac::lidar;

    memset(&iface, 0, sizeof(iface));

    iface.getLidarHandle = getLidarHandle;
    iface.getDepthData = getDepthData;

    iface.getHorizontalFov = getHorizontalFov;
    iface.getVerticalFov = getVerticalFov;
    iface.getRotationRate = getRotationRate;
    iface.getHorizontalResolution = getHorizontalResolution;
    iface.getVerticalResolution = getVerticalResolution;
    iface.getMinRange = getMinRange;
    iface.getMaxRange = getMaxRange;
    iface.getHighLod = getHighLod;
    iface.getDrawLidarPoints = getDrawLidarPoints;

    iface.setHorizontalFov = setHorizontalFov;
    iface.setVerticalFov = setVerticalFov;
    iface.setRotationRate = setRotationRate;
    iface.setHorizontalResolution = setHorizontalResolution;
    iface.setVerticalResolution = setVerticalResolution;
    iface.setMinRange = setMinRange;
    iface.setMaxRange = setMaxRange;
    iface.setHighLod = setHighLod;
    iface.setDrawLidarPoints = setDrawLidarPoints;

    iface.getNumCols = getNumCols;
    iface.getNumRows = getNumRows;
    iface.getNumColsTicked = getNumColsTicked;

    iface.getDepthData = getDepthData;
    iface.getIntensityData = getIntensityData;
    iface.getZenithData = getZenithData;
    iface.getAzimuthData = getAzimuthData;
}
