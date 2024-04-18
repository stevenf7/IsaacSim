// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on
#include "OgnROS2Utils.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <include/Ros2Node.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/Math.h>

#include <OgnROS2ServiceClientDatabase.h>


class OgnROS2ServiceClient : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2ServiceClientDatabase::sPerInstanceState<OgnROS2ServiceClient>(nodeObj, instanceId);
        state.mNodeObj = nodeObj;
        // register change event for message type
        AttributeObj attrMessagePackageObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messagePackage");
        AttributeObj attrMessageSubfolderObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageSubfolder");
        AttributeObj attrServiceNameObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageName");
        attrMessagePackageObj.iAttribute->registerValueChangedCallback(attrMessagePackageObj, onPackageChanged, true);
        attrMessageSubfolderObj.iAttribute->registerValueChangedCallback(attrMessageSubfolderObj, onPackageChanged, true);
        attrServiceNameObj.iAttribute->registerValueChangedCallback(attrServiceNameObj, onPackageChanged, true);
    }

    static bool compute(OgnROS2ServiceClientDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnROS2ServiceClient>();
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
        if (messageName != state.mMassageName)
        {
            state.mIsMessageUpdateNeeded = true;
            state.mMassageName = messageName;
        }
        // update message and node attributes
        if (state.mIsMessageUpdateNeeded)
        {
            state.mMessageRequest = state.mFactory->createDynamicMessage(
                state.mMessagePackage, state.mMessageSubfolder, state.mMassageName, BackendMessageType::eRequest);
            OgnDynamicMesssageUtils::createOgAttributesForMessage<OgnROS2ServiceClientDatabase, false>(
                db, nodeObj, state.mMessagePackage, state.mMessageSubfolder, state.mMassageName, state.mMessageRequest,
                "Request:");
            state.mMessageResponse = state.mFactory->createDynamicMessage(
                state.mMessagePackage, state.mMessageSubfolder, state.mMassageName, BackendMessageType::eResponse);
            OgnDynamicMesssageUtils::createOgAttributesForMessage<OgnROS2ServiceClientDatabase, true>(
                db, nodeObj, state.mMessagePackage, state.mMessageSubfolder, state.mMassageName, state.mMessageResponse,
                "Response:");

            state.mIsMessageUpdateNeeded = false;
            state.mIsServiceUpdateNeeded = true;
            return false;
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

        // ServiceServer was not valid, create a new one
        if (state.mIsServiceUpdateNeeded)
        {
            // Setup ROS ServiceServer
            const std::string& serviceName = db.inputs.serviceName();
            std::string fullServiceName = addTopicPrefix(db.inputs.nodeNamespace(), serviceName);
            if (!state.mFactory->validateTopic(fullServiceName))
            {
                db.logWarning("No Valid service name : %s", fullServiceName.c_str());
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

            state.mServiceClient = state.mFactory->CreateClient(
                state.mNodeHandle.get(), fullServiceName.c_str(), state.mMessageRequest->getTypeSupportHandle(), qos);
            state.mIsServiceUpdateNeeded = false;
        }

        return state.serviceClient(db, context);
    }


    bool serviceClient(OgnROS2ServiceClientDatabase& db, const GraphContextObj& context)
    {
        auto& state = db.perInstanceState<OgnROS2ServiceClient>();
        if (!state.mServiceClient->isValid())
        {
            db.logWarning("Service is invalid");
            return false;
        }

        // Write the request field/data from the node and compose a message
        OgnDynamicMesssageUtils::writeMessageDataFromNode(db, state.mMessageRequest, "Request:", false);
        // CARB_LOG_INFO("Client: Sending Request ...");
        state.mServiceClient->sendRequest(state.mMessageRequest->ptr());
        // CARB_LOG_INFO("Client: Getting Response ...");
        state.mServiceClient->getResponse(state.mMessageResponse->ptr());
        // write response of the node from server to the node outputs
        OgnDynamicMesssageUtils::writeNodeAttributeFromMessage(db, state.mMessageResponse, "Response:", true);

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2ServiceClientDatabase::sPerInstanceState<OgnROS2ServiceClient>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mServiceClient.reset(); // This should be reset before we reset the handle.
        mMessagePackage.clear();
        mMessageSubfolder.clear();
        mServiceName.clear();
        mMassageName.clear();
        mQosProfile.clear();
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Client> mServiceClient = nullptr;
    std::shared_ptr<Ros2Message> mMessageRequest = nullptr;
    std::shared_ptr<Ros2Message> mMessageResponse = nullptr;
    bool mIsServiceUpdateNeeded = true;
    bool mIsMessageUpdateNeeded = true;
    NodeObj mNodeObj;

    std::string mMessagePackage;
    std::string mMessageSubfolder;
    std::string mMassageName;
    std::string mQosProfile;
    std::string mServiceName;

    static void onPackageChanged(AttributeObj const& attrObj, void const* userData)
    {
        // get message package, subfolder and name
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        auto db = OgnROS2ServiceClientDatabase(nodeObj);
        auto& state = db.perInstanceState<OgnROS2ServiceClient>();
        std::string messagePackage = std::string(db.inputs.messagePackage());
        std::string messageSubfolder = std::string(db.inputs.messageSubfolder());
        std::string messageName = std::string(db.inputs.messageName());
        // build message attributes
        if (!OgnDynamicMesssageUtils::removeDynamicAttributes<true, true>(nodeObj))
        {
            db.logError("Unable to remove existing attributes from the node");
            return;
        }
        state.mMessageRequest = state.mFactory->createDynamicMessage(
            messagePackage, messageSubfolder, messageName, BackendMessageType::eRequest);
        OgnDynamicMesssageUtils::createOgAttributesForMessage<OgnROS2ServiceClientDatabase, false, false>(
            db, nodeObj, messagePackage, messageSubfolder, messageName, state.mMessageRequest, "Request:");
        state.mMessageResponse = state.mFactory->createDynamicMessage(
            messagePackage, messageSubfolder, messageName, BackendMessageType::eResponse);
        OgnDynamicMesssageUtils::createOgAttributesForMessage<OgnROS2ServiceClientDatabase, true, false>(
            db, nodeObj, messagePackage, messageSubfolder, messageName, state.mMessageResponse, "Response:");

        state.mIsServiceUpdateNeeded = true;
    }
};

REGISTER_OGN_NODE()
