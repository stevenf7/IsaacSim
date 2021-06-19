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
using omni::isaac::utils::conversions::asPxTransform;

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

    pxr::SdfPathVector parent;
    typedPrim.GetParentPrimRel().GetTargets(&parent);
    if (parent.size() == 0)
    {
        mParentPath = pxr::SdfPath();
        mParentPrim = pxr::UsdPrim();
    }
    else
    {
        mParentPath = parent[0];
        mParentPrim = mStage->GetPrimAtPath(mParentPath);
    }

    typedPrim.GetTargetPrimsRel().GetTargets(&mTargets);
    if (mTargets.size() == 0)
    {
        return;
    }


    mRosNode->createPublisher<tf2_msgs::msg::TFMessage>(
        mPrim.GetPath().GetString(), mPoseTreePubTopic, mQueueSize, &RosPoseTree::pubCallback, this);
    // mRosNode->createPeriodic<tf2_msgs::msg::TFMessage>(mPrim.GetPath().GetString(), &RosPoseTree::periodicCallback,
    // this);

    mStageUnits = UsdGeomGetStageMetersPerUnit(mStage);
}

void RosPoseTree::pubCallback(rclcpp::PublisherBase* pub)
{
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

    // Get the parent body pose
    physx::PxTransform parent_pose = physx::PxTransform();
    std::string parent_frame = "world";

    if (mParentPrim)
    {
        parent_frame = mParentPrim.GetName().GetString();

        DcObjectType type = mDynamicControlPtr->peekObjectType(mParentPrim.GetPath().GetString().c_str());

        if (type == eDcObjectRigidBody)
        {
            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(mParentPrim.GetPath().GetString().c_str());
            parent_pose = asPxTransform(mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle));
        }
        else if (type == eDcObjectNone)
        {
            parent_pose = asPxTransform(omni::usd::UsdUtils::getWorldTransformMatrix(mParentPrim));
        }
    }


    for (pxr::SdfPath object : mTargets)
    {
        pxr::UsdPrim prim = mStage->GetPrimAtPath(object);
        // Set actor name
        DcObjectType type = mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());

        if (type == eDcObjectArticulation)
        {
            DcHandle artculationHandle = mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
            DcHandle rootBody = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
            physx::PxTransform body1_pose = asPxTransform(mDynamicControlPtr->getRigidBodyPose(rootBody));
            msg.header.frame_id = parent_frame;
            msg.child_frame_id = mDynamicControlPtr->getRigidBodyName(rootBody);

            physx::PxTransform trans(parent_pose.transformInv(body1_pose));
            if (mParentPrim)
            {
                msg.transform = asRosTransform(trans, mStageUnits);
            }
            else
            {
                msg.transform = asRosTransform(body1_pose, mStageUnits);
            }

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

                    physx::PxTransform body0_pose = asPxTransform(mDynamicControlPtr->getRigidBodyPose(parent_body));
                    physx::PxTransform body1_pose = asPxTransform(mDynamicControlPtr->getRigidBodyPose(child_body));
                    physx::PxTransform pos0_1(body0_pose.transformInv(body1_pose));

                    msg.header.frame_id = mDynamicControlPtr->getRigidBodyName(parent_body);
                    msg.child_frame_id = mDynamicControlPtr->getRigidBodyName(child_body);
                    msg.transform = asRosTransform(pos0_1, mStageUnits);
                    tf_msg.transforms.push_back(msg);
                }
            }
        }
        else if (type == eDcObjectRigidBody)
        {
            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
            physx::PxTransform body1_pose = asPxTransform(mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle));
            physx::PxTransform trans(parent_pose.transformInv(body1_pose));
            msg.header.frame_id = parent_frame;
            msg.child_frame_id = prim.GetName().GetString();
            if (mParentPrim)
            {
                msg.transform = asRosTransform(trans, mStageUnits);
            }
            else
            {
                msg.transform = asRosTransform(body1_pose, mStageUnits);
            }

            tf_msg.transforms.push_back(msg);
        }
        else if (type == eDcObjectNone)
        {
            physx::PxTransform body1_pose = asPxTransform(omni::usd::UsdUtils::getWorldTransformMatrix(prim));
            physx::PxTransform trans(parent_pose.transformInv(body1_pose));
            msg.header.frame_id = parent_frame;
            msg.child_frame_id = prim.GetName().GetString();
            if (mParentPrim)
            {
                msg.transform = asRosTransform(trans, mStageUnits);
            }
            else
            {
                msg.transform = asRosTransform(body1_pose, mStageUnits);
            }

            tf_msg.transforms.push_back(msg);
        }
    }


    static_cast<rclcpp::Publisher<tf2_msgs::msg::TFMessage, std::allocator<void>>*>(pub)->publish(tf_msg);
}
}
}
}
