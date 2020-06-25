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

#include "TwoFingerGripper.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

using omni::isaac::dynamic_control::DcDofState;
using omni::isaac::dynamic_control::DcDofType;
using omni::isaac::dynamic_control::DcHandle;

TwoFingerGripper::TwoFingerGripper(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

void TwoFingerGripper::onStart()
{
    onComponentChange();
}

void TwoFingerGripper::tick()
{
    CARB_PROFILE_ZONE(0, "REB TwoFingerGripper Tick");

    {
        MessageHeader header;
        IsaacMessage<isaac_message::Composite> commandsComposite;
        auto commands = commandsComposite.initProto();
        std::vector<IsaacHostBuffer> buffers;
        if (receive(mInputComponent, mGripperControlChannelName, header, commands, buffers))
        {

            if (mArticulationHandle)
            {
                mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
            }
            else
            {
                CARB_LOG_ERROR("mArticulationHandle Invalid");
                return;
            }

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
                    CARB_LOG_WARN("Gripper Closed");
                    setDistance(mLeftFingerHandle, mClosedDistance);
                    setDistance(mRightFingerHandle, mClosedDistance);
                }
                else
                {
                    CARB_LOG_WARN("Gripper Open");
                    setDistance(mLeftFingerHandle, mOpenDistance);
                    setDistance(mRightFingerHandle, mOpenDistance);
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
        elements[0] = isClosed();

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

        publish(mOutputComponent, mGripperStateChannelName, statusProto, isaac_message::CompositeProtoId, buffers);
    }
}

void TwoFingerGripper::onComponentChange()
{
    IsaacComponent::onComponentChange();


    const pxr::RobotEngineBridgeSchemaRobotEngineTwoFingerGripper& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineTwoFingerGripper)mPrim;


    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mGripperControlChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mGripperStateChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetGripperEntityAttr(), mGripperEntityName);

    isaac::utils::safeGetAttribute(typedPrim.GetLeftFingerJointAttr(), mLeftJointName);
    isaac::utils::safeGetAttribute(typedPrim.GetRightFingerJointAttr(), mRightJointName);
    isaac::utils::safeGetAttribute(typedPrim.GetOpenDistanceAttr(), mOpenDistance);
    isaac::utils::safeGetAttribute(typedPrim.GetClosedDistanceAttr(), mClosedDistance);
    pxr::SdfPathVector targets;
    typedPrim.GetArticulationPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    if (mDynamicControlPtr->peekObjectType(targets[0].GetString().c_str()) ==
        omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        mArticulationHandle = mDynamicControlPtr->getArticulation(targets[0].GetString().c_str());
    }
    else
    {
        CARB_LOG_ERROR("ArticulationPrim is not a valid articulation");
        return;
    }
    if (!mArticulationHandle)
    {
        CARB_LOG_ERROR("Articulation not found for ArticulationPrim");
        return;
    }

    mLeftFingerHandle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, mLeftJointName.c_str());
    if (!mLeftFingerHandle)
    {
        CARB_LOG_ERROR("LeftFingerJoint Name %s not valid", mLeftJointName.c_str());
        return;
    }

    mRightFingerHandle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, mRightJointName.c_str());
    if (!mRightFingerHandle)
    {
        CARB_LOG_ERROR("RightFingerJoint Name %s not valid", mRightJointName.c_str());
        return;
    }
    mUnitScale = 1.0f / UsdGeomGetStageMetersPerUnit(mStage);
}

void TwoFingerGripper::setDistance(const omni::isaac::dynamic_control::DcHandle& fingerHandle, float distance)
{
    omni::isaac::dynamic_control::DcDofProperties props;
    mDynamicControlPtr->getDofProperties(fingerHandle, &props);
    if (props.type == omni::isaac::dynamic_control::DcDofType::eTranslation)
    {
        distance *= mUnitScale;
    }
    if (props.hasLimits)
    {
        distance = std::max(props.lower + mLimitOffset, std::min(distance, props.upper - mLimitOffset));
    }

    mDynamicControlPtr->setDofPositionTarget(fingerHandle, distance);
}
bool TwoFingerGripper::isClosed()
{
    if (!mLeftFingerHandle || !mRightFingerHandle)
    {
        return false;
    }
    float leftTarget = mDynamicControlPtr->getDofPositionTarget(mLeftFingerHandle);
    float rightTarget = mDynamicControlPtr->getDofPositionTarget(mRightFingerHandle);

    if (leftTarget <= mClosedDistance + mTolerance && rightTarget <= mClosedDistance + mTolerance)
    {
        return true;
    }
    return false;
}

}
}
}
