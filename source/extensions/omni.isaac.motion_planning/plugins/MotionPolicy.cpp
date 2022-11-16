// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "MotionPlanningPCH.h"
// clang-format on
#include "MotionPolicy.h"

#include <carb/InterfaceUtils.h>

#include <lula/robot_description.h>

#include <math.h>
#include <memory>

using namespace lula;

Eigen::Vector3d asEigenVector3d(const carb::Float3& v)
{
    return Eigen::Vector3d(v.x, v.y, v.z);
}

carb::Float3 asCarbFloat3(const Eigen::Vector3d& v)
{
    return carb::Float3({ static_cast<float>(v[0]), static_cast<float>(v[1]), static_cast<float>(v[2]) });
}

MotionPolicy::MotionPolicy(pxr::UsdStageWeakPtr stage, omni::isaac::dynamic_control::DynamicControl* dynamicControl)
    : mState(1) // Set `mState` to a zero vector of minimum length (overwritten in `initialize()`).
{
    mStage = stage;
    mDynamicControl = dynamicControl;
    mFrequency = 120.0f;
    mFixedDt = 1.0f / mFrequency;

    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
}
void MotionPolicy::initialize(const std::string& robotUrdfPath,
                              const std::string& robotDescriptorPath,
                              const std::string& rmpFlowCommonPath,
                              const std::string& controlFrame)
{
    mRegisteredObstacles.clear();
    mRmpflowWorld = lula::CreateWorld();
    mRmpflowWorldView = mRmpflowWorld->addWorldView();
    mRmpflowPolicy = std::make_shared<rmp::RmpflowRobotPolicy>();
    auto robotDescription = lula::LoadRobot(robotDescriptorPath, robotUrdfPath);
    mKinematics = robotDescription->kinematics();
    mEndEffectorFrame = mKinematics->frame(controlFrame);

    CARB_LOG_INFO("Creating rmp from \n %s\n %s\n %s", robotUrdfPath.c_str(), robotDescriptorPath.c_str(),
                  rmpFlowCommonPath.c_str());

    YAML::Node rmpConfigYAML;
    try
    {
        rmpConfigYAML = YAML::LoadFile(rmpFlowCommonPath);
    }
    catch (YAML::BadFile)
    {
        CARB_LOG_ERROR("Error %s cound not be found", rmpFlowCommonPath.c_str());
    }
    YAML::Node robotYAML;
    try
    {
        robotYAML = YAML::LoadFile(robotDescriptorPath);
    }
    catch (YAML::BadFile)
    {
        CARB_LOG_ERROR("Error %s cound not be found", robotDescriptorPath.c_str());
    }

    auto robotURDF = urdf::parseURDFFile(robotUrdfPath);
    if (robotURDF == 0)
    {
        CARB_LOG_ERROR("Error %s cound not be found/parsed", robotUrdfPath.c_str());
    }
    mRmpflowPolicy->Build(
        rmpConfigYAML, std::make_shared<kinematics::Robot>(robotURDF, robotYAML), mRmpflowWorldView, controlFrame);

    q = mRmpflowPolicy->GetDefaultConfig();
    qd = Eigen::VectorXd::Zero(mRmpflowPolicy->cspace_dim());
    mState = math::State(q, qd);
    mEndEffectorError.resize(4);

    mRmpflowPolicyInitialized = true;
}

void MotionPolicy::setFrequency(const float frequency)
{
    if (frequency > 0)
    {
        mFrequency = frequency;
        mFixedDt = 1.0f / mFrequency;
    }
}

void MotionPolicy::reset()
{
    q = mRmpflowPolicy->GetDefaultConfig();
    qd = Eigen::VectorXd::Zero(mRmpflowPolicy->cspace_dim());
    mState = math::State(q, qd);
}

