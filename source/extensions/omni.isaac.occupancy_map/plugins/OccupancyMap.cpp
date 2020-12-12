// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
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
// clang-format on

#include <omni/isaac/occupancy_map/OccupancyMap.h>


#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <omni/physx/IPhysx.h>

#include <PxActor.h>
#include <PxArticulationJointReducedCoordinate.h>
#include <PxArticulationLink.h>
#include <PxArticulationReducedCoordinate.h>
#include <PxPhysicsAPI.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <extensions/PxSceneQueryExt.h>

#include <usdPhysics/scene.h>

#include <omni/kit/IStageUpdate.h>
#include <omni/renderer/IDebugDraw.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

#include <octomap/octomap.h>
#include <octomap/math/Utils.h>

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
std::unique_ptr<octomap::OcTree> gTree;
carb::Float3 inputOrigin = { 0, 0, 0 };
carb::Float2 inputMinPoint = { -100, -100 };
carb::Float2 inputMaxPoint = { 100, 100 };
}

bool raycastClosest(const ::physx::PxVec3& pos,
                    const ::physx::PxVec3& dir,
                    const float distance,
                    const ::physx::PxHitFlags& hitFlags,
                    ::physx::PxRaycastHit& hit,
                    ::physx::PxScene* physxScene)
{


    // ::physx::PxRaycastHit hit;


    const bool ret = ::physx::PxSceneQueryExt::raycastSingle(*physxScene, pos, dir, distance, hitFlags, hit);
    // if (ret)
    // {
    //     outHit.distance = hit.distance;
    //     outHit.normal = (const Float3&)hit.normal;
    //     outHit.position = (const Float3&)hit.position;
    //     outHit.faceIndex = hit.faceIndex;
    //     const InternalHandle shapeIndex = (InternalHandle)hit.shape->userData;
    //     const InternalHandle bodyIndex = (InternalHandle)hit.actor->userData;
    //     outHit.collision = shapeIndex < gInternalScene->getRecords().size() ?
    //                            gInternalScene->getRecords()[shapeIndex].mPrim.GetPath().GetText() :
    //                            nullptr;
    //     outHit.rigidBody = bodyIndex < gInternalScene->getRecords().size() ?
    //                            gInternalScene->getRecords()[bodyIndex].mPrim.GetPath().GetText() :
    //                            nullptr;
    // }
    return ret;
}

