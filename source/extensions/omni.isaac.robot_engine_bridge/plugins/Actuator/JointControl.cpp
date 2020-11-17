// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
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

#include "JointControl.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

using omni::isaac::dynamic_control::DcDofProperties;
using omni::isaac::dynamic_control::DcDofState;
using omni::isaac::dynamic_control::DcDofType;
using omni::isaac::dynamic_control::DcHandle;

JointControl::JointControl(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

void JointControl::onStart()
{
    onComponentChange();
}

void JointControl::tick()
{
    if (!mArticulationHandle)
    {
        return;
    }
    CARB_PROFILE_ZONE(0, "REB JointControl Tick");

    {
        MessageHeader header;
        IsaacMessage<isaac_message::Composite> commandComposite;
        std::vector<IsaacHostBuffer> buffers;
        if (checkErrorCode(receive(mInputComponent, mJointControlChannelName, header, commandComposite, buffers)))
        {
            auto commands = commandComposite.getProto();

            std::vector<double> elements(buffers[0].size() / sizeof(double));
            std::memcpy(elements.data(), buffers[0].data(), elements.size() * sizeof(double));

            auto quantities = commands.getQuantities();
            if (elements.size() != quantities.size())
            {
                CARB_LOG_ERROR("Element size is not same as quantities size %zu %d", elements.size(), quantities.size());
                return;
            }

            mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);

            for (size_t i = 0; i < quantities.size(); i++)
            {
                auto entity = quantities[i].getEntity(); // name
                // auto elementType = quantities[i].getElementType();
                auto measure = quantities[i].getMeasure(); // control mode: position or velocity
                // auto dimensions = quantities[i].getDimensions();
                // CARB_LOG_ERROR("Data: %d %s %d %f", i, entity.cStr(), dimensions.size(), elements[i]);

                auto handle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, entity.cStr());
                if (handle)
                {
                    float elementValue = static_cast<float>(elements[i]);
                    DcDofProperties props;
                    mDynamicControlPtr->getDofProperties(handle, &props);
                    if (props.type == omni::isaac::dynamic_control::DcDofType::eTranslation)
                    {
                        elementValue *= mUnitScale;
                    }
                    if (props.hasLimits)
                    {
                        // Joints become unstable if we get close to 2*pi limit. Artificially limit as a workaround
                        elementValue = CARB_CLAMP(elementValue, props.lower, props.upper);
                        elementValue = CARB_CLAMP(elementValue, -6.25, 6.25);
                    }
                    if (measure == isaac_message::Composite::Measure::POSITION)
                    {
                        mDynamicControlPtr->setDofPositionTarget(handle, elementValue);
                    }
                    else if (measure == isaac_message::Composite::Measure::SPEED)
                    {
                        mDynamicControlPtr->setDofVelocityTarget(handle, elementValue);
                    }
                }
                else
                {
                    CARB_LOG_ERROR("Entity not found in articulation");
                }
            }
        }
    }
    {
        IsaacMessage<isaac_message::Composite> statusComposite;
        auto statusProto = statusComposite.initProto();

        int numDofs = mDynamicControlPtr->getArticulationDofCount(mArticulationHandle);
        // set quantities
        auto quantities = statusProto.initQuantities(numDofs * 2);
        std::vector<double> elements(numDofs * 2);

        if (numDofs > 0)
        {
            DcDofState* states = mDynamicControlPtr->getArticulationDofStates(
                mArticulationHandle, omni::isaac::dynamic_control::kDcStateAll);
            if (states != nullptr)
            {
                for (int i = 0; i < numDofs; i++)
                {
                    DcHandle dof = mDynamicControlPtr->getArticulationDof(mArticulationHandle, i);
                    quantities[i * 2 + 0].setEntity(mDynamicControlPtr->getDofName(dof));
                    quantities[i * 2 + 1].setEntity(mDynamicControlPtr->getDofName(dof));
                    quantities[i * 2 + 0].setMeasure(isaac_message::Composite::Measure::POSITION);
                    quantities[i * 2 + 1].setMeasure(isaac_message::Composite::Measure::SPEED);
                    elements[i * 2 + 0] = states[i].pos;
                    elements[i * 2 + 1] = states[i].vel;
                }
            }
        }
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

        publish(mOutputComponent, mJointStateChannelName, statusComposite, isaac_message::CompositeProtoId, buffers);
    }
}

void JointControl::onComponentChange()
{
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineJointControl& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineJointControl)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mJointControlChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mJointStateChannelName);


    pxr::SdfPathVector targets;
    typedPrim.GetArticulationPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    pxr::SdfPath articulationPath = targets[0];

    if (mDynamicControlPtr->peekObjectType(articulationPath.GetString().c_str()) ==
        omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        mArticulationHandle = mDynamicControlPtr->getArticulation(articulationPath.GetString().c_str());
    }
    else
    {
        CARB_LOG_ERROR("Articulation %s is not valid art", articulationPath.GetString().c_str());
        return;
    }
    if (!mArticulationHandle)
    {
        CARB_LOG_ERROR("Articulation %s not found", articulationPath.GetString().c_str());
        return;
    }
    mUnitScale = 1.0f / UsdGeomGetStageMetersPerUnit(mStage);
}
}
}
}
