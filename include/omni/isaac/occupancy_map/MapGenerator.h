// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <PxPhysicsAPI.h>

namespace octomap
{
class OcTree;
}

namespace physx
{
class PxShape;
class PxRigidStatic;
class PxMaterial;
class PxScene;
}

namespace omni
{
namespace physx
{
class IPhysx;
}
namespace isaac
{
namespace occupancy_map
{


class MapGenerator

{


public:
    MapGenerator(omni::physx::IPhysx* physXPtr, pxr::UsdStageWeakPtr stagePtr);
    ~MapGenerator();
    void updateSettings(const float resolution = 5,
                        const float occupancyThreshold = 1.0,
                        const float minSearchDistance = 2.0f,
                        const float degreesBetweenRays = 5.0f,
                        const size_t maxRays = 1e8,
                        const float occupiedValue = 1.0f,
                        const float unoccupiedValue = 0.0f,
                        const float unknownValue = 0.5f);
    void setTransform(carb::Float3 inputOrigin, carb::Float2 inputMinPoint, carb::Float2 inputMaxPoint);
    void generate();
    std::vector<carb::Float2> getOccupiedPositions();
    std::vector<carb::Float2> getFreePositions();
    carb::Float2 getMinBound();
    carb::Float2 getMaxBound();
    carb::Int2 getDimensions();
    std::vector<float> getBuffer();
    std::vector<char> getColoredByteBuffer(const carb::Int4& occupied,
                                           const carb::Int4& unoccupied,
                                           const carb::Int4& unknown);


private:
    float mResolution = 5;
    float mMinSearchDistance = 2;
    float mDegreesBetweenRays = 5;
    float mOccupancyThreshold = 1.0;
    float mMaxDepth = 1e8;
    size_t mMaxRays = 1e6;
    omni::physx::IPhysx* mPhysx = nullptr;
    pxr::UsdStageWeakPtr mStage = nullptr;
    pxr::UsdPrim mParentPrim;
    octomap::OcTree* mTree;
    ::physx::PxShape* mShapes[4];
    ::physx::PxRigidStatic* mActors[4];
    ::physx::PxMaterial* mDefaultMaterial = nullptr;
    ::physx::PxScene* mPhysxScenePtr = nullptr;
    carb::Float3 mInputOrigin;
    carb::Float2 mInputMinPoint;
    carb::Float2 mInputMaxPoint;
    float mOccupiedValue = 1.0;
    float mUnoccupiedValue = 0.0;
    float mUnknownValue = 0.5;
    std::vector<::physx::PxVec3> mUnitDirs;
};

}
}
}
