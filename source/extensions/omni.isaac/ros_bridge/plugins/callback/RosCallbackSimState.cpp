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


RosCallbackSimState::RosCallbackSimState(RosNode* node) : RosCallback(node)
{
}

void RosCallbackSimState::pubCallback(ros::Publisher* pub)
{
    if (enable_pub == false)
    {
        return;
    }
    // CARB_LOG_ERROR("Publish Sim State Message");
    rosgraph_msgs::Clock time_msg;
    ros::Time t;
    t.fromSec(node_->getClock());
    time_msg.clock = t;
    pub->publish(time_msg);
}
}
}
}
