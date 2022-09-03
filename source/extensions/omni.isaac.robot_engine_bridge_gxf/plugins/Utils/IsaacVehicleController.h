// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// #pragma once
// #include <omni/physx/IPhysx.h>
// #include <omni/physx/IPhysxVehicle.h>
// #include <physx/include/PxPhysicsAPI.h>
// #include <physxSchema/physxVehicleAPI.h>
// #include <physxSchema/physxVehicleWheelAPI.h>
// #include <physxSchema/physxVehicleWheelAttachmentAPI.h>
// #include <usdPhysics/massAPI.h>

// namespace omni
// {
// namespace isaac
// {
// namespace robot_engine_bridge_gxf
// {
// struct WheelFlag
// {
//     enum Enum
//     {
//         eHAS_WHEEL_CONTROLLER = (1 << 0),
//         eHAS_DRIVE = (1 << 1), // only valid for DriveType::eBASIC
//         eHAS_STEER = (1 << 2), // only valid for DriveType::eBASIC
//         eHAS_BRAKE = (1 << 3) // only valid for DriveType::eBASIC
//     };
// };

// struct DriveType
// {
//     enum Enum
//     {
//         eNONE = 0, // user wants to control wheels directly
//         eBASIC, // simple steering support and max brake/drive torque
//         eSTANDARD // full engine, gears etc. setup
//     };
// };

// struct WheelCache
// {
//     pxr::SdfPath usdPath;
//     int32_t index;
//     uint32_t wheelFlags;
//     float maxSteerAngle;
//     // float maxBrakeTorque;
//     // float maxHandBrakeTorque;
//     float mass;
//     float radius;

//     static const uint32_t sInitialWheelCapacity = 4;
// };

// // This vehicle controller assumes:
// // 4 wheels, any of which can be driven
// // Two wheels with steering with indices 0, 1 (the front two wheels)
// // TODO: No Drive associated with the vehicle, in the future this restriction should be removed.
// class VehicleController
// {
// public:
//     void Initialize(omni::physx::IPhysx* physxPtr, pxr::UsdStageWeakPtr stage, pxr::UsdPrim vehiclePrim)
//     {
//         mStage = stage;
//         // omni::physx::usdparser::IPhysxUsdLoad* mPhysxUsdLoad =
//         //     carb::getFramework()->acquireInterface<omni::physx::usdparser::IPhysxUsdLoad>();
//         mCache.vehiclePrim = vehiclePrim;

//         if (!mCache.vehiclePrim)
//         {
//             CARB_LOG_ERROR("Vehicle Prim is not valid");
//             return;
//         }


//         mPhysxPtr = physxPtr;
//         mCacheFilled = false;
//     }
//     void fillCache()
//     {
//         if (mCacheFilled)
//         {
//             return;
//         }
//         if (!mCache.vehiclePrim.HasAPI<pxr::PhysxSchemaPhysxVehicleAPI>())
//         {
//             CARB_LOG_ERROR("Vehicle Prim does not have a PhysxVehicleAPI");
//             return;
//         }
//         mCache.vehicleId = mPhysxPtr->getObjectId(mCache.vehiclePrim.GetPath(), omni::physx::PhysXType::ePTVehicle);
//         mCache.vehiclePtr = (::physx::PxVehicleNoDrive*)mPhysxPtr->getPhysXPtrFast(mCache.vehicleId);
//         if (!mCache.vehiclePtr)
//         {
//             CARB_LOG_ERROR("Vehicle Ptr not valid");
//             return;
//         }
//         mCache.wheelQueryResult =
//         (::physx::PxVehicleWheelQueryResult*)(mPhysxPtr->getWheelQueryResult(mCache.vehicleId));

//         if (!mCache.wheelQueryResult)
//         {
//             CARB_LOG_ERROR(" mCache.wheelQueryResult not valid");
//             return;
//         }

//         ::physx::PxWheelQueryResult* wheelQueryResults = mCache.wheelQueryResult->wheelQueryResults;


