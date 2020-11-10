// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <vector>
#include <string>

#include "../Core/IsaacComponent.h"
#include <carb/logging/Log.h>

#include "ScissorLiftSimulator.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

using omni::isaac::dynamic_control::DcDofState;
using omni::isaac::dynamic_control::DcDofType;
using omni::isaac::dynamic_control::DcHandle;

ScissorLiftSimulator::ScissorLiftSimulator(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

void ScissorLiftSimulator::onStart()
{
    mState = LiftState::Lowered;
    mCurrentHeight = 0.0f;
    mRaiseRequest = false;
    mLowerRequest = false;
    onComponentChange();
}

void ScissorLiftSimulator::tick()
{
    if (!mArticulationHandle)
    {
        return;
    }

    {
        MessageHeader header;
        IsaacMessage<isaac_message::State> commandComposite;
        std::vector<IsaacHostBuffer> buffers;
        if (checkErrorCode(receive(mInputComponent, mCommandChannelName, header, commandComposite, buffers)))
        {


            std::vector<double> elements(buffers[0].size() / sizeof(double));
            std::memcpy(elements.data(), buffers[0].data(), elements.size() * sizeof(double));

            if (elements.size() != 2)
            {
                CARB_LOG_ERROR("Wrong number of elements");
                return;
            }

            float liftCommand = (float)(elements[0]);
            if (liftCommand > 0)
            {
                mRaiseRequest = true;
            }
            else if (liftCommand < 0)
            {
                mLowerRequest = true;
            }

            // Handle command according to current state
            if (mRaiseRequest)
            {
                // only accept the raise command if lift is in default state
                if (mState == LiftState::Lowered)
                {
                    mState = LiftState::Raising;
                }
                mRaiseRequest = false;
            }
            if (mLowerRequest)
            {
                // only accept the lower command if lift is in raised state
                if (mState == LiftState::Raised)
                {
                    mState = LiftState::Lowering;
                }
                mLowerRequest = false;
            }
        }
    }
    {
        mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
        auto handle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, mLiftJointName.c_str());

        float currentPosition = mDynamicControlPtr->getDofPosition(handle);
        if (mState == LiftState::Raised && pxr::GfIsClose(currentPosition, 0.0f, 0.0001f))
        {
            mState = LiftState::Lowered;
            mCurrentHeight = 0.0f;
        }

        if (mState == LiftState::Raising)
        {
            if (mCurrentHeight < mMaxHeight)
            {
                mCurrentHeight += mDeltaHeight;
                if (handle)
                {
                    mDynamicControlPtr->setDofPositionTarget(handle, mCurrentHeight * static_cast<float>(mUnitScale));
                }
                else
                {
                    CARB_LOG_ERROR("Entity not found in articulation");
                }
            }
            else
            {
                mState = LiftState::Raised;
            }
        }
        else if (mState == LiftState::Lowering)
        {
            if (mCurrentHeight > 0.0f)
            {
                mCurrentHeight -= mDeltaHeight;
                if (handle)
                {
                    mDynamicControlPtr->setDofPositionTarget(handle, mCurrentHeight * static_cast<float>(mUnitScale));
                }
                else
                {
                    CARB_LOG_ERROR("Entity not found in articulation");
                }
            }
            else
            {
                mState = LiftState::Lowered;
            }
        }

        // Publish current state.
        double stateVal = 0.0;
        if (mState == LiftState::Raised)
            stateVal = 1.0;
        else if (mState == LiftState::Lowered)
            stateVal = -1.0;

        // message format as state/DifferentialBaseControl
        // (linear_speed, angular speed)
        IsaacMessage<isaac_message::State> statusComposite;
        auto statusProto = statusComposite.initProto();
        std::vector<double> elements{ stateVal, 0.0 };
        // set tensor proto to specify dimension of buffer
        auto tensor = statusProto.initPack();
        tensor.setElementType(ElementType::FLOAT64);
        auto tensor_sizes = tensor.initSizes(1);
        tensor_sizes.set(0, static_cast<int>(elements.size()));
        tensor.setScanlineStride(0);
        tensor.setDataBufferIndex(0);
        // copy actual buffer data
        std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
        buffers[0] = std::make_unique<IsaacHostBuffer>(elements.size() * sizeof(double));
        std::memcpy(buffers[0]->data(), elements.data(), elements.size() * sizeof(double));
        publish(mOutputComponent, mStateChannelName, statusComposite, isaac_message::StateProtoId, buffers);
    }
}

void ScissorLiftSimulator::onComponentChange()
{
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineScissorLift& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineScissorLift)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mCommandChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mStateChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetLiftJointNameAttr(), mLiftJointName);

    pxr::SdfPathVector targets;
    typedPrim.GetArticulationPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    mArticulationPath = targets[0];


    if (mDynamicControlPtr->peekObjectType(mArticulationPath.GetString().c_str()) ==
        omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        mArticulationHandle = mDynamicControlPtr->getArticulation(mArticulationPath.GetString().c_str());
    }
    else
    {
        CARB_LOG_ERROR("Articulation %s is not valid art", mArticulationPath.GetString().c_str());
        return;
    }
    if (!mArticulationHandle)
    {
        CARB_LOG_ERROR("Articulation %s not found", mArticulationPath.GetString().c_str());
        return;
    }
    mUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(mStage);
}
}
}
}
