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
        IsaacMessage<isaac_message::State> commandsState;
        auto commands = commandsState.initProto();
        std::vector<std::vector<uint8_t>> buffers;
        if (receive(mInputComponent, mCommandChannelName, header, commands, buffers))
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
        std::vector<std::vector<uint8_t>> buffers(1);
        auto statusProto = statusComposite.initProto();
        std::vector<double> elements{ stateVal, 0.0 };
        // copy actual buffer data
        buffers[0].resize(elements.size() * sizeof(double));
        std::memcpy(buffers[0].data(), elements.data(), elements.size() * sizeof(double));
        publish(mOutputComponent, mStateChannelName, statusProto, isaac_message::StateProtoId, buffers);
    }
}

void ScissorLiftSimulator::onComponentChange()
{
    IsaacComponent::onComponentChange();

    if (auto attr = mPrim.GetAttribute(pxr::TfToken("inputComponent")))
    {
        attr.Get(&mInputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("outputComponent")))
    {
        attr.Get(&mOutputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("commandChannelName")))
    {
        attr.Get(&mCommandChannelName);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("stateChannelName")))
    {
        attr.Get(&mStateChannelName);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("liftJointName")))
    {
        attr.Get(&mLiftJointName);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("articulationPath")))
    {
        attr.Get(&mArticulationPath);
    }

    if (mArticulationPath.size() <= 1)
    {
        return;
    }

    if (mDynamicControlPtr->peekObjectType(mArticulationPath.c_str()) ==
        omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        mArticulationHandle = mDynamicControlPtr->getArticulation(mArticulationPath.c_str());
    }
    else
    {
        CARB_LOG_ERROR("Articulation %s is not valid art", mArticulationPath.c_str());
        return;
    }
    if (!mArticulationHandle)
    {
        CARB_LOG_ERROR("Articulation %s not found", mArticulationPath.c_str());
        return;
    }
    mUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(mStage);
}
}
}
}
