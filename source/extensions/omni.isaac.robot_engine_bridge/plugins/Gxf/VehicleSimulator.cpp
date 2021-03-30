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

#include <omni/isaac/dynamic_control/DynamicControl.h>

#include <string>
#include <vector>
#include <carb/InterfaceUtils.h>
#include <carb/profiler/Profile.h>
#include <carb/filesystem/IFileSystem.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

#include "../Core/GxfComponent.h"
#include <omni/isaac/utils/Conversions.h>
#include "VehicleSimulator.h"

#include <physx/include/PxPhysicsAPI.h>

#include <usdPhysics/massAPI.h>
#include <physxSchema/physxVehicleAPI.h>
#include <physxSchema/physxVehicleDriveBasic.h>
#include <physxSchema/physxVehicleDriveStandard.h>
#include <physxSchema/physxVehicleWheel.h>
#include <physxSchema/physxVehicleWheelAttachmentAPI.h>
#include <physxSchema/physxVehicleWheelControllerAPI.h>
#include <physxSchema/physxVehicleGlobalSettings.h>

#include "gems/control_types/ackermann_drive.hpp"


namespace omni
{
namespace isaac
{
using utils::conversions::asGfRotation;
using utils::conversions::asGfVec3d;
namespace robot_engine_bridge
{
namespace gxf_bridge
{
// static ::physx::PxVehicleWheels* getVehicleNoCheck(const pxr::SdfPath& vehiclePath,
//                                                    omni::physx::IPhysx* physxInterface,
//                                                    size_t& vehicleId)
// {
//     vehicleId = physxInterface->getObjectId(vehiclePath, omni::physx::PhysXType::ePTVehicle);
//     ::physx::PxVehicleWheels* physxVehicle =
//         reinterpret_cast<::physx::PxVehicleWheels*>(physxInterface->getPhysXPtrFast(vehicleId));
//     CARB_ASSERT(physxVehicle);
//     return physxVehicle;
// }

// static ::physx::PxVehicleWheels* getVehicleWithErrorLog(const pxr::SdfPath& vehiclePath,
//                                                         omni::physx::IPhysx* physxInterface,
//                                                         pxr::UsdStageRefPtr usdStage,
//                                                         const char* functionNameForErrorMsg)
// {
//     pxr::UsdPrim vehiclePrim = usdStage->GetPrimAtPath(vehiclePath);

//     if (vehiclePrim)
//     {
//         if (vehiclePrim.HasAPI<pxr::PhysxSchemaPhysxVehicleAPI>())
//         {
//             size_t vehicleId;
//             return getVehicleNoCheck(vehiclePath, physxInterface, vehicleId);
//         }
//         else
//         {
//             CARB_LOG_ERROR("PhysX Vehicle: %s: prim at \"%s\" must have API schema \"PhysxVehicleAPI\" applied\n",
//                            functionNameForErrorMsg, vehiclePath.GetText());
//         }
//     }
//     else
//     {
//         CARB_LOG_ERROR("PhysX Vehicle: %s: no prim at path \"%s\"\n", functionNameForErrorMsg,
//         vehiclePath.GetText());
//     }

//     return nullptr;
// }
template <typename T>
static void cacheWheelIndices(std::vector<T>& wheelCacheList, const size_t vehicleId, omni::physx::IPhysx* physXInterface)
{
    const uint32_t wheelCount = static_cast<uint32_t>(wheelCacheList.size());
    uint32_t currentIndex = 0;
    for (uint32_t i = 0; i < wheelCount; i++)
    {
        T& wheelCache = wheelCacheList[currentIndex];

        const int32_t index = physXInterface->getWheelIndex(wheelCache.usdPath);
        if (index >= 0)
        {
            wheelCache.index = index;
            currentIndex++;
        }
        else
        {
            CARB_LOG_ERROR("PhysX Vehicle: failed to get index for wheel attachment at path \"%s\"\n",
                           wheelCache.usdPath.GetText());

            wheelCacheList[currentIndex] = wheelCacheList.back();
            wheelCacheList.pop_back();
        }
    }
}

VehicleSimulator::VehicleSimulator() : GxfComponent()
{

    mPhysxPtr = carb::getFramework()->acquireInterface<omni::physx::IPhysx>();
    if (!mPhysxPtr)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }

