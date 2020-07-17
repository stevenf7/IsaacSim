// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
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
#include <carb/physx/physx.h>

#include <PxActor.h>
#include <PxArticulationJointReducedCoordinate.h>
#include <PxArticulationLink.h>
#include <PxArticulationReducedCoordinate.h>
#include <PxPhysicsAPI.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>

#include <PhysicsSchema/physicsScene.h>

#include <omni/kit/IStageUpdate.h>

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
CARB_PLUGIN_IMPL_DEPS(carb::physics::PhysX, omni::kit::IStageUpdate)

// private stuff
namespace
{
pxr::UsdStageWeakPtr gStage = nullptr;
carb::Framework* gFramework = nullptr;
omni::kit::IStageUpdate* gStageUpdate = nullptr;
omni::kit::StageUpdateNode* gStageUpdateNode = nullptr;
carb::physics::PhysX* gPhysx = nullptr;
std::unique_ptr<octomap::OcTree> gTree;
}

bool raycastClosest(const physx::PxVec3& pos,
                    const physx::PxVec3& dir,
                    const float distance,
                    const physx::PxHitFlags& hitFlags,
                    physx::PxRaycastHit& hit,
                    physx::PxScene* physxScene)
{


    // physx::PxRaycastHit hit;


    const bool ret = physx::PxSceneQueryExt::raycastSingle(*physxScene, pos, dir, distance, hitFlags, hit);
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
          carb::Float3 minPoint,
          carb::Float3 maxPoint,
          physx::PxScene* physxScenePtr,
          float rayResolution,
          float minSearchDistance,
          float occupancyThreshold)
{
    if (!physxScenePtr)
    {
        return;
    }
    std::vector<physx::PxVec3> startList;
    startList.push_back(physx::PxVec3(inputOrigin.x, inputOrigin.y, inputOrigin.z));
    size_t count = 0;
    std::vector<physx::PxVec3> unitDirs;
    float maxDepth = 1e8;
    physx::PxHitFlags hitFlags = physx::PxHitFlag::eDEFAULT | physx::PxHitFlag::eMESH_BOTH_SIDES;
    for (float degree = 0; degree < 360; degree += rayResolution)
    {
        physx::PxQuat rot = physx::PxQuat(degree * M_PI / 180.0f, physx::PxVec3(0.0f, 0.0f, 1.0f));
        unitDirs.push_back(rot.rotate(physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized());
    }

    while (startList.size() > 0)
    {
        if (count % 10000 == 0)
        {
            printf("STARTLIST: %d %d\n", startList.size(), count);
        }
        physx::PxVec3 origin = startList.back();
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
            physx::PxRaycastHit raycastHit;

            if (raycastClosest(origin, unitDir, maxDepth, hitFlags, raycastHit, physxScenePtr))
            {
                raycastHit.position.x = std::min(raycastHit.position.x, maxPoint.x);
                raycastHit.position.y = std::min(raycastHit.position.y, maxPoint.y);
                raycastHit.position.z = std::min(raycastHit.position.z, maxPoint.z);

                raycastHit.position.x = std::max(raycastHit.position.x, minPoint.x);
                raycastHit.position.y = std::max(raycastHit.position.y, minPoint.y);
                raycastHit.position.z = std::max(raycastHit.position.z, minPoint.z);

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
                    std::cout << "ERROR while inserting ray" << std::endl;
                }
                // if (raycastHit.distance > minSearchDistance)
                {
                    // printf("d: %f\n", raycastHit.distance);
                    startList.push_back(physx::PxVec3((raycastHit.normal.x * minSearchDistance + raycastHit.position.x),
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


void CARB_ABI GenerateMap(carb::Float3 inputOrigin,
                          carb::Float3 minPoint,
                          carb::Float3 maxPoint,
                          float gridResolution,
                          float rayResolution,
                          float minSearchDistance,
                          float occupancyThreshold)
{
    pxr::UsdPrimRange range = gStage->Traverse();

    physx::PxScene* physxScenePtr = nullptr;
    for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;

        if (prim.IsA<pxr::PhysicsSchemaPhysicsScene>())
        {

            physxScenePtr =
                static_cast<physx::PxScene*>(gPhysx->getPhysXPtr(prim.GetPrimPath(), carb::physics::ePTScene));

            if (physxScenePtr)
            {
                break;
            }
        }
    }
    gTree = std::make_unique<octomap::OcTree>(gridResolution);
    gTree->setOccupancyThres(0.5);
    gTree->setProbHit(0.7);
    gTree->setClampingThresMin(0.1);
    // Insert outer edge of map
    // gTree->prune();
    // gTree->updateInnerOccupancy();
    scan(inputOrigin, minPoint, maxPoint, physxScenePtr, rayResolution, minSearchDistance, occupancyThreshold);
    gTree->prune();
    gTree->updateInnerOccupancy();
}

std::vector<carb::Float3> GetOccupiedPositions()
{
    std::vector<carb::Float3> pos;
    auto beginLeafIter = gTree->begin_leafs();
    auto endLeafIter = gTree->end_leafs();
    for (octomap::OcTree::leaf_iterator it = beginLeafIter, end = endLeafIter; it != end; ++it)
    {
        if (gTree->isNodeOccupied(&(*it)))
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
    double x, y, z;
    gTree->getMetricMin(x, y, z);
    return carb::Float3({ x, y, z });
}
carb::Float3 GetMaxBound()
{
    double x, y, z;
    gTree->getMetricMax(x, y, z);
    return carb::Float3({ x, y, z });
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

    gPhysx = gFramework->acquireInterface<carb::physics::PhysX>();
    if (!gPhysx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "OccupancyMap";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    desc.onStop = onStop;
    // Create the stage update node and make sure it runs after physx
    size_t index = gStageUpdate->getStageUpdateNodeCount();
    gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);
    gStageUpdate->setStageUpdateNodeOrder(index, 75);
}

CARB_EXPORT void carbOnPluginShutdown()
{
    gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
}

void fillInterface(omni::isaac::occupancy_map::OccupancyMap& iface)
{
    using namespace omni::isaac::occupancy_map;

    memset(&iface, 0, sizeof(iface));

    iface.generateMap = GenerateMap;
    iface.getOccupiedPositions = GetOccupiedPositions;
    iface.getFreePositions = GetFreePositions;
    iface.getMinBound = GetMinBound;
    iface.getMaxBound = GetMaxBound;
}
