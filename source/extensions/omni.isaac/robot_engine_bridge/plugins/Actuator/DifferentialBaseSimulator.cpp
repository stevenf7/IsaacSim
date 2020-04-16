// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <omni/isaac/dynamic_control/DynamicControl.h>

#include <string>
#include <vector>
#include <carb/InterfaceUtils.h>
#include <carb/profiler/Profile.h>
#include <carb/filesystem/IFileSystem.h>

#include <omni/usd/UsdUtils.h>

#include "../Core/IsaacComponent.h"
#include <omni/isaac/utils/Conversions.h>
#include "DifferentialBaseSimulator.h"

namespace omni
{
namespace isaac
{
using utils::conversions::asGfRotation;
using utils::conversions::asGfVec3d;
namespace robot_engine_bridge
{

DifferentialBaseSimulator::DifferentialBaseSimulator(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
    mCommandedSpeed = pxr::GfVec2d(0);
    mLastSpeed = pxr::GfVec2d(0);
    mBrakeRequested = false;
    mLastAcceleration = pxr::GfVec2d(0);
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);

    onComponentChange();
}


void DifferentialBaseSimulator::onStart()
{
    mZUp = UsdGeomGetStageUpAxis(mStage) == "Z" ? true : false;
    onComponentChange();
}

void DifferentialBaseSimulator::tick()
{
    CARB_PROFILE_ZONE(0, "REB DifferentialBaseSimulator Tick");

    IsaacMessage<isaac_message::State> commandComposite;
    auto command_composite_proto = commandComposite.initProto();
    {
        // Receive current command
        std::vector<std::vector<uint8_t>> buffers;
        MessageHeader header;
        if (receive(mInputComponent, mCommandChannelName, header, command_composite_proto, buffers))
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
                CARB_LOG_ERROR("Wrong number of elements: %d", elements.size());
            }
            mCommandedSpeed[0] = pxr::GfClamp(elements[0], -mMaximumSpeed[0], mMaximumSpeed[0]);
            mCommandedSpeed[1] = pxr::GfClamp(elements[1], -mMaximumSpeed[1], mMaximumSpeed[1]);

            mLastCommandTime = mTimeSeconds;

            // CARB_LOG_ERROR("Received %f %f %d %d", elements[0], elements[1], buffers.size(), elements.size());
        }
        // Use latest command only for a certain period of time in case no new command arrives
        if (mTimeSeconds - mLastCommandTime > mMaximumTimeWithoutCommand)
        {
            mCommandedSpeed = pxr::GfVec2d(0, 0);
        }
    }
    // Compute new velocities
    getWheelDesireSpeed(mCommandedSpeed);
    // CARB_LOG_ERROR("Speeds %f %f", mWheelDesiredSpeed[0], mWheelDesiredSpeed[1]);
    if (mArticulationHandle)
    {
        mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
    }
    else
    {
        CARB_LOG_ERROR("mArticulationHandle Invalid");
        return;
    }
    // Apply velocities
    if (mWheelFLHandle)
    {
        mDynamicControlPtr->setDofVelocityTarget(mWheelFLHandle, getVelocity(static_cast<float>(mWheelDesiredSpeed[0])));
    }
    else
    {
        CARB_LOG_ERROR("mWheelFLHandle Invalid");
        return;
    }
    if (mWheelFRHandle)
    {
        mDynamicControlPtr->setDofVelocityTarget(mWheelFRHandle, getVelocity(static_cast<float>(mWheelDesiredSpeed[1])));
    }
    else
    {
        CARB_LOG_ERROR("mWheelFRHandle Invalid");
        return;
    }

    IsaacMessage<isaac_message::State> stateMessage;
    auto stateMessageProto = stateMessage.initProto();
    stateMessageProto.setSchema("");

    auto tensorProto = stateMessageProto.initPack();
    tensorProto.setElementType(ElementType::FLOAT64);
    tensorProto.initSizes(3);
    tensorProto.setSizes({ 1, 1, 4 });
    tensorProto.setScanlineStride(0);
    tensorProto.setDataBufferIndex(0);

    auto chassisPose = mDynamicControlPtr->getRigidBodyPose(mChassisHandle);
    auto chassisLinVel = mDynamicControlPtr->getRigidBodyLinearVelocity(mChassisHandle);
    auto chassisAngVel = mDynamicControlPtr->getRigidBodyAngularVelocity(mChassisHandle);

    // CARB_LOG_ERROR("[%f %f %f] [%f %f %f] [%f %f %f]", chassisPose.p.x, chassisPose.p.y, chassisPose.p.z,
    // chassisLinVel.x, chassisLinVel.y, chassisLinVel.z, chassisAngVel.x, chassisAngVel.y, chassisAngVel.z);

    pxr::GfVec3d vecForward =
        asGfRotation(chassisPose.r).TransformDir(pxr::GfVec3d(mRobotFront[0], mRobotFront[1], mRobotFront[2]));

    pxr::GfVec2d measuredSpeed = pxr::GfVec2d(
        pxr::GfDot(asGfVec3d(chassisLinVel), vecForward) * mUnitScale, mZUp ? chassisAngVel.z : chassisAngVel.y);
    pxr::GfVec2d measuredAcceleration = (measuredSpeed - mLastSpeed) / mTimeDelta;
    mLastAcceleration +=
        timedSmoothingFactor(mTimeDelta, mAccelerationSmoothing) * (measuredAcceleration - mLastAcceleration);
    // no data to set in state message, skip ?
    std::vector<double> real_data = {
        mLastSpeed[0],
        mLastSpeed[1],
        mLastAcceleration[0],
        mLastAcceleration[1],
    };