//         // Distance between left and right rear wheels
//         mCache.rearWidth = (wheelQueryResults[2].localPose.p - wheelQueryResults[3].localPose.p).magnitude();
//         // distance between front and rear axles
//         mCache.axleSeparation = (wheelQueryResults[0].localPose.p - wheelQueryResults[2].localPose.p).magnitude();

//         // Determine which wheels are driven
//         pxr::UsdPrimSubtreeRange subPrims = mCache.vehiclePrim.GetDescendants();
//         mCache.numDrivenWheels = 0;
//         mCache.numBrakedWheels = 0;
//         mCache.totalMass = 0;
//         for (pxr::UsdPrim subPrim : subPrims)
//         {
//             if (subPrim.HasAPI<pxr::PhysxSchemaPhysxVehicleWheelAttachmentAPI>())
//             {
//                 WheelCache wheelCache;
//                 wheelCache.usdPath = subPrim.GetPath();
//                 wheelCache.index = mPhysxPtr->getWheelIndex(wheelCache.usdPath);
//                 wheelCache.wheelFlags = 0;

//                 pxr::PhysxSchemaPhysxVehicleWheelAttachmentAPI wheelAttachmentAPI(subPrim);
//                 bool driven;
//                 wheelAttachmentAPI.GetDrivenAttr().Get(&driven);
//                 if (driven)
//                 {
//                     wheelCache.wheelFlags |= WheelFlag::eHAS_DRIVE;
//                     mCache.numDrivenWheels++;
//                 }


//                 if (subPrim.HasAPI<pxr::PhysxSchemaPhysxVehicleWheelAPI>())
//                 {
//                     pxr::UsdPrim wheelPrim = subPrim;
//                     pxr::PhysxSchemaPhysxVehicleWheelAPI wheel(wheelPrim);

//                     wheel.GetMassAttr().Get(&wheelCache.mass);
//                     mCache.totalMass += wheelCache.mass;

//                     wheel.GetRadiusAttr().Get(&wheelCache.radius);
//                     wheel.GetMaxSteerAngleAttr().Get(&wheelCache.maxSteerAngle);
//                 }
//                 else
//                 {


//                     pxr::UsdRelationship wheelRel = wheelAttachmentAPI.GetWheelRel();
//                     pxr::SdfPathVector paths;
//                     wheelRel.GetTargets(&paths);


//                     if (paths.size() != 1)
//                     {
//                         CARB_LOG_ERROR("Wheel reference not correct");
//                         return;
//                     }

//                     pxr::SdfPath wheelPath = paths[0];
//                     pxr::UsdPrim wheelPrim = mStage->GetPrimAtPath(wheelPath);
//                     pxr::PhysxSchemaPhysxVehicleWheelAPI wheel(wheelPrim);

//                     wheel.GetMassAttr().Get(&wheelCache.mass);
//                     mCache.totalMass += wheelCache.mass;

//                     wheel.GetRadiusAttr().Get(&wheelCache.radius);
//                     wheel.GetMaxSteerAngleAttr().Get(&wheelCache.maxSteerAngle);
//                 }
//                 mCache.wheels.push_back(wheelCache);
//             }
//         }

//         if (mCache.vehiclePrim.HasAPI<pxr::UsdPhysicsMassAPI>())
//         {
//             pxr::UsdPhysicsMassAPI massAPI(mCache.vehiclePrim);
//             if (massAPI.GetMassAttr())
//             {
//                 massAPI.GetMassAttr().Get(&mCache.chassisMass);
//                 CARB_LOG_INFO("Chassis mass: %f", mCache.chassisMass);
//             }
//             else
//             {
//                 mCache.chassisMass = 100;
//                 CARB_LOG_WARN("No chassis mass, using deault value of %f", mCache.chassisMass);
//             }
//             mCache.totalMass += mCache.chassisMass;
//         }

