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

#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <include/Ros2Node.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/utils/Math.h>

#include <OgnROS2PublishJointStateDatabase.h>


class OgnROS2PublishJointState : public Ros2Node
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishJointStateDatabase::sInternalState<OgnROS2PublishJointState>(nodeObj);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }


    static bool compute(OgnROS2PublishJointStateDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnROS2PublishJointState>();

        const auto& prim = db.inputs.targetPrim();
        const char* primPath;
        if (prim.size() > 0)
        {
            primPath = omni::fabric::toSdfPath(prim[0]).GetText();
        }
        else
        {
            db.logError("Could not find target prim");
            return false;
        }

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
            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }
            state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

            // Verify we have a valid articulation prim
            if (state.mDynamicControlPtr->peekObjectType(primPath) == omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                state.mArticulationHandle = state.mDynamicControlPtr->getArticulation(primPath);
            }
            else
            {
                db.logError("Prim is not an articulation");
                return false;
            }

            if (!state.mArticulationHandle)
            {

                db.logError("Articulation %s not found", primPath);
                return false;
            }

            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);
            if (!state.mFactory->validateTopic(fullTopicName))
            {
                return false;
            }
            state.mMessage = state.mFactory->CreateJointStateMessage();

            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            return true;
        }

        return state.publishJointStates(db, context);
    }


    bool publishJointStates(OgnROS2PublishJointStateDatabase& db, const GraphContextObj& context)
    {
        auto& state = db.internalState<OgnROS2PublishJointState>();
        if (state.mPublisher.get()->get_subscription_count() != 0)
        {
            double stageUnits = 1.0 / mUnitScale;
            double dt = db.inputs.timeStamp() - mPreviousTimeStamp;
            mPreviousTimeStamp = db.inputs.timeStamp();

            long stageId = context.iContext->getStageId(context);
            mStage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            state.mMessage->fillData(db.inputs.timeStamp(), mDynamicControlPtr, mArticulationHandle, mStage, mDofProps,
                                     mPrevJointPosition, mCalculatedJointVelocity, dt, stageUnits);
            state.mPublisher.get()->publish(state.mMessage->ptr());
        }
        return true;
    }


    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishJointStateDatabase::sInternalState<OgnROS2PublishJointState>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mResetJointState = true;
        mStates = nullptr;
        mStage = nullptr;
        mDofProps.clear();
        mPrevJointPosition.clear();
        mCalculatedJointVelocity.clear();
        mPreviousTimeStamp = 0;
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2JointStateMessage> mMessage = nullptr;

    pxr::UsdStageWeakPtr mStage = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    pxr::SdfPath mArticulationPath;

    std::vector<float> mPrevJointPosition;
    std::vector<float> mCalculatedJointVelocity;
    omni::isaac::dynamic_control::DcDofState* mStates = nullptr;
    std::vector<omni::isaac::dynamic_control::DcDofProperties> mDofProps;

    double mUnitScale = 1;
    double mPreviousTimeStamp = 0;

    bool mResetJointState = true;
};

REGISTER_OGN_NODE()
