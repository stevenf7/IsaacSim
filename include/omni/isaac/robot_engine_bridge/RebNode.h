// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../utils/BaseResetNode.h"
#include "IsaacCApi.h"
#include "IsaacMessage.h"
#include "RobotEngineBridge.h"

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>

#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/usd/UsdContext.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{


/**
 * @brief Base class for all ROS1 bridge nodes. It handles the lifetime of the internal ROS node handle automatically.
 *
 */
class RebNode : public BaseResetNode
{

public:
    /**
     * @brief Construct a new Ros Node object
     *
     */
    RebNode()
    {
        mRobotEngineBridge =
            carb::getFramework()->acquireInterface<omni::isaac::robot_engine_bridge::RobotEngineBridge>();
    }
    /**
     * @brief Destroy the Ros Node object
     *
     */
    ~RebNode()
    {
        reset();
    }

    /**
     * @brief Reset the node handle
     * Should be called by all derived classes after they reset any publishers/subscribers attached to the node
     *
     */
    virtual void reset()
    {
    }

    template <class T>
    isaac_error_t publish(const std::string& component,
                          const std::string& channel,
                          T& data,
                          const std::vector<std::unique_ptr<IsaacBuffer>>& buffers,
                          bool publishBinary = true)
    {
        CARB_PROFILE_ZONE(0, "publishMessage");

        isaac_uuid_t uuid;
        mError = (mIsaacCApiPtr->isaac_create_message)(mAppHandle, &uuid);


        if (publishBinary)
        {

            data.capnpSegmentsToFlatArray();
            // data.printJson();

            (mIsaacCApiPtr->isaac_set_message_proto_segments(
                mAppHandle, &uuid, reinterpret_cast<const void**>(data.segment_ptrs.data()),
                reinterpret_cast<int64_t*>(data.segment_sizes.data()), data.segment_ptrs.size()));
        }
        else
        {
            kj::String message_json = isaac_message::gJsonCodec.encode(data.getProto());
            isaac_const_json_t json = { message_json.cStr(), message_json.size() };
            (mIsaacCApiPtr->isaac_write_message_json)(mAppHandle, &uuid, &json);
            // CARB_LOG_ERROR("%s", message_json.cStr());
        }

        int64_t buffer_index = 0;

        for (size_t i = 0; i < buffers.size(); ++i)
        {
            if (buffers[i]->size() > 0)
            {
                isaac_buffer_t isaac_buffer = { buffers[i]->data(), buffers[i]->size(), buffers[i]->type() };
                mError = (mIsaacCApiPtr->isaac_message_append_buffer)(mAppHandle, &uuid, &isaac_buffer, &buffer_index);
                if (!checkErrorCode(mError))
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


        mError = (mIsaacCApiPtr->isaac_set_message_acqtime)(
            mAppHandle, &uuid, this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds + mTimeDifferenceNanoSeconds);
        if (!checkErrorCode(mError))
        {
            return mError;
        }
        mError = (mIsaacCApiPtr->isaac_set_message_proto_id)(mAppHandle, &uuid, data.protoId());
        if (!checkErrorCode(mError))
        {
            return mError;
        }
        mError = (mIsaacCApiPtr->isaac_set_message_auto_convert)(
            mAppHandle, &uuid, isaac_message_convert_t::isaac_message_type_proto);
        if (!checkErrorCode(mError))
        {
            return mError;
        }


        mError = (mIsaacCApiPtr->isaac_publish_message)(
            mAppHandle, mNodeName.c_str(), component.c_str(), channel.c_str(), &uuid);
        if (!checkErrorCode(mError))
        {
            (mIsaacCApiPtr->isaac_destroy_message)(mAppHandle, &uuid);
            return mError;
        }

        return mError;
    }

    template <class T>
    isaac_error_t receive(const std::string& component, const std::string& channel, MessageHeader& header, T& data)
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
    isaac_error_t receive(const std::string component,
                          const std::string channel,
                          MessageHeader& header,
                          T& data,
                          std::vector<IsaacHostBuffer>& buffers)
    {
        CARB_PROFILE_ZONE(0, "receive");
        // printf("receive %s %s %s\n", mNodeName.c_str(), component.c_str(), channel.c_str());


        isaac_uuid_t uuid = { 0, 0 };
        header = {
            uuid,
            0,
            0,
        };


        // Grabs UUID
        mError = (mIsaacCApiPtr->isaac_receive_latest_new_message)(
            mAppHandle, mNodeName.c_str(), component.c_str(), channel.c_str(), &uuid);

        if (!checkErrorCode(mError))
        {
            return mError;
        }
        // Check to make sure that the proto received matches that requested
        int64_t protoID = 0;
        mError = (mIsaacCApiPtr->isaac_get_message_proto_id)(mAppHandle, &uuid, &protoID);

        if (!checkErrorCode(mError))
        {
            return mError;
        }
        if (data.checkType(protoID) == false)
        {
            return isaac_error_invalid_message;
        }
        {
#if 0
            CARB_PROFILE_ZONE(0, "receive decode");
            kj::String message_json = kj::String();

            // Grabs message data in JSON
            isaac_const_json_t isaac_json = { nullptr, 0 };

            mError = (mIsaacCApiPtr->isaac_get_message_json)(mAppHandle, &uuid, &isaac_json);
            if (!checkErrorCode(mError))
            {
                return mError;
            }
            if (isaac_json.size <= 0)
            {
                return isaac_error_invalid_message;
            }
            message_json = kj::heapString(isaac_json.data, isaac_json.size);

            isaac_message::gJsonCodec.decode(message_json, data.initProto());
            // CARB_LOG_ERROR("Message json: %s", message_json.cStr());
#else
            uint64_t num_segments = 0;
            mError =
                (mIsaacCApiPtr->isaac_read_message_proto_segments)(mAppHandle, &uuid, nullptr, nullptr, &num_segments);
            if (!checkErrorCode(mError))
            {
                return mError;
            }
            if (num_segments)
            {
                data.segment_ptrs.resize(num_segments);
                data.segment_sizes.resize(num_segments);


                mError = (mIsaacCApiPtr->isaac_read_message_proto_segments)(
                    mAppHandle, &uuid, reinterpret_cast<const void**>(data.segment_ptrs.data()),
                    data.segment_sizes.data(), &num_segments);
                if (!checkErrorCode(mError))
                {
                    return mError;
                }
                data.flatArrayToCapnpBuffer();
                // data.printJson();
            }
            // else
            // {
            //     return isaac_error_invalid_message;
            // }
#endif
        }
        // Grabs message buffers meta data
        int64_t size = 0;
        mError = (mIsaacCApiPtr->isaac_message_get_buffers)(
            mAppHandle, &uuid, nullptr, &size, isaac_memory_t::isaac_memory_host);
        if (!checkErrorCode(mError))
        {
            return mError;
        }
        if (size < 0)
        {
            return isaac_error_invalid_message;
        }
        std::vector<isaac_buffer_t> isaac_buffers(size);
        mError = (mIsaacCApiPtr->isaac_message_get_buffers)(
            mAppHandle, &uuid, isaac_buffers.data(), &size, isaac_memory_t::isaac_memory_host);
        if (!checkErrorCode(mError))
        {
            return mError;
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

        mError = (mIsaacCApiPtr->isaac_get_message_acqtime)(mAppHandle, &uuid, &header.acqtime);
        header.acqtime -= mTimeDifferenceNanoSeconds;
        if (!checkErrorCode(mError))
        {
            return mError;
        }

        mError = (mIsaacCApiPtr->isaac_get_message_pubtime)(mAppHandle, &uuid, &header.pubtime);
        if (!checkErrorCode(mError))
        {
            return mError;
        }

        // Releases received Isaac message
        if (uuid.upper != 0 || uuid.lower != 0)
        {
            mError = (mIsaacCApiPtr->isaac_release_message)(mAppHandle, &uuid);
            if (!checkErrorCode(mError))
            {
                return mError;
            }
        }
        return mError;
    }

    /**
     * @brief Initialize handles
     *
     * @return true if successful
     * @return false if app or capi were not accessible
     */
    virtual bool initializeHandles()
    {
        mAppHandle = mRobotEngineBridge->getAppHandle();
        mIsaacCApiPtr = (IsaacCApi*)mRobotEngineBridge->getCApiHandle();
        if (!mAppHandle || !mIsaacCApiPtr)
        {
            return false;
        }

        return true;
    }

    virtual void updateTimestamp(double timeStamp, int64_t timeOffset)
    {

        mTimeDelta = timeStamp - mTimeSeconds;
        mTimeSeconds = timeStamp;
        mTimeNanoSeconds = mTimeSeconds * 1e9;
        mComponentTimeOffsetNanoSeconds = timeOffset;

        (mIsaacCApiPtr->isaac_get_external_time_difference)(mAppHandle, mTimeSeconds, &mTimeDifferenceNanoSeconds);
    }

private:
protected:
    omni::isaac::robot_engine_bridge::RobotEngineBridge* mRobotEngineBridge = nullptr;
    IsaacCApi* mIsaacCApiPtr = nullptr;
    isaac_handle_t mAppHandle = 0;
    std::string mNodeName = "interface";
    isaac_error_t mError = isaac_error_t::isaac_error_success;
    int64_t mTimeDifferenceNanoSeconds = 0;
    int64_t mComponentTimeOffsetNanoSeconds = 0;
    double mTimeSeconds = 0; // current time in seconds
    int64_t mTimeNanoSeconds = 0; // current time in nano seconds
    double mTimeDelta = 0; // delta time for current tick
};
}
}
}
