// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../Scenario/SceneLoader.h"
#include "IsaacComponent.h"
#include "omni/isaac/bridge/BridgeApplication.h"
#include "omni/isaac/bridge/ViewportManager.h"

#include <carb/dictionary/DictionaryUtils.h>
#include <carb/logging/Log.h>
#include <carb/tasking/ITasking.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/robot_engine_bridge/IsaacCApi.h>
#include <omni/kit/IViewport.h>
#include <packages/engine_c_api/isaac_c_api.h>
#include <robotEngineBridgeSchema/robotEngineBridgeComponent.h>

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>


namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
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
    IsaacApplication(IsaacCApi* isaacCApiPtr,
                     omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr,
                     carb::dictionary::ISerializer* jsonSerializer,
                     carb::dictionary::IDictionary* iDict);

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

    /**
     * @brief Create the application from JSON
     *
     * @param asset_path
     * @param app_file
     * @param module_paths
     * @param json_files
     * @return isaac_error_t
     */
    isaac_error_t create(std::string asset_path,
                         std::string app_file,
                         std::vector<const char*> module_paths,
                         std::vector<const char*> json_files);
    /**
     * @brief Start the application
     *
     * @return isaac_error_t
     */
    isaac_error_t start();
    /**
     * @brief Stop the application
     *
     * @return isaac_error_t
     */
    isaac_error_t stop();
    /**
     * @brief Destroy the application
     *
     * @return isaac_error_t
     */
    isaac_error_t destroy();
    /**
     * @brief Tick the application and all components
     *
     * @param dt
     */
    void tick(double dt);
    /**
     * @brief Call stop on all components to do any cleanup
     *
     */
    void onStop();
    /**
     * @brief Create a supported component in this application
     *
     * @param prim
     */
    void onComponentAdd(const pxr::UsdPrim& prim);
    /**
     * @brief Get the handle to the application
     *
     * @return isaac_handle_t
     */
    isaac_handle_t getHandle();
    /**
     * @brief Get the last error from the application
     *
     * @return std::string
     */
    std::string getLastError();
    /**
     * @brief Set the USD stage for this application
     *
     * @param stage
     */
    void setStage(pxr::UsdStageWeakPtr stage);
    /**
     * @brief initialize stage loader parameters
     *
     * @param inputComponent
     * @param requestChannelName
     * @param outputComponent
     * @param replyChannelName
     */
    void initializeStageLoader(const std::string& inputComponent,
                               const std::string& requestChannelName,
                               const std::string& cameraRequestChannelName,
                               const std::string& outputComponent,
                               const std::string& replyChannelName);

    /**
     * @brief
     *
     * @param prim
     * @return true
     * @return false
     */
    bool tickComponent(const pxr::UsdPrim& prim);

    /**
     * @brief
     *
     * @param node
     * @param component
     * @param channel
     * @param typeID
     * @param jsonString
     */
    bool publishJsonMessage(
        std::string node, std::string component, std::string channel, uint64_t typeID, std::string jsonString);

    /**
     * @brief Get the current simulation time in nanoseconds
     *
     * @return int64_t
     */
    int64_t getSimTimeNano()
    {
        return mTimeNanoSeconds;
    }
    /**
     * @brief Get the current SDK app offset in nanoseconds
     *
     * @return int64_t
     */
    int64_t getAppOffsetNano()
    {

        mError =
            (mIsaacCApiPtr->isaac_get_external_time_difference)(mAppHandle, mTimeSeconds, &mTimeDifferenceNanoSeconds);
        if (mError != isaac_error_t::isaac_error_success)
        {
            return 0;
        }

        return mTimeDifferenceNanoSeconds;
    }
    int64_t getAppHandle()
    {
        return mAppHandle;
    }
    IsaacCApi* mIsaacCApiPtr = nullptr;

private:
    isaac_handle_t mAppHandle = 0;
    isaac_error_t mError = isaac_error_t::isaac_error_success;
    std::vector<std::string> mJsonFiles;
    std::string mAppFilename;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr;
    carb::dictionary::ISerializer* mJsonSerializer;
    carb::dictionary::IDictionary* mIDict;
    std::unique_ptr<SceneLoader> mSceneLoaderComponent = nullptr;
    carb::tasking::ITasking* mTasking = nullptr;
    carb::tasking::Counter* mTaskCounter = nullptr;
    carb::settings::ISettings* mSettings = nullptr;

    omni::kit::IViewport* mViewportInterface = nullptr;
    std::unique_ptr<utils::ViewportManager> mViewportManager = nullptr;

    int64_t mTimeDifferenceNanoSeconds = 0;
    bool mRunning = false;
};
}
}
}
