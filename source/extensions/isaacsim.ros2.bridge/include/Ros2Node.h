// Copyright (c) 2022-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

/** @file
 * @brief ROS 2 Node definition.
 */
#pragma once

#include "isaacsim/core/utils/BaseResetNode.h"

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>
#include <carb/settings/ISettings.h>

#include <include/Ros2Bridge.h>
#include <include/Ros2Factory.h>
#include <omni/usd/UsdContextIncludes.h>

#include <CoreNodes.h>
//
#include <omni/usd/UsdContext.h>

namespace isaacsim
{
namespace ros2
{
namespace bridge
{

/**
 * Base class for ROS 2 bridge nodes.
 *
 * This class handles the lifetime of the internal ROS 2 node handle automatically.
 */
class Ros2Node : public BaseResetNode
{

public:
    /**
     * Constructor.
     *
     * During the construction of the object, the carb interfaces and the ROS 2 factory will be retrieved to be used by
     * the derived classes.
     */
    Ros2Node()
    {
        m_coreNodeFramework = carb::getCachedInterface<isaacsim::core::nodes::CoreNodes>();
        m_ros2Bridge = carb::getCachedInterface<isaacsim::ros2::bridge::Ros2Bridge>();

        m_settings = carb::getCachedInterface<carb::settings::ISettings>();
        static constexpr char setting[] = "/exts/isaacsim.ros2.bridge/publish_without_verification";
        m_publishWithoutVerification = m_settings->getAsBool(setting);

        // Here m_factory should be set according to the env var for ROS Distro..?
        m_factory = m_ros2Bridge->getFactory();
    }

    /**
     * Destructor.
     */
    ~Ros2Node()
    {
        reset();
    }

    /**
     * Reset the \ref Ros2NodeHandle handler.
     *
     * This method should be called by derived classes after they reset any publishers/subscribers attached to the node.
     */
    virtual void reset()
    {
        if (m_nodeHandle)
        {
            // std::cout << "Calling RESET for this ROS2 Node..." << std::endl;
            // m_nodeHandle->getContextHandle()->shutdown();
            m_nodeHandle.reset();
        }
    }

    /**
     * Do node work to initialize the node handler once.
     *
     * This function should be called before doing any work with any OmniGraph node.
     * Changes to the node name are only handled if Stop and Play are pressed.
     *
     * @param nodeName Name of the node.
     * @param namespaceName Namespace of the node.
     * @param contextHandleAddr Context handler's memory address.
     * @returns Whether the node handler has been initialized.
     */
    bool initializeNodeHandle(const std::string& nodeName, const std::string& namespaceName, uint64_t contextHandleAddr)
    {
        // Handle is initialized, so we should be ok, return true
        if (m_nodeHandle)
        {
            return true;
        }

        // Handle is not valid, try to initialize handle.
        // Make sure the ROS node name is valid
        std::string sanitizedNodeName = sanitizeName(nodeName);
        if (!m_factory->validateNodeName(sanitizedNodeName))
        {
            return false;
        }

        m_namespaceName = trimNonAlnum(namespaceName);
        if (m_namespaceName.size() > 0)
        {
            m_namespaceName = std::string("/") + m_namespaceName;
        }

        // Set the ROS 2 context if its available, if this is zero we use the default context
        if (contextHandleAddr)
        {
            // CARB_LOG_WARN("GET HANDLE %" PRIu64 "\n", contextHandleAddr);
            void* contextHandlePtr = m_coreNodeFramework->getHandle(contextHandleAddr);
            if (contextHandlePtr == nullptr)
            {
                // CARB_LOG_WARN("CONTEXT DOES NOT EXIST");
                return false;
            }
            m_contextHandle = reinterpret_cast<std::shared_ptr<Ros2ContextHandle>*>(contextHandlePtr);
        }
        else
        {
            m_contextHandle =
                reinterpret_cast<std::shared_ptr<Ros2ContextHandle>*>(m_ros2Bridge->getDefaultContextHandleAddr());
        }

        // Create the ROS 2 node handler
        if (m_namespaceName.size() == 0)
        {
            m_nodeHandle = m_factory->createNodeHandle(sanitizedNodeName.c_str(), "", m_contextHandle->get());
        }
        else if (m_factory->validateNamespaceName(m_namespaceName))
        {
            m_nodeHandle =
                m_factory->createNodeHandle(sanitizedNodeName.c_str(), m_namespaceName.c_str(), m_contextHandle->get());
        }
        else
        {
            return false;
        }
        return m_nodeHandle->getNode() != nullptr;
    }

