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

#include <vector>
#include <string>

#include "../Core/IsaacComponent.h"
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/utils/Conversions.h>

#include "SurfaceGripper.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

using omni::isaac::dynamic_control::DcDofState;
using omni::isaac::dynamic_control::DcDofType;
using omni::isaac::dynamic_control::DcHandle;

SurfaceGripper::SurfaceGripper(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{

    mGripperJoint = std::make_unique<omni::isaac::utils::SurfaceGripper>(dynamicControlPtr);
}

void SurfaceGripper::onStart()
{
    onComponentChange();
}

void SurfaceGripper::tick()
{
    CARB_PROFILE_ZONE(0, "REB SurfaceGripper Tick");

    {
        MessageHeader header;
        IsaacMessage<isaac_message::Composite> commandComposite;
        std::vector<IsaacHostBuffer> buffers;
        if (checkErrorCode(receive(mInputComponent, mGripperControlChannelName, header, commandComposite, buffers)))
        {
            auto commands = commandComposite.getProto();

            std::vector<double> elements(buffers[0].size() / sizeof(double));
            std::memcpy(elements.data(), buffers[0].data(), elements.size() * sizeof(double));
            auto quantities = commands.getQuantities();

            if (elements.size() != quantities.size())
            {
                CARB_LOG_ERROR("Element size is not same as quantities size");
                return;
            }
            if (elements.size() > 0)
            {
                if (elements[0] == 1)
                {
                    CARB_LOG_INFO("Closing Gripper");

                    if (!mGripperJoint->isClosed())
                    {
                        bool status = mGripperJoint->close();
                        if (status)
                        {
                            CARB_LOG_INFO("Gripper Closed");
                        }
                        else
                        {
                            CARB_LOG_WARN("Gripper not closed successfully");
                        }
                    }
                    else
                    {
                        CARB_LOG_INFO("Gripper already closed");
                    }
                }
                else
                {
                    CARB_LOG_INFO("Opening Gripper");
                    if (mGripperJoint->isClosed())
                    {
                        bool status = mGripperJoint->open();
                        if (status)
                        {
                            CARB_LOG_INFO("Gripper Opened");
                        }
                        else
                        {
                            CARB_LOG_WARN("Gripper not opened successfully");
                        }
                    }
                    else
                    {
                        CARB_LOG_INFO("Gripper already opened");
                    }
                }
            }
        }
    }
    {
        IsaacMessage<isaac_message::Composite> statusComposite;
        auto statusProto = statusComposite.initProto();

        // set quantities
        auto quantities = statusProto.initQuantities(1);
        quantities[0].setEntity(mGripperEntityName);
        quantities[0].setMeasure(isaac_message::Composite::Measure::NONE);
        std::vector<double> elements(1);
        elements[0] = mGripperJoint->isClosed();

        // set tensor proto to specify dimension of buffer
        auto tensor = statusProto.initValues();
        tensor.setElementType(ElementType::FLOAT64);
        auto tensor_sizes = tensor.initSizes(1);
        tensor_sizes.set(0, static_cast<int>(elements.size()));
        tensor.setScanlineStride(0);
        tensor.setDataBufferIndex(0);
        // copy actual buffer data
        std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
        buffers[0] = std::make_unique<IsaacHostBuffer>(elements.size() * sizeof(double));
        std::memcpy(buffers[0]->data(), elements.data(), elements.size() * sizeof(double));

        publish(mOutputComponent, mGripperStateChannelName, statusComposite, buffers);
    }
}

void SurfaceGripper::onComponentChange()
{
    IsaacComponent::onComponentChange();


    const pxr::RobotEngineBridgeSchemaRobotEngineSurfaceGripper& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineSurfaceGripper)mPrim;


    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mGripperControlChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mGripperStateChannelName);

    isaac::utils::safeGetAttribute(typedPrim.GetGripperEntityAttr(), mGripperEntityName);

    pxr::SdfPathVector targets;
    typedPrim.GetD6JointPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        std::string jointPath = mPrim.GetPath().GetString() + "/d6Joint";

        CARB_LOG_WARN("JointPrim path not specified, using %s", jointPath.c_str());
        mProps.d6JointPath = jointPath;
    }
    else
    {
        mProps.d6JointPath = targets[0].GetString();
    }


    typedPrim.GetParentPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        CARB_LOG_ERROR("Parent prim relationsip for surface gripper not specified");
        return;
    }
    mProps.parentPath = targets[0].GetString();

    pxr::GfVec3f offsetPosition(0, 0, 0);
    pxr::GfQuatf offsetRotation(1, 0, 0, 0);

    mProps.gripThreshold = 1;
    mProps.forceLimit = 1e10;
    mProps.torqueLimit = 1e10;
    mProps.bendAngle = 0;
    mProps.stiffness = 1e10;
    mProps.damping = 1e3;

    isaac::utils::safeGetAttribute(typedPrim.GetOffsetPositionAttr(), offsetPosition);
    isaac::utils::safeGetAttribute(typedPrim.GetOffsetRotationAttr(), offsetRotation);
    isaac::utils::safeGetAttribute(typedPrim.GetGripThresholdAttr(), mProps.gripThreshold);
    isaac::utils::safeGetAttribute(typedPrim.GetForceLimitAttr(), mProps.forceLimit);
    isaac::utils::safeGetAttribute(typedPrim.GetTorqueLimitAttr(), mProps.torqueLimit);
    isaac::utils::safeGetAttribute(typedPrim.GetBendAngleAttr(), mProps.bendAngle);
    isaac::utils::safeGetAttribute(typedPrim.GetStiffnessAttr(), mProps.stiffness);
    isaac::utils::safeGetAttribute(typedPrim.GetDampingAttr(), mProps.damping);
    mProps.offset = omni::isaac::utils::conversions::asDcTransform(offsetPosition, offsetRotation);
    mGripperJoint->initialize(mProps);
}
}
}
}
