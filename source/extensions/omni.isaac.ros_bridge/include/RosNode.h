// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "omni/isaac/utils/BaseResetNode.h"
#include "ros/callback_queue.h"
#include "ros/ros.h"

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>

#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/usd/UsdContext.h>

/**
 * @brief Base class for all ROS1 bridge nodes. It handles the lifetime of the internal ROS node handle automatically.
 *
 */
class RosNode : public BaseResetNode
{

public:
    /**
     * @brief Construct a new Ros Node object
     *
     */
    RosNode()
    {
    }
    /**
     * @brief Destroy the Ros Node object
     *
     */
    ~RosNode()
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
        mNodeHandle.reset();
    }

    /**
     * @brief This function should be called before doing any work  with the OGN Node. It makes sure that ROS master is
     * running, the node is valid and all subscribers are called. Generally this should be called each frame.
     * Changes to the nodeName are only handled if stop or play are pressed.
     *
     * @param nodeName
     * @return true
     * @return false
     */
    bool spinOnce(const std::string& nodeName)
    {
        // Check that the ROS master node is running, if not, reset the node handle
        if (!ros::master::check())
        {
            reset();
            return false;
        }
        // If the handle was not initialized, try to initialize it
        if (!initializeNodeHandle(nodeName))
        {
            return false;
        }
        // Call and subscriber callbacks that are attachd to this node.
        mCallbackQueue.callAvailable();
        return true;
    }
    /**
     * @brief Validates a ROS topic name, returns true if valid, false if not
     *
     * @param topicName
     * @return true
     * @return false
     */
    static bool validateTopic(const std::string& topicName)
    {
        std::string result;
        if (!ros::names::validate(topicName, result))
        {
            CARB_LOG_ERROR("Topic name %s not valid %s", topicName.data(), result.c_str());
            return false;
        }
        return true;
    }

    /**
     * @brief Set prefixes to frameIds
     *
     * @param prefix rosNodePrefix
     * @param string_value frameId string
     *
     */

    static inline void addFramePrefix(const std::string& prefix, std::string& string_value)
    {
        size_t start_idx = 0;

        for (size_t i = 0; prefix[i] == '/'; i++)
        {
            start_idx++;
        }

        if (prefix != "" && prefix.size() != start_idx)
        {
            // Setting prefix to frameIds
            string_value.insert(0, prefix.substr(start_idx));
            string_value.insert(prefix.substr(start_idx).length(), "/");
        }
    }

private:
    /**
     * @brief Handles initialization and validation of the ROS node handle.
     *
     * @param nodeName
     * @return true
     * @return false
     */
    bool initializeNodeHandle(const std::string& nodeName)
    {
        // Handle is initialized, so we should be ok, return true
        if (mNodeHandle)
        {
            return true;
        }
        // Handle is not valid, try to initialize handle
        std::string result;
        // Make sure the ROS node name is valid
        if (!ros::names::validate(nodeName, result))
        {
            return false;
        }
        mNodeHandle = std::make_unique<ros::NodeHandle>(nodeName);

        // The callback queue is only useful for nodes that have registered subscribers
        mNodeHandle->setCallbackQueue(&(mCallbackQueue));


        return true;
    }

protected:
    std::unique_ptr<ros::NodeHandle> mNodeHandle;
    ros::CallbackQueue mCallbackQueue;
};
