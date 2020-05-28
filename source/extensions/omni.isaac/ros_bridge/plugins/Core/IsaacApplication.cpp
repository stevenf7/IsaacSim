// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "IsaacApplication.h"
#include "../Components/RosClock.h"
#include "../Components/RosCamera.h"
#include "../Components/RosLidar.h"
#include "../Components/RosJointState.h"

#include "plugins/core/ScopedTimer.h"
#include "ros/ros.h"

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
IsaacApplication::IsaacApplication(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
{
    mDynamicControlPtr = dynamicControlPtr;
    carb::Framework* framework = carb::getFramework();
    mTasking = framework->acquireInterface<carb::tasking::ITasking>();
    mTaskCounter = mTasking->createCounter();
}


IsaacApplication::~IsaacApplication()
{
    mTasking->yieldUntilCounter(mTaskCounter);
    mTasking->destroyCounter(mTaskCounter);

    deleteAllComponents();
}

void IsaacApplication::initialize(pxr::UsdStageWeakPtr stage)
{
    utils::BridgeApplicationBase<IsaacComponent>::initialize(stage);
}


void IsaacApplication::tick(double dt)
{
    for (auto& component : mComponents)
    {
        component.second.get()->updateTimestamp(mTimeSeconds, dt, mTimeNanoSeconds);
    }

    for (auto& node : mRosNodes)
    {
        if (node.second)
        {
            node.second->tick();
        }
    }
    mTimeSeconds += dt;
    mTimeNanoSeconds = mTimeSeconds * 1e9;
}

RosNode* IsaacApplication::getRosNode(const pxr::UsdPrim& prim)
{
    const pxr::RosBridgeSchemaRosBridgeComponent& typedPrim = pxr::RosBridgeSchemaRosBridgeComponent(prim);

    std::string nodeName = "";
    isaac::utils::safeGetAttribute(typedPrim.GetRosNodePrefixAttr(), nodeName);


    if (mRosNodes.find(nodeName) == mRosNodes.end())
    {
        mRosNodes[nodeName] = std::make_unique<RosNode>(nodeName);
    }
    return mRosNodes[nodeName].get();
}
void IsaacApplication::onComponentAdd(const pxr::UsdPrim& prim)
{

    std::unique_ptr<IsaacComponent> component;
    if (prim.IsA<pxr::RosBridgeSchemaRosClock>())
    {
        CARB_LOG_ERROR("RosBridgeSchemaRosClock");

        component = std::make_unique<RosClock>();
        component->initialize(getRosNode(prim), pxr::RosBridgeSchemaRosClock(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosCamera>())
    {
        CARB_LOG_ERROR("RosBridgeSchemaRosCamera");

        component = std::make_unique<RosCamera>();
        component->initialize(getRosNode(prim), pxr::RosBridgeSchemaRosCamera(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosJointState>())
    {
        CARB_LOG_ERROR("RosBridgeSchemaRosJointState");

        component = std::make_unique<RosJointState>(mDynamicControlPtr);
        component->initialize(getRosNode(prim), pxr::RosBridgeSchemaRosJointState(prim), mStage);
    }
    else if (prim.IsA<pxr::RosBridgeSchemaRosLidar>())
    {
        CARB_LOG_ERROR("RosBridgeSchemaRosLidar");

        component = std::make_unique<RosLidar>();
        component->initialize(getRosNode(prim), pxr::RosBridgeSchemaRosLidar(prim), mStage);
    }

    if (component)
    {
        CARB_LOG_ERROR("Create: Prim %s with type: %s", prim.GetPath().GetString().c_str(),
                       component->getPrim().GetPrim().GetTypeName().GetString().c_str());
        mComponents[prim.GetPath().GetString()] = std::move(component);
    }
}


}
}
}