    /**
     * Get whether the ROS 2 node has been initialized.
     *
     * @returns True if the node handle has been initialized, False otherwise.
     */
    bool isInitialized() const
    {
        return m_nodeHandle != nullptr;
    }

    /**
     * Add the specified prefix to the given topic name.
     *
     * This method will insert the separator character (`/`) between the prefix and the topic name.
     *
     * @param prefix Prefix to add to the topic.
     * @param topicName Name of the topic.
     * @returns Name of the topic prefixed with the specified prefix.
     */
    static inline std::string addTopicPrefix(const std::string& prefix, const std::string& topicName)
    {
        if (topicName.size() == 0)
        {
            return std::string("");
        }
        return prefix + std::string("/") + trimNonAlnum(topicName);
    }

    /**
     * Collect namespaces defined for parent prims in a stage and automatically form a node namespace.
     *
     * This method performs a reverse search up a USD stage and for each parent prim containing isaac:namespace
     * attribute, it will continue prepending the each namespace value. It will insert the separator character (`/`)
     * between each namespace value.
     *
     * @param namespaceInput Node Namespace. If not empty, it will be returned as it is and no search will be performed.
     * @param startPrim USD Prim to start the reverse search.
     * @param tfNode Set to true if collecting namespace for a TF ROS 2 node
     * @returns Name of the topic prefixed with the specified prefix.
     */
    static inline std::string collectNamespace(const std::string& namespaceInput,
                                               const PXR_NS::UsdPrim& startPrim,
                                               const bool tfNode = false)
    {
        if (namespaceInput.size() > 0)
        {
            return namespaceInput;
        }
        std::string namespaceString = "";
        PXR_NS::UsdPrim currentPrim = startPrim;
        static const PXR_NS::TfToken isaacNamespace("isaac:namespace");

        std::string namespaceValue = "";

        // Traverse upwards until there are no more parents
        while (currentPrim.IsValid())
        {
            const pxr::UsdAttribute attr = currentPrim.GetAttribute(isaacNamespace);
            if (currentPrim.GetAttribute(isaacNamespace).HasValue())
            {
                if (attr.Get(&namespaceValue))
                {
                    if (!tfNode)
                    {
                        // Prepend the value to the accumulated string
                        if (!namespaceString.empty())
                        {
                            namespaceString = namespaceValue + "/" + namespaceString;
                        }
                        else
                        {
                            namespaceString = namespaceValue;
                        }
                    }
                    else
                    { // If collecting namespace for a TF node, only retrieve the highest level prim namespace
                        if (!namespaceValue.empty())
                        {
                            namespaceString = namespaceValue;
                        }
                    }
                }
            }

            // Move to the parent prim
            currentPrim = currentPrim.GetParent();
        }

        return namespaceString;
    }

private:
    static inline std::string sanitizeName(std::string input)
    {
        std::replace_if(
            input.begin(), input.end(), [](auto ch) { return !(::isalnum(ch) || ch == '_'); }, '_');
        return input;
    }

    static inline std::string trimNonAlnum(const std::string& s)
    {
        if (s.size() == 0)
        {
            return "";
        }

        size_t startIdx = 0;
        size_t endIdx = s.size() - 1;

        while (startIdx < s.size() && !std::isalnum(s[startIdx]))
            startIdx++;

        while (endIdx > startIdx && !std::isalnum(s[endIdx]))
            endIdx--;

        return s.substr(startIdx, endIdx - startIdx + 1);
    }

protected:
    isaacsim::ros2::bridge::Ros2Bridge* m_ros2Bridge = nullptr; //!< \ref Ros2Bridge (carb) interface.
    std::shared_ptr<Ros2NodeHandle> m_nodeHandle = nullptr; //!< Node handler.
    carb::settings::ISettings* m_settings = nullptr; //!< Settings (carb) interface.
    bool m_publishWithoutVerification; //!< Whether to publish in a topic even if there are no subscription to it.
    std::shared_ptr<Ros2ContextHandle>* m_contextHandle; //!< Context handler.
    isaacsim::core::nodes::CoreNodes* m_coreNodeFramework; //!< CoreNodes (carb) interface.
    Ros2Factory* m_factory = nullptr; //!< Factory instance for creating ROS 2 related objects according to the sourced
                                      //!< ROS 2 distribution.
    std::string m_namespaceName; //!< Namespace name.
};

} // namespace bridge
} // namespace ros2
} // namespace isaacsim