void MotionPolicy::step(const float t, const float sourceDt)
{
    mRmpflowPolicy->updateWorldView();

    float dt = sourceDt;

    static double remaining = 0.f;
    int numRmpSubsteps = std::max(1, (int)((dt + remaining) * (mFrequency)));

    const int maxIters = 6;
    if (numRmpSubsteps > maxIters)
        numRmpSubsteps = maxIters;

    for (int rmpSubstep = 0; rmpSubstep < numRmpSubsteps; rmpSubstep++)
    {
        // printf("t: %f, dt: %f, t+: %f \n", t, dt, t + dt / numRmpSubsteps * rmpSubstep);
        auto qdd = mRmpflowPolicy->Eval(mState);
        mState = mState.Step(dt / numRmpSubsteps, qdd);
    }

    mEndEffectorPose = mKinematics->pose(mState.pos(), mEndEffectorFrame);
    const Eigen::Matrix3d endEffectorRotationMatrix = mEndEffectorPose.rotation.matrix();

    mTargetOrig = mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::ORIG)->data()->target;
    if (mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_X)->data().has_value())
    {
        mTargetAxisX = mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_X)->data()->target;
    }
    else
    {
        mTargetAxisX = endEffectorRotationMatrix.col(0);
    }
    if (mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_Y)->data().has_value())
    {
        mTargetAxisY = mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_Y)->data()->target;
    }
    else
    {
        mTargetAxisY = endEffectorRotationMatrix.col(1);
    }
    if (mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_Z)->data().has_value())
    {
        mTargetAxisZ = mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_Z)->data()->target;
    }
    else
    {
        mTargetAxisZ = endEffectorRotationMatrix.col(2);
    }

    mEndEffectorError[0] = (mTargetOrig - mEndEffectorPose.translation).norm();
    mEndEffectorError[1] = (mTargetAxisX - endEffectorRotationMatrix.col(0)).norm();
    mEndEffectorError[2] = (mTargetAxisY - endEffectorRotationMatrix.col(1)).norm();
    mEndEffectorError[3] = (mTargetAxisZ - endEffectorRotationMatrix.col(2)).norm();

    if (mRobotHandle)
    {
        if (t > 0)
        {
            mDynamicControl->wakeUpArticulation(mRobotHandle);
        }

        for (size_t idx = 0; idx < mRmpflowPolicy->cspace_dim(); idx++)
        {
            omni::isaac::dynamic_control::DcHandle dof = mDynamicControl->getArticulationDof(mRobotHandle, idx);
            if (dof)
            {
                if (isnan(mState.pos()[idx]) == false)
                {
                    mDynamicControl->setDofPositionTarget(dof, static_cast<float>(mState.pos()[idx]));
                }
                else
                {
                    q[idx] = mDynamicControl->getDofPosition(dof);
                    qd[idx] = mDynamicControl->getDofVelocity(dof);
                    mState.pos()[idx] = mDynamicControl->getDofPosition(dof);
                    mState.vel()[idx] = 0;
                }
            }
        }
    }
}


