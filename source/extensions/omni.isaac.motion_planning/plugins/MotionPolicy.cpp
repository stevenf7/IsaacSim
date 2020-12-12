// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "MotionPlanningPCH.h"
// clang-format on
#include <carb/InterfaceUtils.h>

#include "MotionPolicy.h"

#include <math.h>
#include <memory>

using namespace lula;

Eigen::Vector3d asEigenVector3d(const carb::Float3& v)
{
    return Eigen::Vector3d(v.x, v.y, v.z);
}

MotionPolicy::MotionPolicy(pxr::UsdStageWeakPtr stage, omni::isaac::dynamic_control::DynamicControl* dynamicControl)
{
    mStage = stage;
    mDynamicControl = dynamicControl;
    mOverrideDt = false;
    mFrequency = 120.0f;
    mFixedDt = 1.0f / mFrequency;

    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
}
void MotionPolicy::initialize(const std::string& robotUrdfPath,
                              const std::string& robotDescriptorPath,
                              const std::string& rmpFlowCommonPath,
                              const std::string& controlFrame)
{
    mRmpflowPolicy = std::make_shared<rmp::RmpflowRobotPolicy>();
    mRegisteredSuppressionTokens = std::make_shared<MotionPolicySuppressionToken>();
    mRmpflowPolicy->AddGlobalSuppressionToken(controlFrame, mRegisteredSuppressionTokens);

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
        rmpConfigYAML, std::make_shared<kinematics::Robot>(robotURDF, robotYAML), controlFrame, true, false);

    q = mRmpflowPolicy->GetDefaultConfig();
    qd = Eigen::VectorXd::Zero(mRmpflowPolicy->cspace_dim());
    mState = math::State(q, qd);
    mOrigMap = mRmpflowPolicy->GetControlFrameElementMap(rmp::FrameElement::ORIG);
    mAxisXMap = mRmpflowPolicy->GetControlFrameElementMap(rmp::FrameElement::AXIS_X);
    mAxisYMap = mRmpflowPolicy->GetControlFrameElementMap(rmp::FrameElement::AXIS_Y);
    mAxisZMap = mRmpflowPolicy->GetControlFrameElementMap(rmp::FrameElement::AXIS_Z);
    mEndEffectorState.resize(4);
    mEndEffectorTarget.resize(4);
    mEndEffectorError.resize(4);
}

void MotionPolicy::setFrequency(const float frequency, const bool useFixedDt)
{
    if (frequency > 0)
    {
        mFrequency = frequency;
        mFixedDt = 1.0f / mFrequency;
    }
    mOverrideDt = useFixedDt;
}

void MotionPolicy::reset()
{
    q = mRmpflowPolicy->GetDefaultConfig();
    qd = Eigen::VectorXd::Zero(mRmpflowPolicy->cspace_dim());
    mState = math::State(q, qd);
}