void scan(carb::Float3 inputOrigin,
          carb::Float2 minPoint,
          carb::Float2 maxPoint,
          ::physx::PxScene* physxScenePtr,
          float rayResolution,
          float minSearchDistance,
          float occupancyThreshold,
          size_t maxRays)
{
    if (!physxScenePtr)
    {
        return;
    }


    std::vector<::physx::PxVec3> startList;
    startList.push_back(::physx::PxVec3(inputOrigin.x, inputOrigin.y, inputOrigin.z));
    size_t count = 0;
    std::vector<::physx::PxVec3> unitDirs;
    float maxDepth = 1e8;
    ::physx::PxHitFlags hitFlags = ::physx::PxHitFlag::eDEFAULT | ::physx::PxHitFlag::eMESH_BOTH_SIDES;
    for (float degree = 0; degree < 360; degree += rayResolution)
    {
        ::physx::PxQuat rot = ::physx::PxQuat(degree * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        unitDirs.push_back(rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized());
    }

    while (startList.size() > 0 && count < maxRays)
    {
        if (count % 10000 == 0)
        {
            printf("Processing occupancy map: points left %zu, points processed: %zu\n", startList.size(), count);
        }
        ::physx::PxVec3 origin = startList.back();
        startList.pop_back();
        count++;
        // Skip this point if it's outside of the min/max range
        // if (origin.x < minPoint.x || origin.y < minPoint.y || origin.z < minPoint.z)
        // {
        //     continue;
        // }
        // if (origin.x > maxPoint.x || origin.y > maxPoint.y || origin.z > maxPoint.z)
        // {
        //     continue;
        // }
        for (auto& unitDir : unitDirs)
        {
            ::physx::PxRaycastHit raycastHit;

            if (raycastClosest(origin, unitDir, maxDepth, hitFlags, raycastHit, physxScenePtr))
            {
                raycastHit.position.x = std::min(raycastHit.position.x, inputOrigin.x + maxPoint.x);
                raycastHit.position.y = std::min(raycastHit.position.y, inputOrigin.y + maxPoint.y);

                raycastHit.position.x = std::max(raycastHit.position.x, inputOrigin.x + minPoint.x);
                raycastHit.position.y = std::max(raycastHit.position.y, inputOrigin.y + minPoint.y);

                auto node =
                    gTree->search(octomap::point3d(raycastHit.position.x, raycastHit.position.y, raycastHit.position.z));
                if (node && node->getValue() > occupancyThreshold)
                {
                    // printf("found: %f\n", node->getValue());
                    continue;
                }

                // printf("node %f\n", node->getValue());
                if (!gTree->insertRay(
                        octomap::point3d(origin.x, origin.y, origin.z),
                        octomap::point3d(raycastHit.position.x, raycastHit.position.y, raycastHit.position.z), maxDepth,
                        true))
                {
                    CARB_LOG_ERROR("ERROR while inserting ray");
                }
                // if (raycastHit.distance > minSearchDistance)
                {
                    // printf("d: %f\n", raycastHit.distance);
                    startList.push_back(::physx::PxVec3((raycastHit.normal.x * minSearchDistance + raycastHit.position.x),
                                                        (raycastHit.normal.y * minSearchDistance + raycastHit.position.y),
                                                        (inputOrigin.z))); // Normals are not guaranteed to be at the
                                                                           // same height so we flatten
                }
            }
            else
            {
            }
        }
    }
}


void CARB_ABI
GenerateMap(float gridResolution, float rayResolution, float minSearchDistance, float occupancyThreshold, size_t maxRays)
{
    pxr::UsdPrimRange range = gStage->Traverse();

    ::physx::PxScene* physxScenePtr = nullptr;
    for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;

        if (prim.IsA<pxr::UsdPhysicsScene>())
        {

            physxScenePtr =
                static_cast<::physx::PxScene*>(gPhysx->getPhysXPtr(prim.GetPrimPath(), omni::physx::PhysXType::ePTScene));

            if (physxScenePtr)
            {
                break;
            }
        }
    }
    if (!physxScenePtr)
    {
        CARB_LOG_ERROR("No Physics Scene Present");
        return;
    }

    // printf("gen [%f %f %f], [%f %f], [%f %f]\n", inputOrigin.x, inputOrigin.y, inputOrigin.z, inputMinPoint.x,
    //        inputMinPoint.y, inputMaxPoint.x, inputMaxPoint.y);

    ::physx::PxMaterial* defaultMaterial = physxScenePtr->getPhysics().createMaterial(0.5f, 0.5f, 0.6f);

    ::physx::PxShape* shape1 =
        physxScenePtr->getPhysics().createShape(::physx::PxPlaneGeometry(), *defaultMaterial, false);
    ::physx::PxRigidStatic* actor1 = physxScenePtr->getPhysics().createRigidStatic(
        ::physx::PxTransform(::physx::PxVec3(inputOrigin.x + inputMinPoint.x, 0, 0),
                             ::physx::PxQuat(0 * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f))));
    actor1->attachShape(*shape1);

    ::physx::PxShape* shape2 =
        physxScenePtr->getPhysics().createShape(::physx::PxPlaneGeometry(), *defaultMaterial, true);
    ::physx::PxRigidStatic* actor2 = physxScenePtr->getPhysics().createRigidStatic(
        ::physx::PxTransform(::physx::PxVec3(0, inputOrigin.y + inputMinPoint.y, 0),
                             ::physx::PxQuat(90 * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f))));
    actor2->attachShape(*shape2);


    ::physx::PxShape* shape3 =
        physxScenePtr->getPhysics().createShape(::physx::PxPlaneGeometry(), *defaultMaterial, true);
    ::physx::PxRigidStatic* actor3 = physxScenePtr->getPhysics().createRigidStatic(
        ::physx::PxTransform(::physx::PxVec3(0, inputOrigin.y + inputMaxPoint.y, 0),
                             ::physx::PxQuat(-90 * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f))));
    actor3->attachShape(*shape3);


    ::physx::PxShape* shape4 =
        physxScenePtr->getPhysics().createShape(::physx::PxPlaneGeometry(), *defaultMaterial, true);
    ::physx::PxRigidStatic* actor4 = physxScenePtr->getPhysics().createRigidStatic(
        ::physx::PxTransform(::physx::PxVec3(inputOrigin.x + inputMaxPoint.x, 0, 0),
                             ::physx::PxQuat(180 * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f))));
    actor4->attachShape(*shape4);

    physxScenePtr->addActor(*actor1);
    physxScenePtr->addActor(*actor2);
    physxScenePtr->addActor(*actor3);
    physxScenePtr->addActor(*actor4);

    gTree = std::make_unique<octomap::OcTree>(gridResolution);
    gTree->setOccupancyThres(0.5);
    gTree->setProbHit(0.7);
    gTree->setClampingThresMin(0.1);
    // Insert outer edge of map
    // gTree->prune();
    // gTree->updateInnerOccupancy();
    scan(inputOrigin, inputMinPoint, inputMaxPoint, physxScenePtr, rayResolution, minSearchDistance, occupancyThreshold,
         maxRays);
    gTree->prune();
    gTree->updateInnerOccupancy();

    physxScenePtr->removeActor(*actor1);
    physxScenePtr->removeActor(*actor2);
    physxScenePtr->removeActor(*actor3);
    physxScenePtr->removeActor(*actor4);
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
std::vector<carb::Float3> GetOccupiedPositions()
{
    std::vector<carb::Float3> pos;
    if (gTree)
    {
        auto beginLeafIter = gTree->begin_leafs();
        auto endLeafIter = gTree->end_leafs();
        for (octomap::OcTree::leaf_iterator it = beginLeafIter, end = endLeafIter; it != end; ++it)
        {
            if (gTree->isNodeOccupied(&(*it)))
            {
                pos.push_back(carb::Float3({ it.getCoordinate().x(), it.getCoordinate().y(), it.getCoordinate().z() }));
            }
        }
    }
    return pos;
}
std::vector<carb::Float3> GetFreePositions()
{
    std::vector<carb::Float3> pos;
    auto beginLeafIter = gTree->begin_leafs();
    auto endLeafIter = gTree->end_leafs();
    for (octomap::OcTree::leaf_iterator it = beginLeafIter, end = endLeafIter; it != end; ++it)
    {
        if (!gTree->isNodeOccupied(&(*it)))
        {
            pos.push_back(carb::Float3({ it.getCoordinate().x(), it.getCoordinate().y(), it.getCoordinate().z() }));
        }

        // manipulate node, e.g.:
        // std::cout << "Node center: " << it.getCoordinate() << std::endl;
        // std::cout << "Node size: " << it.getSize() << std::endl;
        // std::cout << "Node value: " << it->getValue() << std::endl;
    }
    return pos;
}
carb::Float3 GetMinBound()
{
    double x = 0, y = 0, z = 0;
    if (gTree)
    {
        gTree->getMetricMin(x, y, z);
    }
    return carb::Float3({ static_cast<float>(x), static_cast<float>(y), static_cast<float>(z) });
}
carb::Float3 GetMaxBound()
{
    double x = 0, y = 0, z = 0;
    if (gTree)
    {
        gTree->getMetricMax(x, y, z);
    }
    return carb::Float3({ static_cast<float>(x), static_cast<float>(y), static_cast<float>(z) });
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

void onDetach(void* userData)
{
}


void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{

    if (!settings->isPlaying)
    {
        return;
    }
}

void onStop(void* userData)
{
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
    desc.onDetach = onDetach;
    // desc.onStop = onStop;
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
}
