// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosTeleport.h"

#include "geometry_msgs/msg/transform.hpp"
#include "rosgraph_msgs/msg/clock.hpp"
#include "std_msgs/msg/int64.hpp"
#include "std_msgs/msg/u_int8.hpp"
#include "std_srvs/srv/empty.hpp"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <omni/isaac/ros/Conversions.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <time.h>
namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
using namespace omni::isaac::dynamic_control;

RosTeleport::RosTeleport(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

RosTeleport::~RosTeleport()
{
    CARB_LOG_INFO("RosTeleport Destroyed");
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mPoseSrvTopic);
}

void RosTeleport::initialize(RosNode* rosNode,
                             const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                             pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
}
void RosTeleport::onStart()
{
    onComponentChange();
}
void RosTeleport::onStop()
{
}
void RosTeleport::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosTeleport& typedPrim = (pxr::RosBridgeSchemaRosTeleport)mPrim;
    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mPoseSrvTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetPoseSrvTopicAttr(), mPoseSrvTopic);


    mRosNode->createService<isaac_ros2_messages::srv::IsaacPose>(
        mPrim.GetPath().GetString(), mPoseSrvTopic, &RosTeleport::srvCallback, this);

    pxr::SdfPathVector targets;
    typedPrim.GetTeleportPrimsRel().GetTargets(&targets);
    if (targets.size() == 0)
    {
        return;
    }
    for (pxr::SdfPath eachRigidBodyPath : targets)
    {
        pxr::UsdPrim rigidBodyPrim = mStage->GetPrimAtPath(eachRigidBodyPath);
        const std::string actorName = eachRigidBodyPath.GetString();
        if (rigidBodyPrim)
        {
            if (mObjects.find(actorName) != mObjects.end())
                eraseObject(actorName);
            addObject(actorName, rigidBodyPrim);
        }
    }
    mUnitScale = 1.0f / UsdGeomGetStageMetersPerUnit(mStage);
}

void RosTeleport::addObject(const std::string& actorName, pxr::UsdPrim& prim)
{
    mObjects[actorName] = std::pair<size_t, pxr::UsdPrim>(mObjects.size(), prim);
}
void RosTeleport::eraseObject(const std::string& actorName)
{
    const size_t removed_index = mObjects[actorName].first;
    mObjects.erase(actorName);

    for (auto& object : mObjects)
    {
        // Once the index is removed, all items "higher" should be decremented by one
        if (object.second.first > removed_index)
        {
            object.second.first -= 1;
        }
    }
}

bool RosTeleport::srvCallback(const isaac_ros2_messages::srv::IsaacPose::Request::SharedPtr req,
                              isaac_ros2_messages::srv::IsaacPose::Response::SharedPtr res)
{
    const unsigned int num_actors = req->names.size();
    for (size_t req_idx = 0; req_idx < num_actors; req_idx++)
    {
        // int bodyIndex = 0;
        for (auto& object : mObjects)
        {
            // bodyIndex = object.second.first;
            pxr::UsdPrim prim = object.second.second;
            // Set actor name
            std::string actorName = object.first;
            DcObjectType type = mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());

            if (prim && actorName == req->names[req_idx])
            {
                DcTransform body_pose;
                if (req->poses.size() == num_actors)
                {
                    body_pose = omni::isaac::conversions::rosPoseAsDcTransform(req->poses[req_idx], mUnitScale);

                    if (type == omni::isaac::dynamic_control::eDcObjectArticulation)
                    {

                        CARB_LOG_INFO("Pose service message for Articulation");
                        DcHandle artculationHandle =
                            mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
                        mDynamicControlPtr->wakeUpArticulation(artculationHandle);
                        DcHandle rigidBodyHandle = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
                        mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, body_pose);
                    }
                    else if (type == omni::isaac::dynamic_control::eDcObjectRigidBody)
                    {
                        DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
                        CARB_LOG_INFO("Pose service message for Rigid");
                        mDynamicControlPtr->wakeUpRigidBody(rigidBodyHandle);
                        mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, body_pose);
                    }
                    else if (type == omni::isaac::dynamic_control::eDcObjectNone)
                    {
                        CARB_LOG_INFO("Pose service message for None");
                        omni::usd::UsdUtils::setLocalTransformMatrix(
                            prim, omni::isaac::utils::conversions::asGfTransform(body_pose).GetMatrix());
                    }
                    CARB_LOG_INFO("Pose service message recieved");
                }

                if (req->velocities.size() == num_actors)
                {
                    carb::Float3 linear_velocity =
                        omni::isaac::conversions::asCarbFloat3(req->velocities[req_idx].linear);
                    carb::Float3 angular_velocity =
                        omni::isaac::conversions::asCarbFloat3(req->velocities[req_idx].angular);

                    if (type == omni::isaac::dynamic_control::eDcObjectArticulation)
                    {

                        CARB_LOG_INFO("Velocity service message for Articulation Root");
                        DcHandle artculationHandle =
                            mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
                        mDynamicControlPtr->wakeUpArticulation(artculationHandle);
                        DcHandle rigidBodyHandle = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
                        mDynamicControlPtr->setRigidBodyLinearVelocity(rigidBodyHandle, linear_velocity);
                        mDynamicControlPtr->setRigidBodyAngularVelocity(rigidBodyHandle, angular_velocity);
                    }
                    else if (type == omni::isaac::dynamic_control::eDcObjectRigidBody)
                    {
                        DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
                        CARB_LOG_INFO("Velocity service message for Rigid");
                        mDynamicControlPtr->wakeUpRigidBody(rigidBodyHandle);
                        mDynamicControlPtr->setRigidBodyLinearVelocity(rigidBodyHandle, linear_velocity);
                        mDynamicControlPtr->setRigidBodyAngularVelocity(rigidBodyHandle, angular_velocity);
                    }
                    else if (type == omni::isaac::dynamic_control::eDcObjectNone)
                    {
                        CARB_LOG_WARN("Velocity service cannot be applied to non physics object with path: %s",
                                      prim.GetPath().GetString().c_str());
                    }
                }

                if (req->scales.size() == num_actors)
                {
                    // carb::Float3 body_scale = { req.scales[req_idx].x, req.scales[req_idx].y, req.scales[req_idx].z
                    // };
                    CARB_LOG_WARN("Scale service message not supported currently");
                }
                return true;
            }
        }
    }
    return false;
}

}
}
}
