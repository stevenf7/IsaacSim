// // Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// // clang-format off
// #include <UsdPCH.h>
// // clang-format on

// #include "VehicleSimulator.h"

// #include "../Core/GxfComponent.h"
// #include "gems/control_types/ackermann_drive.hpp"

// #include <carb/InterfaceUtils.h>
// #include <carb/filesystem/IFileSystem.h>
// #include <carb/profiler/Profile.h>

// #include <omni/isaac/dynamic_control/DynamicControl.h>
// #include <omni/isaac/utils/Conversions.h>
// #include <omni/usd/UsdUtils.h>
// #include <omni/usd/UtilsIncludes.h>
// #include <physx/include/PxPhysicsAPI.h>

// #include <string>
// #include <vector>


// namespace omni
// {
// namespace isaac
// {
// using utils::conversions::asGfRotation;
// using utils::conversions::asGfVec3d;
// namespace robot_engine_bridge_gxf
// {

// VehicleSimulator::VehicleSimulator() : GxfComponent()
// {

//     mPhysxPtr = carb::getCachedInterface<omni::physx::IPhysx>();
//     if (!mPhysxPtr)
//     {
//         CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
//         return;
//     }

//     // mPhysxVehiclePtr = carb::getCachedInterface<omni::physx::IPhysxVehicle>();
//     // if (!mPhysxVehiclePtr)
//     // {
//     //     CARB_LOG_ERROR("*** Failed to acquire PhysXVehicle interface\n");
//     //     return;
//     // }
// }


// void VehicleSimulator::onStart()
// {
//     // mZUp = UsdGeomGetStageUpAxis(mStage) == "Z" ? true : false;
//     mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
//     onComponentChange();
// }

// void VehicleSimulator::onStop()
// {
//     mAveragedAcceleration.clear();
//     mPrevForwardSpeed = 0;
// }
// void VehicleSimulator::tick()
// {
//     CARB_PROFILE_ZONE(0, "REB VehicleSimulator Tick");

//     if (!mVehiclePrim)
//     {
//         CARB_LOG_ERROR("Vehicle Prim is not valid");
//         return;
//     }

//     mVehicleController.fillCache();

//     {
//         float forwardSpeed = mVehicleController.getForwardSpeed();
//         float accel = (forwardSpeed - mPrevForwardSpeed) / mTimeDelta;
//         if (mAveragedAcceleration.size() > static_cast<size_t>(mMovingAverageSize))
//         {
//             mAveragedAcceleration.pop_front();
//         }
//         mAveragedAcceleration.push_back(accel);

//         mPrevForwardSpeed = forwardSpeed;

//         mForwardAcceleration = 0;
//         for (size_t i = 0; i < mAveragedAcceleration.size(); i++)
//         {
//             mForwardAcceleration += mAveragedAcceleration[i];
//         }
//         mForwardAcceleration /= mAveragedAcceleration.size();
//     }

//     {
//         // Receive current command
//         auto message = nvidia::gxf::Entity::New(mContext);

//         if (receive(mInputComponent, mCommandChannelName, message) == gxf_result_t::GXF_SUCCESS)
//         {
//             auto maybe_message_parts = nvidia::isaac::ParseCompositeMessage(std::move(message.value()));

//             if (maybe_message_parts)
//             {
//                 nvidia::isaac::AckermannControlConstView<double> control;
//                 control.pointer = maybe_message_parts.value().view.element_wise_begin();

//                 // mCommandedSpeed[0] = pxr::GfClamp(elements[0], -mMaximumSpeed[0], mMaximumSpeed[0]);
//                 // mCommandedSpeed[1] = pxr::GfClamp(elements[1], -mMaximumSpeed[1], mMaximumSpeed[1]);

//                 // mLastCommandTime = mTimeSeconds;

//                 // CARB_LOG_ERROR("Received %f %f %d %d", elements[0], elements[1], buffers.size(),
//                 // elements.size());

//                 // Use latest command only for a certain period of time in case no new command arrives
//                 // if (mTimeSeconds - mLastCommandTime > mMaximumTimeWithoutCommand)
//                 // {
//                 //     mCommandedSpeed = pxr::GfVec2d(0, 0);
//                 // }

