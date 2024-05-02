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


class OgnROS2ServiceServerRequest : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2ServiceServerRequestDatabase::sPerInstanceState<OgnROS2ServiceServerRequest>(nodeObj, instanceId);
        state.mNodeObj = nodeObj;
        state.mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
        // register change event for message type
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
        // spin once calls reset automatically if it was not successful
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

        if (messagePackage != state.mMessagePackage)
        {
            state.mIsMessageUpdateNeeded = true;
            state.mMessagePackage = messagePackage;
        }
        if (messageSubfolder != state.mMessageSubfolder)
        {
            state.mIsMessageUpdateNeeded = true;
            state.mMessageSubfolder = messageSubfolder;
        }
        if (messageName != state.mMessageName)
        {
            state.mIsMessageUpdateNeeded = true;
            state.mMessageName = messageName;
        }
        // update message and node attributes
        if (state.mIsMessageUpdateNeeded)
        {
            state.mMessageRequest = state.mFactory->createDynamicMessage(
                state.mMessagePackage, state.mMessageSubfolder, state.mMessageName, BackendMessageType::eRequest);
            OgnDynamicMesssageUtils::createOgAttributesForMessage<OgnROS2ServiceServerRequestDatabase, true>(
                db, nodeObj, state.mMessagePackage, state.mMessageSubfolder, state.mMessageName, state.mMessageRequest,
                "Request:");
            state.mIsMessageUpdateNeeded = false;
        }

        std::string qosProfile = std::string(db.inputs.qosProfile());
        std::string serviceName = std::string(db.inputs.serviceName());
        if (qosProfile != state.mQosProfile)
        {
            state.mQosProfile = qosProfile;
            state.mIsServiceUpdateNeeded = true;
        }
        if (serviceName != state.mServiceName)
        {
            state.mServiceName = serviceName;
            state.mIsServiceUpdateNeeded = true;
        }

        if (!state.mServiceServer || state.mIsServiceUpdateNeeded)
        {
            // Setup ROS ServiceServer
            const std::string& serviceName = db.inputs.serviceName();
            std::string fullServiceName = addTopicPrefix(db.inputs.nodeNamespace(), serviceName);
            if (!state.mFactory->validateTopic(fullServiceName))
            {
                db.logWarning("No Valid Topic : %s", fullServiceName.c_str());
                return false;
            }

            Ros2QoSProfile qos;
            if (qosProfile != "")
            {
                if (!jsonToRos2QoSProfile(qos, state.mQosProfile))
                {
                    db.logWarning("No qos");
                    return false;
                }
            }

            CARB_LOG_INFO("Creating server for topic name %s", fullServiceName.c_str());
            state.mServiceServer = state.mFactory->CreateService(
                state.mNodeHandle.get(), fullServiceName.c_str(), state.mMessageRequest->getTypeSupportHandle(), qos);

            state.mServerHandle = state.mCoreNodeFramework->addHandle(&state.mServiceServer);
            db.outputs.serverHandle() = state.mServerHandle;
            state.mIsServiceUpdateNeeded = false;
        }

        return state.serviceServer(db, context);
    }


    bool serviceServer(OgnROS2ServiceServerRequestDatabase& db, const GraphContextObj& context)
    {
        auto& state = db.perInstanceState<OgnROS2ServiceServerRequest>();
        db.outputs.onReceived() = kExecutionAttributeStateDisabled;
        if (state.mServiceServer->getRequest(state.mMessageRequest->ptr()))
        {
            // Check if all sub-message size match size of actuators before setting data
            if (!state.mServiceServer->isValid())
            {
                db.logWarning("service is invalid");
                return false;
            }
            // write incoming request data field/data to output
            OgnDynamicMesssageUtils::writeNodeAttributeFromMessage(db, state.mMessageRequest, "Request:", true);
            // only if the server received  a request
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
        mCoreNodeFramework->removeHandle(mServerHandle);
        mServiceServer.reset(); // This should be reset before we reset the handle.
        mMessagePackage.clear();
        mMessageSubfolder.clear();
        mMessageName.clear();
        mServiceName.clear();
        mQosProfile.clear();
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Service> mServiceServer = nullptr;
    std::shared_ptr<Ros2Message> mMessageRequest = nullptr;

    bool mIsServiceUpdateNeeded = true;
    bool mIsMessageUpdateNeeded = true;
    NodeObj mNodeObj;
    uint64_t mServerHandle;

    std::string mMessagePackage;
    std::string mMessageSubfolder;
    std::string mMessageName;
    std::string mServiceName;
    std::string mQosProfile;
    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;

    static void onPackageChanged(AttributeObj const& attrObj, void const* userData)
    {
        // get message package, subfolder and name
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        auto db = OgnROS2ServiceServerRequestDatabase(nodeObj);
        auto& state = db.perInstanceState<OgnROS2ServiceServerRequest>();
        std::string messagePackage = std::string(db.inputs.messagePackage());
        std::string messageSubfolder = std::string(db.inputs.messageSubfolder());
        std::string messageName = std::string(db.inputs.messageName());
        if (!OgnDynamicMesssageUtils::removeDynamicAttributes<true, true>(nodeObj))
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


        // build message attributes
        state.mMessageRequest = state.mFactory->createDynamicMessage(
            messagePackage, messageSubfolder, messageName, BackendMessageType::eRequest);
        OgnDynamicMesssageUtils::createOgAttributesForMessage<OgnROS2ServiceServerRequestDatabase, true, false>(
            db, nodeObj, messagePackage, messageSubfolder, messageName, state.mMessageRequest, "Request:");
    }
};

REGISTER_OGN_NODE()
