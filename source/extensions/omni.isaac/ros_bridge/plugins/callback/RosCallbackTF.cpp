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
using utils::conversions::asPxTransform;

namespace ros_bridge
{

using namespace omni::isaac::dynamic_control;

RosCallbackTF::RosCallbackTF(RosNode* node, const std::vector<std::string>& paths, tf2_ros::Buffer* tf_buffer)
    : RosCallback(node, paths)
{
    message_type = eRosMessageTf;
    tf_buffer_ = tf_buffer;
}

void RosCallbackTF::pubCallback(ros::Publisher* pub)
{
    DynamicControl* dynamic_control = node_->getGlobals()->dynamic_control;
    double stageUnits = UsdGeomGetStageMetersPerUnit(node_->getGlobals()->stage);
    tf2_msgs::TFMessage tf_msg;
    geometry_msgs::TransformStamped msg;
    msg.header.seq = 0; // TODO: use frame number?
    msg.header.stamp.fromSec(node_->getClock());

    for (size_t i = 0; i < actor_list.size(); i++)
    {
        RosActor actor = actor_list[i];

        if (actor.type == eDcObjectArticulation)
        {
            DcHandle root_body = dynamic_control->getArticulationRootBody(actor.handle);
            DcTransform trans = dynamic_control->getRigidBodyPose(root_body);
            msg.header.frame_id = "world";
            msg.child_frame_id = dynamic_control->getRigidBodyName(root_body);
            msg.transform = asRosTransform(trans, stageUnits);

            tf_msg.transforms.push_back(msg);
            int num_dofs = dynamic_control->getArticulationBodyCount(actor.handle);
            for (int j = 0; j < num_dofs; j++)
            {
                DcHandle parent_body = dynamic_control->getArticulationBody(actor.handle, j);
                int num_joints = dynamic_control->getRigidBodyChildJointCount(parent_body);
                for (int k = 0; k < num_joints; k++)
                {
                    DcHandle joint = dynamic_control->getRigidBodyChildJoint(parent_body, k);
                    DcHandle child_body = dynamic_control->getJointChildBody(joint);

                    physx::PxTransform body0_pose = asPxTransform(dynamic_control->getRigidBodyPose(parent_body));
                    physx::PxTransform body1_pose = asPxTransform(dynamic_control->getRigidBodyPose(child_body));
                    physx::PxTransform pos0_1(body0_pose.transformInv(body1_pose));

                    msg.header.frame_id = dynamic_control->getRigidBodyName(parent_body);
                    msg.child_frame_id = dynamic_control->getRigidBodyName(child_body);
                    msg.transform = asRosTransform(pos0_1, stageUnits);
                    tf_msg.transforms.push_back(msg);
                }
            }
        }
        else if (actor.type == eDcObjectRigidBody)
        {
            DcTransform trans = dynamic_control->getRigidBodyPose(actor.handle);
            msg.header.frame_id = "world";
            msg.child_frame_id = actor.prim.GetName().GetString();
            msg.transform = asRosTransform(trans, stageUnits);
            tf_msg.transforms.push_back(msg);
        }
        else if (actor.type == eDcObjectNone)
        {
            const pxr::GfTransform body_0_world(omni::usd::UsdUtils::getWorldTransformMatrix(actor.prim));
            msg.header.frame_id = "world";
            msg.child_frame_id = actor.prim.GetName().GetString();
            msg.transform = asRosTransform(body_0_world, stageUnits);
            tf_msg.transforms.push_back(msg);
        }
    }


    pub->publish(tf_msg);
}

void RosCallbackTF::tickCallback()
{
    DynamicControl* dynamic_control = node_->getGlobals()->dynamic_control;
    double unitScale = 1.0f / UsdGeomGetStageMetersPerUnit(node_->getGlobals()->stage);
    // use the topic name as the name of the base frame to transform from
    for (size_t i = 0; i < actor_list.size(); i++)
    {
        RosActor actor = actor_list[i];
        std::string name = actor.prim.GetName().GetString();
        geometry_msgs::TransformStamped transformStamped;
        if (tf_buffer_->canTransform("world", name, ros::Time(0)))
        {
            transformStamped = tf_buffer_->lookupTransform("world", name, ros::Time(0));

            DcTransform trans = asDcTransform(transformStamped.transform, unitScale);

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
}
}
}
