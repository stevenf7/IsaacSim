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
#include "HolonomicBaseSimulator.h"

namespace omni
{
namespace isaac
{
using utils::conversions::asGfRotation;
using utils::conversions::asGfVec3d;
namespace robot_engine_bridge
{

HolonomicBaseSimulator::HolonomicBaseSimulator(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}


void HolonomicBaseSimulator::onStart()
{
    mZUp = UsdGeomGetStageUpAxis(mStage) == "Z" ? true : false;
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    onComponentChange();
}

void HolonomicBaseSimulator::tick()
{
    CARB_PROFILE_ZONE(0, "REB HolonomicBaseSimulator Tick");

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
            if (elements.size() != 3)
            {
                CARB_LOG_ERROR("Wrong number of elements: %lu", elements.size());
            }
            // Input comes in m/s
            mCommandedSpeed[0] = pxr::GfClamp(elements[0], -mMaximumSpeed[0], mMaximumSpeed[0]) / mUnitScale;
            mCommandedSpeed[1] = pxr::GfClamp(elements[1], -mMaximumSpeed[0], mMaximumSpeed[0]) / mUnitScale;
            mCommandedSpeed[2] = pxr::GfClamp(elements[2], -mMaximumSpeed[1], mMaximumSpeed[1]);

            mLastCommandTime = mTimeSeconds;

            // CARB_LOG_ERROR("Received %f %f %d %d", elements[0], elements[1], buffers.size(), elements.size());
        }
        // Use latest command only for a certain period of time in case no new command arrives
        if (mTimeSeconds - mLastCommandTime > mMaximumTimeWithoutCommand)
        {
            mCommandedSpeed = pxr::GfVec3d(0, 0, 0);
        }
    }
    // Compute new velocities
    mWheelDesiredSpeed = getWheelDesireSpeed(mCommandedSpeed);
    if (mArticulationHandle)
    {
        mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
    }
    else
    {
        CARB_LOG_ERROR("Holonomic Base Articulation Handle Is Invalid");
        return;
    }
    // Apply velocities
    if (mWheel1Handle)
    {
        mDynamicControlPtr->setDofVelocityTarget(mWheel1Handle, getVelocity(static_cast<float>(mWheelDesiredSpeed[0])));
    }
    else
    {
        CARB_LOG_ERROR("Holonomic Base Wheel 1 Handle Invalid");
        return;
    }
    if (mWheel2Handle)
    {
        mDynamicControlPtr->setDofVelocityTarget(mWheel2Handle, getVelocity(static_cast<float>(mWheelDesiredSpeed[1])));
    }
    else
    {
        CARB_LOG_ERROR("Holonomic Base Wheel 1 Handle Invalid");
        return;
    }

    if (mWheel3Handle)
    {
        mDynamicControlPtr->setDofVelocityTarget(mWheel3Handle, getVelocity(static_cast<float>(mWheelDesiredSpeed[2])));
    }
    else
    {
        CARB_LOG_ERROR("Holonomic Base Wheel 1 Handle Invalid");
        return;
    }
    IsaacMessage<isaac_message::State> stateMessage;
    auto stateMessageProto = stateMessage.initProto();
    stateMessageProto.setSchema("");

    auto tensorProto = stateMessageProto.initPack();
    tensorProto.setElementType(ElementType::FLOAT64);
    tensorProto.initSizes(3);
    tensorProto.setSizes({ 1, 1, 5 });
    tensorProto.setScanlineStride(0);
    tensorProto.setDataBufferIndex(0);

    auto chassisPose = mDynamicControlPtr->getRigidBodyPose(mChassisHandle);
    auto chassisLinVel = mDynamicControlPtr->getRigidBodyLinearVelocity(mChassisHandle);
    auto chassisAngVel = mDynamicControlPtr->getRigidBodyAngularVelocity(mChassisHandle);

    // CARB_LOG_ERROR("[%f %f %f] [%f %f %f] [%f %f %f]", chassisPose.p.x, chassisPose.p.y, chassisPose.p.z,
    // chassisLinVel.x, chassisLinVel.y, chassisLinVel.z, chassisAngVel.x, chassisAngVel.y, chassisAngVel.z);

