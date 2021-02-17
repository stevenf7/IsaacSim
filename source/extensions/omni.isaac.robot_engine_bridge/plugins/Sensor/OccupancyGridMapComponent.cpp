// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <carb/Framework.h>
#include <carb/Types.h>
#include <vector>
#include <string>

#include "../Core/IsaacComponent.h"
#include "OccupancyGridMapComponent.h"
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>
#include <omni/physx/IPhysx.h>


namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

OccupancyGridMapComponent::OccupancyGridMapComponent() : IsaacComponent()
{
    framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
        return;
    }

    mPhysx = framework->acquireInterface<omni::physx::IPhysx>();
    if (!mPhysx)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }
    mFastCachePtr = framework->acquireInterface<carb::fastcache::FastCache>();
    if (!mFastCachePtr)
    {
        CARB_LOG_ERROR("*** Failed to acquire FastCache interface\n");
        return;
    }
}

OccupancyGridMapComponent::~OccupancyGridMapComponent()
{
}

void OccupancyGridMapComponent::onStart()
{
    mGenerator = std::make_unique<omni::isaac::occupancy_map::MapGenerator>(mPhysx, mStage);
    mStageUnits = static_cast<float>(UsdGeomGetStageMetersPerUnit(mStage));

    onComponentChange();
    mSkipFirstFrame = true;
}
void OccupancyGridMapComponent::tick()
{
}

void OccupancyGridMapComponent::publishAllMessages()
{
    if (mSkipFirstFrame)
    {
        mSkipFirstFrame = false;
        return;
    }
    CARB_PROFILE_ZONE(0, "REB OccupancyGridMapComponent Tick");
    carb::fastcache::Transform parentTrans;
    parentTrans.position = { 0, 0, 0 };
    if (mParentPrimPath != pxr::SdfPath())
    {
        mFastCachePtr->getTransform(mParentPrimPath, parentTrans);
    }
    carb::Float2 inputMinPoint = {
        parentTrans.position.x + mOffset[0] - (mCellSize * static_cast<float>(mMapSize[0])) * 0.5f,
        parentTrans.position.y + mOffset[1] - (mCellSize * static_cast<float>(mMapSize[1])) * 0.5f
    };

    carb::Float2 inputMaxPoint = {
        parentTrans.position.x + mOffset[0] + (mCellSize * static_cast<float>(mMapSize[0])) * 0.5f,
        parentTrans.position.y + mOffset[1] + (mCellSize * static_cast<float>(mMapSize[1])) * 0.5f
    };
    inputMinPoint = { inputMinPoint.x / mStageUnits, inputMinPoint.y / mStageUnits };
    inputMaxPoint = { inputMaxPoint.x / mStageUnits, inputMaxPoint.y / mStageUnits };

    if (mGenerator)
    {
        mGenerator->setTransform(parentTrans.position, inputMinPoint, inputMaxPoint);
        mGenerator->generate();
    }
    else
    {
        CARB_LOG_ERROR("Generator not valid");
        return;
    }
    std::vector<float> data = mGenerator->getBuffer();
    if (data.size() != static_cast<size_t>(mMapSize[0] * mMapSize[1]))
    {
        // CARB_LOG_ERROR("Array size %lu does not match %d", data.size(), mMapSize[0] * mMapSize[1]);
        return;
    }
    IsaacMessage<isaac_message::State> stateMessage;
    auto stateMessageProto = stateMessage.initProto();
    stateMessageProto.setSchema("");

    auto tensorProto = stateMessageProto.initPack();
    tensorProto.setElementType(ElementType::FLOAT32);
    tensorProto.initSizes(2);
    tensorProto.setSizes({ mMapSize[0], mMapSize[1] });
    tensorProto.setScanlineStride(0);
    tensorProto.setDataBufferIndex(0);


    std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
    buffers[0] = std::make_unique<IsaacHostBuffer>(mMapSize[0] * mMapSize[1] * sizeof(float));
    std::memcpy(buffers[0]->data(), data.data(), mMapSize[0] * mMapSize[1] * sizeof(float));
    publish(mOutputComponent, mChannelName, stateMessage, buffers);
}
void OccupancyGridMapComponent::onComponentChange()
{
    // CARB_LOG_ERROR("OccupancyGridMapComponent Update");
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineOccupancyGridMap& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineOccupancyGridMap)mPrim;
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetOffsetAttr(), mOffset);
    isaac::utils::safeGetAttribute(typedPrim.GetCellSizeAttr(), mCellSize);
    isaac::utils::safeGetAttribute(typedPrim.GetDegreesPerRayAttr(), mDegreesPerRay);
    isaac::utils::safeGetAttribute(typedPrim.GetSurfaceOffsetAttr(), mSurfaceOffset);
    isaac::utils::safeGetAttribute(typedPrim.GetOccupancyThresholdAttr(), mOccupancyThreshold);
    isaac::utils::safeGetAttribute(typedPrim.GetMaxRaysAttr(), mMaxRays);
    isaac::utils::safeGetAttribute(typedPrim.GetMapSizeAttr(), mMapSize);
    isaac::utils::safeGetAttribute(typedPrim.GetDebugDrawAttr(), mDebugDraw);

    isaac::utils::safeGetAttribute(typedPrim.GetOccupiedValueAttr(), mOccupiedValue);
    isaac::utils::safeGetAttribute(typedPrim.GetUnoccupiedValueAttr(), mUnoccupiedValue);
    isaac::utils::safeGetAttribute(typedPrim.GetUnknownValueAttr(), mUnknownValue);

    pxr::SdfPathVector targets;
    typedPrim.GetParentPrimRel().GetTargets(&targets);

    if (targets.size() == 1)
    {
        mParentPrimPath = targets[0];

        mParentPrim = mStage->GetPrimAtPath(mParentPrimPath);
        if (!mParentPrim)
        {
            CARB_LOG_ERROR("Parent Prim %s not valid", mParentPrimPath.GetString().c_str());
        }
    }


    printf("Comp: %f %f %f %f %d %f %f %f\n", mCellSize / mStageUnits, mSurfaceOffset / mStageUnits, mDegreesPerRay,
           mOccupancyThreshold, mMaxRays, mOccupiedValue, mUnoccupiedValue, mUnknownValue);

    mGenerator->updateSettings(mCellSize / mStageUnits, mOccupancyThreshold, mSurfaceOffset / mStageUnits,
                               mDegreesPerRay, mMaxRays, mOccupiedValue, mUnoccupiedValue, mUnknownValue);
}
}
}
}