    // mPhysxVehiclePtr = carb::getFramework()->acquireInterface<omni::physx::IPhysxVehicle>();
    // if (!mPhysxVehiclePtr)
    // {
    //     CARB_LOG_ERROR("*** Failed to acquire PhysXVehicle interface\n");
    //     return;
    // }
}


void VehicleSimulator::onStart()
{
    // mZUp = UsdGeomGetStageUpAxis(mStage) == "Z" ? true : false;
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    onComponentChange();
}

void VehicleSimulator::onStop()
{
    mAveragedAcceleration.clear();
    if (mCache.wheels)
    {
        delete mCache.wheels;
    }
    mCache = Cache();
    mPrevForwardSpeed = 0;
    mCurrentSteeringAngle = 0;
}
void VehicleSimulator::setAckermannSteering(const float steeringAngle, const int leftWheel, const int rightWheel)
{

    ::physx::PxVehicleNoDrive* vehicleNoDrive = static_cast<::physx::PxVehicleNoDrive*>(mCache.mVehiclePtr);

    float leftAngle = atan((2.0f * mCache.axleSeparation * sin(steeringAngle)) /
                           (2.0f * mCache.axleSeparation * cos(steeringAngle) - mCache.rearWidth * sin(steeringAngle)));
    float rightAngle = atan((2.0f * mCache.axleSeparation * sin(steeringAngle)) /
                            (2.0f * mCache.axleSeparation * cos(steeringAngle) + mCache.rearWidth * sin(steeringAngle)));
    // CARB_LOG_ERROR("Ackermann Angles: left: %f right: %f", leftAngle, rightAngle);

    vehicleNoDrive->setSteerAngle(leftWheel, leftAngle);
    vehicleNoDrive->setSteerAngle(rightWheel, rightAngle);
}
void VehicleSimulator::tick()
{
    CARB_PROFILE_ZONE(0, "REB VehicleSimulator Tick");
    fillCache();
    if (mCache.state != CacheStateFlag::eVALID)
    {
        return;
    }

    if (mCache.driveType != DriveType::eNONE)
    {
        CARB_LOG_ERROR("Only None Drive is supportred currently");
        return;
    }
    else
    {
        ::physx::PxVehicleNoDrive* vehicleNoDrive = static_cast<::physx::PxVehicleNoDrive*>(mCache.mVehiclePtr);
        ::physx::PxRigidDynamic* dynamicActor = vehicleNoDrive->getRigidDynamicActor();
        // float speed = dynamicActor->getLinearVelocity().magnitude() *
        // (float)pxr::UsdGeomGetStageMetersPerUnit(mStage);

        const ::physx::PxTransform vehicleChassisTrnsfm =
            dynamicActor->getGlobalPose().transform(dynamicActor->getCMassLocalPose());
        float forwardSpeed = dynamicActor->getLinearVelocity().dot(vehicleChassisTrnsfm.q.rotate(mCache.forward));
        float accel = (forwardSpeed - mPrevForwardSpeed) / mTimeDelta;
        if (mAveragedAcceleration.size() > static_cast<size_t>(mMovingAverageSize))
        {
            mAveragedAcceleration.pop_front();
        }
        mAveragedAcceleration.push_back(accel);

        mPrevForwardSpeed = forwardSpeed;

        mForwardAcceleration = 0;
        for (size_t i = 0; i < mAveragedAcceleration.size(); i++)
        {
            mForwardAcceleration += mAveragedAcceleration[i];
        }
        mForwardAcceleration /= mAveragedAcceleration.size();
    }

    {
        // Receive current command
        auto message = nvidia::gxf::Entity::New(mContext);

        if (receive(mInputComponent, mCommandChannelName, message) == gxf_result_t::GXF_SUCCESS)
        {
            auto maybe_message_parts = nvidia::isaac::ParseCompositeMessage(message.value());

            if (maybe_message_parts)
            {
                nvidia::isaac::AckermannControlConstView<double> control;
                control.pointer = maybe_message_parts.value().view.element_wise_begin();

                // mCommandedSpeed[0] = pxr::GfClamp(elements[0], -mMaximumSpeed[0], mMaximumSpeed[0]);
                // mCommandedSpeed[1] = pxr::GfClamp(elements[1], -mMaximumSpeed[1], mMaximumSpeed[1]);

                // mLastCommandTime = mTimeSeconds;

                // CARB_LOG_ERROR("Received %f %f %d %d", elements[0], elements[1], buffers.size(),
                // elements.size());

                // Use latest command only for a certain period of time in case no new command arrives
                // if (mTimeSeconds - mLastCommandTime > mMaximumTimeWithoutCommand)
                // {
                //     mCommandedSpeed = pxr::GfVec2d(0, 0);
                // }

                ::physx::PxVehicleNoDrive* vehicleNoDrive = static_cast<::physx::PxVehicleNoDrive*>(mCache.mVehiclePtr);
                // const float signMultiplier = mInReverse ? -1.0f : 1.0f;
                const float requestedAcceleration = control.acceleration() / mUnitScale; // m/s^2 -> cm/s^2

                // CARB_LOG_ERROR("Chassis speed forward %f cm/s, computed forward accel: %f cm/s^2",
                // mPrevForwardSpeed,
                //                mForwardAcceleration);

                float commandedAcceleration = requestedAcceleration;
                if (mUsePID)
                {
                    commandedAcceleration =
                        mPID->update(requestedAcceleration, mForwardAcceleration, mPrevForwardAcceleration);
                }
                float driveTorque = 0;

                driveTorque =
                    commandedAcceleration * (*mCache.wheels)[0].radius * mCache.totalMass / mCache.numDrivenWheels;

                // CARB_LOG_INFO("requested acceleration: %f commanded %f, drive torque: %f", requestedAcceleration,
                //               commandedAcceleration, driveTorque);


                // steering angle in radians
                float maxSteerAngle = (*mCache.wheels)[0].maxSteerAngle;
                double steeringAngle = std::atan(control.curvature() * double(mCache.axleSeparation)); // convert from
                                                                                                       // turning radius
                                                                                                       // to angle
                mCurrentSteeringAngle = pxr::GfClamp(steeringAngle, double(-maxSteerAngle), double(maxSteerAngle));
                setAckermannSteering(mCurrentSteeringAngle, (*mCache.wheels)[0].index, (*mCache.wheels)[1].index);

                const uint32_t wheelCount = static_cast<uint32_t>(mCache.wheels->size());
                for (uint32_t i = 0; i < wheelCount; i++)
                {
                    const WheelCache& wheelCache = (*mCache.wheels)[i];

                    if (wheelCache.wheelFlags & WheelFlag::eHAS_DRIVE)
                    {
                        vehicleNoDrive->setDriveTorque(wheelCache.index, driveTorque);
                    }
                }
            }
            else
            {
                {
                    // return maybe_message_parts.error();
                    CARB_LOG_WARN("AckermannControlView Message Could Not Be Parsed");
                    return;
                }
            }
        }
    }

    {
        std::string path = mVehiclePath.GetString();
        auto maybeUid = mPoseTreeMap->findFrame(path);
        if (!maybeUid)
        {
            CARB_LOG_WARN("Cannot find pose uid for vehicle %s", path.c_str());
            return;
        }

        auto maybe_message = nvidia::gxf::Entity::New(mContext);

        auto maybe_message_parts =
            nvidia::isaac::PrepareCompositeMessage(mContext, mAllocator->cid(), maybe_message.value().eid(), 1,
                                                   nvidia::isaac::AckermannDynamicState<double>::kDimension, false);
        maybe_message_parts.value().timestamp->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
        maybe_message_parts.value().timestamp->pubtime = ::isaac::NowCount();
        maybe_message_parts.value().pose_frame_uid->uid = maybeUid.value();
        // maybe_message_parts.value().composite_schema_uid = 0;

        nvidia::isaac::AckermannDynamicStateView<double> state_view;
        state_view.pointer = maybe_message_parts.value().view.element_wise_begin();

        state_view.speed() = double(mPrevForwardSpeed);
        state_view.acceleration() = double(mForwardAcceleration);
        state_view.curvature() = double(std::tan(mCurrentSteeringAngle) / mCache.axleSeparation);
        state_view.curvature_derivative() = 0.0;

        publish(mOutputComponent, mStateChannelName, std::move(maybe_message.value()));
    }

    mPrevForwardAcceleration = mForwardAcceleration;
}

void VehicleSimulator::fillCache()
{

    if (mCache.state == CacheStateFlag::eVALID)
    {
        return;
    }
    bool success = true;

    // Locate the Global Vehicle Settings to get forward axis
    pxr::UsdPrimRange range = mStage->Traverse();
    for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;

        if (prim.IsA<pxr::PhysxSchemaPhysxVehicleGlobalSettings>())
        {
            pxr::PhysxSchemaPhysxVehicleGlobalSettings vehicleGlobalSettings(prim);
            pxr::GfVec3f forward;
            if (vehicleGlobalSettings.GetForwardAxisAttr())
            {
                vehicleGlobalSettings.GetForwardAxisAttr().Get(&forward);
                mCache.forward = ::physx::PxVec3(forward[0], forward[1], forward[2]);
            }
        }
    }
    if (!mVehiclePrim)
    {
        CARB_LOG_ERROR("Vehicle Prim is not valid");
        return;
    }

