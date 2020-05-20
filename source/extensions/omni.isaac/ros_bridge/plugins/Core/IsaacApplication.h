#pragma once

#include "IsaacComponent.h"
#include "RosNode.h"
#include "plugins/bridge/BridgeApplication.h"

#include <carb/dictionary/DictionaryUtils.h>
#include <carb/logging/Log.h>
#include <carb/tasking/ITasking.h>

#include <RosBridgeSchema/rosBridgeComponent.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>


namespace omni
{
namespace isaac
{
namespace ros_bridge
{
class IsaacApplication : public utils::BridgeApplicationBase<IsaacComponent>
{
public:
    /**
     * @brief Construct a new Isaac Application object
     *
     * @param isaacCApiPtr
     * @param dynamicControlPtr
     */
    IsaacApplication(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);

    /**
     * @brief Destroy the Isaac Application object
     *
     */
    ~IsaacApplication();

    /**
     * @brief Initialize this application
     *
     * @param stage
     */
    virtual void initialize(pxr::UsdStageWeakPtr stage);


    void tick(double dt);
    /**
     * @brief Create a supported component in this application
     *
     * @param prim
     */
    void onComponentAdd(const pxr::UsdPrim& prim);

private:
    RosNode* getRosNode(const pxr::UsdPrim& prim);
    std::string mAppFilename;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    carb::tasking::ITasking* mTasking = nullptr;
    carb::tasking::Counter* mTaskCounter = nullptr;

    int64_t mTimeDifferenceNanoSeconds = 0;
    bool mRunning = false;

    std::unordered_map<std::string, std::unique_ptr<RosNode>> mRosNodes;
};
}
}
}
