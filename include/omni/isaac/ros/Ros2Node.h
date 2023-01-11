// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../utils/BaseResetNode.h"
#include "rclcpp/rclcpp.hpp"
#include "rmw/validate_full_topic_name.h"
#include "rmw/validate_namespace.h"
#include "rmw/validate_node_name.h"

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>

#include <omni/isaac/core_nodes/CoreNodes.h>
#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/usd/UsdContext.h>

/**
 * @brief Base class for all ROS1 bridge nodes. It handles the lifetime of the internal ROS node handle automatically.
 *
 */
class Ros2Node : public BaseResetNode
{

public:
    /**
     * @brief Construct a new Ros Node object
     *
     */
    Ros2Node()
    {
        mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
    }
    /**
     * @brief Destroy the Ros Node object
     *
     */
    ~Ros2Node()
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
        if (executor)
        {
            executor->cancel();
            executor->remove_node(mNodeHandle);
            executor.reset();
        }
        if (mNodeHandle)
        {

            mNodeHandle.reset();
        }
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
    bool spinOnce(const std::string& nodeName, const std::string namespaceName, uint64_t contextHandle)
    {
        // If the handle was not initialized, try to initialize it
        if (!initializeNodeHandle(nodeName, namespaceName, contextHandle))
        {
            return false;
        }
        // Call and subscriber callbacks that are attachd to this node.
        executor->spin_once(std::chrono::nanoseconds(0));
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
        int invalid_result;
        size_t invalid_index;

        std::ignore = rmw_validate_full_topic_name(topicName.c_str(), &invalid_result, &invalid_index);

        if (invalid_result)
        {
            CARB_LOG_ERROR("Topic name %s not valid, %s", topicName.c_str(),
                           rmw_full_topic_name_validation_result_string(invalid_result));
            return false;
        }
        return true;
    }
    /**
     * @brief Validates a ROS namespace, returns true if valid, false if not
     *
     * @param topicName
     * @return true
     * @return false
     */
    static bool validateNodeNamespace(const std::string& nodeNamespace)
    {
        int invalid_result;
        size_t invalid_index;

        std::ignore = rmw_validate_namespace(nodeNamespace.c_str(), &invalid_result, &invalid_index);

        if (invalid_result)
        {
            CARB_LOG_ERROR("Namespace name %s not valid, %s", nodeNamespace.c_str(),
                           rmw_namespace_validation_result_string(invalid_result));
            return false;
        }
        return true;
    }

    /**
     * @brief Validates a ROS node name, returns true if valid, false if not
     *
     * @param topicName
     * @return true
     * @return false
     */
    static bool validateNodeName(const std::string& nodeName)
    {
        int invalid_result;
        size_t invalid_index;

        std::ignore = rmw_validate_node_name(nodeName.c_str(), &invalid_result, &invalid_index);

        if (invalid_result)
        {
            CARB_LOG_ERROR(
                "Node name %s not valid, %s", nodeName.c_str(), rmw_node_name_validation_result_string(invalid_result));
            return false;
        }
        return true;
    }

    /**
     * @brief Set prefixes to frameIds
     *
     * @param prefix ros2NodePrefix
     * @param string_value frameId string
     *
     */

    static inline std::string addTopicPrefix(const std::string& prefix, const std::string& topic_name)
    {
        std::string full_topic_name;

        size_t start_idx = 0;
        size_t start_topic_idx = 0;

        for (size_t i = 0; !(::isalnum(prefix[i])); i++)
        {
            start_idx++;
        }

        for (size_t i = 0; !(::isalnum(topic_name[i])); i++)
        {
            start_topic_idx++;
        }

        full_topic_name.insert(0, "/" + topic_name.substr(start_topic_idx));

        if (prefix != "" && prefix.size() != start_idx)
        {
            // Setting prefix to full topic
            full_topic_name.insert(0, "/" + prefix.substr(start_idx));
        }
        return full_topic_name;
    }

    static inline std::string sanitizeName(std::string input)
    {
        std::replace_if(input.begin(), input.end(), [](auto ch) { return !(::isalnum(ch) || ch == '_'); }, '_');
        return input;
    }

private:
    /**
     * @brief Handles initialization and validation of the ROS node handle.
     *
     * @param nodeName
     * @return true
     * @return false
     */
    bool initializeNodeHandle(const std::string& nodeName, const std::string& nodeNamespace, uint64_t contexthandle)
    {
        // Handle is initialized, so we should be ok, return true
        if (mNodeHandle)
        {
            return true;
        }
        // Check rclcpp is running
        if (!rclcpp::ok())
        {
            return false;
        }

        // Handle is not valid, try to initialize handle
        // Make sure the ROS node name is valid
        std::string sanitizedNodeName = sanitizeName(nodeName);
        if (!validateNodeName(sanitizedNodeName))
        {
            return false;
        }

        // Set the ROS context if its available, if this is zero we use the default context
        if (contexthandle)
        {
            // CARB_LOG_WARN("GET HANDLE %" PRIu64 "\n", contexthandle);
            void* voidPtr = mCoreNodeFramework->getHandle(contexthandle);
            if (voidPtr == nullptr)
            {
                // CARB_LOG_WARN("CONTEXT DOES NOT EXIST");
                return false;
            }

            std::shared_ptr<rclcpp::Context>* contextPtr = reinterpret_cast<std::shared_ptr<rclcpp::Context>*>(voidPtr);
            if (contexthandle && contextPtr && (*contextPtr)->is_valid())
            {
                options.context((*contextPtr));
            }
        }
        else
        {
            options.context(rclcpp::contexts::get_global_default_context());
        }

        if (nodeNamespace.size() == 0 || !validateNodeNamespace(nodeNamespace))
        {
            mNodeHandle = std::make_shared<rclcpp::Node>(sanitizedNodeName, options);
        }
        else
        {
            mNodeHandle = std::make_shared<rclcpp::Node>(sanitizedNodeName, nodeNamespace, options);
        }
        executor = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();

        executor->add_node(mNodeHandle);
        return true;
    }

protected:
    std::shared_ptr<rclcpp::Node> mNodeHandle = nullptr;
    std::shared_ptr<rclcpp::executors::SingleThreadedExecutor> executor = nullptr;
    rclcpp::NodeOptions options;
    std::shared_ptr<rclcpp::Context> contextSharedPtr = nullptr;
    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
};