    if (!mVehiclePrim.HasAPI<pxr::PhysxSchemaPhysxVehicleAPI>())
    {
        CARB_LOG_ERROR("Vehicle Prim does not have a PhysxVehicleAPI");
        return;
    }


    // pxr::PhysxSchemaPhysxVehicleAPI vehicleAPI(mVehiclePrim);

    // pxr::UsdRelationship driveRel = vehicleAPI.GetDriveRel();
    // if (driveRel)
    // {
    //     pxr::SdfPathVector paths;
    //     driveRel.GetTargets(&paths);
    //     if (paths.size() == 1)
    //     {
    //         pxr::SdfPath drivePath = paths[0];
    //         pxr::UsdPrim drivePrim = mStage->GetPrimAtPath(drivePath);
    //         if (drivePrim)
    //         {
    //             if (drivePrim.IsA<pxr::PhysxSchemaPhysxVehicleDriveStandard>())
    //             {
    //                 mCache.driveType = DriveType::eSTANDARD;
    //                 mCache.wheels = new std::vector<WheelCache>;
    //                 mCache.wheels->reserve(WheelCache::sInitialWheelCapacity);
    //             }
    //             else
    //             {
    //                 CARB_ASSERT(drivePrim.IsA<pxr::PhysxSchemaPhysxVehicleDriveBasic>());
    //                 // vehicleManager.registerDriveBasicVehicle(drivePath, this);
    //                 pxr::PhysxSchemaPhysxVehicleDriveBasic driveBasic(drivePrim);
    //                 mCache.driveType = DriveType::eBASIC;
    //                 mCache.wheelsDriveBasic = new std::vector<WheelCacheDriveBasic>;
    //                 mCache.wheelsDriveBasic->reserve(WheelCache::sInitialWheelCapacity);

