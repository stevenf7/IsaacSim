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

#include "omni/isaac/utils/UsdUtilities.h"
#include "pxr/usd/usdPhysics/joint.h"
#include "sensor_msgs/JointState.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/Math.h>

#include <DynamicControl.h>
#include <OgnROS1PublishJointStateDatabase.h>
#include <RosNode.h>

class OgnROS1PublishJointState : public RosNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS1PublishJointStateDatabase::sPerInstanceState<OgnROS1PublishJointState>(nodeObj, instanceId);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }


    static bool compute(OgnROS1PublishJointStateDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnROS1PublishJointState>();
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
        if (!state.spinOnce(db.inputs.nodeNamespace()))
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

            if (!validateTopic(topicName))
            {
                return false;
            }
            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<sensor_msgs::JointState>(topicName, db.inputs.queueSize()));

            return true;
        }

        state.publishJointStates(db, context);
        return true;
    }


    void publishJointStates(OgnROS1PublishJointStateDatabase& db, const GraphContextObj& context)
    {
        double stageUnits = 1.0 / mUnitScale;
        sensor_msgs::JointState msg;
        msg.header.seq = 0;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logError("Timestamp is invalid");
            return;
        }

        double dt = db.inputs.timeStamp() - mPreviousTimeStamp;
        mPreviousTimeStamp = db.inputs.timeStamp();

        mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
        int num_dofs = mDynamicControlPtr->getArticulationDofCount(mArticulationHandle);
        mDofProps.resize(num_dofs);
        mDynamicControlPtr->getArticulationDofProperties(mArticulationHandle, mDofProps.data());
        mStates =
            mDynamicControlPtr->getArticulationDofStates(mArticulationHandle, omni::isaac::dynamic_control::kDcStateAll);

        mPrevJointPosition.resize(num_dofs);
        mCalculatedJointVelocity.resize(num_dofs);

        long stageId = context.iContext->getStageId(context);
        auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

        if (mStates != nullptr)
        {
            for (int j = 0; j < num_dofs; j++)
            {
                // calculate velocity
                mCalculatedJointVelocity[j] = (mStates[j].pos - mPrevJointPosition[j]) / dt;
                mPrevJointPosition[j] = mStates[j].pos;

                omni::isaac::dynamic_control::DcHandle dof =
                    mDynamicControlPtr->getArticulationDof(mArticulationHandle, j);

                if (dof)
                {
                    msg.name.push_back(mDynamicControlPtr->getDofName(dof));

                    // sign check
                    mParentName = mDynamicControlPtr->getRigidBodyName(mDynamicControlPtr->getDofParentBody(dof));
                    const char* jointPath = mDynamicControlPtr->getDofPath(dof);
                    pxr::SdfPathVector targets;
                    pxr::UsdPhysicsJoint joint = pxr::UsdPhysicsJoint::Get(stage, pxr::SdfPath(jointPath));
                    joint.GetBody0Rel().GetTargets(&targets);
                    const char* body0Name = targets.at(0).GetName().c_str();
                    signCheck = (strcmp(mParentName, body0Name) == 0) ? 1 : -1;
                    // printf("signCheck %d\n", signCheck);
                }

                if (mDofProps[j].type == omni::isaac::dynamic_control::DcDofType::eTranslation)
                {
                    msg.position.push_back(
                        omni::isaac::utils::math::roundNearest(mStates[j].pos * stageUnits * signCheck, 10000.0)); // m
                    msg.velocity.push_back(omni::isaac::utils::math::roundNearest(
                        mCalculatedJointVelocity[j] * stageUnits * signCheck, 10000.0)); // m/s
                    msg.effort.push_back(omni::isaac::utils::math::roundNearest(
                        mStates[j].effort * stageUnits * signCheck, 10000.0)); // N
                }
                else
                {
                    msg.position.push_back(omni::isaac::utils::math::roundNearest(mStates[j].pos * signCheck, 10000.0)); // rad
                    msg.velocity.push_back(omni::isaac::utils::math::roundNearest(
                        mCalculatedJointVelocity[j] * signCheck, 10000.0)); // rad/s
                    msg.effort.push_back(omni::isaac::utils::math::roundNearest(
                        mStates[j].effort * stageUnits * stageUnits * signCheck, 10000.0)); // N*m
                }
            }
            mPublisher->publish(msg);
        }
    }


    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS1PublishJointStateDatabase::sPerInstanceState<OgnROS1PublishJointState>(nodeObj, instanceId);
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
        RosNode::reset();
    }

private:
    std::unique_ptr<ros::Publisher> mPublisher;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    pxr::SdfPath mArticulationPath;

    std::vector<float> mPrevJointPosition;
    std::vector<float> mCalculatedJointVelocity;
    omni::isaac::dynamic_control::DcDofState* mStates = nullptr;
    std::vector<omni::isaac::dynamic_control::DcDofProperties> mDofProps;

    const char* mParentName;
    int signCheck = 1;

    double mUnitScale = 1;
    double mPreviousTimeStamp = 0;

    bool mResetJointState = true;
};

REGISTER_OGN_NODE()