void MotionPolicy::setTargetGlobal(const carb::Float3& position, const carb::Float4& rotation)
{
    // convert the position and rotation into local coordinates
    if (mRobotPrim)
    {
        const pxr::GfTransform parent(omni::usd::UsdUtils::getWorldTransformMatrix(mRobotPrim));

        pxr::GfRotation qinv = parent.GetRotation().GetQuat().GetConjugate();
        pxr::GfQuatd tr =
            (pxr::GfRotation(pxr::GfQuatd(rotation.w, rotation.x, rotation.y, rotation.z)) * qinv).GetQuat();
        pxr::GfVec3d tp = qinv.TransformDir(pxr::GfVec3d(position.x, position.y, position.z) - parent.GetTranslation());

        mRmpflowPolicy->SetPoseTarget(
            Eigen::Vector3d(tp[0], tp[1], tp[2]),
            Eigen::Quaterniond(tr.GetReal(), tr.GetImaginary()[0], tr.GetImaginary()[1], tr.GetImaginary()[2]));
    }
    else
    {
    }
}
void MotionPolicy::setTargetLocal(const carb::Float3& position, const carb::Float4& rotation)
{
    mRmpflowPolicy->SetPoseTarget(Eigen::Vector3d(position.x, position.y, position.z),
                                  Eigen::Quaterniond(rotation.w, rotation.x, rotation.y, rotation.z));
}
void MotionPolicy::goLocal(const omni::isaac::motion_planning::PartialPoseCommand& command)
{
    auto partialPose = lula::rmp::PartialPoseCommand();
    for (size_t i = 0; i < command.commands.size(); i++)
    {
        if (command.commands[i].has_value())
        {
            auto temp = command.commands[i];
            auto target = asEigenVector3d(temp->target);
            if (temp->approach.has_value())
            {
                auto approach = lula::rmp::TargetRmp::Approach(
                    asEigenVector3d(temp->approach->direction), temp->approach->standoff, temp->approach->std_dev);

                partialPose.commands[i] = lula::rmp::TargetRmp::Command(target, approach);
            }
            else
            {
                partialPose.commands[i] = lula::rmp::TargetRmp::Command(asEigenVector3d(temp->target).normalized());
            }
        }
        else
        {
            // CARB_LOG_ERROR("Target: %d no data", i);
        }
    }
    mRmpflowPolicy->SetPartialPoseTarget(partialPose);
}
std::vector<double> MotionPolicy::getError()
{
    return mEndEffectorError;
}

std::vector<carb::Float3> MotionPolicy::getRmpState()
{
    std::vector<carb::Float3> endEffectorState(4);

    endEffectorState[0] = asCarbFloat3(mEndEffectorPose.translation);
    const Eigen::Matrix3d endEffectorRotationMatrix = mEndEffectorPose.rotation.matrix();
    endEffectorState[1] = asCarbFloat3(endEffectorRotationMatrix.col(0));
    endEffectorState[2] = asCarbFloat3(endEffectorRotationMatrix.col(1));
    endEffectorState[3] = asCarbFloat3(endEffectorRotationMatrix.col(2));

    return endEffectorState;
}

std::vector<carb::Float3> MotionPolicy::getRmpTarget()
{
    std::vector<carb::Float3> endEffectorTarget(4);

    endEffectorTarget[0] = asCarbFloat3(mTargetOrig);
    endEffectorTarget[1] = asCarbFloat3(mTargetAxisX);
    endEffectorTarget[2] = asCarbFloat3(mTargetAxisY);
    endEffectorTarget[3] = asCarbFloat3(mTargetAxisZ);

    return endEffectorTarget;
}

