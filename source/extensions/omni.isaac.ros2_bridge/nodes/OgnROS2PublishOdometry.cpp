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

#include <OgnROS2PublishOdometryDatabase.h>


class OgnROS2PublishOdometry : public Ros2Node
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS2PublishOdometryDatabase::sPerInstanceState<OgnROS2PublishOdometry>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS2PublishOdometryDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnROS2PublishOdometry>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        // Either publisher was not valid, create a new one
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

            state.mZUp = UsdGeomGetStageUpAxis(stage) == "Z" ? true : false;
            state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

            auto& robotFrontVec = db.inputs.robotFront();

            state.mRobotFront = pxr::GfVec3f(static_cast<float>(robotFrontVec[0]), static_cast<float>(robotFrontVec[1]),
                                             static_cast<float>(robotFrontVec[2]));

            state.mRobotFront = pxr::GfGetNormalized(state.mRobotFront, 1.0f);

            if (state.mZUp)
            {
                state.mRobotSide = pxr::GfCross(pxr::GfVec3f(0.0, 0.0, 1.0), state.mRobotFront);
            }
            else
            {
                state.mRobotSide = pxr::GfCross(pxr::GfVec3f(0.0, 1.0, 0.0), state.mRobotFront);
            }

            // Setup ROS odom publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                return false;
            }
            state.mMessage = state.mFactory->CreateOdomMessage();

            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            state.mOdomFrameId = db.inputs.odomFrameId();
            state.mChassisFrameId = db.inputs.chassisFrameId();

            return true;
        }

        state.publishOdom(db);

        return true;
    }


    void publishOdom(OgnROS2PublishOdometryDatabase& db)
    {

        auto& state = db.perInstanceState<OgnROS2PublishOdometry>();

        // Check if subscription count is 0
        if (!state.mPublisher.get()->get_subscription_count())
        {
            return;
        }
        auto& linVel = db.inputs.linearVelocity();
        auto& angVel = db.inputs.angularVelocity();
        auto& position = db.inputs.position();
        auto& orientation = db.inputs.orientation();


        state.mMessage->fillHeader(db.inputs.timeStamp(), state.mOdomFrameId);
        state.mMessage->fillData(
            state.mChassisFrameId, linVel, angVel, mRobotFront, mRobotSide, mUnitScale, mZUp, position, orientation);

        state.mPublisher.get()->publish(state.mMessage->ptr());
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishOdometryDatabase::sPerInstanceState<OgnROS2PublishOdometry>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2OdomMessage> mMessage = nullptr;

    double mUnitScale;
    bool mZUp = true;

    // The front of the robot
    pxr::GfVec3f mRobotFront = pxr::GfVec3f(1.0, 0.0, 0.0);

    pxr::GfVec3f mRobotSide = pxr::GfVec3f(0.0, 1.0, 0.0);

    pxr::GfVec3f mStageup = pxr::GfVec3f(0.0, 0.0, 1.0);

    std::string mOdomFrameId = "odom";
    std::string mChassisFrameId = "base_link";
};

REGISTER_OGN_NODE()
