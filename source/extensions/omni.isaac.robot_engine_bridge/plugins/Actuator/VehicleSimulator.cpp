// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
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

#include "../Core/IsaacComponent.h"
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
namespace omni
{
namespace isaac
{
using utils::conversions::asGfRotation;
using utils::conversions::asGfVec3d;
namespace robot_engine_bridge
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

VehicleSimulator::VehicleSimulator() : IsaacComponent()
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
    mCache.state = 0;
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

    if (mCache.driveType == DriveType::eSTANDARD)
    {
        CARB_LOG_ERROR("Only Basic Drive is supportred currently");
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
        if (mAveragedAcceleration.size() > mMovingAverageSize)
        {
            mAveragedAcceleration.pop_front();
        }
        mAveragedAcceleration.push_back(accel);

        mPrevForwardSpeed = forwardSpeed;
    }


    IsaacMessage<isaac_message::State> commandComposite;
    {
        // Receive current command
        std::vector<IsaacHostBuffer> buffers;
        MessageHeader header;
        if (checkErrorCode(receive(mInputComponent, mCommandChannelName, header, commandComposite, buffers)))
        {
            // State need buffer for data
            if (buffers.size() == 0)
            {
                return;
            }
            std::vector<double> elements(buffers[0].size() / sizeof(double));
            std::memcpy(elements.data(), buffers[0].data(), elements.size() * sizeof(double));
            if (elements.size() != 2)
            {
                CARB_LOG_ERROR("Wrong number of elements: %zu", elements.size());
            }
            // mCommandedSpeed[0] = pxr::GfClamp(elements[0], -mMaximumSpeed[0], mMaximumSpeed[0]);
            // mCommandedSpeed[1] = pxr::GfClamp(elements[1], -mMaximumSpeed[1], mMaximumSpeed[1]);

            // mLastCommandTime = mTimeSeconds;

            // CARB_LOG_ERROR("Received %f %f %d %d", elements[0], elements[1], buffers.size(), elements.size());

            // Use latest command only for a certain period of time in case no new command arrives
            // if (mTimeSeconds - mLastCommandTime > mMaximumTimeWithoutCommand)
            // {
            //     mCommandedSpeed = pxr::GfVec2d(0, 0);
            // }

            ::physx::PxVehicleNoDrive* vehicleNoDrive = static_cast<::physx::PxVehicleNoDrive*>(mCache.mVehiclePtr);
            // const float signMultiplier = mInReverse ? -1.0f : 1.0f;
            const float acceleration = elements[0] / mUnitScale; // m/s^2 -> cm/s^2

            float forwardAcceleration = 0;
            for (size_t i = 0; i < mAveragedAcceleration.size(); i++)
            {
                forwardAcceleration += mAveragedAcceleration[i];
            }
            forwardAcceleration /= mAveragedAcceleration.size();
            // CARB_LOG_ERROR("Chassis speed forward %f cm/s, computed forward accel: %f cm/s^2", mPrevForwardSpeed,
            //                forwardAcceleration);


            float driveTorque = 0;

            driveTorque = acceleration * (*mCache.wheelsDriveBasic)[0].radius * mCache.totalMass / mCache.numDrivenWheels;

            // CARB_LOG_ERROR("requested acceleration: %f cm/s^2, drive torque: %f N*cm on %d wheels", acceleration,
            //                driveTorque, mCache.numDrivenWheels);


            // steering angle in radians
            float maxSteerAngle = (*mCache.wheelsDriveBasic)[0].maxSteerAngle;
            mCurrentSteeringAngle = pxr::GfClamp(elements[1], double(-maxSteerAngle), double(maxSteerAngle));
            setAckermannSteering(
                mCurrentSteeringAngle, (*mCache.wheelsDriveBasic)[0].index, (*mCache.wheelsDriveBasic)[1].index);

            const uint32_t wheelCount = static_cast<uint32_t>(mCache.wheelsDriveBasic->size());
            for (uint32_t i = 0; i < wheelCount; i++)
            {
                const WheelCacheDriveBasic& wheelCache = (*mCache.wheelsDriveBasic)[i];

                if (wheelCache.wheelFlags & WheelFlag::eHAS_DRIVE)
                {
                    vehicleNoDrive->setDriveTorque(wheelCache.index, driveTorque);
                }
            }
        }
    }