void MotionPolicy::addObstacle(const std::string& obstaclePath, const int inputType, const carb::Float3 inputScale)
{
    if (mRmpflowPolicyInitialized)
    {
        auto obstacle = mRegisteredObstacles.find(obstaclePath);
        if (obstacle == mRegisteredObstacles.end())
        {
            pxr::UsdPrim obstaclePrim = mStage->GetPrimAtPath(pxr::SdfPath(obstaclePath));
            if (!obstaclePrim)
            {
                return;
            }

            double buffer = 0.01;

            std::unique_ptr<Obstacle> obstacle;
            if (inputType == 1)
            {
                obstacle = lula::CreateObstacle(lula::Obstacle::Type::CYLINDER);
                if (inputScale.x != inputScale.y)
                {
                    CARB_LOG_ERROR("MotionPolicy::AddObstacle Cylinder x [%f] and y [%f] inputScale should match",
                                   inputScale.x, inputScale.y);
                }
                obstacle->setAttribute(lula::Obstacle::Attribute::RADIUS, inputScale.x + buffer);
                obstacle->setAttribute(lula::Obstacle::Attribute::HEIGHT, inputScale.z + (2.0 * buffer));
            }
            else if (inputType == 2)
            {
                obstacle = lula::CreateObstacle(lula::Obstacle::Type::SPHERE);
                if (inputScale.x != inputScale.y || inputScale.x != inputScale.z)
                {
                    CARB_LOG_ERROR("MotionPolicy::AddObstacle Sphere x [%f], y [%f] and z [%f] inputScale should match",
                                   inputScale.x, inputScale.y, inputScale.z);
                }
                obstacle->setAttribute(lula::Obstacle::Attribute::RADIUS, inputScale.x + buffer);
            }
            else if (inputType == 3)
            {
                obstacle = lula::CreateObstacle(lula::Obstacle::Type::CUBE);
                obstacle->setAttribute(lula::Obstacle::Attribute::SIDE_LENGTHS,
                                       Eigen::Vector3d(inputScale.x + (2.0 * buffer), inputScale.y + (2.0 * buffer),
                                                       inputScale.z + (2.0 * buffer)));
            }
            else
            {
                CARB_LOG_ERROR("MotionPolicy::AddObstacle NOT VALID TYPE %s", obstaclePath.c_str());
                return;
            }

            pxr::UsdGeomXformable xform(obstaclePrim);

            const pxr::GfTransform tr(xform.ComputeLocalToWorldTransform(pxr::UsdTimeCode()));
            const pxr::GfVec3d t = tr.GetTranslation();
            const pxr::GfQuatd q = tr.GetRotation().GetQuat();
            const lula::Pose3 pose =
                lula::Pose3(lula::Rotation3(q.GetReal(), q.GetImaginary()[0], q.GetImaginary()[1], q.GetImaginary()[2]),
                            Eigen::Vector3d(t[0], t[1], t[2]) * mUnitScale);

            lula::World::ObstacleHandle handle = mRmpflowWorld->addObstacle(obstacle, &pose);
            mRegisteredObstacles[obstaclePath] =
                std::pair<pxr::UsdPrim, lula::World::ObstacleHandle>(obstaclePrim, handle);
        }
        else
        {
            CARB_LOG_ERROR("MotionPolicy::addObstacle OBSTACLE ALREADY ADDED %s", obstaclePath.c_str());
        }
    }
    else
    {
        CARB_LOG_ERROR("MotionPolicy::addObstacle POLICY NOT INITIALIZED %s", obstaclePath.c_str());
    }
}

