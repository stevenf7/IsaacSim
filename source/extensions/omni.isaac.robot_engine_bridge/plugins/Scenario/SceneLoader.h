// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../Core/IsaacComponent.h"

#include <carb/dictionary/DictionaryUtils.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <robotEngineBridgeSchema/robotEngineSceneLoader.h>

#include <memory>
#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

/**
 * @brief
 *
 */
class SceneLoader : public IsaacComponent
{
public:
    /**
     * @brief Construct a new Scenario From Message object
     *
     * @param appHandle
     * @param prim
     * @param stage
     * @param dynamicControlPtr
     */
    SceneLoader(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr,
                carb::dictionary::ISerializer* jsonSerializer,
                carb::dictionary::IDictionary* iDict);
    /**
     * @brief
     *
     */
    virtual void tick();
    /**
     * @brief Initialize SDK parameters
     *
     * @param inputComponent
     * @param requestChannelName
     * @param cameraRequestChannelName,
     * @param outputComponent
     * @param replyChannelName
     */
    void initializeParams(std::string inputComponent,
                          std::string requestChannelName,
                          std::string cameraRequestChannelName,
                          std::string outputComponent,
                          std::string replyChannelName);


private:
    /**
     * @brief Sends reply to robot engine
     *
     * @param status
     * @param request
     */
    void sendResponse(int status, std::string request);
    /**
     * @brief Load scene and scenario from robot engine message
     *
     * @param sceneName
     * @param scenarioIndex
     * @param request
     */
    void loadSceneAndScenario(std::string sceneName, int scenarioIndex, std::string request);

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    carb::dictionary::ISerializer* mJsonSerializer = nullptr;
    carb::dictionary::IDictionary* mIDict = nullptr;


    // The name of the channel for receiving scenario commands
    std::string mInputComponent = "input";
    std::string mRequestChannelName = "scenario_control";
    std::string mCameraRequestChannelName = "camera_switch";

    // The name of the channel for replying to scenario commands
    std::string mOutputComponent = "output";
    std::string mReplyChannelName = "scenario_reply";

    // true is not currently loading any scene and is available to process new request
    bool available = true;
};
}
}
}
