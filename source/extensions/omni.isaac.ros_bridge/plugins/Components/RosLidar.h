#pragma once

// #include "RosCallback.h"
#include "../Core/IsaacComponent.h"
#include "../Core/RosNode.h"

#include <lidarSchema/lidar.h>
#include <omni/isaac/lidar/LidarInterface.h>
#include <rosBridgeSchema/rosLidar.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{


class RosLidar : public IsaacComponent
{

public:
    RosLidar();
    // Virtual so that it can be called when object is destroyed
    virtual ~RosLidar();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);

    virtual void onComponentChange();
    void pubCallback(ros::Publisher* pub);
    void pointCloudPubCallback(ros::Publisher* pub);

private:
    std::string mLaserScanPubTopic = "/laser_scan";
    int mQueueSize = 0;
    pxr::SdfPath mLidarPath = pxr::SdfPath("/");
    omni::isaac::lidar::LidarHandle mLidarHandle = omni::isaac::lidar::kLidarInvalidHandle;
    carb::Framework* mFramework = nullptr;
    omni::isaac::lidar::LidarInterface* mLidarInterface = nullptr;
    pxr::LidarSchemaLidar mLidarPrim;
    std::string mFrameId = "/sim_lidar";

    bool mEnablePointCloud = false;
    std::string mPointCloudPubTopic = "/point_cloud";

    double mUnitScale;
};
}
}
}