//         CARB_LOG_INFO("Vehicle Rear Width: %f, Axle Separation: %f", mCache.rearWidth, mCache.axleSeparation);
//         mCacheFilled = true;
//     }
//     float getForwardSpeed()
//     {
//         // TODO: change this to get the actual forward direction
//         return mCache.vehiclePtr->computeForwardSpeed(::physx::PxVec3(1.0, 0.0, 0.0));
//     }
//     float getCurvature()
//     {
//         return std::tan(mCurrentSteeringAngle) / mCache.axleSeparation;
//     }
//     float getWheelRotationSpeed(const size_t index)
//     {
//         return mCache.vehiclePtr->mWheelsDynData.getWheelRotationSpeed(index);
//     }
//     float getSteeringAngle()
//     {
//         return mCurrentSteeringAngle;
//     }
//     float getAxleSeparation()
//     {
//         return mCache.axleSeparation;
//     }
//     void setAckermannSteering(float steeringAngle)
//     {
//         float maxSteerAngle = (mCache.wheels)[0].maxSteerAngle;
//         mCurrentSteeringAngle = pxr::GfClamp(steeringAngle, -maxSteerAngle, maxSteerAngle);
//         float leftAngle = atan(
//             (2.0f * mCache.axleSeparation * sin(mCurrentSteeringAngle)) /
//             (2.0f * mCache.axleSeparation * cos(mCurrentSteeringAngle) - mCache.rearWidth *
//             sin(mCurrentSteeringAngle)));
//         float rightAngle = atan(
//             (2.0f * mCache.axleSeparation * sin(mCurrentSteeringAngle)) /
//             (2.0f * mCache.axleSeparation * cos(mCurrentSteeringAngle) + mCache.rearWidth *
//             sin(mCurrentSteeringAngle)));
//         // CARB_LOG_ERROR("Ackermann Angles: left: %f right: %f", leftAngle, rightAngle);

//         mCache.vehiclePtr->setSteerAngle(mCache.wheels[0].index, leftAngle);
//         mCache.vehiclePtr->setSteerAngle(mCache.wheels[1].index, rightAngle);
//     }

//     void setAcceleration(const float commandedAcceleration)
//     {
//         float driveTorque = commandedAcceleration * mCache.wheels[0].radius * mCache.totalMass /
//         mCache.numDrivenWheels; const uint32_t wheelCount = static_cast<uint32_t>(mCache.wheels.size()); for
//         (uint32_t i = 0; i < wheelCount; i++)
//         {
//             const WheelCache& wheelCache = mCache.wheels[i];

//             if (wheelCache.wheelFlags & WheelFlag::eHAS_DRIVE)
//             {
//                 mCache.vehiclePtr->setDriveTorque(wheelCache.index, driveTorque);
//             }
//         }
//     }

// private:
//     struct Cache
//     {
//         Cache()
//         {
//         }

//         size_t vehicleId;
//         pxr::UsdPrim vehiclePrim;
//         ::physx::PxVehicleNoDrive* vehiclePtr = nullptr;
//         ::physx::PxVehicleWheelQueryResult* wheelQueryResult = nullptr;
//         DriveType::Enum driveType;
//         std::vector<WheelCache> wheels;

//         float rearWidth = 0.0f;
//         float axleSeparation = 0.0f;
//         int numDrivenWheels = 0; // Lets us divide torque evenly between all driven wheels
//         int numBrakedWheels = 0; // Lets us divide torque evenly between all braked wheels
//         float chassisMass = 0.0f;
//         float totalMass = 0.0f;
//     };
//     bool mCacheFilled = false;
//     Cache mCache;
//     omni::physx::IPhysx* mPhysxPtr = nullptr;
//     pxr::UsdStageWeakPtr mStage = nullptr;
//     float mCurrentSteeringAngle = 0.0f;

//     // omni::physx::usdparser::IPhysxUsdLoad* mPhysxUsdLoad = nullptr;
// };
// }
// }
// }
