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
#include "sensor_msgs/msg/joint_state.hpp"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/ros/Ros2Node.h>
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
            db.logWarning("no prim path found");
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
            if (!validateTopic(fullTopicName))
            {
                return false;
            }
            state.mPublisher =
                state.mNodeHandle->create_publisher<sensor_msgs::msg::JointState>(fullTopicName, db.inputs.queueSize());

            return true;
        }

        state.publishJointStates(db);
        return true;
    }


    void publishJointStates(OgnROS2PublishJointStateDatabase& db)
    {
        double stageUnits = 1.0 / mUnitScale;
        sensor_msgs::msg::JointState msg;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));
        }
        else
        {
            db.logError("Timestamp is invalid");
            return;
        }

        double dt = db.inputs.timeStamp() - mPreviousTimeStamp;
        mPreviousTimeStamp = db.inputs.timeStamp();

        mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
        size_t num_dofs = mDynamicControlPtr->getArticulationDofCount(mArticulationHandle);
        mDofProps.resize(num_dofs);
        mDynamicControlPtr->getArticulationDofProperties(mArticulationHandle, mDofProps.data());
        mStates =
            mDynamicControlPtr->getArticulationDofStates(mArticulationHandle, omni::isaac::dynamic_control::kDcStateAll);

        mPrevJointPosition.resize(num_dofs);
        mCalculatedJointVelocity.resize(num_dofs);

        if (mStates != nullptr)
        {
            for (size_t j = 0; j < num_dofs; j++)
            {
                // calculate velocity
                mCalculatedJointVelocity[j] = static_cast<float>((mStates[j].pos - mPrevJointPosition[j]) / dt);
                mPrevJointPosition[j] = mStates[j].pos;

                omni::isaac::dynamic_control::DcHandle dof =
                    mDynamicControlPtr->getArticulationDof(mArticulationHandle, j);
                if (dof)
                {
                    msg.name.push_back(mDynamicControlPtr->getDofName(dof));
                }
                if (mDofProps[j].type == omni::isaac::dynamic_control::DcDofType::eTranslation)
                {
                    msg.position.push_back(omni::isaac::utils::math::roundNearest(mStates[j].pos * stageUnits, 10000.0)); // m
                    msg.velocity.push_back(omni::isaac::utils::math::roundNearest(
                        mCalculatedJointVelocity[j] * stageUnits, 10000.0)); // m/s
                    msg.effort.push_back(
                        omni::isaac::utils::math::roundNearest(mStates[j].effort * stageUnits, 10000.0)); // N
                }
                else
                {
                    msg.position.push_back(omni::isaac::utils::math::roundNearest(mStates[j].pos, 10000.0)); // rad
                    msg.velocity.push_back(
                        omni::isaac::utils::math::roundNearest(mCalculatedJointVelocity[j], 10000.0)); // rad/s
                    msg.effort.push_back(omni::isaac::utils::math::roundNearest(
                        mStates[j].effort * stageUnits * stageUnits, 10000.0)); // N*m
                }
            }
            mPublisher->publish(msg);
        }
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
        mDofProps.clear();
        mPrevJointPosition.clear();
        mCalculatedJointVelocity.clear();
        mPreviousTimeStamp = 0;
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<rclcpp::Publisher<sensor_msgs::msg::JointState>> mPublisher = nullptr;

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
