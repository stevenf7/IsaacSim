// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/isaac/occupancy_map/MapGenerator.h>
#include <omni/physx/IPhysx.h>

#include <extensions/PxSceneQueryExt.h>
#include <usdPhysics/scene.h>

#include <octomap/octomap.h>

#include <PxActor.h>
#include <PxArticulationJointReducedCoordinate.h>
#include <PxArticulationLink.h>
#include <PxArticulationReducedCoordinate.h>
#include <PxPhysicsAPI.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <stack>
#include "plugins/core/ScopedTimer.h"

namespace omni
{
namespace isaac
{
namespace occupancy_map
{


const ::physx::PxHitFlags gHitFlags = ::physx::PxHitFlag::eDEFAULT | ::physx::PxHitFlag::eMESH_BOTH_SIDES;
::physx::PxScene* findScene(omni::physx::IPhysx* physXPtr, pxr::UsdStageWeakPtr stagePtr)
{
    pxr::UsdPrimRange range = stagePtr->Traverse();
    ::physx::PxScene* physxScenePtr = nullptr;
    for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;

        if (prim.IsA<pxr::UsdPhysicsScene>())
        {

            physxScenePtr = static_cast<::physx::PxScene*>(
                physXPtr->getPhysXPtr(prim.GetPrimPath(), omni::physx::PhysXType::ePTScene));

            if (physxScenePtr)
            {
                return physxScenePtr;
            }
        }
    }
    return nullptr;
}


MapGenerator::MapGenerator(omni::physx::IPhysx* physXPtr, pxr::UsdStageWeakPtr stagePtr)
{
    mPhysx = physXPtr;
    mStage = stagePtr;
    mTree = new octomap::OcTree(mResolution);
    mPhysxScenePtr = findScene(mPhysx, mStage);
    if (!mPhysxScenePtr)
    {
        printf("No Physics Scene Present\n");
        return;
    }

    mDefaultMaterial = mPhysxScenePtr->getPhysics().createMaterial(0.5f, 0.5f, 0.6f);

    for (int i = 0; i < 4; i++)
    {
        mShapes[i] = mPhysxScenePtr->getPhysics().createShape(::physx::PxPlaneGeometry(), *mDefaultMaterial, false);
        mActors[i] = mPhysxScenePtr->getPhysics().createRigidStatic(::physx::PxTransform());
        mActors[i]->attachShape(*mShapes[i]);
    }

    mTree->setOccupancyThres(0.5);
    mTree->setProbHit(0.7);
    mTree->setClampingThresMin(0.1);
}
MapGenerator::~MapGenerator()
{
    delete mTree;
}

void MapGenerator::updateSettings(const float resolution,
                                  const float occupancyThreshold,
                                  const float minSearchDistance,
                                  const float degreesBetweenRays,
                                  const size_t maxRays,
                                  const float occupiedValue,
                                  const float unoccupiedValue,
                                  const float unknownValue)
{
    mResolution = resolution;
    mMinSearchDistance = minSearchDistance;
    mDegreesBetweenRays = degreesBetweenRays;
    mOccupancyThreshold = occupancyThreshold;
    mMaxRays = maxRays;
    mOccupiedValue = occupiedValue;
    mUnoccupiedValue = unoccupiedValue;
    mUnknownValue = unknownValue;

    // printf("%f %f %f %f %lu %f %f %f\n", mResolution, mMinSearchDistance, mDegreesBetweenRays, mOccupancyThreshold,
    //        mMaxRays, mOccupiedValue, mUnoccupiedValue, mUnknownValue);
    mTree->setResolution(mResolution);

    mUnitDirs.clear();
    for (float degree = 0; degree < 360; degree += mDegreesBetweenRays)
    {
        ::physx::PxQuat rot = ::physx::PxQuat(degree * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f));
        mUnitDirs.push_back(rot.rotate(::physx::PxVec3(1.0f, 0.0f, 0.0f)).getNormalized());
    }
}
void MapGenerator::setTransform(carb::Float3 inputOrigin, carb::Float2 inputMinPoint, carb::Float2 inputMaxPoint)
{
    mInputOrigin = inputOrigin;
    mInputMinPoint = inputMinPoint;
    mInputMaxPoint = inputMaxPoint;
}
void MapGenerator::generate()
{
    // omni::isaac::utils::ScopedTimer TimerApp("Generate");

    if (!mPhysxScenePtr)
    {
        printf("No Physics Scene Present\n");
        return;
    }

    if (!mTree)
    {
        printf("Tree not valid\n");
        return;
    }

    mTree->clear();

    mActors[0]->setGlobalPose(::physx::PxTransform(::physx::PxVec3(mInputOrigin.x + mInputMinPoint.x, 0, 0),
                                                   ::physx::PxQuat(0 * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f))));