void MotionPolicy::updateObstacle(const std::string& obstaclePath)
{
    auto obstacle = mRegisteredObstacles.find(obstaclePath);
    if (obstacle != mRegisteredObstacles.end())
    {
        pxr::UsdPrim obstaclePrim = obstacle->second.first;
        if (!obstaclePrim)
        {
            return;
        }
        omni::isaac::dynamic_control::DcObjectType primType = mDynamicControl->peekObjectType(obstaclePath.c_str());

        lula::Pose3 pose;
        if (primType == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {
            omni::isaac::dynamic_control::DcTransform trans =
                mDynamicControl->getRigidBodyPose(mDynamicControl->getRigidBody(obstaclePath.c_str()));
            pose = lula::Pose3(lula::Rotation3(trans.r.w, trans.r.x, trans.r.y, trans.r.z),
                               Eigen::Vector3d(trans.p.x, trans.p.y, trans.p.z) * mUnitScale);
        }
        else
        {
            pxr::UsdGeomXformable xform(obstaclePrim);
            const pxr::GfTransform tr(xform.ComputeLocalToWorldTransform(pxr::UsdTimeCode()));
            const pxr::GfVec3d t = tr.GetTranslation();
            const pxr::GfQuatd q = tr.GetRotation().GetQuat();
            pose =
                lula::Pose3(lula::Rotation3(q.GetReal(), q.GetImaginary()[0], q.GetImaginary()[1], q.GetImaginary()[2]),
                            Eigen::Vector3d(t[0], t[1], t[2]) * mUnitScale);
        }
        auto& handle = obstacle->second.second;
        mRmpflowWorld->setPose(handle, pose);
    }
    else
    {
        CARB_LOG_ERROR("MotionPolicy::updateObstacle OBSTACLE NOT FOUND %s", obstaclePath.c_str());
    }
}

void MotionPolicy::updateObstacle(const std::string& obstaclePath, const omni::isaac::dynamic_control::DcTransform& trans)
{
    auto obstacle = mRegisteredObstacles.find(obstaclePath);
    if (obstacle != mRegisteredObstacles.end())
    {
        lula::Pose3 pose = lula::Pose3(lula::Rotation3(trans.r.w, trans.r.x, trans.r.y, trans.r.z),
                                       Eigen::Vector3d(trans.p.x, trans.p.y, trans.p.z));
        auto& handle = obstacle->second.second;
        mRmpflowWorld->setPose(handle, pose);
    }
    else
    {
        CARB_LOG_ERROR("MotionPolicy::updateObstacle OBSTACLE NOT FOUND %s", obstaclePath.c_str());
    }
}
void MotionPolicy::removeObstacle(const std::string& obstaclePath)
{
    auto obstacle = mRegisteredObstacles.find(obstaclePath);
    if (obstacle != mRegisteredObstacles.end())
    {
        auto& handle = obstacle->second.second;
        mRmpflowWorld->removeObstacle(handle);
        mRegisteredObstacles.erase(obstacle);
    }
    else
    {
        CARB_LOG_ERROR("MotionPolicy::removeObstacle OBSTACLE NOT FOUND %s", obstaclePath.c_str());
    }
}
void MotionPolicy::enableObstacle(const std::string& obstaclePath)
{
    auto obstacle = mRegisteredObstacles.find(obstaclePath);
    if (obstacle != mRegisteredObstacles.end())
    {
        auto& handle = obstacle->second.second;
        mRmpflowWorld->enableObstacle(handle);
    }
    else
    {
        CARB_LOG_ERROR("MotionPolicy::enableObstacle OBSTACLE NOT FOUND %s", obstaclePath.c_str());
    }
}
void MotionPolicy::disableObstacle(const std::string& obstaclePath)
{
    auto obstacle = mRegisteredObstacles.find(obstaclePath);
    if (obstacle != mRegisteredObstacles.end())
    {
        auto& handle = obstacle->second.second;
        mRmpflowWorld->disableObstacle(handle);
    }
    else
    {
        CARB_LOG_ERROR("MotionPolicy::disableObstacle OBSTACLE NOT FOUND %s", obstaclePath.c_str());
    }
}
bool MotionPolicy::hasObstacle(const std::string& obstaclePath) const
{
    auto obstacle = mRegisteredObstacles.find(obstaclePath);
    return (obstacle != mRegisteredObstacles.end());
}

void MotionPolicy::setDefaultConfig(const std::vector<double>& config)
{
    Eigen::VectorXd defaultQ = mRmpflowPolicy->GetDefaultConfig();
    if ((int)config.size() != defaultQ.size())
    {
        CARB_LOG_ERROR("MotionPolicy::SetDefaultConfig sizes do not match");
        return;
    }
    for (size_t i = 0; i < config.size(); i++)
    {
        defaultQ[i] = config[i];
    }

    mRmpflowPolicy->SetDefaultConfig(defaultQ);
}

bool MotionPolicy::setRobotPrim(const pxr::UsdPrim& prim)
{
    mRobotPrim = prim;
    mRobotHandle = mDynamicControl->getArticulation(mRobotPrim.GetPath().GetString().c_str());
    if (mRobotHandle)
    {
        mRobotRootHandle = mDynamicControl->getArticulationRootBody(mRobotHandle);
        if (!mRobotRootHandle)
        {
            return false;
        }
        return true;
    }
    return false;
}

omni::isaac::dynamic_control::DcHandle MotionPolicy::getRobotRootHandle()
{
    return mRobotRootHandle;
}
