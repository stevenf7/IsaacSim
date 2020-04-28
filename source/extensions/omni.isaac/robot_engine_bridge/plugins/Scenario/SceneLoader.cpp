// clang-format off
#include <UsdPCH.h>
// clang-format on
#include <vector>
#include <memory>
#include <string>

#include <carb/dictionary/DictionaryUtils.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/UsdContext.h>
#include <carb/profiler/Profile.h>
#include <carb/InterfaceUtils.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

#include "../Core/IsaacComponent.h"
#include "../Utils/IsaacUtilities.h"

#include "SceneLoader.h"

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

void SceneLoader::setAppHandle(isaac_handle_t appHandle)
{
    IsaacComponent::setAppHandle(appHandle);
}

void SceneLoader::updateTimestamp(double timeSeconds, double dt, int64_t timeNano, int64_t timeDifferenceNano)
{
    IsaacComponent::updateTimestamp(timeSeconds, dt, timeNano, timeDifferenceNano);
}

void SceneLoader::tick()
{
    CARB_PROFILE_ZONE(0, "REB SceneLoader Tick");

    IsaacMessage<isaac_message::Json> json;
    auto jsonProto = json.initProto();
    {
        // Receive current command
        std::vector<std::vector<uint8_t>> buffers;
        MessageHeader header;
        if (receive(mInputComponent, mRequestChannelName, header, jsonProto, buffers))
        {
            CARB_LOG_INFO("SceneLoader got message");
            std::string jsonConfig = jsonProto.getSerialized().asString();
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
                LoadSceneAndScenario(sceneName, scenarioIndex, request);
            }
        }
    }
}

void SceneLoader::initializeParams(std::string inputComponent,
                                   std::string requestChannelName,
                                   std::string outputComponent,
                                   std::string replyChannelName)
{

    mInputComponent = inputComponent;
    mRequestChannelName = requestChannelName;
    mOutputComponent = outputComponent;
    mReplyChannelName = replyChannelName;
}

void SceneLoader::SendResponse(int status, std::string request)
{
    IsaacMessage<isaac_message::Json> json;
    auto jsonReplyProto = json.initProto();

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
    std::vector<std::vector<uint8_t>> buffers;
    publish(mOutputComponent, mReplyChannelName, jsonReplyProto, isaac_message::JsonProtoId, buffers);
}

void SceneLoader::LoadSceneAndScenario(std::string sceneName, int scenarioIndex, std::string request)
{
    // handle loading scene request
    CARB_LOG_WARN("Loading scene: %s", sceneName.c_str());
    bool result =
        omni::usd::UsdContext::getContext()->openStage(sceneName.c_str(), [this](bool success, const char* err) {
            if (!success)
            {
                CARB_LOG_ERROR("Open USD error: %s", err);
            }
            else
            {
                CARB_LOG_INFO("Open USD complete");
            }
        });
    SendResponse(1, request);
}
}
}
}