    //                 pxr::UsdAttribute peakTorqueAttr = driveBasic.GetPeakTorqueAttr();
    //                 if (peakTorqueAttr.HasValue())
    //                     peakTorqueAttr.Get(&mCache.peakDriveTorque);
    //                 else
    //                 {
    //                     const float lengthScale = 1.0f /
    //                     static_cast<float>(pxr::UsdGeomGetStageMetersPerUnit(mStage)); mCache.peakDriveTorque =
    //                     500.0f * lengthScale * lengthScale;
    //                     // hardcoded value is not nice but the plan is to have a dictionary with default values
    //                     // at some point. Plus, there is an automated test that covers this value.
    //                 }
    //             }
    //         }
    //         else
    //         {
    //             success = false;
    //         }
    //     }
    //     else
    //     {
    //         success = false;
    //     }
    // }
    // else
    // {
    mCache.driveType = DriveType::eNONE;
    mCache.wheels = new std::vector<WheelCache>;
    mCache.wheels->reserve(WheelCache::sInitialWheelCapacity);
    // }

    // caching the wheel attachment paths and other USD info to avoid parsing USD all the time
    pxr::UsdPrimSubtreeRange subPrims = mVehiclePrim.GetDescendants();
    mCache.numDrivenWheels = 0;
    mCache.numBrakedWheels = 0;
    mCache.totalMass = 0;
    for (pxr::UsdPrim subPrim : subPrims)
    {
        if (subPrim.HasAPI<pxr::PhysxSchemaPhysxVehicleWheelAttachmentAPI>())
        {
            WheelCache wheelCache;
            wheelCache.usdPath = subPrim.GetPath();
            wheelCache.index = -1;
            wheelCache.wheelFlags = 0;

            if (subPrim.HasAPI<pxr::PhysxSchemaPhysxVehicleWheelControllerAPI>())
            {
                wheelCache.wheelFlags |= WheelFlag::eHAS_WHEEL_CONTROLLER;
                mCache.hasController = true;
            }

            pxr::PhysxSchemaPhysxVehicleWheelAttachmentAPI wheelAttachmentAPI(subPrim);
            bool driven;
            wheelAttachmentAPI.GetDrivenAttr().Get(&driven);
            if (driven)
            {
                wheelCache.wheelFlags |= WheelFlag::eHAS_DRIVE;
                mCache.numDrivenWheels++;
            }


            pxr::UsdRelationship wheelRel = wheelAttachmentAPI.GetWheelRel();
            pxr::SdfPathVector paths;
            wheelRel.GetTargets(&paths);
            CARB_ASSERT(paths.size() == 1); // else it should not have loaded

            pxr::SdfPath wheelPath = paths[0];
            pxr::UsdPrim wheelPrim = mStage->GetPrimAtPath(wheelPath);
            CARB_ASSERT(wheelPrim); // else it should not have loaded
            pxr::PhysxSchemaPhysxVehicleWheel wheel(wheelPrim);
            // note: as long as the following attributes do not have fallback values,
            //       there is no need to take length scale into account

            CARB_ASSERT(wheel.GetMassAttr()); // else it should not have loaded
            wheel.GetMassAttr().Get(&wheelCache.mass);
            mCache.totalMass += wheelCache.mass;

            CARB_ASSERT(wheel.GetRadiusAttr()); // else it should not have loaded
            wheel.GetRadiusAttr().Get(&wheelCache.radius);

            CARB_ASSERT(wheel.GetMaxSteerAngleAttr()); // else it should not have loaded
            wheel.GetMaxSteerAngleAttr().Get(&wheelCache.maxSteerAngle);
            if (wheelCache.maxSteerAngle != 0.0f)
            {
                wheelCache.wheelFlags |= WheelFlag::eHAS_STEER;
            }


            CARB_ASSERT(wheel.GetMaxBrakeTorqueAttr()); // else it should not have loaded
            wheel.GetMaxBrakeTorqueAttr().Get(&wheelCache.maxBrakeTorque);

            CARB_ASSERT(wheel.GetMaxHandBrakeTorqueAttr()); // else it should not have loaded
            wheel.GetMaxHandBrakeTorqueAttr().Get(&wheelCache.maxHandBrakeTorque);

            if ((wheelCache.maxBrakeTorque + wheelCache.maxHandBrakeTorque) != 0.0f)
            {
                wheelCache.wheelFlags |= WheelFlag::eHAS_BRAKE;
                mCache.numBrakedWheels++;
            }

            // if (mCache.driveType != DriveType::eNONE)
            mCache.wheels->push_back(wheelCache);
            // else
            // {
            //     WheelCacheDriveBasic wheelCacheDriveBasic;
            //     static_cast<WheelCache&>(wheelCacheDriveBasic) = wheelCache;


            // }
        }
    }

