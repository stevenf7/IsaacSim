#pragma once

// #include "RosCallback.h"
#include "../Core/IsaacComponent.h"
#include "../Core/RosNode.h"

#include <RosBridgeSchema/rosClock.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{


class RosClock : public IsaacComponent
{

public:
    // Virtual so that it can be called when object is destroyed
    virtual ~RosClock();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);

    virtual void onComponentChange();
    void pubCallback(ros::Publisher* pub);

private:
    std::string mClockPubTopic = "/clock";
};
}
}
}
