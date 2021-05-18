// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>
#include <carb/sensors/Sensors.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/kit/IViewport.h>
#include <carb/profiler/Profile.h>
#include "plugins/core/ViewportManager.h"
#include <robotEngineBridgeSchema/robotEngineCamera.h>

#include <carb/Types.h>
#include <vector>
#include <string>

#include "../Core/IsaacComponent.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{


class CameraComponent : public IsaacComponent
{
public:
    /**
     * @brief Construct a new Camera Component object
     *
     */
    CameraComponent(utils::ViewportManager* viewportManager);

    /**
     * @brief Destroy the Camera Component object
     *
     */
    ~CameraComponent();

    /**
     * @brief
     *
     */
    virtual void tick();

    /**
     * @brief
     *
     */
    virtual void onStart();

    /**
     * @brief
     *
     */
    virtual void onStop();

    /**
     * @brief
     *
     */
    virtual void onComponentChange();


private:
    /// Publish camera intrinsics with pinhole parameters
    void publishIntrinsics(std::string outputComponent,
                           std::string channelName,
                           const carb::sensors::SensorInfo& info,
                           float focalLength,
                           float horizontalAperture,
                           float verticalAperture);
    void updateViewportSettings();
    carb::Framework* mFramework = nullptr;
    omni::kit::IViewport* mViewportInterface = nullptr;
    omni::syntheticdata::SyntheticData* mSyntheticDataInterface = nullptr;
    carb::sensors::Sensors* mSensorsInterface = nullptr;
    utils::ViewportManager* mViewportManager = nullptr;

    omni::kit::IViewportWindow* mViewportWindow = nullptr;
    pxr::SdfPath mCameraPath;
    pxr::UsdPrim mCameraPrim;
    pxr::GfVec2i mResolution;

    carb::sensors::Sensor* mRgbSensor = nullptr;
    void* mRgbSensorData = nullptr;

    carb::sensors::Sensor* mDepthSensor = nullptr;
    void* mDepthSensorData = nullptr;

    carb::sensors::Sensor* mSegmentationSensor = nullptr;
    void* mSegmentationSensorData = nullptr;

    carb::sensors::Sensor* mSemanticSensor = nullptr;
    void* mSemanticSensorData = nullptr;

    carb::sensors::Sensor* mBoundingBox2DSensor = nullptr;
    void* mBoundingBox2DSensorData = nullptr;

    carb::sensors::Sensor* mBoundingBox3DSensor = nullptr;
    void* mBoundingBox3DSensorData = nullptr;


    /// <summary>
    /// The name of the channel where captured color images will be published
    /// </summary>
    std::string mRgbOutputComponent = "output";
    std::string mRgbChannelName = "color";
    bool mEnableRgb = false;

    /// <summary>
    /// The name of the channel where captured depth images will be published
    /// </summary>
    std::string mDepthOutputComponent = "output";
    std::string mDepthChannelName = "depth";
    bool mEnableDepth = false;


    /// <summary>
    /// The name of the channel where captured segmentation images will be published
    /// </summary>
    std::string mSegmentationOutputComponent = "output";
    std::string mSegmentationChannelName = "segmentation";
    std::map<uint8_t, std::string> mSegmentationIDLabelMap;
    bool mEnableSegmentation = false;

    /// <summary>
    /// The name of the channel where captured 2D bounding box data will be published
    /// </summary>
    std::string mBoundingBox2DOutputComponent = "output";
    std::string mBoundingBox2DChannelName = "bbox";
    std::vector<std::string> mBoundingBox2DClassList;
    bool mEnableBoundingBox2D = false;

    /// <summary>
    /// The name of the channel where captured 3D bounding box data will be published
    /// </summary>
    std::string mBoundingBox3DOutputComponent = "output";
    std::string mBoundingBox3DChannelName = "bbox3d";
    std::vector<std::string> mBoundingBox3DClassList;
    bool mEnableBoundingBox3D = false;

    double mUnitScale;

    std::vector<std::unique_ptr<IsaacBuffer>> mRgbBuffers;
    std::vector<std::unique_ptr<IsaacBuffer>> mDepthBuffers;
    std::vector<std::unique_ptr<IsaacBuffer>> mSegmentationBuffers;
    std::vector<std::unique_ptr<IsaacBuffer>> mSemanticBuffers;
    bool mSkipFirstFrame = true;
};
}
}
}
