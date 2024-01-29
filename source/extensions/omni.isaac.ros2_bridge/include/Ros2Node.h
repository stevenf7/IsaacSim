// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "omni/isaac//utils/BaseResetNode.h"

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>

#include <include/Ros2Bridge.h>
#include <include/Ros2Factory.h>
#include <omni/usd/UsdContextIncludes.h>

#include <CoreNodes.h>
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
        mRos2Bridge = carb::getCachedInterface<omni::isaac::ros2_bridge::Ros2Bridge>();
        // Here mFactory should be set according to the env var for ROS Distro..?
        mFactory = mRos2Bridge->getFactory();
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
        // if (executor)
        // {
        //     executor->cancel();
        //     executor->remove_node(mNodeHandle);
        //     executor.reset();
        // }
        if (mNodeHandle)
        {
            // std::cout << "Calling RESET for this ROS2 Node..." << std::endl;
            // mNodeHandle->handle()->shutdown();
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
        // executor->spin_once(std::chrono::nanoseconds(0));
        return true;
    }
    /**
     * @brief Validates a ROS topic name, returns true if valid, false if not
     *
     * @param topicName
     * @return true
     * @return false
     */

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
        if (topic_name.size() == 0)
        {
            return full_topic_name;
        }
        if (prefix.size() > 0)
        {
            for (size_t i = 0; !(::isalnum(prefix[i])); i++)
            {
                start_idx++;
            }
        }
        for (size_t i = 0; !(::isalnum(topic_name[i])); i++)
        {
            start_topic_idx++;
        }

        full_topic_name.insert(0, "/" + topic_name.substr(start_topic_idx));

        if (prefix.size() != start_idx)
        {
            // Setting prefix to full topic
            full_topic_name.insert(0, "/" + prefix.substr(start_idx));
        }
        return full_topic_name;
    }

    static inline std::string sanitizeName(std::string input)
    {
        std::replace_if(
            input.begin(), input.end(), [](auto ch) { return !(::isalnum(ch) || ch == '_'); }, '_');
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
        // // Check rclcpp is running
        // if (!rclcpp::ok())
        // {
        //     return false;
        // }

        // Handle is not valid, try to initialize handle
        // Make sure the ROS node name is valid
        std::string sanitizedNodeName = sanitizeName(nodeName);
        if (!mFactory->validateNodeName(sanitizedNodeName))
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

            contextPtr = reinterpret_cast<std::shared_ptr<Ros2HandleBase>*>(voidPtr);
        }
        else
        {
            contextPtr = reinterpret_cast<std::shared_ptr<Ros2HandleBase>*>(mRos2Bridge->getDefaultContextHandle());
        }

        if (nodeNamespace.size() == 0 || !mFactory->validateNodeNamespace(nodeNamespace))
        {
            mNodeHandle = mFactory->CreateNode(sanitizedNodeName.c_str(), "", contextPtr->get());
        }
        else
        {
            mNodeHandle = mFactory->CreateNode(sanitizedNodeName.c_str(), nodeNamespace.c_str(), contextPtr->get());
        }
        return true;
    }

protected:
    omni::isaac::ros2_bridge::Ros2Bridge* mRos2Bridge = nullptr;
    std::shared_ptr<Ros2NodeBase> mNodeHandle = nullptr;
    std::shared_ptr<Ros2HandleBase>* contextPtr;
    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
    Ros2Factory* mFactory = nullptr;
};
