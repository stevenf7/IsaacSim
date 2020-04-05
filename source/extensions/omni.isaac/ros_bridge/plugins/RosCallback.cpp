// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosCallback.h"

#include "RosGlobals.h"
#include "RosNode.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{

using namespace omni::isaac::dynamic_control;

RosCallback::RosCallback(RosNode* node)
{
    node_ = node;
    message_type = eRosMessageNone;
    globals_ = node_->getGlobals();
    if (!globals_)
    {
        CARB_LOG_ERROR("globals pointer not valid");
        return;
    }
}
RosCallback::RosCallback(RosNode* node, const std::vector<std::string>& paths)
{
    node_ = node;
    paths_ = paths;
    message_type = eRosMessageNone;
    globals_ = node_->getGlobals();
    if (!globals_)
    {
        CARB_LOG_ERROR("globals pointer not valid");
        return;
    }
    DynamicControl* dynamic_control = node_->getGlobals()->dynamic_control;

    for (size_t i = 0; i < paths.size(); i++)
    {
        std::string wildcard = paths_[i].substr(paths_[i].size() - 2, 2);
        std::string base_path = paths_[i];
        // if (wildcard == "/*")
        // {

        //     base_path.pop_back();
        //     base_path.pop_back();
        //     pxr::UsdPrim base_prim = node_->getGlobals()->stage->GetPrimAtPath(pxr::SdfPath(base_path));
        //     pxr::UsdPrimSubtreeRange range = base_prim.GetDescendants();
        //     for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        //     {
        //         pxr::UsdPrim child_prim = *iter;
        //         if (child_prim)
        //         {
        //             RosActor actor;
        //             actor.prim = child_prim;
        //             DcObjectType prim_type =
        //             dynamic_control->peekObjectType(child_prim.GetPath().GetString().c_str());

        //             if (prim_type == eDcObjectArticulation)
        //             {
        //                 actor.handle = dynamic_control->getArticulation(child_prim.GetPath().GetString().c_str());
        //                 actor.type = prim_type;
        //                 CARB_LOG_INFO("Register Articulation at %s", child_prim.GetPath().GetString().c_str());
        //             }
        //             else if (prim_type == eDcObjectRigidBody)
        //             {
        //                 actor.handle = dynamic_control->getRigidBody(child_prim.GetPath().GetString().c_str());
        //                 actor.type = eDcObjectRigidBody;
        //                 CARB_LOG_INFO("Register Rigid Body at %s", child_prim.GetPath().GetString().c_str());
        //             }
        //             else
        //             {
        //                 actor.handle = dynamic_control->getObject(child_prim.GetPath().GetString().c_str());
        //                 actor.type = eDcObjectNone;
        //                 CARB_LOG_INFO("Register Prim at %s", child_prim.GetPath().GetString().c_str());
        //             }
        //             actor_list.push_back(actor);
        //         }
        //     }
        // }
        // else
        {
            pxr::UsdPrim child_prim = node_->getGlobals()->stage->GetPrimAtPath(pxr::SdfPath(base_path));
            if (child_prim)
            {
                RosActor actor;
                actor.prim = child_prim;
                DcObjectType prim_type = dynamic_control->peekObjectType(child_prim.GetPath().GetString().c_str());

                if (prim_type == eDcObjectArticulation)
                {
                    actor.handle = dynamic_control->getArticulation(child_prim.GetPath().GetString().c_str());
                    actor.type = prim_type;
                    CARB_LOG_INFO("Register Articulation at %s", child_prim.GetPath().GetString().c_str());
                }
                else if (prim_type == eDcObjectRigidBody)
                {
                    actor.handle = dynamic_control->getRigidBody(child_prim.GetPath().GetString().c_str());
                    actor.type = eDcObjectRigidBody;
                    CARB_LOG_INFO("Register Rigid Body at %s", child_prim.GetPath().GetString().c_str());
                }
                else
                {
                    actor.handle = dynamic_control->getObject(child_prim.GetPath().GetString().c_str());
                    actor.type = eDcObjectNone;
                    CARB_LOG_INFO("Register Prim at %s", child_prim.GetPath().GetString().c_str());
                }
                actor_list.push_back(actor);
            }
        }
    }
}
void RosCallback::pubCallback(ros::Publisher* pub)
{
    CARB_LOG_ERROR("Publisher Called but not implemented!");
}
void RosCallback::tickCallback()
{
}
// void RosCallback::setPaths(const std::vector<std::string>& paths)
// {
//     CARB_LOG_INFO("Set Paths:");

//     for (size_t i = 0; i < paths.size(); i++)
//     {
//         CARB_LOG_INFO("   %s", paths[i].c_str());
//         paths_.push_back(paths[i]);
//     }
// }
std::vector<std::string> RosCallback::getPaths()
{
    return paths_;
}
void RosCallback::set_enable_pub(const bool enabled)
{
    enable_pub = enabled;
}
void RosCallback::set_enable_sub(const bool enabled)
{
    enable_sub = enabled;
}
void RosCallback::set_enable_srv(const bool enabled)
{
    enable_srv = enabled;
}
bool RosCallback::get_enable_pub()
{
    return enable_pub;
}
bool RosCallback::get_enable_sub()
{
    return enable_sub;
}
bool RosCallback::get_enable_srv()
{
    return enable_srv;
}
RosMessageType RosCallback::getMessageType()
{
    return message_type;
}
}
}
}
