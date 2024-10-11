// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "isaacsim/core/utils/UsdUtilities.h"
#include "omni/isaac/bridge/Component.h"

#include <carb/renderer/Renderer.h>

#include <omni/fabric/FabricUSD.h>
#include <omni/fabric/IToken.h>
#include <omni/fabric/SimStageWithHistory.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/timeline/ITimeline.h>
#include <pxr/usd/usdPhysics/scene.h>
#include <rangeSensorSchema/rangeSensor.h>

#include <PrimitiveDrawingHelper.h>
#include <PxActor.h>
#include <RangeSensorInterface.h>
#if defined(_WIN32)
#    include <PxRigidDynamic.h>
#else
#    pragma GCC diagnostic push
#    pragma GCC diagnostic ignored "-Wpragmas"
#    include <PxRigidDynamic.h>
#    pragma GCC diagnostic pop
#endif
namespace isaacsim
{
namespace sensors
{
namespace physx
{

/**
 * @brief Base class which simulates a range sensor
 */
template <class PrimType>
class RangeSensorComponentBase : public isaacsim::core::utils::ComponentBase<PrimType>
{

public:
    /**
     * @brief Construct a new Isaac Component
     */
    RangeSensorComponentBase(omni::physx::IPhysx* physxPtr)
    {
        mPhysx = physxPtr;
        mTimeline = carb::getCachedInterface<omni::timeline::ITimeline>();
        mTasking = carb::getCachedInterface<carb::tasking::ITasking>();
        mToken = carb::getCachedInterface<omni::fabric::IToken>();

        mLineDrawing = std::make_shared<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(),
            isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::eLines);

        mPointDrawing = std::make_shared<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(),
            isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper::RenderingMode::ePoints);
    }
    /**
     * @brief Destroy the Range Sensor Component Base object
     *
     */
    ~RangeSensorComponentBase()
    {
        mLineDrawing.reset();
        mPointDrawing.reset();
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
        isaacsim::core::utils::ComponentBase<PrimType>::initialize(prim, stage);
        this->mRangeSensorPrim = pxr::RangeSensorRangeSensor(this->mPrim);
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
     * @brief Called before tick, sequential, used to get sensor transforms
     *
     */
    virtual void preTick(){};

    /**
     * @brief Called every frame in parallel
     *
     */
    virtual void tick() = 0;

    // check
    virtual void onPhysicsStep(){};

    /**
     * @brief Called after all sensors have simulated to perform any drawing related tasks.
     *
     */
    virtual void draw()
    {

        mLineDrawing->draw();
        mPointDrawing->draw();
    }

    /**
     * @brief Run when stop is pressed
     *
     */
    virtual void onStop()
    {
        mLineDrawing->clear();
        mPointDrawing->clear();
        mLineDrawing->draw();
        mPointDrawing->draw();
    };
    /**
     * @brief Called every time the Prim is changed
     *
     */
    virtual void onComponentChange()
    {
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetEnabledAttr(), this->mEnabled);
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetMinRangeAttr(), mMinRange);
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetMaxRangeAttr(), mMaxRange);
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetDrawPointsAttr(), mDrawPoints);
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetDrawLinesAttr(), mDrawLines);


        mParentPrim = this->mStage->GetPrimAtPath(this->mPrim.GetPath()).GetParent();
        // printf("PARENT: %s\n", mParentPrim.GetPath().GetString().c_str());
        mMetersPerUnit = static_cast<float>(UsdGeomGetStageMetersPerUnit(this->mStage));

        if (mParentPrim.IsA<pxr::UsdGeomXformable>())
        {
            std::vector<double> times;
            pxr::UsdGeomXformable(mParentPrim).GetTimeSamples(&times);

            mIsParentPrimTimeSampled = times.size() > 1;
        }
        this->mSequenceNumber = 0;
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
        isaacsim::core::utils::ComponentBase<PrimType>::updateTimestamp(timeSeconds, dt, timeNano);

        mParentPrimTimeCode = pxr::UsdTimeCode::Default();
        if (mIsParentPrimTimeSampled)
        {
            mParentPrimTimeCode = round(mTimeline->getCurrentTime() * this->mStage->GetTimeCodesPerSecond());
        }
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

    std::vector<carb::Float3>& getPointCloud()
    {
        return mLastHitPos;
    }


protected:
    bool mDrawPoints = false;
    bool mDrawLines = false;
    std::vector<carb::Float3> mLastHitPos;

    float mMinRange = 0.4f;
    float mMaxRange = 100.0f;

    float mMetersPerUnit = 1.0;


    pxr::UsdPrim mParentPrim;

    omni::physx::IPhysx* mPhysx = nullptr;
    ::physx::PxScene* mPxScene = nullptr;
    omni::timeline::ITimeline* mTimeline = nullptr;
    omni::fabric::IToken* mToken = nullptr;
    carb::tasking::ITasking* mTasking = nullptr;
    std::shared_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> mLineDrawing;
    std::shared_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> mPointDrawing;

    pxr::RangeSensorRangeSensor mRangeSensorPrim;

    pxr::UsdTimeCode mParentPrimTimeCode;
    bool mIsParentPrimTimeSampled = false;

    bool mFirstFrame = true;
};

typedef RangeSensorComponentBase<pxr::RangeSensorRangeSensor> RangeSensorComponent;

}
}
}
