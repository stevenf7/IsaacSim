// Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "omni/isaac/bridge/BridgeApplication.h"
#include "omni/isaac/bridge/ViewportManager.h"

#include <carb/dictionary/DictionaryUtils.h>
#include <carb/logging/Log.h>
#include <carb/tasking/ITasking.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/kit/IViewport.h>
#include <rosBridgeSchema/rosBridgeComponent.h>

#include <chrono>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>


namespace omni
{
namespace isaac
{
namespace ros_base
{
template <typename PrimType>
class RosApplication : public utils::BridgeApplicationBase<PrimType>
{
public:
    RosApplication(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    {
        mDynamicControlPtr = dynamicControlPtr;
        carb::Framework* framework = carb::getFramework();
        mTasking = framework->acquireInterface<carb::tasking::ITasking>();
        mTaskCounter = mTasking->createCounter();
        mViewportInterface = framework->acquireInterface<omni::kit::IViewport>();
    }

    /**
     * @brief Destroy the Isaac Application object
     *
     */
    virtual ~RosApplication()
    {
        mTasking->yieldUntilCounter(mTaskCounter);
        mTasking->destroyCounter(mTaskCounter);

        this->deleteAllComponents();
    }

    /**
     * @brief Initialize this application
     *
     * @param stage
     */
    virtual void initialize(pxr::UsdStageWeakPtr stage)
    {

        utils::BridgeApplicationBase<PrimType>::initialize(stage);
        mViewportManager = std::make_unique<utils::ViewportManager>(mViewportInterface);
    }


    virtual void tick(double dt)
    {
        CARB_PROFILE_ZONE(0, "Isaac ROS Bridge Tick");
        // System time is calculated the start of the frame
        mSystemTimeNanoSeconds =
            std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();

        for (auto& component : this->mComponents)
        {
            if (component.second->mDoStart == true)
            {
                // if the component has not started yet, check to see if its enabled
                // if not enabled, do not start
                component.second->PrimType::onComponentChange();
                if (component.second->getEnabled())
                {
                    component.second->onStart();
                    component.second->mDoStart = false;
                }
            }
        }

        for (auto& component : this->mComponents)
        {
            component.second.get()->updateTimestamp(
                this->mTimeSeconds, dt, this->mTimeNanoSeconds, mSystemTimeNanoSeconds);
        }

        for (auto& component : this->mComponents)
        {
            if (component.second->getEnabled())
            {
                component.second->tick();
            }
        }
        this->mTimeSeconds += dt;
        this->mTimeNanoSeconds = this->mTimeSeconds * 1e9;
    }
    /**
     * @brief Call stop on all components to do any cleanup
     *
     */
    virtual void onStop()
    {
        for (auto& component : this->mComponents)
        {
            component.second->onStop();
            component.second->mDoStart = true;
        }
    }
    /**
     * @brief Create a supported component in this application
     *
     * @param prim
     */
    virtual void onComponentAdd(const pxr::UsdPrim& prim) = 0;
    /**
     * @brief Call any components that are only updated when physics steps occur
     *
     * @param dt
     */
    virtual void onPhysicsStep(float dt)
    {
        if (mUsePhysicsStepSimTime)
        {
            mSystemTimeNanoSeconds =
                std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch())
                    .count();
        }
        for (auto& component : this->mComponents)
        {
            component.second->updatePhysicsTimestamp(mPhysicsTimeSeconds, dt);
            component.second->onPhysicsStep(dt);
        }
        mPhysicsTimeSeconds += dt;
    }

    /**
     * @brief Set the Ros State object
     *
     * @param state
     */
    virtual void setRosState(const bool state)
    {
        mROSInitialize = state;
    }
    /**
     * @brief Get the Ros State object
     *
     */
    virtual bool getRosState()
    {
        return mROSInitialize;
    }
    /**
     * @brief Use sim time or system time for components
     *
     * @param useSimTime
     */
    virtual void setUseSimTime(const bool useSimTime)
    {
        mUseSimTime = useSimTime;
        for (auto& component : this->mComponents)
        {
            component.second.get()->setUseSimTime(mUseSimTime);
        }
    }


    /**
     * @brief Use physics step for sim time
     *
     * @param useSimTime
     */
    void setUsePhysicsStepSimTime(const bool usePhysicsStepSimTime)
    {
        mUsePhysicsStepSimTime = usePhysicsStepSimTime;
        for (auto& component : this->mComponents)
        {
            component.second.get()->setUsePhysicsStepSimTime(mUseSimTime);
        }
    }


    /**
     * @brief Ticks a specific ROS component
     *
     * @param prim
     * @return true
     * @return false
     */
    virtual bool tickComponent(const pxr::UsdPrim& prim)
    {
        if (prim)
        {
            if (this->mComponents.find(prim.GetPath().GetString()) != this->mComponents.end())
            {
                auto* component = this->mComponents[prim.GetPath().GetString()].get();


                if (component->mDoStart == true)
                {
                    component->onStart();
                    component->mDoStart = false;
                }

                component->tick();
                return true;
            }
        }
        return false;
    }

protected:
    std::string mAppFilename;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    carb::tasking::ITasking* mTasking = nullptr;
    carb::tasking::Counter* mTaskCounter = nullptr;

    omni::kit::IViewport* mViewportInterface = nullptr;
    std::unique_ptr<utils::ViewportManager> mViewportManager = nullptr;
    double mPhysicsTimeSeconds = 0;

    int64_t mTimeDifferenceNanoSeconds = 0;
    bool mROSInitialize = true;
    std::chrono::_V2::system_clock::rep mSystemTimeNanoSeconds = 0;
    bool mUseSimTime = true;
    bool mUsePhysicsStepSimTime = false;
};
}
}
}
