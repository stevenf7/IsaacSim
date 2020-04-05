// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosState.h"

#include "RosGlobals.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <time.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
RosState::RosState(RosGlobals* globals)
{
    globals_ = globals;

    CARB_LOG_INFO("RosState Created");

    SimStateNode = std::make_unique<RosNode>(globals_);
    std::unique_ptr<RosCallbackSimState> SimStateCallback = std::make_unique<RosCallbackSimState>(SimStateNode.get());
    SimStateCallback_ = SimStateCallback.get();
    SimStateNode->start();
    SimStateNode->createPublisher<rosgraph_msgs::Clock>(
        "clock", 100, &RosCallbackSimState::pubCallback, std::move(SimStateCallback));
}

RosState::~RosState()
{
    CARB_LOG_INFO("RosState Destroyed");

    SimStateCallback_ = nullptr;
    SimStateNode = nullptr;
}
void RosState::start()
{
    globals_->clock = 0;
}
void RosState::stop()
{
}
void RosState::tick(const float dt)
{
    // CARB_LOG_ERROR("RosState Tick %f", dt);
    SimStateNode->tick();
    if (enable_clock)
    {
        globals_->clock += dt;
    }
    else
    {
        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, &ts);
        globals_->clock = static_cast<double>(ts.tv_sec) + static_cast<double>(ts.tv_nsec) / 1e9;
    }
}
}
}
}
