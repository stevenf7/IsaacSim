// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
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
 * @class RangeSensorComponentBase
 * @brief Base class which simulates a range sensor
 * @details This template class provides the core functionality for range-based sensors,
 *          including initialization, lifecycle management, and data processing. It handles
 *          sensor transforms, visualization, and interaction with the physics simulation.
 * @tparam PrimType The USD prim type associated with this sensor component
 */
template <class PrimType>
class RangeSensorComponentBase : public isaacsim::core::utils::ComponentBase<PrimType>
{

public:
    /**
     * @brief Constructs a new Isaac Component
     * @param[in] physxPtr Pointer to the PhysX interface for physics simulation
     * @details Initializes the component with necessary interfaces and creates visualization helpers
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
     * @brief Destroys the Range Sensor Component Base object
     * @details Cleans up visualization resources
     */
    ~RangeSensorComponentBase()
    {
        mLineDrawing.reset();
        mPointDrawing.reset();
    }

    /**
     * @brief Initializes various pointers and handles in the component
     * @details Must be called after creation, can be overridden to initialize subcomponents
     * @param[in] prim The USD prim representing this sensor
     * @param[in] stage The USD stage containing the sensor prim
     */
    virtual void initialize(const PrimType& prim, pxr::UsdStageWeakPtr stage)
    {
        isaacsim::core::utils::ComponentBase<PrimType>::initialize(prim, stage);
        this->mRangeSensorPrim = pxr::RangeSensorRangeSensor(this->mPrim);
    }

    /**
     * @brief Function that runs after start is pressed
     * @details Initializes the component and locates the PhysX scene for sensor operations
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
     * @details Empty base implementation that can be overridden by derived classes
     */
    virtual void preTick(){};

    /**
     * @brief Called every frame in parallel
     * @details Pure virtual function that must be implemented by derived classes to
     *          perform the main sensor update during each simulation frame
     */
    virtual void tick() = 0;

    /**
     * @brief Called after each physics step to update sensor data
     * @details This function is called after each physics simulation step to process and update
     *          the range sensor data based on the latest physics state
     */
    virtual void onPhysicsStep(){};

    /**
     * @brief Called after all sensors have simulated to perform any drawing related tasks
     * @details Renders the debug visualization for both points and lines if enabled
     */
    virtual void draw()
    {
        mLineDrawing->draw();
        mPointDrawing->draw();
    }

    /**
     * @brief Run when stop is pressed
     * @details Clears all visualization data and ensures it's properly rendered
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
     * @details Updates component properties from the USD prim attributes and
     *          refreshes transform-related data
     */
    virtual void onComponentChange()
    {
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetEnabledAttr(), this->mEnabled);
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetMinRangeAttr(), mMinRange);
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetMaxRangeAttr(), mMaxRange);
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetDrawPointsAttr(), mDrawPoints);
        isaacsim::core::utils::safeGetAttribute(this->mRangeSensorPrim.GetDrawLinesAttr(), mDrawLines);

        mParentPrim = this->mStage->GetPrimAtPath(this->mPrim.GetPath()).GetParent();
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
     * @brief Updates timestamps for component
     * @param[in] timeSeconds Current simulation time in seconds
     * @param[in] dt Time step duration in seconds
     * @param[in] timeNano Current simulation time in nanoseconds
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
     * @brief Gets the draw points visualization state
     * @return True if point visualization is enabled, false otherwise
     */
    bool getDrawPoints()
    {
        return mDrawPoints;
    }

    /**
     * @brief Gets the draw lines visualization state
     * @return True if line visualization is enabled, false otherwise
     */
    bool getDrawLines()
    {
        return mDrawLines;
    }

    /**
     * @brief Gets the latest point cloud data from the range sensor
     * @details Returns a reference to the vector containing the most recent hit positions
     *          detected by the range sensor. Each point represents a detected surface in 3D space.
     * @return Reference to vector of 3D points representing the latest point cloud data
     */
    std::vector<carb::Float3>& getPointCloud()
    {
        return mLastHitPos;
    }

protected:
    /** @brief Flag to enable/disable point visualization */
    bool mDrawPoints = false;
    /** @brief Flag to enable/disable line visualization */
    bool mDrawLines = false;
    /** @brief Vector storing the most recent hit positions from the sensor */
    std::vector<carb::Float3> mLastHitPos;

    /** @brief Minimum range of the sensor in meters */
    float mMinRange = 0.4f;
    /** @brief Maximum range of the sensor in meters */
    float mMaxRange = 100.0f;

    /** @brief Conversion factor from scene units to meters */
    float mMetersPerUnit = 1.0;

    /** @brief Reference to the parent USD prim containing this sensor */
    pxr::UsdPrim mParentPrim;

    /** @brief Pointer to the PhysX interface */
    omni::physx::IPhysx* mPhysx = nullptr;
    /** @brief Pointer to the PhysX scene */
    ::physx::PxScene* mPxScene = nullptr;
    /** @brief Pointer to the timeline interface */
    omni::timeline::ITimeline* mTimeline = nullptr;
    /** @brief Pointer to the fabric token interface */
    omni::fabric::IToken* mToken = nullptr;
    /** @brief Pointer to the tasking interface */
    carb::tasking::ITasking* mTasking = nullptr;
    /** @brief Helper for drawing debug lines */
    std::shared_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> mLineDrawing;
    /** @brief Helper for drawing debug points */
    std::shared_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> mPointDrawing;

    /** @brief Reference to the range sensor USD prim */
    pxr::RangeSensorRangeSensor mRangeSensorPrim;

    /** @brief Time code for the parent prim's current state */
    pxr::UsdTimeCode mParentPrimTimeCode;
    /** @brief Flag indicating if the parent prim has time-sampled transforms */
    bool mIsParentPrimTimeSampled = false;

    /** @brief Flag indicating if this is the first frame */
    bool mFirstFrame = true;
};

/**
 * @typedef RangeSensorComponent
 * @brief Convenience typedef for a range sensor component using the RangeSensorRangeSensor prim type
 */
typedef RangeSensorComponentBase<pxr::RangeSensorRangeSensor> RangeSensorComponent;

}
}
}
