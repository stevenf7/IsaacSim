#pragma once

#include "IsaacCApi.h"
#include "IsaacMessage.h"
#include "plugins/core/Component.h"
#include "plugins/core/UsdUtilities.h"

#include <carb/profiler/Profile.h>

#include <RobotEngineBridgeSchema/robotEngineBridgeComponent.h>
#include <engine/alice/c_api/isaac_c_api_error.h>

#include <string>
#include <vector>
namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

/**
 * @brief Base class which exchanges data with an Isaac SDK application.
 * This class provides helper functions to facilitate the data exchange.
 */
template <typename PrimType>
class IsaacComponentBase : public utils::ComponentBase<PrimType>
{
public:
    /**
     * @brief Initialize various pointers and handles in the component
     * Must be called after creation, can be overridden to initialize subcomponents
     *
     * @param isaacCApiPtr
     * @param appHandle
     * @param prim
     * @param stage
     */

    virtual void initialize(IsaacCApi* isaacCApiPtr,
                            const isaac_handle_t& appHandle,
                            const PrimType& prim,
                            pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<PrimType>::initialize(prim, stage);

        mIsaacCApiPtr = isaacCApiPtr;
        mAppHandle = appHandle;
    }
    /**
     * @brief Function that runs after start is pressed
     *
     */
    virtual void onStart()
    {
    }

    /**
     * @brief Called every frame
     *
     */
    virtual void tick(){};

    /**
     * @brief Publish any Messages
     *
     */
    virtual void publishAllMessages(){};

    /**
     * @brief Called every time the Prim is changed
     *
     */
    virtual void onComponentChange()
    {
        isaac::utils::safeGetAttribute(this->mPrim.GetNodeNameAttr(), mNodeName);
        isaac::utils::safeGetAttribute(this->mPrim.GetEnabledAttr(), this->mEnabled);
    }

    /**
     * @brief Update timestamps for component
     *
     * @param timeSeconds
     * @param dt
     * @param timeNano
     * @param timeDifferenceNano
     */
    virtual void updateTimestamp(double timeSeconds, double dt, int64_t timeNano, int64_t timeDifferenceNano)
    {
        this->mTimeNanoSeconds = timeNano;
        mTimeDifferenceNanoSeconds = timeDifferenceNano;
        this->mTimeSeconds = timeSeconds;
        this->mTimeDelta = dt;
    }


    /**
     * @brief Returns true if the error code is set to success.
     *
     * @param code
     * @return true
     * @return false
     */
    bool checkErrorCode(const isaac_error_t& code)
    {
        return code == isaac_error_t::isaac_error_success;
    }

    /**
     * @brief Publishes serialized JSON string. Used for messages whose json data can be cached.
     *
     * @tparam T
     * @param component
     * @param channel
     * @param data
     * @param protoId
     * @param buffers
     * @return true
     * @return false
     */
    template <class T>
    bool publish(const std::string& component,
                 const std::string& channel,
                 const T& data,
                 uint64_t protoId,
                 const std::vector<std::unique_ptr<IsaacBuffer>>& buffers)
    {
        kj::String json_message = isaac_message::gJsonCodec.encode(data);

        return checkErrorCode(publishJSONMessage(mNodeName, component, channel,
                                                 this->mTimeNanoSeconds + mTimeDifferenceNanoSeconds, json_message,
                                                 protoId, buffers));
    }


    /**
     * @brief Publishes a JSON object on specified component/channel as JsonProto message.
     *
     * @param component
     * @param channel
     * @param data
     * @return true
     * @return false
     */
    bool publish(const std::string& component, const std::string& channel, const std::string& data)
    {
        std::vector<std::unique_ptr<IsaacBuffer>> buffers;

        return checkErrorCode(publishJSONMessage(mNodeName, component, channel,
                                                 this->mTimeNanoSeconds + mTimeDifferenceNanoSeconds,
                                                 kj::StringPtr(data), isaac_message::JsonProtoId, buffers));
    }

