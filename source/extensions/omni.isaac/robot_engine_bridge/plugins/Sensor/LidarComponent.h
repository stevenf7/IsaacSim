#pragma once

#include "../Core/IsaacComponent.h"

#include <carb/Types.h>

#include <RobotEngineBridgeSchema/robotEngineLidar.h>
#include <omni/isaac/lidar/LidarInterface.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
class LidarComponent : public IsaacComponent
{
public:
    /**
     * @brief Construct a new Lidar Component object
     *
     * @param appHandle
     * @param prim
     * @param stage
     */
    LidarComponent();

    /**
     * @brief Destroy the Lidar Component object
     *
     */
    ~LidarComponent();


    /**
     * @brief The lidar pointer might not be valid, so force update on start
     *
     */
    virtual void onStart();

    /**
     * @brief
     *
     */
    virtual void tick();

    /**
     * @brief
     *
     */
    virtual void onComponentChange();

private:
    carb::Framework* framework = nullptr;
    omni::isaac::lidar::LidarInterface* mLidarInterface = nullptr;


    /// The name of the channel on which state informations is published
    std::string mOutputComponent = "output";
    std::string mScanChannelName = "rangescan";
    pxr::SdfPath mLidarPath = pxr::SdfPath("/");

    omni::isaac::lidar::LidarHandle mLidarHandle = omni::isaac::lidar::kLidarInvalidHandle;
};
}
}
}
