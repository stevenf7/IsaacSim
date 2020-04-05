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

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
using namespace omni::isaac::dynamic_control;

RosCallbackJointState::RosCallbackJointState(RosNode* node, const std::vector<std::string>& paths)
    : RosCallback(node, paths)
{
    message_type = eRosMessageJointState;
}


void RosCallbackJointState::buildMessage(const sensor_msgs::JointState::ConstPtr& msg, const bool teleport)
{
    DynamicControl* dynamic_control = node_->getGlobals()->dynamic_control;
    double unitScale = 1.0 / UsdGeomGetStageMetersPerUnit(node_->getGlobals()->stage);
    const unsigned int num_actuators = msg->name.size();
    if (msg->position.size() != num_actuators)
    {
        return;
    }

    for (size_t i = 0; i < actor_list.size(); i++)
    {
        RosActor actor = actor_list[i];
        if (actor.type == eDcObjectArticulation)
        {
            if (!actor.handle)
            {
                continue;
            }
            dynamic_control->wakeUpArticulation(actor.handle);
            for (unsigned int actuator_idx = 0; actuator_idx < num_actuators; actuator_idx++)
            {
                DcHandle dof = dynamic_control->findArticulationDof(actor.handle, msg->name[actuator_idx].c_str());
                if (dof)
                {
                    DcDofProperties props;
                    dynamic_control->getDofProperties(dof, &props);
                    if (props.type == DcDofType::eTranslation)
                    {
                        dynamic_control->setDofPositionTarget(dof, msg->position[actuator_idx] * unitScale);
                    }
                    else
                    {
                        dynamic_control->setDofPositionTarget(dof, msg->position[actuator_idx]);
                    }
                }
            }
        }
    }
}
void RosCallbackJointState::subCallback(const sensor_msgs::JointState::ConstPtr& msg)
{
    // CARB_LOG_ERROR("RosCallbackJointState::subCallback");
    buildMessage(msg, false);
}
bool RosCallbackJointState::srvCallback(isaac_bridge::IsaacJointStates::Request& req,
                                        isaac_bridge::IsaacJointStates::Response& res)
{
    auto msg = sensor_msgs::JointState::ConstPtr(new sensor_msgs::JointState(req.joint_states));

    buildMessage(msg, true);
    return true;
}


void RosCallbackJointState::pubCallback(ros::Publisher* pub)
{
    DynamicControl* dynamic_control = node_->getGlobals()->dynamic_control;
    double stageUnits = UsdGeomGetStageMetersPerUnit(node_->getGlobals()->stage);
    sensor_msgs::JointState msg;
    msg.header.seq = 0;
    msg.header.stamp.fromSec(node_->getClock());

    for (size_t i = 0; i < actor_list.size(); i++)
    {

        RosActor actor = actor_list[i];
        if (actor.type == eDcObjectArticulation)
        {
            if (!actor.handle)
            {
                continue;
            }
            dynamic_control->wakeUpArticulation(actor.handle);

            int num_dofs = dynamic_control->getArticulationDofCount(actor.handle);

            for (int j = 0; j < num_dofs; j++)
            {

                DcHandle dof = dynamic_control->getArticulationDof(actor.handle, j);
                if (dof)
                {
                    msg.name.push_back(dynamic_control->getDofName(dof));
                    DcDofProperties props;
                    dynamic_control->getDofProperties(dof, &props);
                    if (props.type == DcDofType::eTranslation)
                    {
                        msg.position.push_back(dynamic_control->getDofPosition(dof) * stageUnits);
                    }
                    else
                    {
                        msg.position.push_back(dynamic_control->getDofPosition(dof));
                    }
                    msg.velocity.push_back(dynamic_control->getDofVelocity(dof));
                    msg.effort.push_back(0 /*dynamic_control->getDofForce(dof)*/); // TODO
                }
            }
        }
    }

    pub->publish(msg);
    //     {
    //         CARB_LOG_ERROR("Could not find %s in stage", paths_[i].c_str());
    //     }
}
}
}
}
