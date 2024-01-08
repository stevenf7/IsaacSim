// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
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

#include "isaac_ros_messages/IsaacPose.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdUtils.h>

#include <DynamicControl.h>
#include <OgnROS1ServiceTeleportDatabase.h>
#include <RosConversions.h>
#include <RosNode.h>


class OgnROS1ServiceTeleport : public RosNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS1ServiceTeleportDatabase::sInternalState<OgnROS1ServiceTeleport>(nodeObj);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnROS1ServiceTeleportDatabase& db)
    {
        auto& state = db.internalState<OgnROS1ServiceTeleport>();
        const GraphContextObj& context = db.abi_context();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {

            return false;
        }

        // Subscriber was not valid, create a new one
        if (!state.mServer)
        {
            // Find our stage
            state.stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(state.stageId));
            if (!stage)
            {
                db.logError("Could not find USD stage %ld", state.stageId);
                return false;
            }
            state.mUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(stage);

            // Setup ROS server
            const std::string& serviceName = db.inputs.serviceName();

            if (!validateTopic(serviceName))
            {
                return false;
            }
            if (ros::service::exists(serviceName, false))
            {
                db.logError("Service of the same name already exist");
                return false;
            }
            state.mCallback =
                [&state, &db](isaac_ros_messages::IsaacPose::Request& req, isaac_ros_messages::IsaacPose::Response& res)
            { return state.srvCallback(req, res, db); };
            state.mServer = std::make_unique<ros::ServiceServer>(
                state.mNodeHandle
                    ->advertiseService<isaac_ros_messages::IsaacPose::Request, isaac_ros_messages::IsaacPose::Response>(
                        serviceName, state.mCallback));

            return true;
        }

        return true;
    }


    bool srvCallback(isaac_ros_messages::IsaacPose::Request& req,
                     isaac_ros_messages::IsaacPose::Response& res,
                     OgnROS1ServiceTeleportDatabase& db)
    {
        const unsigned int num_prims = req.names.size();
        for (size_t req_idx = 0; req_idx < num_prims; req_idx++)
        {
            std::string prim_name = req.names[req_idx];
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
            pxr::UsdPrim prim = stage->GetPrimAtPath(pxr::SdfPath(prim_name));
            if (!prim)
            {
                db.logWarning("Prim %s does not exist", prim_name.c_str());
                // TODO: Add a server response if IsaacPose.srv is updated with response field
                continue;
            }
            omni::isaac::dynamic_control::DcObjectType type = mDynamicControlPtr->peekObjectType(prim_name.c_str());
            omni::isaac::dynamic_control::DcTransform body_pose;
            if (req.poses.size() == num_prims)
            {
                body_pose = omni::isaac::conversions::rosPoseAsDcTransform(req.poses[req_idx], mUnitScale);

                if (type == omni::isaac::dynamic_control::eDcObjectArticulation)
                {

                    omni::isaac::dynamic_control::DcHandle articulationHandle =
                        mDynamicControlPtr->getArticulation(prim_name.c_str());
                    mDynamicControlPtr->wakeUpArticulation(articulationHandle);
                    omni::isaac::dynamic_control::DcHandle rigidBodyHandle =
                        mDynamicControlPtr->getArticulationRootBody(articulationHandle);
                    mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, body_pose);
                }
                else if (type == omni::isaac::dynamic_control::eDcObjectRigidBody)
                {
                    omni::isaac::dynamic_control::DcHandle rigidBodyHandle =
                        mDynamicControlPtr->getRigidBody(prim_name.c_str());
                    mDynamicControlPtr->wakeUpRigidBody(rigidBodyHandle);
                    mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, body_pose);
                }
                else if (type == omni::isaac::dynamic_control::eDcObjectNone)
                {
                    omni::usd::UsdUtils::setLocalTransformMatrix(
                        stage->GetPrimAtPath(pxr::SdfPath(prim_name)),
                        omni::isaac::utils::conversions::asGfTransform(body_pose).GetMatrix());
                }
            }

            if (req.velocities.size() == num_prims)
            {
                carb::Float3 linear_velocity =
                    omni::isaac::conversions::asCarbFloat3(req.velocities[req_idx].linear, mUnitScale);
                carb::Float3 angular_velocity = omni::isaac::conversions::asCarbFloat3(req.velocities[req_idx].angular);

                if (type == omni::isaac::dynamic_control::eDcObjectArticulation)
                {

                    omni::isaac::dynamic_control::DcHandle articulationHandle =
                        mDynamicControlPtr->getArticulation(prim_name.c_str());
                    mDynamicControlPtr->wakeUpArticulation(articulationHandle);
                    omni::isaac::dynamic_control::DcHandle rigidBodyHandle =
                        mDynamicControlPtr->getArticulationRootBody(articulationHandle);
                    mDynamicControlPtr->setRigidBodyLinearVelocity(rigidBodyHandle, linear_velocity);
                    mDynamicControlPtr->setRigidBodyAngularVelocity(rigidBodyHandle, angular_velocity);
                }
                else if (type == omni::isaac::dynamic_control::eDcObjectRigidBody)
                {
                    omni::isaac::dynamic_control::DcHandle rigidBodyHandle =
                        mDynamicControlPtr->getRigidBody(prim_name.c_str());
                    mDynamicControlPtr->wakeUpRigidBody(rigidBodyHandle);
                    mDynamicControlPtr->setRigidBodyLinearVelocity(rigidBodyHandle, linear_velocity);
                    mDynamicControlPtr->setRigidBodyAngularVelocity(rigidBodyHandle, angular_velocity);
                }
                else if (type == omni::isaac::dynamic_control::eDcObjectNone)
                {
                    db.logWarning(
                        "Velocity service cannot be applied to non physics object with path: %s", prim_name.c_str());
                }
            }

            if (req.scales.size() == num_prims)
            {
                db.logWarning("Scale service message not supported currently");
            }
        }
        return true;
    }


    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1ServiceTeleportDatabase::sInternalState<OgnROS1ServiceTeleport>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mServer.reset(); // This should be reset before we reset the handle.
        mCallback = nullptr;
        RosNode::reset();
    }

private:
    std::unique_ptr<ros::ServiceServer> mServer;
    std::function<bool(isaac_ros_messages::IsaacPose::Request&, isaac_ros_messages::IsaacPose::Response&)> mCallback;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    double mUnitScale = 1;
    long stageId;
};

REGISTER_OGN_NODE()
