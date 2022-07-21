// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "VehicleSimulator.h"

#include "../Core/IsaacComponent.h"

#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <carb/profiler/Profile.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <physx/include/PxPhysicsAPI.h>

#include <string>
#include <vector>


namespace omni
{
namespace isaac
{
using utils::conversions::asGfRotation;
using utils::conversions::asGfVec3d;
namespace robot_engine_bridge
{


VehicleSimulator::VehicleSimulator() : IsaacComponent()
{

    mPhysxPtr = carb::getCachedInterface<omni::physx::IPhysx>();
    if (!mPhysxPtr)
    {
        CARB_LOG_ERROR("*** Failed to acquire PhysX interface\n");
        return;
    }

    // mPhysxVehiclePtr = carb::getCachedInterface<omni::physx::IPhysxVehicle>();
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
    mPrevForwardSpeed = 0;
}

void VehicleSimulator::tick()
{
    CARB_PROFILE_ZONE(0, "REB VehicleSimulator Tick");

    if (!mVehiclePrim)
    {
        CARB_LOG_ERROR("Vehicle Prim is not valid");
        return;
    }
    mVehicleController.fillCache();


    {

        float forwardSpeed = mVehicleController.getForwardSpeed();
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
        IsaacMessage<isaac_message::Composite> commandComposite;
        std::vector<IsaacHostBuffer> buffers;
        MessageHeader header;
        if (checkErrorCode(receive(mInputComponent, mCommandChannelName, header, commandComposite, buffers)))
        {
            std::vector<double> elements(buffers[0].size() / sizeof(double));
            std::memcpy(elements.data(), buffers[0].data(), elements.size() * sizeof(double));
            if (elements.size() != 2)
            {
                CARB_LOG_ERROR("Wrong number of elements: %zu", elements.size());
            }
            // const float signMultiplier = mInReverse ? -1.0f : 1.0f;
            const float requestedAcceleration = elements[0] / mUnitScale; // m/s^2 -> cm/s^2


            float commandedAcceleration = requestedAcceleration;
            if (mUsePID)
            {
                commandedAcceleration =
                    mPID->update(requestedAcceleration, mForwardAcceleration, mPrevForwardAcceleration);
            }
            mPrevForwardAcceleration = mForwardAcceleration;

            // CARB_LOG_ERROR("requested acceleration: %f", requestedAcceleration);


            // steering angle in radians
            mVehicleController.setAckermannSteering(elements[1]);
            mVehicleController.setAcceleration(commandedAcceleration);
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
        std::vector<double> elements = {
            mVehicleController.getSteeringAngle(),       mVehicleController.getWheelRotationSpeed(0),
            mVehicleController.getWheelRotationSpeed(1), mVehicleController.getWheelRotationSpeed(2),
            mVehicleController.getWheelRotationSpeed(3),
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

    isaac::utils::safeGetAttribute(typedPrim.GetHistoryLengthAttr(), mMovingAverageSize);
    isaac::utils::safeGetAttribute(typedPrim.GetUsePIDAttr(), mUsePID);

    mAveragedAcceleration.clear(); // clear this in case the requested average moving size was changed.

    if (mUsePID)
    {
        pxr::GfVec3f pidValues;
        isaac::utils::safeGetAttribute(typedPrim.GetControllerPIDValuesAttr(), pidValues);
        mPID = std::make_unique<utils::PIDController>(pidValues[0], pidValues[1], pidValues[2]);
    }

    mVehicleController.Initialize(mPhysxPtr, mStage, mVehiclePrim);
}

}
}
}