    if (mVehiclePrim.HasAPI<pxr::UsdPhysicsMassAPI>())
    {
        pxr::UsdPhysicsMassAPI massAPI(mVehiclePrim);
        if (massAPI.GetMassAttr())
        {
            massAPI.GetMassAttr().Get(&mCache.chassisMass);
            CARB_LOG_INFO("Chassis mass: %f", mCache.chassisMass);
        }
        else
        {
            mCache.chassisMass = 100;
            CARB_LOG_WARN("NO Chassis Mass using deault %f", mCache.chassisMass);
        }
        mCache.totalMass += mCache.chassisMass;
    }
    CARB_LOG_INFO("Total Vehicle Mass: %f kg", mCache.totalMass);
    if (success)
        mCache.state |= CacheStateFlag::eUSD;


    mCache.vehicleId = mPhysxPtr->getObjectId(mVehiclePath, omni::physx::PhysXType::ePTVehicle);
    mCache.mVehiclePtr = (::physx::PxVehicleWheels*)mPhysxPtr->getPhysXPtrFast(mCache.vehicleId);

    if (mCache.driveType == DriveType::eNONE)
    {
        cacheWheelIndices(*mCache.wheels, mCache.vehicleId, mPhysxPtr);
    }
    // else
    // {
    //     cacheWheelIndices(*mCache.wheelsDriveBasic, mCache.vehicleId, mPhysxPtr);
    // }

