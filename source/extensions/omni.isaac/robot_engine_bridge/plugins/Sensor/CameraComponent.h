#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on
#include <omni/kit/IEditor.h>
#include <omni/usd/UsdUtils.h>
#include <carb/syntheticdata/SyntheticData.h>
#include <carb/sensors/Sensors.h>
#include <carb/profiler/Profile.h>

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
    CameraComponent();

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
    virtual void onComponentChange();


private:
    carb::Framework* mFramework = nullptr;
    omni::kit::IEditor* mEditorInterface = nullptr;
    carb::syntheticdata::SyntheticData* mSyntheticDataInterface = nullptr;
    carb::sensors::Sensors* mSensorsInterface = nullptr;

    carb::sensors::Sensor* mRgbSensor = nullptr;
    void* mRgbSensorData = nullptr;

    carb::sensors::Sensor* mDepthSensor = nullptr;
    void* mDepthSensorData = nullptr;

    carb::sensors::Sensor* mSegmentationSensor = nullptr;
    void* mSegmentationSensorData = nullptr;


    /// <summary>
    /// The name of the channel where captured color images will be published
    /// </summary>
    std::string mOutputComponent = "output";
    std::string mChannelName = "color";
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

    double mUnitScale;
};
}
}
}