    mActors[1]->setGlobalPose(
        ::physx::PxTransform(::physx::PxVec3(0, mInputOrigin.y + mInputMinPoint.y, 0),
                             ::physx::PxQuat(90 * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f))));
    mActors[2]->setGlobalPose(
        ::physx::PxTransform(::physx::PxVec3(0, mInputOrigin.y + mInputMaxPoint.y - mResolution, 0),
                             ::physx::PxQuat(-90 * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f))));
    mActors[3]->setGlobalPose(
        ::physx::PxTransform(::physx::PxVec3(mInputOrigin.x + mInputMaxPoint.x - mResolution, 0, 0),
                             ::physx::PxQuat(180 * M_PI / 180.0f, ::physx::PxVec3(0.0f, 0.0f, 1.0f))));

    for (int i = 0; i < 4; i++)
    {
        mPhysxScenePtr->addActor(*mActors[i]);
    }

    std::vector<::physx::PxVec3> startList;
    startList.push_back(::physx::PxVec3(mInputOrigin.x, mInputOrigin.y, mInputOrigin.z));
    size_t count = 0;

    while (startList.size() > 0 && count < mMaxRays)
    {
        // if (count % 10000 == 0)
        // {
        //     printf("Processing occupancy map: points left %zu, points processed: %zu\n", startList.size(), count);
        // }
        ::physx::PxVec3 origin = startList.back();
        startList.pop_back();
        count++;
        for (auto& unitDir : mUnitDirs)
        {
            ::physx::PxRaycastHit raycastHit;

            if (::physx::PxSceneQueryExt::raycastSingle(
                    *mPhysxScenePtr, origin, unitDir, mMaxDepth, gHitFlags, raycastHit))
            {
                raycastHit.position.x = std::min(raycastHit.position.x, mInputOrigin.x + mInputMaxPoint.x);
                raycastHit.position.y = std::min(raycastHit.position.y, mInputOrigin.y + mInputMaxPoint.y);

                raycastHit.position.x = std::max(raycastHit.position.x, mInputOrigin.x + mInputMinPoint.x);
                raycastHit.position.y = std::max(raycastHit.position.y, mInputOrigin.y + mInputMinPoint.y);
                // printf("num nodes %lu\n", mTree->calcNumNodes());

                auto node =
                    mTree->search(octomap::point3d(raycastHit.position.x, raycastHit.position.y, raycastHit.position.z));
                if (node && node->getValue() > mOccupancyThreshold)
                {
                    // printf("found: %f\n", node->getValue());
                    continue;
                }


                mTree->insertRay(octomap::point3d(origin.x, origin.y, origin.z),
                                 octomap::point3d(raycastHit.position.x, raycastHit.position.y, raycastHit.position.z),
                                 mMaxDepth, true);

                // printf("d: %f\n", raycastHit.distance);
                // Normals are not guaranteed to be at the same height so we flatten
                startList.push_back(::physx::PxVec3(raycastHit.normal.x * mMinSearchDistance + raycastHit.position.x,
                                                    raycastHit.normal.y * mMinSearchDistance + raycastHit.position.y,
                                                    mInputOrigin.z));
            }
        }
    }
    mTree->prune();
    // mTree->updateInnerOccupancy();
    for (int i = 0; i < 4; i++)
    {
        mPhysxScenePtr->removeActor(*mActors[i]);
    }
}

std::vector<carb::Float2> MapGenerator::getOccupiedPositions()
{
    std::vector<carb::Float2> pos;
    if (mTree)
    {
        auto beginLeafIter = mTree->begin_leafs();
        auto endLeafIter = mTree->end_leafs();
        for (octomap::OcTree::leaf_iterator it = beginLeafIter, end = endLeafIter; it != end; ++it)
        {
            if (mTree->isNodeOccupied(&(*it)))
            {
                pos.push_back(carb::Float2({ it.getCoordinate().x(), it.getCoordinate().y() }));
            }
        }
    }
    return pos;
}
std::vector<carb::Float2> MapGenerator::getFreePositions()
{
    std::vector<carb::Float2> pos;
    auto beginLeafIter = mTree->begin_leafs();
    auto endLeafIter = mTree->end_leafs();
    for (octomap::OcTree::leaf_iterator it = beginLeafIter, end = endLeafIter; it != end; ++it)
    {
        if (!mTree->isNodeOccupied(&(*it)))
        {
            pos.push_back(carb::Float2({ it.getCoordinate().x(), it.getCoordinate().y() }));
        }

        // manipulate node, e.g.:
        // std::cout << "Node center: " << it.getCoordinate() << std::endl;
        // std::cout << "Node size: " << it.getSize() << std::endl;
        // std::cout << "Node value: " << it->getValue() << std::endl;
    }
    return pos;
}
carb::Float2 MapGenerator::getMinBound()
{
    double x = 0, y = 0, z = 0;
    if (mTree)
    {
        mTree->getMetricMin(x, y, z);
    }
    return carb::Float2({ static_cast<float>(x), static_cast<float>(y) });
}
carb::Float2 MapGenerator::getMaxBound()
{

    double x = 0, y = 0, z = 0;
    if (mTree)
    {
        mTree->getMetricMax(x, y, z);
    }
    return carb::Float2({ static_cast<float>(x), static_cast<float>(y) });
}