//                 // const float signMultiplier = mInReverse ? -1.0f : 1.0f;
//                 const float requestedAcceleration = control.acceleration() / mUnitScale; // m/s^2 -> cm/s^2

//                 // CARB_LOG_ERROR("Chassis speed forward %f cm/s, computed forward accel: %f cm/s^2",
//                 // mPrevForwardSpeed,
//                 //                mForwardAcceleration);

//                 float commandedAcceleration = requestedAcceleration;
//                 if (mUsePID)
//                 {
//                     commandedAcceleration =
//                         mPID->update(requestedAcceleration, mForwardAcceleration, mPrevForwardAcceleration);
//                 }
//                 // steering angle in radians
//                 double steeringAngle =
//                     std::atan(control.curvature() * double(mVehicleController.getAxleSeparation())); // convert from
//                                                                                                      // turning
//                                                                                                      radius
//                                                                                                      // to angle
//                 mVehicleController.setAckermannSteering(steeringAngle);
//                 mVehicleController.setAcceleration(commandedAcceleration);
//             }
//             else
//             {
//                 {
//                     // return maybe_message_parts.error();
//                     CARB_LOG_WARN("AckermannControlView Message Could Not Be Parsed");
//                     return;
//                 }
//             }
//         }
//     }

//     {
//         std::string path = mVehiclePath.GetString();
//         auto maybeUid = mPoseTreeMap->findOrCreateNamedFrame(path);
//         if (!maybeUid)
//         {
//             CARB_LOG_WARN("Cannot find pose uid for vehicle %s", path.c_str());
//             return;
//         }

//         auto maybe_message = nvidia::gxf::Entity::New(mContext);

//         auto maybe_message_parts =
//             nvidia::isaac::PrepareCompositeMessage(mContext, mAllocator->cid(), maybe_message.value().eid(), 1,
//                                                    nvidia::isaac::AckermannDynamicState<double>::kDimension, false);
//         maybe_message_parts.value().timestamp->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
//         maybe_message_parts.value().timestamp->pubtime = ::isaac::NowCount();
//         maybe_message_parts.value().pose_frame_uid->uid = maybeUid.value();
//         // maybe_message_parts.value().composite_schema_uid = 0;

//         nvidia::isaac::AckermannDynamicStateView<double> state_view;
//         state_view.pointer = maybe_message_parts.value().view.element_wise_begin();

//         state_view.speed() = double(mPrevForwardSpeed);
//         state_view.acceleration() = double(mForwardAcceleration);
//         state_view.curvature() = double(mVehicleController.getCurvature());
//         state_view.curvature_derivative() = 0.0;

//         publish(mOutputComponent, mStateChannelName, std::move(maybe_message.value()));
//     }

//     mPrevForwardAcceleration = mForwardAcceleration;
// }

// void VehicleSimulator::onComponentChange()
// {
//     GxfComponent::onComponentChange();

//     const pxr::RobotEngineBridgeSchemaRobotEngineVehicle& typedPrim =
//         (pxr::RobotEngineBridgeSchemaRobotEngineVehicle)mPrim;

//     // Parse component and channel
//     isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
//     isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mCommandChannelName);
//     isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
//     isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mStateChannelName);

//     std::string wheelFLName;
//     std::string wheelFRName;

//     pxr::SdfPathVector targets;
//     typedPrim.GetVehiclePrimRel().GetTargets(&targets);
//     if (targets.size() == 0)
//     {
//         return;
//     }

//     mVehiclePath = targets[0];
//     mVehiclePrim = mStage->GetPrimAtPath(mVehiclePath);

//     isaac::utils::safeGetAttribute(typedPrim.GetHistoryLengthAttr(), mMovingAverageSize);
//     isaac::utils::safeGetAttribute(typedPrim.GetUsePIDAttr(), mUsePID);

//     mAveragedAcceleration.clear(); // clear this in case the requested average moving size was changed.

//     if (mUsePID)
//     {
//         pxr::GfVec3f pidValues;
//         isaac::utils::safeGetAttribute(typedPrim.GetControllerPIDValuesAttr(), pidValues);
//         mPID = std::make_unique<utils::PIDController>(pidValues[0], pidValues[1], pidValues[2]);
//     }

//     mVehicleController.Initialize(mPhysxPtr, mStage, mVehiclePrim);
// }
// }
// }
// }
