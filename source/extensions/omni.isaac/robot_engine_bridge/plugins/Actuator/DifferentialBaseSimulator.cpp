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
}


void DifferentialBaseSimulator::onStart()
{
    mZUp = UsdGeomGetStageUpAxis(mStage) == "Z" ? true : false;
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    onComponentChange();
}

void DifferentialBaseSimulator::tick()
{
    CARB_PROFILE_ZONE(0, "REB DifferentialBaseSimulator Tick");

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
                CARB_LOG_ERROR("Wrong number of elements: %d", elements.size());
            }
            mCommandedSpeed[0] = pxr::GfClamp(elements[0], -mMaximumSpeed[0], mMaximumSpeed[0]) / mUnitScale;
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
        CARB_LOG_ERROR("Differential Base Articulation Handle Is Invalid");
        return;
    }
    // Apply velocities
    if (mWheelFLHandle)
    {
        mDynamicControlPtr->setDofVelocityTarget(mWheelFLHandle, mWheelDesiredSpeed[0]);
    }
    else
    {
        CARB_LOG_ERROR("Differential Base Left Wheel Invalid");
        return;
    }
    if (mWheelFRHandle)
    {
        mDynamicControlPtr->setDofVelocityTarget(mWheelFRHandle, mWheelDesiredSpeed[1]);
    }
    else
    {
        CARB_LOG_ERROR("Differential Base Right Wheel Invalid");
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

    std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
    buffers[0] = std::make_unique<IsaacHostBuffer>(real_data.size() * sizeof(double));
    std::memcpy(buffers[0]->data(), real_data.data(), real_data.size() * sizeof(double));
    publish(mOutputComponent, mStateChannelName, stateMessage, isaac_message::StateProtoId, buffers);
    mLastSpeed = measuredSpeed;
}


void DifferentialBaseSimulator::onComponentChange()
{
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineDifferentialBase& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineDifferentialBase)mPrim;

    // Parse component and channel
    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mCommandChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mStateChannelName);

    // Parse parameters

    isaac::utils::safeGetAttribute(typedPrim.GetRobotFrontAttr(), mRobotFront);
    isaac::utils::safeGetAttribute(typedPrim.GetMaxSpeedAttr(), mMaximumSpeed);
    isaac::utils::safeGetAttribute(typedPrim.GetMaxTimeWithoutCommandAttr(), mMaximumTimeWithoutCommand);
    isaac::utils::safeGetAttribute(typedPrim.GetAccelerationSmoothingAttr(), mAccelerationSmoothing);
    isaac::utils::safeGetAttribute(typedPrim.GetWheelRadiusAttr(), mWheelRadius);
    mWheelRadius = mWheelRadius / mUnitScale;

    isaac::utils::safeGetAttribute(typedPrim.GetWheelBaseAttr(), mWheelBase);
    mWheelBase = mWheelBase / mUnitScale;

    pxr::SdfPath chassisPath;
    std::string wheelFLName;
    std::string wheelFRName;

    pxr::SdfPathVector targets;
    typedPrim.GetChassisPrimRel().GetTargets(&targets);
    if (targets.size() == 0)
    {
        return;
    }

    chassisPath = targets[0];

    if (mDynamicControlPtr->peekObjectType(chassisPath.GetString().c_str()) ==
        omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        mArticulationHandle = mDynamicControlPtr->getArticulation(chassisPath.GetString().c_str());
    }
    else
    {
        CARB_LOG_ERROR("chassisPrim is not a valid articulation");
        return;
    }
    if (!mArticulationHandle)
    {
        CARB_LOG_ERROR("Articulation not found for chassisPrim");
        return;
    }
    mChassisHandle = mDynamicControlPtr->getArticulationRootBody(mArticulationHandle);


    isaac::utils::safeGetAttribute(typedPrim.GetLeftWheelJointNameAttr(), wheelFLName);

    mWheelFLHandle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, wheelFLName.c_str());
    // Get the wheel prim from the joint
    if (!mWheelFLHandle)
    {
        CARB_LOG_ERROR("leftWheelJointPrim %s not valid", wheelFLName.c_str());
        return;
    }
    isaac::utils::safeGetAttribute(typedPrim.GetRightWheelJointNameAttr(), wheelFRName);


    mWheelFRHandle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, wheelFRName.c_str());

    if (!mWheelFRHandle)
    {
        CARB_LOG_ERROR("rightWheelJointPrim %s not valid", wheelFRName.c_str());
        return;
    }


    // auto leftWheel = mDynamicControlPtr->getDofChildBody(mWheelFLHandle);
    // auto rightWheel = mDynamicControlPtr->getDofChildBody(mWheelFRHandle);

    // if (leftWheel && rightWheel)
    // {
    //     omni::isaac::dynamic_control::DcTransform poseLeft = mDynamicControlPtr->getRigidBodyPose(leftWheel);
    //     omni::isaac::dynamic_control::DcTransform poseRight = mDynamicControlPtr->getRigidBodyPose(rightWheel);

    //     pxr::GfVec3d wheelFL_0_world(poseLeft.p.x, poseLeft.p.y, poseLeft.p.z);
    //     pxr::GfVec3d wheelRL_0_world(poseRight.p.x, poseRight.p.y, poseRight.p.z);
    //     mWheelBase = pxr::GfGetLength(wheelFL_0_world - wheelRL_0_world);
    //     CARB_LOG_INFO("DifferentialBaseSimulator Wheelbase %f", mWheelBase);
    // }
    // else
    // {
    //     CARB_LOG_ERROR("Wheel rigid body not valid");
    // }
}

void DifferentialBaseSimulator::getWheelDesireSpeed(const pxr::GfVec2d& mCommandedSpeed)
{
    mBrakeRequested =
        pxr::GfIsClose(mCommandedSpeed[0], 0.0f, FLT_EPSILON) && pxr::GfIsClose(mCommandedSpeed[1], 0.0f, FLT_EPSILON);
    // mCommandedSpeed[0] is in stageunits/s
    // mCommandedSpeed[1] is in rad/s
    // mWheelBase is in stageunits
    // mWheelRadius is in stageunits
    // mWheelDesiredSpeed is in rad/s

    mWheelDesiredSpeed[0] = (mCommandedSpeed[0] - mCommandedSpeed[1] * mWheelBase) / mWheelRadius;
    mWheelDesiredSpeed[1] = (mCommandedSpeed[0] + mCommandedSpeed[1] * mWheelBase) / mWheelRadius;
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