    pxr::GfVec3d vecForward =
        asGfRotation(chassisPose.r).TransformDir(pxr::GfVec3d(mRobotFront[0], mRobotFront[1], mRobotFront[2]));
    pxr::GfVec3d vecRight = pxr::GfCross(vecForward, mZUp ? pxr::GfVec3d(0, 0, 1) : pxr::GfVec3d(0, 1, 0));


    // CARB_LOG_ERROR("forward %f %f %f rotated %f %f %f", mRobotFront[0], mRobotFront[1], mRobotFront[2],
    // vecForward[0],
    //                vecForward[1], vecForward[2]);

    pxr::GfVec3d measuredSpeed;
    auto forwardVel = pxr::GfDot(asGfVec3d(chassisLinVel), vecForward);
    auto rightVel = pxr::GfDot(asGfVec3d(chassisLinVel), vecRight);
    measuredSpeed[0] = forwardVel * mUnitScale;
    measuredSpeed[1] = rightVel * mUnitScale;
    measuredSpeed[2] = mZUp ? chassisAngVel.z : chassisAngVel.y;

    pxr::GfVec3d measuredAcceleration = (measuredSpeed - mLastSpeed) / mTimeDelta;
    mLastAcceleration +=
        timedSmoothingFactor(mTimeDelta, mAccelerationSmoothing) * (measuredAcceleration - mLastAcceleration);

    // CARB_LOG_ERROR("Request %f %f %f Actual %f %f %f", mCommandedSpeed[0], mCommandedSpeed[1], mCommandedSpeed[2],
    //                mLastSpeed[0], mLastSpeed[1], mLastSpeed[2]);

    // no data to set in state message, skip ?
    std::vector<double> real_data = {
        mLastSpeed[0], // x velocity
        mLastSpeed[1], // y velocity
        mLastSpeed[2], // angular velocity
        mLastAcceleration[0], // x acceleration
        mLastAcceleration[1] // y acceleration
    };

    std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
    buffers[0] = std::make_unique<IsaacHostBuffer>(real_data.size() * sizeof(double));
    std::memcpy(buffers[0]->data(), real_data.data(), real_data.size() * sizeof(double));
    publish(mOutputComponent, mStateChannelName, stateMessage, isaac_message::StateProtoId, buffers);
    mLastSpeed = measuredSpeed;
}


void HolonomicBaseSimulator::onComponentChange()
{
    IsaacComponent::onComponentChange();
    double stageUnits = UsdGeomGetStageMetersPerUnit(mStage);

    const pxr::RobotEngineBridgeSchemaRobotEngineHolonomicBase& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineHolonomicBase)mPrim;