    mCache.state = CacheStateFlag::eVALID;


    // auto& wheelCacheList = *mCache.wheelsDriveBasic;
    ::physx::PxVehicleWheelQueryResult* wheelQueryResult =
        (::physx::PxVehicleWheelQueryResult*)(mPhysxPtr->getWheelQueryResult(mCache.vehicleId));
    // Distance between left and right rear wheels
    mCache.rearWidth =
        (wheelQueryResult->wheelQueryResults[2].localPose.p - wheelQueryResult->wheelQueryResults[3].localPose.p).magnitude();
    // distance between front and rear axles
    mCache.axleSeparation =
        (wheelQueryResult->wheelQueryResults[0].localPose.p - wheelQueryResult->wheelQueryResults[2].localPose.p).magnitude();

    CARB_LOG_INFO("mRearWidth: %f, mAxleSeparation: %f", mCache.rearWidth, mCache.axleSeparation);
}

void VehicleSimulator::onComponentChange()
{
    GxfComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineVehicle& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineVehicle)mPrim;

    // Parse component and channel
    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mCommandChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mStateChannelName);

    std::string wheelFLName;
    std::string wheelFRName;

    pxr::SdfPathVector targets;
    typedPrim.GetVehiclePrimRel().GetTargets(&targets);
    if (targets.size() == 0)
    {
        return;
    }

    mVehiclePath = targets[0];
    mVehiclePrim = mStage->GetPrimAtPath(mVehiclePath);

    isaac::utils::safeGetAttribute(typedPrim.GetHistoryLengthAttr(), mMovingAverageSize);
    isaac::utils::safeGetAttribute(typedPrim.GetUsePIDAttr(), mUsePID);

    mAveragedAcceleration.clear(); // clear this in case the requested average moving size was changed.

    if (mUsePID)
    {
        pxr::GfVec3f pidValues;
        isaac::utils::safeGetAttribute(typedPrim.GetControllerPIDValuesAttr(), pidValues);
        mPID = std::make_unique<PIDController>(pidValues[0], pidValues[1], pidValues[2]);
    }
}
}
}
}
}
