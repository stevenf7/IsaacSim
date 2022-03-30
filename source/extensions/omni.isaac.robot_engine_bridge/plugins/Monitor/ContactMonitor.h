// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../Core/IsaacComponent.h"

#include <omni/isaac/contact_sensor/ContactSensor.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/physx/IPhysx.h>
#include <robotEngineBridgeSchema/robotEngineContactMonitor.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

struct ContactData
{
    std::string thisName;
    std::string otherName;
    omni::isaac::dynamic_control::DcTransform thisPose;
    omni::isaac::dynamic_control::DcTransform otherPose;
    carb::Float3 velocity;
    carb::Float3 normal;
    carb::Float3 position;
};

/**
 * @brief
 *
 */
class ContactMonitor : public IsaacComponent
{
public:
    /**
     * @brief Construct a new Contact Monitor object
     *
     */
    ContactMonitor(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    /**
     * @brief Destroy the Contact Monitor object
     *
     */
    ~ContactMonitor();
    /**
     * @brief Tick the component
     */
    virtual void tick();
    /**
     * @brief
     *
     */
    virtual void publishAllMessages();
    /**
     * @brief The rigid bodies might not be valid, so force update on start
     *
     */
    virtual void onStart();
    /**
     * @brief
     *
     */
    virtual void onComponentChange();

private:
    omni::isaac::isaac_sensor::ContactSensorInterface* mContactSensorInterface = nullptr;
    void processContact(const omni::isaac::isaac_sensor::CsRawData& data);
    omni::physx::IPhysx* mPhysxPtr = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    /// The name of the channel on which contact data is output
    std::string mOutputComponent = "output";
    std::string mOutputChannel = "bodies";
    float mForceThreshold = 100000;
    pxr::UsdPrim mTargetPrim;
    pxr::SdfPathVector mIgnoredTargets;
    // Scale of stage
    double mUnitScale;

    std::vector<ContactData> mContactData;
};
}
}
}
