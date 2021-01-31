// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// #include "RosCallback.h"
#include "../Core/IsaacComponent.h"
#include "../Core/RosNode.h"

#include <carb/sensors/Sensors.h>
#include <carb/syntheticdata/SyntheticData.h>

#include <rosBridgeSchema/rosCamera.h>

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
                            pxr::UsdStageWeakPtr stage);

    virtual void onComponentChange();
    void cameraInfoPubCallback(ros::Publisher* pub);
    void rgbPubCallback(ros::Publisher* pub);
    void depthPubCallback(ros::Publisher* pub);
    void semanticPubCallback(ros::Publisher* pub);
    void instancePubCallback(ros::Publisher* pub);
    void labelPubCallback(ros::Publisher* pub);
    void boundingbox2dPubCallback(ros::Publisher* pub);
    void boundingbox3dPubCallback(ros::Publisher* pub);

private:
    carb::Framework* mFramework = nullptr;

    carb::syntheticdata::SyntheticData* mSyntheticDataInterface = nullptr;
    carb::sensors::Sensors* mSensorsInterface = nullptr;

    carb::sensors::Sensor* mRgbSensor = nullptr;
    void* mRgbSensorData = nullptr;
    bool mEnableRgb = false;

    carb::sensors::Sensor* mDepthSensor = nullptr;
    void* mDepthSensorData = nullptr;
    bool mEnableDepth = false;

    carb::sensors::Sensor* mInstanceSensor = nullptr;
    void* mInstanceSensorData = nullptr;
    bool mEnableInstance = false;

    carb::sensors::Sensor* mSegmentationSensor = nullptr;
    void* mSegmentationSensorData = nullptr;
    bool mEnableSegmentation = false;

    carb::sensors::Sensor* mSemanticSensor = nullptr;
    void* mSemanticSensorData = nullptr;
    bool mEnableSemantic = false;

    carb::sensors::Sensor* mBoundingBox2DSensor = nullptr;
    void* mBoundingBox2DSensorData = nullptr;
    bool mEnableBoundingBox2D = false;
    std::vector<std::string> mBoundingBox2DClassList;

    carb::sensors::Sensor* mBoundingBox3DSensor = nullptr;
    void* mBoundingBox3DSensorData = nullptr;
    bool mEnableBoundingBox3D = false;
    std::vector<std::string> mBoundingBox3DClassList;


    double mUnitScale;

    std::string mCameraInfoPubTopic = "/camera_info";
    std::string mRgbPubTopic = "/rgb";
    std::string mDepthPubTopic = "/depth";
    std::string mFrameId = "/sim_camera";
    std::string mInstancePubTopic = "/instance";
    std::string mSemanticPubTopic = "/semantic";
    std::string mLabelPubTopic = "/label";
    std::string mBoundingBox2DPubTopic = "/bbox_2d";
    std::string mBoundingBox3DPubTopic = "/bbox_3d";
    int mQueueSize = 10;
};
}
}
}
