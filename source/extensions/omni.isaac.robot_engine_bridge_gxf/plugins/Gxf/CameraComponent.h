// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "../Core/GxfComponent.h"
#include "../Core/IsaacMessage.h" // TODO: remove once we get CUDA tensor in GXF
#include "omni/isaac/bridge/ViewportManager.h"
#include "omni/isaac/utils/CameraSensor.h"

#include <carb/Types.h>
#include <carb/profiler/Profile.h>

#include <omni/kit/IViewport.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <robotEngineBridgeSchema/robotEngineCamera.h>

#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge_gxf
{

class CameraComponent : public GxfComponent
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
    void setIntrinsics(
        const nvidia::gxf::Handle<::isaac::geometry::PinholeD>& intrinsics,
        const nvidia::gxf::Handle<::isaac::geometry::CameraDistortionInfo>& distIntrinsics,
        const carb::sensors::SensorInfo& info,
        float focalLength,
        float horizontalAperture,
        float verticalAperture,
        const std::array<double, ::isaac::geometry::CameraDistortionInfo::kMaxNumCoefficients>& distortionCoefficients,
        const pxr::TfToken projectionType);
    void updateViewportSettings();
    omni::syntheticdata::SyntheticData* mSyntheticDataInterface = nullptr;
    utils::ViewportManager* mViewportManager = nullptr;


    pxr::SdfPath mCameraPath;
    pxr::UsdGeomCamera mCameraPrim;
    pxr::GfVec2i mResolution;


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

    bool mSkipFirstFrame = true;
    std::unique_ptr<utils::camera_sensor::CameraSensor> mCameraSensor;
};
}
}
}
