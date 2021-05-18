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

#include "RosPoseTree.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include "rosgraph_msgs/msg/clock.hpp"
#include "std_msgs/msg/int64.hpp"
#include "std_msgs/msg/u_int8.hpp"
#include "std_srvs/srv/empty.hpp"
#include <time.h>
#include "../Core/RosUtils.h"
#include <omni/isaac/utils/Conversions.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>
namespace omni
{
namespace isaac
{
namespace ros2_bridge
{
using namespace omni::isaac::dynamic_control;


RosPoseTree::RosPoseTree(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

RosPoseTree::~RosPoseTree()
{
    CARB_LOG_INFO("RosPoseTree Destroyed");
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mPoseTreePubTopic);
}

void RosPoseTree::initialize(RosNode* rosNode,
                             const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                             pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
}
void RosPoseTree::onStart()
{
    onComponentChange();
}
void RosPoseTree::onStop()
{
}
void RosPoseTree::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosPoseTree& typedPrim = (pxr::RosBridgeSchemaRosPoseTree)mPrim;
    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mPoseTreePubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetPoseTreePubTopicAttr(), mPoseTreePubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetQueueSizeAttr(), mQueueSize);


    pxr::SdfPathVector targets;
    typedPrim.GetTargetPrimsRel().GetTargets(&targets);
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


    mRosNode->createPublisher<tf2_msgs::msg::TFMessage>(
        mPrim.GetPath().GetString(), mPoseTreePubTopic, mQueueSize, &RosPoseTree::pubCallback, this);
    // mRosNode->createPeriodic<tf2_msgs::msg::TFMessage>(mPrim.GetPath().GetString(), &RosPoseTree::periodicCallback,
    // this);

    mStageUnits = UsdGeomGetStageMetersPerUnit(mStage);
}

void RosPoseTree::addObject(const std::string& actorName, pxr::UsdPrim& prim)
{
    mObjects[actorName] = std::pair<size_t, pxr::UsdPrim>(mObjects.size(), prim);
}
void RosPoseTree::eraseObject(const std::string& actorName)
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
void RosPoseTree::pubCallback(rclcpp::PublisherBase* pub)
{
    if (!mEnabled)
    {
        return;
    }

    tf2_msgs::msg::TFMessage tf_msg;
    geometry_msgs::msg::TransformStamped msg;
    if (mUseSimTime)
    {
        msg.header.stamp = rclcpp::Time(mTimeNanoSeconds);
    }
    else
    {
        msg.header.stamp = rclcpp::Time(mSystemTimeNanoSeconds);
    }
    int bodyIndex = 0;
    for (auto& object : mObjects)
    {
        // For each rigid body
        bodyIndex = object.second.first;
        pxr::UsdPrim prim = object.second.second;
        // Set actor name
        std::string actorName = object.first;
        DcObjectType type = mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());

        if (type == omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            DcHandle artculationHandle = mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
            DcHandle rootBody = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
            DcTransform trans = mDynamicControlPtr->getRigidBodyPose(rootBody);
            msg.header.frame_id = "world";
            msg.child_frame_id = mDynamicControlPtr->getRigidBodyName(rootBody);
            msg.transform = asRosTransform(trans, mStageUnits);

            tf_msg.transforms.push_back(msg);
            int num_dofs = mDynamicControlPtr->getArticulationBodyCount(artculationHandle);
            for (int j = 0; j < num_dofs; j++)
            {
                DcHandle parent_body = mDynamicControlPtr->getArticulationBody(artculationHandle, j);
                int num_joints = mDynamicControlPtr->getRigidBodyChildJointCount(parent_body);
                for (int k = 0; k < num_joints; k++)
                {
                    DcHandle joint = mDynamicControlPtr->getRigidBodyChildJoint(parent_body, k);
                    DcHandle child_body = mDynamicControlPtr->getJointChildBody(joint);

                    physx::PxTransform body0_pose =
                        omni::isaac::utils::conversions::asPxTransform(mDynamicControlPtr->getRigidBodyPose(parent_body));
                    physx::PxTransform body1_pose =
                        omni::isaac::utils::conversions::asPxTransform(mDynamicControlPtr->getRigidBodyPose(child_body));
                    physx::PxTransform pos0_1(body0_pose.transformInv(body1_pose));

                    msg.header.frame_id = mDynamicControlPtr->getRigidBodyName(parent_body);
                    msg.child_frame_id = mDynamicControlPtr->getRigidBodyName(child_body);
                    msg.transform = asRosTransform(pos0_1, mStageUnits);
                    tf_msg.transforms.push_back(msg);
                }
            }
        }
        else if (type == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {
            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
            DcTransform trans = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);
            msg.header.frame_id = "world";
            msg.child_frame_id = prim.GetName().GetString();
            msg.transform = asRosTransform(trans, mStageUnits);
            tf_msg.transforms.push_back(msg);
        }
        else if (type == omni::isaac::dynamic_control::eDcObjectNone)
        {
            const pxr::GfTransform body_0_world(omni::usd::UsdUtils::getWorldTransformMatrix(prim));
            msg.header.frame_id = "world";
            msg.child_frame_id = prim.GetName().GetString();
            msg.transform = asRosTransform(body_0_world, mStageUnits);
            tf_msg.transforms.push_back(msg);
        }
    }


    static_cast<rclcpp::Publisher<tf2_msgs::msg::TFMessage, std::allocator<void>>*>(pub)->publish(tf_msg);
}
}
}
}
