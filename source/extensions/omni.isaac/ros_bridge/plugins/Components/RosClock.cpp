// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosClock.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include "rosgraph_msgs/Clock.h"
#include "std_msgs/Int64.h"
#include "std_msgs/UInt8.h"
#include "std_srvs/Empty.h"
#include <time.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{

RosClock::~RosClock()
{
    CARB_LOG_ERROR("RosClock Destroyed");
    mRosNode->destroyMessage(mClockPubTopic);
}

void RosClock::initialize(RosNode* rosNode, const pxr::RosBridgeSchemaRosBridgeComponent& prim, pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
    onComponentChange();
}

void RosClock::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosClock& typedPrim = (pxr::RosBridgeSchemaRosClock)mPrim;
    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mClockPubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetClockPubTopicAttr(), mClockPubTopic);
    // isaac::utils::safeGetAttribute(typedPrim.GetSimTimeAttr(), mSimTime);


    mRosNode->createPublisher<rosgraph_msgs::Clock>(mClockPubTopic, 0, &RosClock::pubCallback, this);
}

void RosClock::pubCallback(ros::Publisher* pub)
{
    if (!mEnabled)
    {
        return;
    }
    CARB_LOG_ERROR("Publish Sim State Message");
    rosgraph_msgs::Clock time_msg;
    ros::Time t;
    t.fromSec(mTimeSeconds);
    time_msg.clock = t;
    pub->publish(time_msg);
}
}
}
}
