// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "IsaacComponent.h"
#include "RosNode.h"
#include "plugins/bridge/BridgeApplication.h"
#include "plugins/core/ViewportManager.h"

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
namespace ros2_bridge
{
class IsaacApplication : public utils::BridgeApplicationBase<IsaacComponent>
{
public:
    /**
     * @brief Construct a new Isaac Application object
     *
     * @param isaacCApiPtr
     * @param dynamicControlPtr
     */
    IsaacApplication(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);

    /**
     * @brief Destroy the Isaac Application object
     *
     */
    ~IsaacApplication();

    /**
     * @brief Initialize this application
     *
     * @param stage
     */
    virtual void initialize(pxr::UsdStageWeakPtr stage);


    void tick(double dt);
    /**
     * @brief Call stop on all components to do any cleanup
     *
     */
    void onStop();
    /**
     * @brief Create a supported component in this application
     *
     * @param prim
     */
    void onComponentAdd(const pxr::UsdPrim& prim);

    /**
     * @brief Set the Ros State object
     *
     * @param state
     */
    void setRosState(const bool state)
    {
        mROSInitialize = state;
    }
    /**
     * @brief Get the Ros State object
     *
     */
    bool getRosState()
    {
        return mROSInitialize;
    }

    void setUseSimTime(const bool useSimTime);

    /**
     * @brief Ticks a specific ROS component
     *
     * @param prim
     * @return true
     * @return false
     */
    bool tickComponent(const pxr::UsdPrim& prim);

private:
    RosNode* getRosNode(const pxr::UsdPrim& prim);
    std::string mAppFilename;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    carb::tasking::ITasking* mTasking = nullptr;
    carb::tasking::Counter* mTaskCounter = nullptr;
    omni::kit::IViewport* mViewportInterface = nullptr;
    std::unique_ptr<utils::ViewportManager> mViewportManager = nullptr;

    int64_t mTimeDifferenceNanoSeconds = 0;
    bool mROSInitialize = true;
    std::chrono::_V2::system_clock::rep mSystemTimeNanoSeconds = 0;
    bool mUseSimTime = true;
};
}
}
}
