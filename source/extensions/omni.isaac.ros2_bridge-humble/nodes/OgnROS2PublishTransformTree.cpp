// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/ros/Conversions.h>
#include <omni/isaac/ros/Ros2Node.h>
#include <omni/isaac/utils/PoseTree.h>
#include <omni/usd/UsdUtils.h>

#include <OgnROS2PublishTransformTreeDatabase.h>
#include <iomanip>
#include <sstream>


using namespace omni::isaac::dynamic_control;

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
            state.mStageId = context.iContext->getStageId(context);
            state.mUsdStage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(state.mStageId));
            if (!state.mUsdStage)
            {
                db.logError("Could not find USD stage %ld", state.mStageId);
                return false;
            }

            state.mStageUnits = UsdGeomGetStageMetersPerUnit(state.mUsdStage);

            const pxr::UsdPrim thisPrim = state.mUsdStage->GetPrimAtPath(pxr::SdfPath(state.mThisPrimPath));

            // Finidng parent prim
            pxr::SdfPathVector parent;
            pxr::TfToken parentPrimInput =
                omni::fabric::toTfToken(OgnROS2PublishTransformTreeAttributes::inputs::parentPrim.m_token);

            const pxr::UsdRelationship parentRel = thisPrim.GetRelationship(parentPrimInput);
            parentRel.GetTargets(&parent);

            if (parent.size() == 0)
            {
                state.mParentPath = pxr::SdfPath();
            }
            else
            {
                state.mParentPath = parent[0];
            }

            // Finidng target prims
            pxr::TfToken targetPrimInputs =
                omni::fabric::toTfToken(OgnROS2PublishTransformTreeAttributes::inputs::targetPrims.m_token);

            const pxr::UsdRelationship targetRel = thisPrim.GetRelationship(targetPrimInputs);
            targetRel.GetTargets(&state.mTargets);

            if (state.mTargets.size() == 0)
            {
                db.logWarning("Please specify atleast one target prim for the ROS pose tree component");
                return false;
            }

            // reset this object
            state.mPoseTree =
                std::make_unique<omni::isaac::utils::posetree::PoseTree>(state.mStageId, state.mDynamicControlPtr);
            state.mPoseTree->setParentPrimPath(state.mParentPath, "world");
            state.mPoseTree->setTargetPrimPaths(state.mTargets);

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


        std::function<void(const std::string&, const std::string&, const physx::PxTransform&)> addPoseLambda =
            [this, &msg, &tf_msg](
                const std::string& parent_frame, const std::string& child_frame, const physx::PxTransform& t)
        {
            msg.header.frame_id = parent_frame;
            msg.child_frame_id = child_frame;
            msg.transform = omni::isaac::conversions::asRosTransform<geometry_msgs::msg::Transform>(
                t, static_cast<float>(mStageUnits));

            tf_msg.transforms.push_back(msg);
        };

        mPoseTree->processAllFrames(addPoseLambda);

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
        mPoseTree.reset();
    }


private:
    std::shared_ptr<rclcpp::Publisher<tf2_msgs::msg::TFMessage>> mPublisher = nullptr;

    const char* mThisPrimPath = nullptr;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    double mStageUnits = 1;
    pxr::SdfPath mParentPath;
    pxr::SdfPathVector mTargets;

    long mStageId;
    pxr::UsdStageRefPtr mUsdStage;
    std::unique_ptr<omni::isaac::utils::posetree::PoseTree> mPoseTree;
};

REGISTER_OGN_NODE()