    std::vector<std::vector<uint8_t>> buffers(1);
    buffers[0] = std::vector<uint8_t>(real_data.size() * sizeof(double));
    std::memcpy(buffers[0].data(), real_data.data(), real_data.size() * sizeof(double));
    publish(mOutputComponent, mStateChannelName, stateMessageProto, isaac_message::StateProtoId, buffers);
    mLastSpeed = measuredSpeed;
}


void DifferentialBaseSimulator::onComponentChange()
{
    IsaacComponent::onComponentChange();
    double stageUnits = UsdGeomGetStageMetersPerUnit(mStage);

    std::string chassisPath;
    std::string wheelFLName;
    std::string wheelFRName;

    if (auto attr = mPrim.GetAttribute(pxr::TfToken("chassisPath")))
    {
        attr.Get(&chassisPath);
    }
    // names for the left/right joints
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("leftWheelName")))
    {
        attr.Get(&wheelFLName);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("rightWheelName")))
    {
        attr.Get(&wheelFRName);
    }
    // Parse component and channel
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("inputComponent")))
    {
        attr.Get(&mInputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("commandChannelName")))
    {
        attr.Get(&mCommandChannelName);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("outputComponent")))
    {
        attr.Get(&mOutputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("stateChannelName")))
    {
        attr.Get(&mStateChannelName);
    }


    // Parse parameters
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("robotFront")))
    {
        attr.Get(&mRobotFront);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("maxSpeed")))
    {
        attr.Get(&mMaximumSpeed);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("maxMotorTorque")))
    {
        attr.Get(&mMaxMotorTorque);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("proportionalGain")))
    {
        attr.Get(&mProportionalGain);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("brakeTorque")))
    {
        attr.Get(&mBrakeTorque);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("accelerationSmoothing")))
    {
        attr.Get(&mAccelerationSmoothing);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("useProprotionalDriver")))
    {
        attr.Get(&mUseProprotionalDriver);
    }
    if (chassisPath.size() <= 1)
    {
        return;
    }

    if (mDynamicControlPtr->peekObjectType(chassisPath.c_str()) == omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        mArticulationHandle = mDynamicControlPtr->getArticulation(chassisPath.c_str());
    }
    else
    {
        CARB_LOG_ERROR("Chassis is not valid art");
        return;
    }
    if (!mArticulationHandle)
    {
        CARB_LOG_ERROR("Articulation not found for chassis");
        return;
    }
    mChassisHandle = mDynamicControlPtr->getArticulationRootBody(mArticulationHandle);

    mWheelFLHandle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, wheelFLName.c_str());
    mWheelFRHandle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, wheelFRName.c_str());

    // Get the wheel prim from the joint
    if (!mWheelFLHandle)
    {
        CARB_LOG_ERROR("mWheelFLJoint %s not valid", wheelFLName.c_str());
        return;
    }
    if (!mWheelFRHandle)
    {
        CARB_LOG_ERROR("mWheelFRJoint %s not valid", wheelFRName.c_str());
        return;
    }

    auto leftWheel = mDynamicControlPtr->getDofChildBody(mWheelFLHandle);
    auto rightWheel = mDynamicControlPtr->getDofChildBody(mWheelFRHandle);

    if (leftWheel && rightWheel)
    {
        omni::isaac::dynamic_control::DcTransform poseLeft = mDynamicControlPtr->getRigidBodyPose(leftWheel);
        omni::isaac::dynamic_control::DcTransform poseRight = mDynamicControlPtr->getRigidBodyPose(rightWheel);

        pxr::GfVec3d wheelFL_0_world(poseLeft.p.x, poseLeft.p.y, poseLeft.p.z);
        pxr::GfVec3d wheelRL_0_world(poseRight.p.x, poseRight.p.y, poseRight.p.z);
        mWheelBase = pxr::GfGetLength(wheelFL_0_world - wheelRL_0_world);
        mWheelBase *= stageUnits;
        CARB_LOG_INFO("DifferentialBaseSimulator Wheelbase %f", mWheelBase);
    }
    else
    {
        CARB_LOG_ERROR("Wheel rigid body not valid");
    }
}

void DifferentialBaseSimulator::getWheelDesireSpeed(const pxr::GfVec2d& mCommandedSpeed)
{
    mBrakeRequested =
        pxr::GfIsClose(mCommandedSpeed[0], 0.0f, FLT_EPSILON) && pxr::GfIsClose(mCommandedSpeed[1], 0.0f, FLT_EPSILON);
    mWheelDesiredSpeed[0] = (mCommandedSpeed[0] - mCommandedSpeed[1] * mWheelBase);
    mWheelDesiredSpeed[1] = (mCommandedSpeed[0] + mCommandedSpeed[1] * mWheelBase);
}

float DifferentialBaseSimulator::getVelocity(float target)
{
    return pxr::GfClamp(target * mProportionalGain, -mMaxMotorTorque, mMaxMotorTorque);
}

float DifferentialBaseSimulator::timedSmoothingFactor(float dt, float lambda)
{
    if (lambda <= dt * 0.01f)
    {
        return 0.0;
    }
    else
    {
        return 1.0f - std::exp(-dt / lambda);
    }
}
}
}
}
