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


#include <include/Ros2Node.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/PoseTree.h>
#include <omni/usd/UsdUtils.h>

#include <DynamicControl.h>
#include <OgnROS2PublishTransformTreeDatabase.h>
#include <iomanip>
#include <sstream>


using namespace omni::isaac::dynamic_control;

class OgnROS2PublishTransformTree : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2PublishTransformTreeDatabase::sPerInstanceState<OgnROS2PublishTransformTree>(nodeObj, instanceId);

        state.mThisPrimPath = nodeObj.iNode->getPrimPath(nodeObj);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();

        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }

        state.mFirstIteration = true;
    }

    static bool compute(OgnROS2PublishTransformTreeDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();
        auto& state = db.perInstanceState<OgnROS2PublishTransformTree>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
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

            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.mMessage = state.mFactory->CreateTfTreeMessage();

            Ros2QoSProfile qos;

            const std::string& qosProfile = db.inputs.qosProfile();
            if (db.inputs.staticPublisher())
            {
                qos.depth = 1;
                qos.durability = Ros2QoSDurabilityPolicyType::eTransientLocal;
            }
            else if (qosProfile == "")
            {
                qos.depth = db.inputs.queueSize();
            }
            else
            {
                if (!jsonToRos2QoSProfile(qos, qosProfile))
                {
                    return false;
                }
            }
            state.mPublisher = state.mFactory->CreatePublisher(
                state.mNodeHandle.get(), fullTopicName.c_str(), state.mMessage->getTypeSupportHandle(), qos);

            return true;
        }

        return state.publishTF(db, context);

        return true;
    }

    bool publishTF(OgnROS2PublishTransformTreeDatabase& db, const GraphContextObj& context)
    {
        //  Find our stage
        long stageId = context.iContext->getStageId(context);
        auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

        auto& state = db.perInstanceState<OgnROS2PublishTransformTree>();

        bool isStaticPublisher = db.inputs.staticPublisher();

        // If we're a static publisher we only publish once on the first iteration.
        // The message will persist as long as the simulation is playing.
        // If we're not a static publisher, we publish every tick only if
        // we have subscribers or mPublishWithoutVerification is true.
        if (isStaticPublisher)
        {
            if (!state.mFirstIteration)
            {
                return false;
            }
            state.mFirstIteration = false;
        }
        else
        {
            // Check if subscription count is 0
            if (!mPublishWithoutVerification && !state.mPublisher.get()->get_subscription_count())
            {
                return false;
            }
        }

        if (!stage)
        {
            db.logError("Could not find USD stage %ld", stageId);
            return false;
        }

        const double time = db.inputs.timeStamp();
        std::vector<tfMessageStruct> tfMsg_vec;

        double stageUnits = mStageUnits;

        // TODO: Define tfmessagevec as state member and load with this

        std::function<void(const std::string&, const std::string&, const physx::PxTransform&)> addPoseLambda =
            [stageUnits, &tfMsg_vec, &time](
                const std::string& parent_frame, const std::string& child_frame, const physx::PxTransform& t)
        {
            tfMessageStruct currentMsg;
            currentMsg.timeStamp = time;
            currentMsg.childFrame = child_frame;
            currentMsg.parentFrame = parent_frame;

            currentMsg.trans_x = t.p.x * static_cast<float>(stageUnits);
            currentMsg.trans_y = t.p.y * static_cast<float>(stageUnits);
            currentMsg.trans_z = t.p.z * static_cast<float>(stageUnits);

            currentMsg.quat_x = t.q.x;
            currentMsg.quat_y = t.q.y;
            currentMsg.quat_z = t.q.z;
            currentMsg.quat_w = t.q.w;

            tfMsg_vec.push_back(currentMsg);
        };

        mPoseTree->processAllFrames(addPoseLambda);

        state.mMessage->fillData(time, tfMsg_vec);

        state.mPublisher.get()->publish(state.mMessage->ptr());

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2PublishTransformTreeDatabase::sPerInstanceState<OgnROS2PublishTransformTree>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
        mPoseTree.reset();
        mFirstIteration = true;
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2TfTreeMessage> mMessage = nullptr;

    bool mFirstIteration = true;

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