carb::Int2 MapGenerator::getDimensions()
{
    carb::Int2 num_cells = { 0, 0 };

    if (mTree)
    {
        // min and max in meters
        carb::Float2 min = getMinBound();
        carb::Float2 max = getMaxBound();
        carb::Float2 size = { max.x - min.x, max.y - min.y };
        // scale by the grid resolution to get the number of pixels
        // num_cells = meters / (meters/cell)
        num_cells = { static_cast<int>(size.x / mResolution), static_cast<int>(size.y / mResolution) };
    }
    return num_cells;
}

// 8 possible directions
// int row[] = { -1, -1, -1, 0, 0, 1, 1, 1 };
// int col[] = { -1, 0, 1, -1, 1, -1, 0, 1 };
// 4 possible directions
int row[] = { 0, -1, 0, 1 };
int col[] = { -1, 0, 1, 0 };

bool isSafe(float* buffer, carb::Int2 num_cells, int x, int y, float target)
{
    size_t index = y * num_cells.x + x;
    return (x >= 0 && x < num_cells.x && y >= 0 && y < num_cells.y) && buffer[index] == target;
}

// Flood fill using DFS
void floodfill(float* buffer, carb::Int2 num_cells, int sx, int sy, float replacement)
{
    // omni::isaac::utils::ScopedTimer TimerApp("floodFill");
    std::stack<std::pair<int, int>> q;
    q.push({ sx, sy });

    size_t index = sy * num_cells.x + sx;
    float target = buffer[index];
    // loop till queue is empty
    while (!q.empty())
    {
        std::pair<int, int> node = q.top();
        q.pop();
        int x = node.first;
        int y = node.second;

        index = y * num_cells.x + x;
        buffer[index] = replacement;

        for (int k = 0; k < 4; k++)
        {
            if (isSafe(buffer, num_cells, x + row[k], y + col[k], target))
            {
                q.push({ x + row[k], y + col[k] });
            }
        }
    }
}


std::vector<float> MapGenerator::getBuffer()
{
    // omni::isaac::utils::ScopedTimer TimerApp("getBuffer");

    std::vector<float> buffer;
    if (mTree)
    {
        // min and max in meters
        carb::Float2 min = getMinBound();
        carb::Float2 max = getMaxBound();
        // scale by the grid resolution to get the number of pixels
        // num_cells = meters / (meters/cell)
        carb::Int2 num_cells = getDimensions();

        buffer.resize(num_cells.x * num_cells.y);
        std::fill(buffer.begin(), buffer.end(), mUnknownValue);


        auto beginLeafIter = mTree->begin_leafs();
        auto endLeafIter = mTree->end_leafs();
        for (octomap::OcTree::leaf_iterator it = beginLeafIter, end = endLeafIter; it != end; ++it)
        {
            if (mTree->isNodeOccupied(&(*it)))
            {
                size_t index =
                    static_cast<size_t>(it.getCoordinate().y() / mResolution - min.y / mResolution) * num_cells.x +
                    static_cast<size_t>((-it.getCoordinate().x() + min.x + max.x) / mResolution - min.x / mResolution);

                buffer[index] = mOccupiedValue;
            }
        }


        carb::Int2 start_pix = { static_cast<int>(mInputOrigin.x / mResolution - min.x / mResolution),
                                 static_cast<int>(mInputOrigin.y / mResolution - min.y / mResolution) };

        floodfill(buffer.data(), num_cells, start_pix.x, start_pix.y, mUnoccupiedValue);


        return buffer;
    }
    return buffer;
}
std::vector<char> MapGenerator::getColoredByteBuffer(const carb::Int4& occupied,
                                                     const carb::Int4& unoccupied,
                                                     const carb::Int4& unknown)
{
    std::vector<char> colorBuffer;
    if (mTree)
    {
        std::vector<float> buffer = getBuffer();
        colorBuffer.resize(buffer.size() * 4);

        for (size_t i = 0; i < buffer.size(); i++)
        {

            if (buffer[i] == mUnknownValue)
            {
                colorBuffer[i * 4 + 0] = unknown.x;
                colorBuffer[i * 4 + 1] = unknown.y;
                colorBuffer[i * 4 + 2] = unknown.z;
                colorBuffer[i * 4 + 3] = unknown.w;
            }
            if (buffer[i] == mUnoccupiedValue)
            {
                colorBuffer[i * 4 + 0] = unoccupied.x;
                colorBuffer[i * 4 + 1] = unoccupied.y;
                colorBuffer[i * 4 + 2] = unoccupied.z;
                colorBuffer[i * 4 + 3] = unoccupied.w;
            }
            if (buffer[i] == mOccupiedValue)
            {
                colorBuffer[i * 4 + 0] = occupied.x;
                colorBuffer[i * 4 + 1] = occupied.y;
                colorBuffer[i * 4 + 2] = occupied.z;
                colorBuffer[i * 4 + 3] = occupied.w;
            }
        }
    }
    return colorBuffer;
}
}
}
}
