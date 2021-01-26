// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "plugins/core/Component.h"

#include <carb/fastcache/FastCache.h>
#include <carb/renderer/Renderer.h>

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <rangeSensorSchema/rangeSensor.h>
#include <usdPhysics/scene.h>

#include <PxActor.h>
#include <PxArticulationJointReducedCoordinate.h>
#include <PxArticulationLink.h>
#include <PxArticulationReducedCoordinate.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <string>
#include <vector>
namespace omni
{
namespace isaac
{
namespace range_sensor
{

/**
 * @brief Base class which simulates a range sensor
 */
template <class PrimType>
class RangeSensorComponentBase : public utils::ComponentBase<PrimType>
{

public:
    /**
     * @brief Construct a new Isaac Component
     */
    RangeSensorComponentBase(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr)
    {
        mPhysx = physxPtr;
        mFastCachePtr = fastCachePtr;
    }
    /**
     * @brief Destroy the Range Sensor Component Base object
     *
     */
    ~RangeSensorComponentBase()
    {
        mDebugLines.clear();
    }
    /**
     * @brief Initialize various pointers and handles in the component
     * Must be called after creation, can be overridden to initialize subcomponents
     *

     * @param prim
     * @param stage
     */

    virtual void initialize(const PrimType& prim, pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<PrimType>::initialize(prim, stage);
    }
    /**
     * @brief Function that runs after start is pressed
     *
     */
    virtual void onStart()
    {
        onComponentChange();

        pxr::UsdPrimRange range = this->mStage->Traverse();

        // TODO: move this to the manager and only run once on start for all sensors
        mPxScene = nullptr;
        for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        {
            pxr::UsdPrim prim = *iter;

            if (prim.IsA<pxr::UsdPhysicsScene>())
            {

                mPxScene = static_cast<::physx::PxScene*>(
                    mPhysx->getPhysXPtr(prim.GetPrimPath(), omni::physx::PhysXType::ePTScene));

                if (mPxScene)
                {
                    break;
                }
            }
        }
    }

    /**
     * @brief Called every frame
     *
     */
    virtual void tick() = 0;

    /**
     * @brief Called every time the Prim is changed
     *
     */
    virtual void onComponentChange()
    {

        if (this->mPrim.GetMinRangeAttr().HasValue())
        {
            this->mPrim.GetMinRangeAttr().Get(&mMinRange);
        }

        if (this->mPrim.GetMaxRangeAttr().HasValue())
        {
            this->mPrim.GetMaxRangeAttr().Get(&mMaxRange);
        }

        if (this->mPrim.GetDrawPointsAttr().HasValue())
        {
            this->mPrim.GetDrawPointsAttr().Get(&mDrawPoints);
        }

        if (this->mPrim.GetDrawLinesAttr().HasValue())
        {
            this->mPrim.GetDrawLinesAttr().Get(&mDrawLines);
        }


        mParentPrim = this->mStage->GetPrimAtPath(this->mPrim.GetPath()).GetParent();
        // printf("PARENT: %s\n", mParentPrim.GetPath().GetString().c_str());
        mMetersPerUnit = static_cast<float>(UsdGeomGetStageMetersPerUnit(this->mStage));
        mDebugLines.clear();
    }

    /**
     * @brief Update timestamps for component
     *
     * @param timeSeconds
     * @param dt
     * @param timeNano
     */
    void updateTimestamp(double timeSeconds, double dt, int64_t timeNano)
    {
        this->mTimeNanoSeconds = timeNano;
        this->mTimeSeconds = timeSeconds;
        this->mTimeDelta = dt;
    }

    /**
     * @brief Get the Draw Points object
     *
     * @return true
     * @return false
     */
    bool getDrawPoints()
    {
        return mDrawPoints;
    }

    /**
     * @brief Get the Draw Lines object
     *
     * @return true
     * @return false
     */
    bool getDrawLines()
    {
        return mDrawLines;
    }

    std::vector<DebugData>& getDebugLines()
    {
        return mDebugLines;
    }

    std::vector<carb::Float3>& getPointCloud()
    {
        return mLastHitPos;
    }


protected:
    bool mDrawPoints = false;
    bool mDrawLines = false;
    std::vector<omni::isaac::range_sensor::DebugData> mDebugLines;
    std::vector<carb::Float3> mLastHitPos;

    float mMinRange = 0.4f;
    float mMaxRange = 100.0f;

    float mMetersPerUnit = 1.0;


    pxr::UsdPrim mParentPrim;

    carb::fastcache::FastCache* mFastCachePtr = nullptr;
    omni::physx::IPhysx* mPhysx = nullptr;
    ::physx::PxScene* mPxScene = nullptr;
};

typedef RangeSensorComponentBase<pxr::RangeSensorSchemaRangeSensor> RangeSensorComponent;

}
}
}
