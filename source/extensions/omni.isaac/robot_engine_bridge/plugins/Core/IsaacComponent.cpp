// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "IsaacComponent.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

IsaacComponent::IsaacComponent()
{
}

void IsaacComponent::initialize(IsaacCApi* isaacCApiPtr,
                                const isaac_handle_t& appHandle,
                                const pxr::UsdPrim& prim,
                                pxr::UsdStageRefPtr stage)
{
    utils::Component::initialize(prim, stage);

    mIsaacCApiPtr = isaacCApiPtr;
    mAppHandle = appHandle;
}

void IsaacComponent::onStart()
{
}

void IsaacComponent::updateTimestamp(double timeSeconds, double dt, int64_t timeNano, int64_t timeDifferenceNano)
{
    mTimeNanoSeconds = timeNano;
    mTimeDifferenceNanoSeconds = timeDifferenceNano;
    mTimeSeconds = timeSeconds;
    mTimeDelta = dt;
}


void IsaacComponent::onComponentChange()
{
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("nodeName")))
    {
        attr.Get(&mNodeName);
    }
}

bool IsaacComponent::checkErrorCode(const isaac_error_t& code)
{
    return code == isaac_error_t::isaac_error_success;
}

bool IsaacComponent::publish(const std::string& component, const std::string& channel, const std::string& data)
{
    std::vector<std::vector<uint8_t>> buffers;

    return checkErrorCode(publishJSONMessage(mNodeName, component, channel, mTimeNanoSeconds + mTimeDifferenceNanoSeconds,
                                             kj::StringPtr(data), isaac_message::JsonProtoId, buffers));
}

bool IsaacComponent::publish(const std::string& component,
                             const std::string& channel,
                             const isaac_message::CameraCapture& data,
                             int64_t acqtime)
{
    return false;
    // kj::String json_message = isaac_message::gJsonCodec.encode(data);


    // return checkErrorCode(publishJSONMessage(mNodeName, component, channel,
    //                                          mTimeNanoSeconds + mTimeDifferenceNanoSeconds, json_message,
    //                                          isaac_message::ColorCameraProtoId, data.image));
}


bool IsaacComponent::receive(const std::string& component,
                             const std::string& channel,
                             MessageHeader& header,
                             std::string& data)
{
    data = nullptr;
    IsaacMessage<isaac_message::Json> json_data;
    auto json_proto = json_data.initProto();
    if (!receive(component, channel, header, json_proto))
    {
        return false;
    }
    header.acqtime -= mTimeDifferenceNanoSeconds;
    data = json_proto.getSerialized().asString();
    return true;
}


isaac_error_t IsaacComponent::publishJSONMessage(const std::string& node_name,
                                                 const std::string& component_name,
                                                 const std::string& channel_name,
                                                 int64_t acqtime,
                                                 const kj::StringPtr& message_json,
                                                 uint64_t protoId,
                                                 const std::vector<std::vector<uint8_t>>& buffers)
{

    isaac_uuid_t uuid;
    mError = (mIsaacCApiPtr->isaac_create_message)(mAppHandle, &uuid);

    isaac_const_json_t json = { message_json.cStr(), message_json.size() };
    (mIsaacCApiPtr->isaac_write_message_json)(mAppHandle, &uuid, &json);

    int64_t buffer_index = 0;

    for (size_t i = 0; i < buffers.size(); ++i)
    {
        if (buffers[i].size() > 0)
        {
            isaac_buffer_t isaac_buffer = { buffers[i].data(), buffers[i].size(), isaac_memory_t::isaac_memory_host };
            mError = (mIsaacCApiPtr->isaac_message_append_buffer)(mAppHandle, &uuid, &isaac_buffer, &buffer_index);
            if (mError != isaac_error_t::isaac_error_success)
            {
                return mError;
            }
        }
        else
        {
            // Append null buffer
            mError = (mIsaacCApiPtr->isaac_message_append_buffer)(mAppHandle, &uuid, nullptr, &buffer_index);
        }
    }
    mError = (mIsaacCApiPtr->isaac_set_message_acqtime)(mAppHandle, &uuid, acqtime);
    if (mError != isaac_error_t::isaac_error_success)
    {
        return mError;
    }
    mError = (mIsaacCApiPtr->isaac_set_message_proto_id)(mAppHandle, &uuid, protoId);
    if (mError != isaac_error_t::isaac_error_success)
    {
        return mError;
    }
    mError = (mIsaacCApiPtr->isaac_set_message_auto_convert)(
        mAppHandle, &uuid, isaac_message_convert_t::isaac_message_type_proto);
    if (mError != isaac_error_t::isaac_error_success)
    {
        return mError;
    }
    mError = (mIsaacCApiPtr->isaac_publish_message)(
        mAppHandle, node_name.c_str(), component_name.c_str(), channel_name.c_str(), &uuid);
    if (mError != isaac_error_t::isaac_error_success)
    {
        return mError;
    }

    return mError;
    // TODO: Make into a class with delete function to cleanup bad messages
}