void MotionPolicy::step(const float t, const float sourceDt)
{
    mRegisteredSuppressionTokens->Update();

    float dt = sourceDt;
    if (mOverrideDt)
    {
        dt = mFixedDt;
    }

    static double remaining = 0.f;
    int numRmpSubsteps = std::max(1, (int)((dt + remaining) * (mFrequency)));

    const int maxIters = 6;
    if (numRmpSubsteps > maxIters)
        numRmpSubsteps = maxIters;

    for (int rmpSubstep = 0; rmpSubstep < numRmpSubsteps; rmpSubstep++)
    {
        // printf("t: %f, dt: %f, t+: %f \n", t, dt, t + dt / numRmpSubsteps * rmpSubstep);
        auto qdd = mRmpflowPolicy->Eval(t + dt / numRmpSubsteps * rmpSubstep, mState);
        mState = mState.Step(dt / numRmpSubsteps, qdd);
    }


    mOrigFk = mOrigMap->Eval(mState.pos());
    mAxisXFk = mAxisXMap->Eval(mState.pos());
    mAxisYFk = mAxisYMap->Eval(mState.pos());
    mAxisZFk = mAxisZMap->Eval(mState.pos());

    mTargetOrig = mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::ORIG)->data()->target;
    if (mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_X)->data().has_value())
    {
        mTargetAxisX = mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_X)->data()->target;
    }
    else
    {
        mTargetAxisX = mAxisXFk;
    }
    if (mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_Y)->data().has_value())
    {
        mTargetAxisY = mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_Y)->data()->target;
    }
    else
    {
        mTargetAxisY = mAxisYFk;
    }
    if (mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_Z)->data().has_value())
    {
        mTargetAxisZ = mRmpflowPolicy->GetControlFrameTargetContainer(rmp::FrameElement::AXIS_Z)->data()->target;
    }
    else
    {
        mTargetAxisZ = mAxisZFk;
    }


    mEndEffectorError[0] = (mTargetOrig - mOrigFk).norm();
    mEndEffectorError[1] = (mTargetAxisX - mAxisXFk).norm();
    mEndEffectorError[2] = (mTargetAxisY - mAxisYFk).norm();
    mEndEffectorError[3] = (mTargetAxisZ - mAxisZFk).norm();

    if (mRobotHandle)
    {
        if (t > 0)
        {
            mDynamicControl->wakeUpArticulation(mRobotHandle);
        }

        for (int idx = 0; idx < mRmpflowPolicy->cspace_dim(); idx++)
        {
            omni::isaac::dynamic_control::DcHandle dof = mDynamicControl->getArticulationDof(mRobotHandle, idx);
            if (dof)
            {
                if (isnan(mState.pos()[idx]) == false)
                {
                    mDynamicControl->setDofPositionTarget(dof, mState.pos()[idx]);
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
    mEndEffectorState[0] = carb::Float3({ mOrigFk[0], mOrigFk[1], mOrigFk[2] });
    mEndEffectorState[1] = carb::Float3({ mAxisXFk[0], mAxisXFk[1], mAxisXFk[2] });
    mEndEffectorState[2] = carb::Float3({ mAxisYFk[0], mAxisYFk[1], mAxisYFk[2] });
    mEndEffectorState[3] = carb::Float3({ mAxisZFk[0], mAxisZFk[1], mAxisZFk[2] });

    return mEndEffectorState;
}

std::vector<carb::Float3> MotionPolicy::getRmpTarget()
{
    mEndEffectorTarget[0] = carb::Float3({ mTargetOrig[0], mTargetOrig[1], mTargetOrig[2] });
    mEndEffectorTarget[1] = carb::Float3({ mTargetAxisX[0], mTargetAxisX[1], mTargetAxisX[2] });
    mEndEffectorTarget[2] = carb::Float3({ mTargetAxisY[0], mTargetAxisY[1], mTargetAxisY[2] });
    mEndEffectorTarget[3] = carb::Float3({ mTargetAxisZ[0], mTargetAxisZ[1], mTargetAxisZ[2] });

    return mEndEffectorTarget;
}

void MotionPolicy::addObstacle(const std::string& obstaclePath, const int inputType, const carb::Float3 inputScale)
{

    pxr::UsdPrim obstaclePrim = mStage->GetPrimAtPath(pxr::SdfPath(obstaclePath));
    if (!obstaclePrim)
    {
        CARB_LOG_ERROR("MotionPolicy::AddObstacle NOT VALID PRIM %s", obstaclePath.c_str());
        return;
    }
    Eigen::Vector3d scale(inputScale.x, inputScale.y, inputScale.z);
    double buffer = 0.01;
    Eigen::Affine3d pose;
    lula::math::DistanceFunction3dFactory::Type type;
    if (inputType == 1)
    {
        type = lula::math::DistanceFunction3dFactory::CYLINDER;
    }
    else if (inputType == 2)
    {
        type = lula::math::DistanceFunction3dFactory::SPHERE;
    }
    else if (inputType == 3)
    {
        type = lula::math::DistanceFunction3dFactory::CUBE;
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
    pose = Eigen::Translation3d(Eigen::Vector3d(t[0], t[1], t[2]) * mUnitScale) *
           Eigen::Quaterniond(q.GetReal(), q.GetImaginary()[0], q.GetImaginary()[1], q.GetImaginary()[2]);


    std::shared_ptr<lula::math::DistanceFunction3d> distanceFunction =
        mDistanceFunction3DFactory->Make(type, scale, buffer);

    std::shared_ptr<lula::math::PosableDistanceFunction3d> obstacle =
        std::make_shared<lula::math::PosableDistanceFunction3d>(distanceFunction, pose);
    mRmpflowPolicy->RegisterObstacle(obstaclePath, obstacle);
    mRegisteredObstacleDistanceFunctions[obstaclePath] =
        std::pair<pxr::UsdPrim, std::shared_ptr<lula::math::PosableDistanceFunction3d>>(obstaclePrim, obstacle);
    mRegisteredSuppressionTokens->Add(obstaclePath, 1);
}

void MotionPolicy::updateObstacle(const std::string& obstaclePath)
{
    if (mRegisteredObstacleDistanceFunctions.find(obstaclePath) == mRegisteredObstacleDistanceFunctions.end())
    {
        return;
    }
    pxr::UsdPrim obstaclePrim = mRegisteredObstacleDistanceFunctions[obstaclePath].first;
    if (!obstaclePrim)
    {
        return;
    }
    omni::isaac::dynamic_control::DcObjectType primType = mDynamicControl->peekObjectType(obstaclePath.c_str());
    Eigen::Affine3d pose;
    if (primType == omni::isaac::dynamic_control::eDcObjectRigidBody)
    {
        omni::isaac::dynamic_control::DcTransform trans =
            mDynamicControl->getRigidBodyPose(mDynamicControl->getRigidBody(obstaclePath.c_str()));
        pose = Eigen::Translation3d(Eigen::Vector3d(trans.p.x, trans.p.y, trans.p.z) * mUnitScale) *
               Eigen::Quaterniond(trans.r.w, trans.r.x, trans.r.y, trans.r.z);
    }
    else
    {
        pxr::UsdGeomXformable xform(obstaclePrim);
        const pxr::GfTransform tr(xform.ComputeLocalToWorldTransform(pxr::UsdTimeCode()));
        const pxr::GfVec3d t = tr.GetTranslation();
        const pxr::GfQuatd q = tr.GetRotation().GetQuat();
        pose = Eigen::Translation3d(Eigen::Vector3d(t[0], t[1], t[2]) * mUnitScale) *
               Eigen::Quaterniond(q.GetReal(), q.GetImaginary()[0], q.GetImaginary()[1], q.GetImaginary()[2]);
    }
    mRegisteredObstacleDistanceFunctions[obstaclePath].second->UpdatePose(pose);
}

void MotionPolicy::updateObstacle(const std::string& obstaclePath, const omni::isaac::dynamic_control::DcTransform& trans)
{
    if (mRegisteredObstacleDistanceFunctions.find(obstaclePath) == mRegisteredObstacleDistanceFunctions.end())
    {
        return;
    }
    Eigen::Affine3d pose = Eigen::Translation3d(Eigen::Vector3d(trans.p.x, trans.p.y, trans.p.z)) *
                           Eigen::Quaterniond(trans.r.w, trans.r.x, trans.r.y, trans.r.z);
    mRegisteredObstacleDistanceFunctions[obstaclePath].second->UpdatePose(pose);
}
void MotionPolicy::removeObstacle(const std::string& obstaclePath)
{
    mRmpflowPolicy->RemoveObstacle(obstaclePath);
    mRegisteredObstacleDistanceFunctions.erase(obstaclePath);
    mRegisteredSuppressionTokens->Remove(obstaclePath);
}
void MotionPolicy::enableObstacle(const std::string& obstaclePath)
{
    mRegisteredSuppressionTokens->Enable(obstaclePath);
}
void MotionPolicy::disableObstacle(const std::string& obstaclePath)
{
    mRegisteredSuppressionTokens->Disable(obstaclePath);
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
