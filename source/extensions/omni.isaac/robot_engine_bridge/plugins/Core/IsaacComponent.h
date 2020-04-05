#pragma once

#include "IsaacCApi.h"
#include "IsaacMessage.h"
#include "plugins/core/Component.h"

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
class IsaacComponent : public utils::Component
{
public:
    /**
     * @brief Construct a new Isaac Component
     */
    IsaacComponent();
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
                            const pxr::UsdPrim& prim,
                            pxr::UsdStageRefPtr stage);
    /**
     * @brief Function that runs after start is pressed
     *
     */
    virtual void onStart();

    /**
     * @brief Called every frame
     *
     */
    virtual void tick(){};

    /**
     * @brief Called every time the Prim is changed
     *
     */
    virtual void onComponentChange();

    /**
     * @brief Update timestamps for component
     *
     * @param timeSeconds
     * @param dt
     * @param timeNano
     * @param timeDifferenceNano
     */
    virtual void updateTimestamp(double timeSeconds, double dt, int64_t timeNano, int64_t timeDifferenceNano);


    /**
     * @brief Returns true if the error code is set to success.
     *
     * @param code
     * @return true
     * @return false
     */
    bool checkErrorCode(const isaac_error_t& code);

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
                 const std::vector<std::vector<uint8_t>>& buffers)
    {
        kj::String json_message = isaac_message::gJsonCodec.encode(data);

        return checkErrorCode(publishJSONMessage(
            mNodeName, component, channel, mTimeNanoSeconds + mTimeDifferenceNanoSeconds, json_message, protoId, buffers));
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
    bool publish(const std::string& component, const std::string& channel, const std::string& data);

    /**
     * @brief Publishes a camera capture on a channel
     * Camera capture pipeline have a one frame delay, so need to give acquire time explicitly
     * @param component
     * @param channel
     * @param data
     * @param acqtime
     * @return true
     * @return false
     */
    bool publish(const std::string& component,
                 const std::string& channel,
                 const isaac_message::CameraCapture& data,
                 int64_t acqtime);

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
        std::vector<std::vector<uint8_t>> buffers;
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
                 std::vector<std::vector<uint8_t>>& buffers)
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
    bool receive(const std::string& component, const std::string& channel, MessageHeader& header, std::string& data);

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
                                     const std::vector<std::vector<uint8_t>>& buffers);

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
                                              std::vector<std::vector<uint8_t>>& buffers);

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
}
}
}