isaac_error_t IsaacComponent::receiveLatestNewJsonMessage(isaac_handle_t appHandle,
                                                          const std::string& node_name,
                                                          const std::string& component_name,
                                                          const std::string& channel_name,
                                                          MessageHeader& header,
                                                          kj::String& message_json,
                                                          std::vector<std::vector<uint8_t>>& buffers)
{
    isaac_error_t result = isaac_error_success;
    message_json = kj::String();

    isaac_uuid_t uuid = { 0, 0 };
    header = {
        uuid,
        0,
        0,
    };


    // Grabs UUID
    result = (mIsaacCApiPtr->isaac_receive_latest_new_message)(
        appHandle, node_name.c_str(), component_name.c_str(), channel_name.c_str(), &uuid);

    if (result != isaac_error_t::isaac_error_success)
    {
        return result;
    }
    // Grabs message data in JSON
    isaac_const_json_t isaac_json = { nullptr, 0 };

    result = (mIsaacCApiPtr->isaac_get_message_json)(appHandle, &uuid, &isaac_json);
    if (result != isaac_error_t::isaac_error_success)
        return result;
    if (isaac_json.size <= 0)
        return isaac_error_invalid_message;
    message_json = kj::heapString(isaac_json.data, isaac_json.size);

    // Grabs message buffers meta data
    int64_t size = 0;
    result =
        (mIsaacCApiPtr->isaac_message_get_buffers)(appHandle, &uuid, nullptr, &size, isaac_memory_t::isaac_memory_host);
    if (size < 0)
    {
        return isaac_error_invalid_message;
    }
    std::vector<isaac_buffer_t> isaac_buffers(size);
    result = (mIsaacCApiPtr->isaac_message_get_buffers)(
        appHandle, &uuid, isaac_buffers.data(), &size, isaac_memory_t::isaac_memory_host);
    if (!checkErrorCode(result))
    {
        return result;
    }
    if (size < 0)
    {
        return isaac_error_invalid_message;
    }
    buffers.resize(size);

    // Copies buffers to managed memory one by one
    for (long i = 0; i < size; ++i)
    {
        buffers[i].resize(isaac_buffers[i].size);
        std::memcpy(buffers[i].data(), isaac_buffers[i].pointer, isaac_buffers[i].size * sizeof(unsigned char));
    }
    // Grabs acquisition time and publish time (in Isaac application clock)

    result = (mIsaacCApiPtr->isaac_get_message_acqtime)(appHandle, &uuid, &header.acqtime);
    if (!checkErrorCode(result))
    {
        return result;
    }

    result = (mIsaacCApiPtr->isaac_get_message_pubtime)(appHandle, &uuid, &header.pubtime);
    if (!checkErrorCode(result))
    {
        return result;
    }

    // Releases received Isaac message
    if (uuid.upper != 0 || uuid.lower != 0)
    {
        (mIsaacCApiPtr->isaac_release_message)(appHandle, &uuid);
    }

    return result;
}
}
}
}
