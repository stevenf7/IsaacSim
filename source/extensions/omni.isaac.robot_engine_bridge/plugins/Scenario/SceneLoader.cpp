// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on
#include "SceneLoader.h"

#include "../Core/IsaacComponent.h"

#include <carb/InterfaceUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/profiler/Profile.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/utils/Transforms.h>
#include <omni/kit/ViewportWindowUtils.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <memory>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{


SceneLoader::SceneLoader(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr,
                         carb::dictionary::ISerializer* jsonSerializer,
                         carb::dictionary::IDictionary* iDict)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr), mJsonSerializer(jsonSerializer), mIDict(iDict)
{
}

void SceneLoader::tick()
{
    CARB_PROFILE_ZONE(0, "REB SceneLoader Tick");

    {
        IsaacMessage<isaac_message::Json> json;

        // Receive current command
        MessageHeader header;
        if (checkErrorCode(receive(mInputComponent, mRequestChannelName, header, json)))
        {
            auto jsonProto = json.getProto();

            std::string jsonConfig = jsonProto.getSerialized();
            CARB_LOG_INFO("SceneLoader got message %s", jsonConfig.c_str());

            carb::dictionary::Item* jsonBase = mJsonSerializer->createDictionaryFromStringBuffer(jsonConfig.c_str());

            const carb::dictionary::Item* requestDict = mIDict->getItem(jsonBase, "request");
            std::string request = mIDict->getStringBuffer(requestDict);
            if (available)
            {
                const carb::dictionary::Item* sceneDict = mIDict->getItem(jsonBase, "scene");
                std::string sceneName = mIDict->getStringBuffer(sceneDict);
                const carb::dictionary::Item* scenarioDict = mIDict->getItem(jsonBase, "scenario");
                int scenarioIndex = mIDict->getAsInt(scenarioDict);
                available = false;
                loadSceneAndScenario(sceneName, scenarioIndex, request);
            }
        }
    }

    {
        IsaacMessage<isaac_message::Json> json;
        MessageHeader header;
        std::vector<IsaacHostBuffer> buffers;
        if (checkErrorCode(receive(mInputComponent, mCameraRequestChannelName, header, json, buffers)))
        {
            auto jsonProto = json.getProto();

            std::string jsonConfig = jsonProto.getSerialized();

            // CARB_LOG_ERROR("Camera got message [%s], [%d]", jsonConfig.c_str(), buffers.size());
            carb::dictionary::Item* jsonBase = mJsonSerializer->createDictionaryFromStringBuffer(jsonConfig.c_str());
            // currently only support camera switch request
            const carb::dictionary::Item* requestDict = mIDict->getItem(jsonBase, "camera_name");
            if (requestDict)
            {
                std::string cameraPath = mIDict->getStringBuffer(requestDict);

                if (mStage->GetPrimAtPath(pxr::SdfPath(cameraPath)))
                {
                    kit::getDefaultViewportWindow()->setActiveCamera(cameraPath.c_str());
                }
                else
                {
                    CARB_LOG_ERROR("Camera %s not found", cameraPath.c_str());
                }
            }
            else
            {
                CARB_LOG_ERROR("Camera switch json not valid");
            }
        }
    }
}

void SceneLoader::initializeParams(std::string inputComponent,
                                   std::string requestChannelName,
                                   std::string cameraRequestChannelName,
                                   std::string outputComponent,
                                   std::string replyChannelName)
{

    mInputComponent = inputComponent;
    mRequestChannelName = requestChannelName;
    mCameraRequestChannelName = cameraRequestChannelName;
    mOutputComponent = outputComponent;
    mReplyChannelName = replyChannelName;
}

void SceneLoader::sendResponse(int status, std::string request)
{
    IsaacMessage<isaac_message::Json> jsonMessage;
    auto jsonReplyProto = jsonMessage.initProto();

    auto dictionaryRoot = mIDict->createItem(nullptr, "<root>", carb::dictionary::ItemType::eDictionary);
    auto statusItem = mIDict->createItem(dictionaryRoot, "status", carb::dictionary::ItemType::eDictionary);
    mIDict->setInt(statusItem, status);
    auto requestItem = mIDict->createItem(dictionaryRoot, "request", carb::dictionary::ItemType::eDictionary);
    mIDict->setString(requestItem, request.c_str());
    const char* serializedMessage =
        mJsonSerializer->createStringBufferFromDictionary(dictionaryRoot, carb::dictionary::kSerializerOptionMakePretty);
    std::string replyMessage(serializedMessage);
    mJsonSerializer->destroyStringBuffer(serializedMessage);
    mIDict->destroyItem(dictionaryRoot);

    jsonReplyProto.setSerialized(replyMessage);
    std::vector<std::unique_ptr<IsaacBuffer>> buffers;

    publish(mOutputComponent, mReplyChannelName, jsonMessage, buffers);
}

bool endsWith(std::string const& fullString, std::string const& ending)
{
    if (fullString.length() >= ending.length())
    {
        return (0 == fullString.compare(fullString.length() - ending.length(), ending.length(), ending));
    }
    else
    {
        return false;
    }
}

void SceneLoader::loadSceneAndScenario(std::string sceneName, int scenarioIndex, std::string request)
{
    // handle loading scene request
    CARB_LOG_INFO("Loading scene: %s", sceneName.c_str());

    if (endsWith(sceneName, ".usd") || endsWith(sceneName, ".usda"))
    {
        omni::usd::UsdContext::getContext()->openStage(sceneName.c_str(),
                                                       [this](bool success, const char* err)
                                                       {
                                                           if (!success)
                                                           {
                                                               CARB_LOG_ERROR("Open USD error: %s", err);
                                                           }
                                                           else
                                                           {
                                                               CARB_LOG_INFO("Open USD complete");
                                                           }
                                                       });
        sendResponse(1, request);
    }
    else
    {
        CARB_LOG_WARN("Scene %s is not a valid usd file", sceneName.c_str());
        sendResponse(1, request);
    }
}
}
}
}
