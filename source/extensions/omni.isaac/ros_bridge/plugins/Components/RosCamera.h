#pragma once

// #include "RosCallback.h"
#include "../Core/IsaacComponent.h"
#include "../Core/RosNode.h"

#include <carb/sensors/Sensors.h>
#include <carb/syntheticdata/SyntheticData.h>

#include <RosBridgeSchema/rosCamera.h>
#include <omni/kit/IEditor.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{


class RosCamera : public IsaacComponent
{

public:
    RosCamera();
    // Virtual so that it can be called when object is destroyed
    virtual ~RosCamera();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageRefPtr stage);

    virtual void onComponentChange();
    void cameraInfoPubCallback(ros::Publisher* pub);
    void rgbPubCallback(ros::Publisher* pub);
    void depthPubCallback(ros::Publisher* pub);

private:
    carb::Framework* mFramework = nullptr;
    omni::kit::IEditor* mEditorInterface = nullptr;

    carb::syntheticdata::SyntheticData* mSyntheticDataInterface = nullptr;
    carb::sensors::Sensors* mSensorsInterface = nullptr;

    carb::sensors::Sensor* mRgbSensor = nullptr;
    void* mRgbSensorData = nullptr;
    bool mEnableRgb = false;


    carb::sensors::Sensor* mDepthSensor = nullptr;
    void* mDepthSensorData = nullptr;
    bool mEnableDepth = false;


    std::string mCameraInfoPubTopic = "/rgb";
    std::string mRgbPubTopic = "/rgb";
    std::string mDepthPubTopic = "/depth";
    std::string mFrameId = "/sim_camera";
    int mQueueSize = 10;
};
}
}
}
