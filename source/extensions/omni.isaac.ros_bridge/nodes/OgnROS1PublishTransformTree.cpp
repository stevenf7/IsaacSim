// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include "tf2_msgs/TFMessage.h"

#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/PoseTree.h>
#include <omni/usd/UsdUtils.h>

#include <DynamicControl.h>
#include <OgnROS1PublishTransformTreeDatabase.h>
#include <RosConversions.h>
#include <RosNode.h>
#include <iomanip>
#include <sstream>

using namespace omni::isaac::dynamic_control;

class OgnROS1PublishTransformTree : public RosNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS1PublishTransformTreeDatabase::sPerInstanceState<OgnROS1PublishTransformTree>(nodeObj, instanceId);

        state.mThisPrimPath = nodeObj.iNode->getPrimPath(nodeObj);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();

        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnROS1PublishTransformTreeDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();
        auto& state = db.perInstanceState<OgnROS1PublishTransformTree>();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
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

            //  Finding target prims
            const auto& targetPrims = db.inputs.targetPrims();

            if (targetPrims.size() > 0)
            {
                state.mTargets.resize(targetPrims.size());
                std::transform(targetPrims.begin(), targetPrims.end(), state.mTargets.begin(),
                               [](TargetPath path) { return omni::fabric::toSdfPath(path); });
            }
            else
            {
                db.logError("Please specify atleast one target prim for the ROS pose tree component");
                return false;
            }
            // Finding Parent Prim
            const auto& parentPrim = db.inputs.parentPrim();

            if (parentPrim.size() > 0)
            {
                state.mParentPath = omni::fabric::toSdfPath(parentPrim[0]);
            }
            else
            {
                state.mParentPath = pxr::SdfPath();
            }

            // reset this object
            state.mPoseTree =
                std::make_unique<omni::isaac::utils::posetree::PoseTree>(state.mStageId, state.mDynamicControlPtr);
            state.mPoseTree->setParentPrimPath(state.mParentPath, "world");
            state.mPoseTree->setTargetPrimPaths(state.mTargets);

            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            if (!validateTopic(topicName))
            {
                return false;
            }

            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<tf2_msgs::TFMessage>(topicName, db.inputs.queueSize()));

            state.mFrameIdPrefix = "";
            addFramePrefix(db.inputs.nodeNamespace(), state.mFrameIdPrefix);

            return true;
        }

        state.publishTF(db, context);

        return true;
    }

    void publishTF(OgnROS1PublishTransformTreeDatabase& db, const GraphContextObj& context)
    {
        tf2_msgs::TFMessage tf_msg;
        geometry_msgs::TransformStamped msg;
        msg.header.seq = 0;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS TF messages");
        }

        std::function<void(const std::string&, const std::string&, const physx::PxTransform&)> addPoseLambda =
            [this, &msg, &tf_msg](
                const std::string& parent_frame, const std::string& child_frame, const physx::PxTransform& t)
        {
            msg.header.frame_id = (parent_frame == "world") ? parent_frame : mFrameIdPrefix + parent_frame;
            msg.child_frame_id = mFrameIdPrefix + child_frame;
            msg.transform = omni::isaac::conversions::asRosTransform<geometry_msgs::Transform>(t, mStageUnits);

            tf_msg.transforms.push_back(msg);
        };

        mPoseTree->processAllFrames(addPoseLambda);

        mPublisher->publish(tf_msg);
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS1PublishTransformTreeDatabase::sPerInstanceState<OgnROS1PublishTransformTree>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        RosNode::reset();
        mPoseTree.reset();
    }


private:
    std::unique_ptr<ros::Publisher> mPublisher;


    const char* mThisPrimPath = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    double mStageUnits = 1;
    std::string mFrameIdPrefix = "";
    pxr::SdfPath mParentPath;
    pxr::SdfPathVector mTargets;

    long mStageId;
    pxr::UsdStageRefPtr mUsdStage;
    std::unique_ptr<omni::isaac::utils::posetree::PoseTree> mPoseTree;
};

REGISTER_OGN_NODE()
