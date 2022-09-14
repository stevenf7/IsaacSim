// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// #pragma once
// #include "../Core/GxfComponent.h"
// #include "../Utils/IsaacVehicleController.h"
// #include "omni/isaac/utils/PIDController.h"

// #include <omni/isaac/dynamic_control/DynamicControl.h>
// #include <omni/physx/IPhysx.h>
// #include <omni/physx/IPhysxVehicle.h>
// #include <physx/include/PxPhysicsAPI.h>
// #include <robotEngineBridgeSchema/robotEngineVehicle.h>

// #include <deque>
// #include <string>

// namespace omni
// {
// namespace isaac
// {
// namespace gxf_bridge
// {

// /**
//  * @brief A simulated differential-base driver based on speed commands.
//  *
//  */
// class VehicleSimulator : public GxfComponent
// {
// public:
//     VehicleSimulator();
//     /**
//      * @brief The articulation for the robot might not be valid, so force update on start
//      *
//      */
//     virtual void onStart();

//     virtual void onStop();

//     /**
//      * @brief Get latest command message and publish ground truth data
//      *
//      */
//     virtual void tick();
//     /**
//      * @brief Update the properties of this component based on any USD changes
//      *
//      */
//     virtual void onComponentChange();


// private:
//     pxr::SdfPath mVehiclePath;
//     pxr::UsdPrim mVehiclePrim;
//     double mUnitScale;

//     /// The name of the channel on which commands are received
//     std::string mInputComponent = "input";
//     std::string mCommandChannelName = "vehicle_command";

//     /// The name of the channel on which state informations is published
//     std::string mOutputComponent = "output";
//     std::string mStateChannelName = "vehicle_state";

//     omni::physx::IPhysx* mPhysxPtr = nullptr;
//     // omni::physx::IPhysxVehicle* mPhysxVehiclePtr = nullptr;

//     const float mReverseTime = 0.5f;
//     const float mReverseSpeed = 1.0f;
//     bool mInReverse = false;
//     float mBrakeTimer = 0.0f;

//     float mPrevForwardSpeed = 0;
//     float mForwardAcceleration = 0;
//     float mPrevForwardAcceleration = 0;
//     std::deque<float> mAveragedAcceleration;
//     int mMovingAverageSize = 200;

//     std::unique_ptr<utils::PIDController> mPID;
//     bool mUsePID = false;

//     VehicleController mVehicleController;
// };
// }
// }
// }