    {
        IsaacMessage<isaac_message::Composite> stateComposite;
        auto stateProto = stateComposite.initProto();
        // set quantities
        auto quantities = stateProto.initQuantities(5);
        quantities[0].setEntity("steering");
        quantities[0].setMeasure(isaac_message::Composite::Measure::POSITION);
        quantities[0].setElementType(ElementType::FLOAT64);
        for (int i = 1; i < 5; i++)
        {
            quantities[i].setEntity("wheel_" + std::to_string(i));
            quantities[i].setMeasure(isaac_message::Composite::Measure::SPEED);
            quantities[i].setElementType(ElementType::FLOAT64);
        }
        ::physx::PxVehicleNoDrive* vehicleNoDrive = static_cast<::physx::PxVehicleNoDrive*>(mCache.mVehiclePtr);
        std::vector<double> elements = {
            mCurrentSteeringAngle,
            vehicleNoDrive->mWheelsDynData.getWheelRotationSpeed(0),
            vehicleNoDrive->mWheelsDynData.getWheelRotationSpeed(1),
            vehicleNoDrive->mWheelsDynData.getWheelRotationSpeed(2),
            vehicleNoDrive->mWheelsDynData.getWheelRotationSpeed(3),
        };

        // set tensor proto to specify dimension of buffer
        auto tensor = stateProto.initValues();
        tensor.setElementType(ElementType::FLOAT64);
        auto tensor_sizes = tensor.initSizes(1);
        tensor_sizes.set(0, static_cast<int>(elements.size()));
        tensor.setScanlineStride(0);
        tensor.setDataBufferIndex(0);
        // copy buffer data
        std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
        buffers[0] = std::make_unique<IsaacHostBuffer>(elements.size() * sizeof(double));
        std::memcpy(buffers[0]->data(), elements.data(), elements.size() * sizeof(double));

        publish(mOutputComponent, mStateChannelName, stateComposite, buffers);
    }
}


void VehicleSimulator::fillCache()
{

    if (mCache.state == CacheStateFlag::eVALID)
    {
        return;
    }
    bool success = true;

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
    if (mVehiclePrim && mVehiclePrim.HasAPI<pxr::PhysxSchemaPhysxVehicleAPI>())
    {
        pxr::PhysxSchemaPhysxVehicleAPI vehicleAPI(mVehiclePrim);
        pxr::UsdRelationship driveRel = vehicleAPI.GetDriveRel();
        if (driveRel)
        {
            pxr::SdfPathVector paths;
            driveRel.GetTargets(&paths);
            if (paths.size() == 1)
            {
                pxr::SdfPath drivePath = paths[0];
                pxr::UsdPrim drivePrim = mStage->GetPrimAtPath(drivePath);
                if (drivePrim)
                {
                    if (drivePrim.IsA<pxr::PhysxSchemaPhysxVehicleDriveStandard>())
                    {
                        mCache.driveType = DriveType::eSTANDARD;
                        mCache.wheels = new std::vector<WheelCache>;
                        mCache.wheels->reserve(WheelCache::sInitialWheelCapacity);
                    }
                    else
                    {
                        CARB_ASSERT(drivePrim.IsA<pxr::PhysxSchemaPhysxVehicleDriveBasic>());
                        // vehicleManager.registerDriveBasicVehicle(drivePath, this);
                        pxr::PhysxSchemaPhysxVehicleDriveBasic driveBasic(drivePrim);
                        mCache.driveType = DriveType::eBASIC;
                        mCache.wheelsDriveBasic = new std::vector<WheelCacheDriveBasic>;
                        mCache.wheelsDriveBasic->reserve(WheelCache::sInitialWheelCapacity);

                        pxr::UsdAttribute peakTorqueAttr = driveBasic.GetPeakTorqueAttr();
                        if (peakTorqueAttr.HasValue())
                            peakTorqueAttr.Get(&mCache.peakDriveTorque);
                        else
                        {
                            const float lengthScale =
                                1.0f / static_cast<float>(pxr::UsdGeomGetStageMetersPerUnit(mStage));
                            mCache.peakDriveTorque = 500.0f * lengthScale * lengthScale;
                            // hardcoded value is not nice but the plan is to have a dictionary with default values
                            // at some point. Plus, there is an automated test that covers this value.
                        }
                    }
                }
                else
                {
                    success = false;
                }
            }
            else
            {
                success = false;
            }
        }
        else
        {
            mCache.driveType = DriveType::eNONE;
            mCache.wheels = new std::vector<WheelCache>;
            mCache.wheels->reserve(WheelCache::sInitialWheelCapacity);
        }

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

                if (mCache.driveType != DriveType::eBASIC)
                    mCache.wheels->push_back(wheelCache);
                else
                {
                    WheelCacheDriveBasic wheelCacheDriveBasic;
                    static_cast<WheelCache&>(wheelCacheDriveBasic) = wheelCache;

                    pxr::PhysxSchemaPhysxVehicleWheelAttachmentAPI wheelAttachmentAPI(subPrim);
                    bool driven;
                    wheelAttachmentAPI.GetDrivenAttr().Get(&driven);
                    if (driven)
                    {
                        wheelCacheDriveBasic.wheelFlags |= WheelFlag::eHAS_DRIVE;
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
                    wheel.GetMassAttr().Get(&wheelCacheDriveBasic.mass);
                    mCache.totalMass += wheelCacheDriveBasic.mass;

                    CARB_ASSERT(wheel.GetRadiusAttr()); // else it should not have loaded
                    wheel.GetRadiusAttr().Get(&wheelCacheDriveBasic.radius);

                    CARB_ASSERT(wheel.GetMaxSteerAngleAttr()); // else it should not have loaded
                    wheel.GetMaxSteerAngleAttr().Get(&wheelCacheDriveBasic.maxSteerAngle);
                    if (wheelCacheDriveBasic.maxSteerAngle != 0.0f)
                        wheelCacheDriveBasic.wheelFlags |= WheelFlag::eHAS_STEER;

                    CARB_ASSERT(wheel.GetMaxBrakeTorqueAttr()); // else it should not have loaded
                    wheel.GetMaxBrakeTorqueAttr().Get(&wheelCacheDriveBasic.maxBrakeTorque);

                    CARB_ASSERT(wheel.GetMaxHandBrakeTorqueAttr()); // else it should not have loaded
                    wheel.GetMaxHandBrakeTorqueAttr().Get(&wheelCacheDriveBasic.maxHandBrakeTorque);

                    if ((wheelCacheDriveBasic.maxBrakeTorque + wheelCacheDriveBasic.maxHandBrakeTorque) != 0.0f)
                    {
                        wheelCacheDriveBasic.wheelFlags |= WheelFlag::eHAS_BRAKE;
                        mCache.numBrakedWheels++;
                    }

                    mCache.wheelsDriveBasic->push_back(wheelCacheDriveBasic);
                }
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

        if (mCache.driveType != DriveType::eBASIC)
        {
            cacheWheelIndices(*mCache.wheels, mCache.vehicleId, mPhysxPtr);
        }
        else
        {
            cacheWheelIndices(*mCache.wheelsDriveBasic, mCache.vehicleId, mPhysxPtr);
        }

        mCache.state = CacheStateFlag::eVALID;


        // auto& wheelCacheList = *mCache.wheelsDriveBasic;
        ::physx::PxVehicleWheelQueryResult* wheelQueryResult =
            (::physx::PxVehicleWheelQueryResult*)(mPhysxPtr->getWheelQueryResult(mCache.vehicleId));
        // Distance between left and right rear wheels
        mCache.rearWidth =
            (wheelQueryResult->wheelQueryResults[2].localPose.p - wheelQueryResult->wheelQueryResults[3].localPose.p)
                .magnitude();
        // distance between front and rear axles
        mCache.axleSeparation =
            (wheelQueryResult->wheelQueryResults[0].localPose.p - wheelQueryResult->wheelQueryResults[2].localPose.p)
                .magnitude();

        CARB_LOG_INFO("mRearWidth: %f, mAxleSeparation: %f", mCache.rearWidth, mCache.axleSeparation);
    }
    else
    {
        CARB_LOG_ERROR("Vehicle Prim is not valid");
    }
}

void VehicleSimulator::onComponentChange()
{
    IsaacComponent::onComponentChange();

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
}

}
}
}
