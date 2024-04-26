// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "omni/isaac/utils/ScopedTimer.h"

#include <extensions/PxSceneQueryExt.h>
#include <octomap/octomap.h>
#include <omni/physx/IPhysx.h>
#include <pxr/usd/usdPhysics/scene.h>

#include <MapGenerator.h>
#include <PxActor.h>
#include <PxArticulationJointReducedCoordinate.h>
#include <PxArticulationLink.h>
#include <PxArticulationReducedCoordinate.h>
#include <PxPhysicsAPI.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <stack>

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
    mTree = new octomap::OcTree(mCellSize);
    mPhysxScenePtr = findScene(mPhysx, mStage);
    if (!mPhysxScenePtr)
    {
        printf("No Physics Scene Present\n");
        return;
    }

    mTree->setOccupancyThres(0.5);
    mTree->setProbHit(0.7);
    mTree->setClampingThresMin(0.1);
}
MapGenerator::~MapGenerator()
{
    delete mTree;
}

void MapGenerator::updateSettings(const float cellSize,
                                  const float occupiedValue,
                                  const float unoccupiedValue,
                                  const float unknownValue)
{
    mCellSize = cellSize;
    mOccupiedValue = occupiedValue;
    mUnoccupiedValue = unoccupiedValue;
    mUnknownValue = unknownValue;
    mTree->setResolution(mCellSize);
}
void MapGenerator::setTransform(carb::Float3 inputOrigin, carb::Float3 inputMinPoint, carb::Float3 inputMaxPoint)
{
    mInputOrigin = inputOrigin;
    mInputMinPoint = inputMinPoint;
    mInputMaxPoint = inputMaxPoint;
}
void MapGenerator::generate2d()
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
    // use half extents for the cube that is used for overlap tests
    // Height of cube must be at least cell size / 2.0
    float geomHeight = ::physx::PxAbs(mInputMaxPoint.z - mInputMinPoint.z) / 2.0f + mCellSize / 2.0f;
    ::physx::PxBoxGeometry cellGeom(::physx::PxVec3(mCellSize / 2.0f, mCellSize / 2.0f, geomHeight));

    octomap::KeySet occupied_cells, unoccupied_cells;
    ::physx::PxOverlapHit hit;

    for (float ix = mInputMinPoint.x + mCellSize / 2.0f; ix <= mInputMaxPoint.x - mCellSize / 2.0f; ix += mCellSize)
    {
        for (float iy = mInputMinPoint.y + mCellSize / 2.0f; iy <= mInputMaxPoint.y - mCellSize / 2.0f; iy += mCellSize)
        {
            octomap::OcTreeKey key;
            key = mTree->coordToKey(octomap::point3d(ix + mInputOrigin.x, iy + mInputOrigin.y, mInputOrigin.z));

            // because the min and max points are relative to origin, they must be offset
            float height = mInputOrigin.z + mInputMinPoint.z + (mInputMaxPoint.z - mInputMinPoint.z) / 2.0f;
            ::physx::PxTransform pose(::physx::PxVec3(ix + mInputOrigin.x, iy + mInputOrigin.y, height));
            if (::physx::PxSceneQueryExt::overlapAny(*mPhysxScenePtr, cellGeom, pose, hit))
            {
                occupied_cells.insert(key);
            }
            else
            {
                unoccupied_cells.insert(key);
            }
        }
    }
    for (octomap::KeySet::iterator it = unoccupied_cells.begin(); it != unoccupied_cells.end(); ++it)
    {
        mTree->updateNode(*it, false, true);
    }
    for (octomap::KeySet::iterator it = occupied_cells.begin(); it != occupied_cells.end(); ++it)
    {
        mTree->updateNode(*it, true, true);
    }
    mTree->updateInnerOccupancy();
}
void MapGenerator::generate3d()
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
    // use half extents for the cube that is used for overlap tests
    // Height of cube must be at least cell size / 2.0
    ::physx::PxBoxGeometry cellGeom(::physx::PxVec3(mCellSize / 2.0f, mCellSize / 2.0f, mCellSize / 2.0f));

    octomap::KeySet occupied_cells, unoccupied_cells;
    ::physx::PxOverlapHit hit;

    for (float ix = mInputMinPoint.x + mCellSize / 2.0f; ix <= mInputMaxPoint.x - mCellSize / 2.0f; ix += mCellSize)
    {
        for (float iy = mInputMinPoint.y + mCellSize / 2.0f; iy <= mInputMaxPoint.y - mCellSize / 2.0f; iy += mCellSize)
        {
            for (float iz = mInputMinPoint.z + mCellSize / 2.0f; iz <= mInputMaxPoint.z - mCellSize / 2.0f;
                 iz += mCellSize)
            {
                octomap::OcTreeKey key;
                key = mTree->coordToKey(octomap::point3d(ix + mInputOrigin.x, iy + mInputOrigin.y, iz + mInputOrigin.z));

                // because the min and max points are relative to origin, they must be offset
                ::physx::PxTransform pose(::physx::PxVec3(ix + mInputOrigin.x, iy + mInputOrigin.y, iz + mInputOrigin.z));
                if (::physx::PxSceneQueryExt::overlapAny(*mPhysxScenePtr, cellGeom, pose, hit))
                {
                    occupied_cells.insert(key);
                }
                else
                {
                    unoccupied_cells.insert(key);
                }
            }
        }
    }
    for (octomap::KeySet::iterator it = unoccupied_cells.begin(); it != unoccupied_cells.end(); ++it)
    {
        mTree->updateNode(*it, false, true);
    }
    for (octomap::KeySet::iterator it = occupied_cells.begin(); it != occupied_cells.end(); ++it)
    {
        mTree->updateNode(*it, true, true);
    }
    mTree->updateInnerOccupancy();
}