    // Parse component and channel
    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mCommandChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mStateChannelName);

    // Parse parameters

    isaac::utils::safeGetAttribute(typedPrim.GetRobotFrontAttr(), mRobotFront);
    // CARB_LOG_ERROR("forward %f %f %f", mRobotFront[0], mRobotFront[1], mRobotFront[2]);
    isaac::utils::safeGetAttribute(typedPrim.GetMaxSpeedAttr(), mMaximumSpeed);
    isaac::utils::safeGetAttribute(typedPrim.GetMaxTimeWithoutCommandAttr(), mMaximumTimeWithoutCommand);
    isaac::utils::safeGetAttribute(typedPrim.GetAccelerationSmoothingAttr(), mAccelerationSmoothing);
    isaac::utils::safeGetAttribute(typedPrim.GetWheelBaseAttr(), mWheelBase);
    isaac::utils::safeGetAttribute(typedPrim.GetWheelRadiusAttr(), mWheelRadius);


    pxr::SdfPath chassisPath;
    std::string wheel1Name;
    std::string wheel2Name;
    std::string wheel3Name;

    pxr::SdfPathVector targets;
    typedPrim.GetArticulationPrimRel().GetTargets(&targets);
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


    isaac::utils::safeGetAttribute(typedPrim.GetWheel1JointNameAttr(), wheel1Name);

    mWheel1Handle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, wheel1Name.c_str());
    // Get the wheel prim from the joint
    if (!mWheel1Handle)
    {
        CARB_LOG_ERROR("wheel1JointPrim %s not valid", wheel1Name.c_str());
        return;
    }
    isaac::utils::safeGetAttribute(typedPrim.GetWheel2JointNameAttr(), wheel2Name);


    mWheel2Handle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, wheel2Name.c_str());

    if (!mWheel2Handle)
    {
        CARB_LOG_ERROR("wheel2JointPrim %s not valid", wheel2Name.c_str());
        return;
    }

    isaac::utils::safeGetAttribute(typedPrim.GetWheel3JointNameAttr(), wheel3Name);

    mWheel3Handle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, wheel3Name.c_str());

    if (!mWheel3Handle)
    {
        CARB_LOG_ERROR("wheel3JointPrim %s not valid", wheel3Name.c_str());
        return;
    }


    // auto wheel1 = mDynamicControlPtr->getDofChildBody(mWheel1Handle);
    // auto wheel2 = mDynamicControlPtr->getDofChildBody(mWheel2Handle);
    // auto wheel3 = mDynamicControlPtr->getDofChildBody(mWheel3Handle);

    // if (wheel1 && wheel2 && wheel3)
    // {
    //     omni::isaac::dynamic_control::DcTransform poseLeft = mDynamicControlPtr->getRigidBodyPose(mChassisHandle);
    //     omni::isaac::dynamic_control::DcTransform poseRight = mDynamicControlPtr->getRigidBodyPose(wheel1);

    //     pxr::GfVec3d wheelFL_0_world(poseLeft.p.x, poseLeft.p.y, poseLeft.p.z);
    //     pxr::GfVec3d wheelRL_0_world(poseRight.p.x, poseRight.p.y, poseRight.p.z);
    //     mWheelBase = pxr::GfGetLength(wheelFL_0_world - wheelRL_0_world);
    //     CARB_LOG_ERROR("HolonomicBaseSimulator Wheelbase %f", mWheelBase);
    // }
    // else
    // {
    //     CARB_LOG_ERROR("Wheel rigid body not valid");
    // }
}

pxr::GfVec3d HolonomicBaseSimulator::getWheelDesireSpeed(const pxr::GfVec3d& mCommandedSpeed)
{
    double kOneByThree = 1.0 / 3.0;
    double kOneBySqrtThree = 1.0 / sqrt(3.0);
    double wheel_distance = mWheelBase / mUnitScale;
    double wheel_radius = mWheelRadius / mUnitScale;
    // CARB_LOG_ERROR("HolonomicBaseSimulator %f %f %f", mCommandedSpeed[0], mCommandedSpeed[1], mCommandedSpeed[2]);

    pxr::GfMatrix3d forward_matrix(0, -kOneBySqrtThree, kOneBySqrtThree, kOneByThree * 2, -kOneByThree, -kOneByThree,
                                   -kOneByThree / wheel_distance, -kOneByThree / wheel_distance,
                                   -kOneByThree / wheel_distance);


    pxr::GfMatrix3d wheels_radius_matrix(wheel_radius, 0, 0, 0, wheel_radius, 0, 0, 0, wheel_radius);
    auto transform_matrix = forward_matrix * wheels_radius_matrix;
    auto inverse_matrix = transform_matrix.GetInverse();
    pxr::GfVec3d wheel_speed = inverse_matrix * mCommandedSpeed;

    // mBrakeRequested =
    //     pxr::GfIsClose(mCommandedSpeed[0], 0.0f, FLT_EPSILON) && pxr::GfIsClose(mCommandedSpeed[1], 0.0f,
    //     FLT_EPSILON);
    return wheel_speed;
}

float HolonomicBaseSimulator::getVelocity(float target)
{
    return target; // pxr::GfClamp(target * mProportionalGain, -mMaxMotorTorque, mMaxMotorTorque);
}

float HolonomicBaseSimulator::timedSmoothingFactor(float dt, float lambda)
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
