// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "OgnROS2Utils.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <include/Ros2Node.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/Math.h>

#include <CoreNodes.h>
#include <OgnROS2ServiceServerRequestDatabase.h>

using namespace omni::isaac::ros2_bridge;

class OgnROS2ServiceServerRequest : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2ServiceServerRequestDatabase::sPerInstanceState<OgnROS2ServiceServerRequest>(nodeObj, instanceId);
        state.m_nodeObj = nodeObj;
        state.m_coreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
        // Register change event for message type
        AttributeObj attrMessagePackageObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messagePackage");
        AttributeObj attrMessageSubfolderObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageSubfolder");
        AttributeObj attrMessageNameObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageName");
        attrMessagePackageObj.iAttribute->registerValueChangedCallback(attrMessagePackageObj, onPackageChanged, true);
        attrMessageSubfolderObj.iAttribute->registerValueChangedCallback(attrMessageSubfolderObj, onPackageChanged, true);
        attrMessageNameObj.iAttribute->registerValueChangedCallback(attrMessageNameObj, onPackageChanged, true);
    }

    static bool compute(OgnROS2ServiceServerRequestDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();
        auto& state = db.perInstanceState<OgnROS2ServiceServerRequest>();
        const auto& nodeObj = db.abi_node();

        // Spin once calls reset automatically if it was not successful
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        auto messagePackage = std::string(db.inputs.messagePackage());
        auto messageSubfolder = std::string(db.inputs.messageSubfolder());
        auto messageName = std::string(db.inputs.messageName());
        if (messagePackage.size() == 0 || messageSubfolder.size() == 0 || messageName.size() == 0)
        {
            db.logWarning("messagePackage [%s] or messageSubfolder [%s] or messageName [%s] empty, skipping compute",
                          messagePackage.c_str(), messageSubfolder.c_str(), messageName.c_str());
            return false;
        }
        if (messagePackage != state.m_messagePackage)
        {
            state.m_messageUpdateNeeded = true;
            state.m_messagePackage = messagePackage;
        }
        if (messageSubfolder != state.m_messageSubfolder)
        {
            state.m_messageUpdateNeeded = true;
            state.m_messageSubfolder = messageSubfolder;
        }
        if (messageName != state.m_messageName)
        {
            state.m_messageUpdateNeeded = true;
            state.m_messageName = messageName;
        }
        // Update message and node attributes
        if (state.m_messageUpdateNeeded)
        {
            state.m_messageRequest = state.m_factory->createDynamicMessage(
                state.m_messagePackage, state.m_messageSubfolder, state.m_messageName, BackendMessageType::eRequest);
            omni::isaac::omnigraph_utils::createOgAttributesForMessage<OgnROS2ServiceServerRequestDatabase, true>(
                db, nodeObj, state.m_messagePackage, state.m_messageSubfolder, state.m_messageName,
                state.m_messageRequest, "Request:");
            state.m_messageUpdateNeeded = false;
        }

        std::string qosProfile = std::string(db.inputs.qosProfile());
        std::string serviceName = std::string(db.inputs.serviceName());
        if (qosProfile != state.m_qosProfile)
        {
            state.m_qosProfile = qosProfile;
            state.m_serviceUpdateNeeded = true;
        }
        if (serviceName != state.m_serviceName)
        {
            state.m_serviceName = serviceName;
            state.m_serviceUpdateNeeded = true;
        }

        if (!state.m_serviceServer || state.m_serviceUpdateNeeded)
        {
            // Setup ROS ServiceServer
            const std::string& serviceName = db.inputs.serviceName();
            std::string fullServiceName = addTopicPrefix(db.inputs.nodeNamespace(), serviceName);
            if (!state.m_factory->validateTopicName(fullServiceName))
            {
                db.logWarning("No Valid Topic : %s", fullServiceName.c_str());
                return false;
            }

            Ros2QoSProfile qos;
            if (qosProfile != "")
            {
                if (!jsonToRos2QoSProfile(qos, state.m_qosProfile))
                {
                    db.logWarning("No qos");
                    return false;
                }
            }

            CARB_LOG_INFO("Creating server for topic name %s", fullServiceName.c_str());
            state.m_serviceServer = state.m_factory->createService(
                state.m_nodeHandle.get(), fullServiceName.c_str(), state.m_messageRequest->getTypeSupportHandle(), qos);

            state.m_serverHandle = state.m_coreNodeFramework->addHandle(&state.m_serviceServer);
            db.outputs.serverHandle() = state.m_serverHandle;
            state.m_serviceUpdateNeeded = false;
        }

        return state.serviceServer(db, context);
    }

    bool serviceServer(OgnROS2ServiceServerRequestDatabase& db, const GraphContextObj& context)
    {
        auto& state = db.perInstanceState<OgnROS2ServiceServerRequest>();
        db.outputs.onReceived() = kExecutionAttributeStateDisabled;
        if (state.m_serviceServer->takeRequest(state.m_messageRequest->getPtr()))
        {
            // Check if all sub-message size match size of actuators before setting data
            if (!state.m_serviceServer->isValid())
            {
                db.logWarning("service is invalid");
                return false;
            }
            // Write incoming request data field/data to output
            omni::isaac::omnigraph_utils::writeNodeAttributeFromMessage(db, state.m_messageRequest, "Request:", true);
            // Only if the server received  a request
            db.outputs.onReceived() = kExecutionAttributeStateEnabled;
        }
        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2ServiceServerRequestDatabase::sPerInstanceState<OgnROS2ServiceServerRequest>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        m_coreNodeFramework->removeHandle(m_serverHandle);
        m_serviceServer.reset(); // This should be reset before we reset the handle.
        m_messagePackage.clear();
        m_messageSubfolder.clear();
        m_messageName.clear();
        m_serviceName.clear();
        m_qosProfile.clear();
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Service> m_serviceServer = nullptr;
    std::shared_ptr<Ros2Message> m_messageRequest = nullptr;

    bool m_serviceUpdateNeeded = true;
    bool m_messageUpdateNeeded = true;
    NodeObj m_nodeObj;
    uint64_t m_serverHandle;

    std::string m_messagePackage;
    std::string m_messageSubfolder;
    std::string m_messageName;
    std::string m_serviceName;
    std::string m_qosProfile;
    omni::isaac::core_nodes::CoreNodes* m_coreNodeFramework;

    static void onPackageChanged(AttributeObj const& attrObj, void const* userData)
    {
        // Get message package, subfolder and name
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        auto db = OgnROS2ServiceServerRequestDatabase(nodeObj);
        auto& state = db.perInstanceState<OgnROS2ServiceServerRequest>();
        std::string messagePackage = std::string(db.inputs.messagePackage());
        std::string messageSubfolder = std::string(db.inputs.messageSubfolder());
        std::string messageName = std::string(db.inputs.messageName());

        if (!omni::isaac::omnigraph_utils::removeDynamicAttributes<true, true>(nodeObj))
        {
            db.logError("Unable to remove existing attributes from the node");
            return;
        }

        if (messagePackage.size() == 0 || messageSubfolder.size() == 0 || messageName.size() == 0)
        {
            db.logWarning("messagePackage [%s] or messageSubfolder [%s] or messageName [%s] empty, skipping compute",
                          messagePackage.c_str(), messageSubfolder.c_str(), messageName.c_str());
            return;
        }

        // Build message attributes
        state.m_messageRequest = state.m_factory->createDynamicMessage(
            messagePackage, messageSubfolder, messageName, BackendMessageType::eRequest);
        omni::isaac::omnigraph_utils::createOgAttributesForMessage<OgnROS2ServiceServerRequestDatabase, true, false>(
            db, nodeObj, messagePackage, messageSubfolder, messageName, state.m_messageRequest, "Request:");
    }
};

REGISTER_OGN_NODE()