std::vector<carb::Float3> MapGenerator::getOccupiedPositions()
{
    std::vector<carb::Float3> pos;
    if (mTree)
    {
        auto beginLeafIter = mTree->begin_leafs();
        auto endLeafIter = mTree->end_leafs();
        for (octomap::OcTree::leaf_iterator it = beginLeafIter, end = endLeafIter; it != end; ++it)
        {
            if (mTree->isNodeOccupied(&(*it)))
            {
                pos.push_back(carb::Float3({ it.getCoordinate().x(), it.getCoordinate().y(), it.getCoordinate().z() }));
            }
        }
    }
    return pos;
}
std::vector<carb::Float3> MapGenerator::getFreePositions()
{
    std::vector<carb::Float3> pos;
    auto beginLeafIter = mTree->begin_leafs();
    auto endLeafIter = mTree->end_leafs();
    for (octomap::OcTree::leaf_iterator it = beginLeafIter, end = endLeafIter; it != end; ++it)
    {
        if (!mTree->isNodeOccupied(&(*it)))
        {
            pos.push_back(carb::Float3({ it.getCoordinate().x(), it.getCoordinate().y(), it.getCoordinate().z() }));
        }
    }
    return pos;
}
carb::Float3 MapGenerator::getMinBound()
{
    double x = 0, y = 0, z = 0;
    if (mTree)
    {
        mTree->getMetricMin(x, y, z);
    }
    return carb::Float3({ static_cast<float>(x), static_cast<float>(y), static_cast<float>(z) });
}
carb::Float3 MapGenerator::getMaxBound()
{

    double x = 0, y = 0, z = 0;
    if (mTree)
    {
        mTree->getMetricMax(x, y, z);
    }
    return carb::Float3({ static_cast<float>(x), static_cast<float>(y), static_cast<float>(z) });
}

carb::Int3 MapGenerator::getDimensions()
{
    carb::Int3 num_cells = { 0, 0, 0 };

    if (mTree)
    {
        // min and max in meters
        carb::Float3 min = getMinBound();
        carb::Float3 max = getMaxBound();
        carb::Float3 size = { max.x - min.x, max.y - min.y, max.z - min.z };
        // scale by the grid resolution to get the number of pixels
        // num_cells = meters / (meters/cell)
        num_cells = { static_cast<int>(size.x / mCellSize), static_cast<int>(size.y / mCellSize),
                      static_cast<int>(size.z / mCellSize) };
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
        carb::Float3 min = getMinBound();
        carb::Float3 max = getMaxBound();
        // scale by the grid resolution to get the number of pixels
        // num_cells = meters / (meters/cell)
        carb::Int3 num_cells = getDimensions();
        if (num_cells.x * num_cells.y <= 0)
        {
            return buffer;
        }
        buffer.resize(num_cells.x * num_cells.y);
        std::fill(buffer.begin(), buffer.end(), mUnknownValue);


        auto beginLeafIter = mTree->begin_leafs();
        auto endLeafIter = mTree->end_leafs();
        for (octomap::OcTree::leaf_iterator it = beginLeafIter, end = endLeafIter; it != end; ++it)
        {
            if (mTree->isNodeOccupied(&(*it)))
            {
                size_t index =
                    static_cast<size_t>(it.getCoordinate().y() / mCellSize - min.y / mCellSize) * num_cells.x +
                    static_cast<size_t>((-it.getCoordinate().x() + min.x + max.x) / mCellSize - min.x / mCellSize);

                buffer[index] = mOccupiedValue;
            }
        }


        carb::Int2 start_pix = { static_cast<int>(-mInputOrigin.x / mCellSize + max.x / mCellSize),
                                 static_cast<int>(mInputOrigin.y / mCellSize - min.y / mCellSize) };

        floodfill(buffer.data(), { num_cells.x, num_cells.y }, start_pix.x, start_pix.y, mUnoccupiedValue);

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
