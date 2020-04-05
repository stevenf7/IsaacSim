// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "../RosCallback.h"

#include "../RosNode.h"
#include "../RosGlobals.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/logging/Log.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{
using utils::conversions::asGfTransform;

namespace ros_bridge
{
using namespace omni::isaac::dynamic_control;

RosCallbackPose::RosCallbackPose(RosNode* node, const std::vector<std::string>& paths) : RosCallback(node, paths)
{
    message_type = eRosMessagePose;
}
void RosCallbackPose::subCallback(const geometry_msgs::PoseStamped::ConstPtr& msg)
{
    DynamicControl* dynamic_control = node_->getGlobals()->dynamic_control;
    double unitScale = 1.0f / UsdGeomGetStageMetersPerUnit(node_->getGlobals()->stage);

    for (size_t i = 0; i < actor_list.size(); i++)
    {
        RosActor actor = actor_list[i];
        if (actor.prim.GetName().GetString() == msg->header.frame_id)
        {
            DcTransform trans = asDcTransform(msg->pose, unitScale);

            if (actor.type == eDcObjectArticulation)
            {
                DcHandle rigid_body = dynamic_control->getArticulationRootBody(actor.handle);
                dynamic_control->setRigidBodyPose(rigid_body, trans);
            }
            else if (actor.type == eDcObjectRigidBody)
            {
                dynamic_control->setRigidBodyPose(actor.handle, trans);
            }
            else if (actor.type == eDcObjectNone)
            {
                pxr::GfTransform body_pose;
                omni::usd::UsdUtils::setLocalTransformMatrix(actor.prim, asGfTransform(trans).GetMatrix());
            }
        }
    }
}
void RosCallbackPose::pubCallback(ros::Publisher* pub)
{
    double stageUnits = UsdGeomGetStageMetersPerUnit(node_->getGlobals()->stage);
    DynamicControl* dynamic_control = node_->getGlobals()->dynamic_control;
    for (size_t i = 0; i < actor_list.size(); i++)
    {
        RosActor actor = actor_list[i];

        geometry_msgs::PoseStamped pose_msg;
        pose_msg.header.seq = 0; // TODO: use frame number?
        pose_msg.header.stamp.fromSec(node_->getClock());
        pose_msg.header.frame_id = actor.prim.GetName().GetString();

        if (actor.type == eDcObjectArticulation)
        {
            DcHandle rigid_body = dynamic_control->getArticulationRootBody(actor.handle);
            DcTransform trans = dynamic_control->getRigidBodyPose(rigid_body);

            pose_msg.pose = asRosPose(trans, stageUnits);
        }
        else if (actor.type == eDcObjectRigidBody)
        {
            DcTransform trans = dynamic_control->getRigidBodyPose(actor.handle);
            pose_msg.pose = asRosPose(trans, stageUnits);
        }
        else if (actor.type == eDcObjectNone)
        {
            const pxr::GfTransform body_0_world(omni::usd::UsdUtils::getWorldTransformMatrix(actor.prim));
            pose_msg.pose = asRosPose(body_0_world, stageUnits);
        }
        pub->publish(pose_msg);
    }
}
bool RosCallbackPose::srvCallback(isaac_bridge::IsaacPose::Request& req, isaac_bridge::IsaacPose::Response& res)
{
    const unsigned int num_actors = req.names.size();
    DynamicControl* dynamic_control = node_->getGlobals()->dynamic_control;
    double stageUnits = UsdGeomGetStageMetersPerUnit(node_->getGlobals()->stage);
    double unitScale = 1.0f / stageUnits;
    for (size_t req_idx = 0; req_idx < num_actors; req_idx++)
    {
        for (size_t i = 0; i < actor_list.size(); i++)
        {
            RosActor actor = actor_list[i];

            if (actor.prim && actor.prim.GetName().GetString() == req.names[req_idx])
            {
                DcTransform body_pose;
                if (req.poses.size() == num_actors)
                {
                    body_pose = asDcTransform(req.poses[req_idx], unitScale);

                    if (actor.type == eDcObjectArticulation)
                    {
                        if (!actor.handle)
                        {
                            continue;
                        }
                        CARB_LOG_INFO("Pose service message for Articulation");
                        dynamic_control->wakeUpArticulation(actor.handle);
                        DcHandle rigid_body = dynamic_control->getArticulationRootBody(actor.handle);
                        dynamic_control->setRigidBodyPose(rigid_body, body_pose);
                    }
                    else if (actor.type == eDcObjectRigidBody)
                    {
                        if (!actor.handle)
                        {
                            continue;
                        }
                        CARB_LOG_INFO("Pose service message for Rigid");
                        dynamic_control->wakeUpRigidBody(actor.handle);
                        dynamic_control->setRigidBodyPose(actor.handle, body_pose);
                    }
                    else if (actor.type == eDcObjectNone)
                    {
                        CARB_LOG_INFO("Pose service message for None");
                        omni::usd::UsdUtils::setLocalTransformMatrix(actor.prim, asGfTransform(body_pose).GetMatrix());
                    }
                    CARB_LOG_INFO("Pose service message recieved");
                }

                if (req.velocities.size() == num_actors)
                {
                    // carb::Float3 linear_velocity = { req.velocities[req_idx].linear.x,
                    // req.velocities[req_idx].linear.y,
                    //                                  req.velocities[req_idx].linear.z };
                    // carb::Float3 angular_velocity = { req.velocities[req_idx].angular.x,
                    //                                   req.velocities[req_idx].angular.y,
                    //                                   req.velocities[req_idx].angular.z };
                    CARB_LOG_INFO("Velocity service message recieved");
                }

                if (req.scales.size() == num_actors)
                {
                    // carb::Float3 body_scale = { req.scales[req_idx].x, req.scales[req_idx].y, req.scales[req_idx].z
                    // };
                    CARB_LOG_INFO("Scale service message recieved");
                }
                return true;
            }
        }
    }
    return false;
}
}
}
}
