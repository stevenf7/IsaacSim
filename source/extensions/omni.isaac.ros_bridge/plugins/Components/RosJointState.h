#pragma once

// #include "RosCallback.h"
#include "../Core/IsaacComponent.h"
#include "../Core/RosNode.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <rosBridgeSchema/rosJointState.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{


class RosJointState : public IsaacComponent
{

public:
    RosJointState(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    // Virtual so that it can be called when object is destroyed
    virtual ~RosJointState();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);

    virtual void onComponentChange();
    void pubCallback(ros::Publisher* pub);
    void subCallback(const sensor_msgs::JointState::ConstPtr& msg);

private:
    std::string mJointStatePubTopic = "/joint_state";
    std::string mJointStateSubTopic = "/joint_command";
    int mQueueSize = 0;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    double mUnitScale = 1;
    pxr::SdfPath mArticulationPath;
};
}
}
}
