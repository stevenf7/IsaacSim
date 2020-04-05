#pragma once

#include "RosCallback.h"
#include "RosNode.h"
#include "rosgraph_msgs/Clock.h"
#include "std_msgs/Int64.h"
#include "std_msgs/UInt8.h"
#include "std_srvs/Empty.h"

namespace omni
{
namespace isaac
{
namespace ros_bridge
{

struct RosGlobals;


class RosState
{

public:
    RosState(RosGlobals* globals);
    ~RosState();
    void start();
    void stop();
    void tick(const float dt = 0.0f);
    void set_enable_clock(const bool state)
    {
        if (!SimStateCallback_)
        {
            CARB_LOG_ERROR("SimStateCallback not valid");
            return;
        }
        SimStateCallback_->set_enable_pub(state);
        enable_clock = state;
    }
    bool get_enable_clock()
    {
        if (!SimStateCallback_)
        {
            CARB_LOG_ERROR("SimStateCallback not valid");
            return false;
        }
        return SimStateCallback_->get_enable_pub();
    }

private:
    std::unique_ptr<RosNode> SimStateNode;
    RosCallbackSimState* SimStateCallback_ = nullptr;
    RosGlobals* globals_;
    bool enable_clock = true;
};
}
}
}
