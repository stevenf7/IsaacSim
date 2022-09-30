// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "tf2_msgs/msg/tf_message.hpp"

#include <carb/flatcache/FlatCache.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/ros/Conversions.h>
#include <omni/isaac/ros/Ros2Node.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdUtils.h>

#include <OgnROS2PublishTransformTreeDatabase.h>


using namespace omni::isaac::dynamic_control;
using omni::isaac::utils::conversions::asPxTransform;

class OgnROS2PublishTransformTree : public Ros2Node
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishTransformTreeDatabase::sInternalState<OgnROS2PublishTransformTree>(nodeObj);

        state.mThisPrimPath = nodeObj.iNode->getPrimPath(nodeObj);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();

        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnROS2PublishTransformTreeDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();
        auto& state = db.internalState<OgnROS2PublishTransformTree>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            //  Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            state.mStageUnits = UsdGeomGetStageMetersPerUnit(stage);

            const pxr::UsdPrim thisPrim = stage->GetPrimAtPath(pxr::SdfPath(state.mThisPrimPath));

            // Finidng parent prim
            pxr::SdfPathVector parent;
            pxr::TfToken parentPrimInput =
                carb::flatcache::toTfToken(OgnROS2PublishTransformTreeAttributes::inputs::parentPrim.m_token);

            const pxr::UsdRelationship parentRel = thisPrim.GetRelationship(parentPrimInput);
            parentRel.GetTargets(&parent);

            if (parent.size() == 0)
            {
                state.mParentPath = pxr::SdfPath();
                state.mParentPrim = pxr::UsdPrim();
            }
            else
            {
                state.mParentPath = parent[0];
                state.mParentPrim = stage->GetPrimAtPath(state.mParentPath);
            }

            // Finidng target prims
            pxr::TfToken targetPrimInputs =
                carb::flatcache::toTfToken(OgnROS2PublishTransformTreeAttributes::inputs::targetPrims.m_token);

            const pxr::UsdRelationship targetRel = thisPrim.GetRelationship(targetPrimInputs);
            targetRel.GetTargets(&state.mTargets);

            if (state.mTargets.size() == 0)
            {
                db.logWarning("Please specify atleast one target prim for the ROS pose tree component");
                return false;
            }

            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!validateTopic(fullTopicName))
            {
                return false;
            }

            state.mPublisher =
                state.mNodeHandle->create_publisher<tf2_msgs::msg::TFMessage>(fullTopicName, db.inputs.queueSize());

            return true;
        }

        state.publishTF(db, context);

        return true;
    }

    void publishTF(OgnROS2PublishTransformTreeDatabase& db, const GraphContextObj& context)
    {
        //  Find our stage
        long stageId = context.iContext->getStageId(context);
        auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

        if (!stage)
        {
            db.logError("Could not find USD stage %ld", stageId);
            return;
        }

        tf2_msgs::msg::TFMessage tf_msg;
        geometry_msgs::msg::TransformStamped msg;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS TF messages");
        }

        // Get the parent body pose
        physx::PxTransform parent_pose = physx::PxTransform(physx::PxIdentity);
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
            else if (type == eDcObjectNone || type == eDcObjectArticulation)
            {
                parent_pose = asPxTransform(omni::usd::UsdUtils::getWorldTransformMatrix(mParentPrim));
            }
        }


        for (pxr::SdfPath object : mTargets)
        {
            pxr::UsdPrim prim = stage->GetPrimAtPath(object);
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
                if (msg.header.frame_id != msg.child_frame_id)
                {
                    if (mParentPrim)
                    {
                        msg.transform =
                            omni::isaac::conversions::asRosTransform<geometry_msgs::msg::Transform>(trans, mStageUnits);
                    }
                    else
                    {
                        msg.transform = omni::isaac::conversions::asRosTransform<geometry_msgs::msg::Transform>(
                            body1_pose, mStageUnits);
                    }
                    tf_msg.transforms.push_back(msg);
                }

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
                        msg.transform =
                            omni::isaac::conversions::asRosTransform<geometry_msgs::msg::Transform>(pos0_1, mStageUnits);

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
                if (msg.header.frame_id != msg.child_frame_id)
                {
                    if (mParentPrim)
                    {
                        msg.transform =
                            omni::isaac::conversions::asRosTransform<geometry_msgs::msg::Transform>(trans, mStageUnits);
                    }
                    else
                    {
                        msg.transform = omni::isaac::conversions::asRosTransform<geometry_msgs::msg::Transform>(
                            body1_pose, mStageUnits);
                    }

                    tf_msg.transforms.push_back(msg);
                }
            }
            else if (type == eDcObjectNone)
            {
                pxr::GfMatrix4d matrix = omni::usd::UsdUtils::getWorldTransformMatrix(prim);

                if (prim.IsA<pxr::UsdGeomCamera>())
                {
                    // Rotate 180 degrees about x-axis
                    const pxr::GfMatrix4d omniTCamera = pxr::GfMatrix4d(1, 0, 0, 0, 0, -1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1);
                    matrix = omniTCamera * matrix;

                    // //Rotating 90 degrees in X axis for RTX Lidar PCL
                    // const pxr::GfMatrix4d omniTCamera = pxr::GfMatrix4d(1,0,0,0, 0,0,-1,0, 0,1,0,0, 0,0,0,1);
                    // matrix = omniTCamera * matrix;

                    // //Then rotate -90 degrees in Z axis for RTX Lidar PCL
                    // const pxr::GfMatrix4d omniTCamera2 = pxr::GfMatrix4d(0,1,0,0, -1,0,0,0, 0,0,1,0, 0,0,0,1);
                    // matrix = omniTCamera2 * matrix;
                }

                physx::PxTransform body1_pose = asPxTransform(matrix);
                physx::PxTransform trans(parent_pose.transformInv(body1_pose));
                msg.header.frame_id = parent_frame;
                msg.child_frame_id = prim.GetName().GetString();
                if (msg.header.frame_id != msg.child_frame_id)
                {
                    if (mParentPrim)
                    {
                        msg.transform =
                            omni::isaac::conversions::asRosTransform<geometry_msgs::msg::Transform>(trans, mStageUnits);
                    }
                    else
                    {
                        msg.transform = omni::isaac::conversions::asRosTransform<geometry_msgs::msg::Transform>(
                            body1_pose, mStageUnits);
                    }

                    tf_msg.transforms.push_back(msg);
                }
            }
        }
        mPublisher->publish(tf_msg);
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishTransformTreeDatabase::sInternalState<OgnROS2PublishTransformTree>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<rclcpp::Publisher<tf2_msgs::msg::TFMessage>> mPublisher = nullptr;

    const char* mThisPrimPath = nullptr;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    double mStageUnits = 1;
    pxr::SdfPath mParentPath;
    pxr::UsdPrim mParentPrim;
    pxr::SdfPathVector mTargets;
};

REGISTER_OGN_NODE()