    /**
     * @brief General receive function without buffers
     *
     * @tparam T
     * @param component
     * @param channel
     * @param header
     * @param data
     * @return true
     * @return false
     */
    template <class T>
    bool receive(const std::string& component, const std::string& channel, MessageHeader& header, T& data)
    {
        std::vector<IsaacHostBuffer> buffers;
        return receive(component, channel, header, data, buffers);
    }

    /**
     * @brief General receive function with buffers
     *
     * @tparam T
     * @param component
     * @param channel
     * @param header
     * @param data
     * @param buffers
     * @return true
     * @return false
     */
    template <class T>
    bool receive(const std::string component,
                 const std::string channel,
                 MessageHeader& header,
                 T& data,
                 std::vector<IsaacHostBuffer>& buffers)
    {
        // printf("receive %s %s %s\n", mNodeName.c_str(), component.c_str(), channel.c_str());
        kj::String json_message;
        mError = receiveLatestNewJsonMessage(mAppHandle, mNodeName, component, channel, header, json_message, buffers);
        if (!checkErrorCode(mError))
        {
            return false;
        }
        header.acqtime -= mTimeDifferenceNanoSeconds;
        isaac_message::gJsonCodec.decode(json_message, data);
        return true;
    }

    /**
     * @brief Receives a JSON object
     *
     * @param component
     * @param channel
     * @param header
     * @param data
     * @return true
     * @return false
     */
    bool receive(const std::string& component, const std::string& channel, MessageHeader& header, std::string& data)
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

    /**
     * @brief Publish a JSON object
     *
     * @param node_name
     * @param component_name
     * @param channel_name
     * @param acqtime
     * @param message_json
     * @param protoId
     * @param buffers
     * @return isaac_error_t
     */
    isaac_error_t publishJSONMessage(const std::string& node_name,
                                     const std::string& component_name,
                                     const std::string& channel_name,
                                     int64_t acqtime,
                                     const kj::StringPtr& message_json,
                                     uint64_t protoId,
                                     const std::vector<std::unique_ptr<IsaacBuffer>>& buffers)
    {
        CARB_PROFILE_ZONE(0, "publishJSONMessage");

        isaac_uuid_t uuid;
        mError = (mIsaacCApiPtr->isaac_create_message)(mAppHandle, &uuid);

        isaac_const_json_t json = { message_json.cStr(), message_json.size() };
        (mIsaacCApiPtr->isaac_write_message_json)(mAppHandle, &uuid, &json);

        int64_t buffer_index = 0;

        for (size_t i = 0; i < buffers.size(); ++i)
        {
            if (buffers[i]->size() > 0)
            {
                isaac_buffer_t isaac_buffer = { buffers[i]->data(), buffers[i]->size(), buffers[i]->type() };
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
            (mIsaacCApiPtr->isaac_destroy_message)(mAppHandle, &uuid);
            return mError;
        }

        return mError;
        // TODO: Make into a class with delete function to cleanup bad messages
    }

    /**
     * @brief Get the latest JSON message
     *
     * @param appHandle
     * @param node_name
     * @param component_name
     * @param channel_name
     * @param header
     * @param message_json
     * @param buffers
     * @return isaac_error_t
     */
    isaac_error_t receiveLatestNewJsonMessage(isaac_handle_t appHandle,
                                              const std::string& node_name,
                                              const std::string& component_name,
                                              const std::string& channel_name,
                                              MessageHeader& header,
                                              kj::String& message_json,
                                              std::vector<IsaacHostBuffer>& buffers)
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
        result = (mIsaacCApiPtr->isaac_message_get_buffers)(
            appHandle, &uuid, nullptr, &size, isaac_memory_t::isaac_memory_host);
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

    /**
     * @brief Set the App Handle
     *
     * @param appHandle
     */
    virtual void setAppHandle(isaac_handle_t appHandle)
    {
        mAppHandle = appHandle;
    }

protected:
    IsaacCApi* mIsaacCApiPtr = nullptr;
    isaac_handle_t mAppHandle = 0;
    std::string mNodeName = "interface";
    isaac_error_t mError = isaac_error_t::isaac_error_success;
    int64_t mTimeDifferenceNanoSeconds = 0;
};


typedef IsaacComponentBase<pxr::RobotEngineBridgeSchemaRobotEngineBridgeComponent> IsaacComponent;


}
}
}
