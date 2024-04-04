// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <include/Ros2Node.h>

#include <OgnROS2SubscriberDatabase.h>


class OgnROS2Subscriber : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2SubscriberDatabase::sPerInstanceState<OgnROS2Subscriber>(nodeObj, instanceId);
        state.mNodeObj = nodeObj;

        // register change event for message type
        AttributeObj attrMessagePackageObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messagePackage");
        AttributeObj attrMessageSubfolderObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageSubfolder");
        AttributeObj attrMessageNameObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageName");
        attrMessagePackageObj.iAttribute->registerValueChangedCallback(
            attrMessagePackageObj, onMessagePackageChanged, true);
        attrMessageSubfolderObj.iAttribute->registerValueChangedCallback(
            attrMessageSubfolderObj, onMessageSubfolderChanged, true);
        attrMessageNameObj.iAttribute->registerValueChangedCallback(attrMessageNameObj, onMessageNameChanged, true);
    }

    static bool compute(OgnROS2SubscriberDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2Subscriber>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }

        // check for changes in message type
        std::string messagePackage = std::string(db.inputs.messagePackage());
        std::string messageSubfolder = std::string(db.inputs.messageSubfolder());
        std::string messageName = std::string(db.inputs.messageName());
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
        if (state.mIsMessageUpdateNeeded || !state.mMessage)
        {
            bool status =
                createMessageAndAttributes(nodeObj, state.mMessagePackage, state.mMessageSubfolder, state.mMessageName);
            if (!status)
                return false;
            state.mIsMessageUpdateNeeded = false;
            state.mIsSubscriberUpdateNeeded = true;
            return false;
        }

        // check for changes in subscriber
        std::string topicName = std::string(db.inputs.topicName());
        uint64_t queueSize = db.inputs.queueSize();
        if (topicName != state.mTopicName)
        {
            state.mIsSubscriberUpdateNeeded = true;
            state.mTopicName = topicName;
        }
        if (queueSize != state.mQueueSize)
        {
            state.mIsSubscriberUpdateNeeded = true;
            state.mQueueSize = queueSize;
        }
        // update subscriber
        if (state.mIsSubscriberUpdateNeeded)
        {
            // destroy previous subscriber
            state.mSubscriber.reset();
            // get topic name
            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, state.mTopicName);
            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 subscriber, invalid topic name");
                return false;
            }
            // create subscriber
            std::string messageType = messagePackage + "/" + messageSubfolder + "/" + messageName;
            CARB_LOG_INFO("OgnROS2Subscriber: creating subscriber: %s (%s)", fullTopicName.c_str(), messageType.c_str());
            state.mSubscriber = state.mFactory->CreateSubscriber(
                state.mNodeHandle.get(), fullTopicName.c_str(), state.mMessage->getTypeSupportHandle(), state.mQueueSize);
            if (!state.mSubscriber->isValid())
            {
                db.logWarning(
                    ("Invalid subscription to the topic " + fullTopicName + " for the message type " + messageType).c_str());
                state.mSubscriber.reset();
                return false;
            }
            state.mIsSubscriberUpdateNeeded = false;
            return true;
        }

        return state.subscriberCallback(db);
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2SubscriberDatabase::sPerInstanceState<OgnROS2Subscriber>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mIsSubscriberUpdateNeeded = false;
        mIsMessageUpdateNeeded = false;

        mMessagePackage.clear();
        mMessageSubfolder.clear();
        mMessageName.clear();
        mTopicName.clear();
        mQueueSize = 0;

        mMessage.reset();
        mSubscriber.reset(); // this should be reset before reset the handle

        Ros2Node::reset();
    }

    bool subscriberCallback(OgnROS2SubscriberDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2Subscriber>();
        if (!state.mSubscriber)
            return false;
        if (!state.mSubscriber->spin(state.mMessage->ptr()))
            return false;

        auto messageData = std::static_pointer_cast<Ros2DynamicMessage>(state.mMessage)->getData(true);
        auto messageFields = std::static_pointer_cast<Ros2DynamicMessage>(state.mMessage)->getMessageFields();

        for (size_t i = 0; i < messageFields.size(); ++i)
        {
            if (!messageData.at(i))
                continue;
            auto messageField = messageFields.at(i);
            switch (messageField.dataType)
            {
            case omni::fabric::BaseDataType::eBool:
            {
                if (messageField.isArray)
                {
                    auto data = *std::static_pointer_cast<const std::vector<bool>>(messageData.at(i));
                    auto outputValue =
                        getAttributeWritableArrayData<bool*>(db.abi_node(), "outputs:" + messageField.name, data.size());
                    for (size_t j = 0; j < data.size(); ++j) // std::vector<bool> is a specialization that has no ::data
                        *((*outputValue) + j) = data.at(j);
                }
                else
                {
                    auto outputValue = getAttributeWritableData<bool>(db.abi_node(), "outputs:" + messageField.name);
                    *outputValue = *std::static_pointer_cast<const bool>(messageData.at(i));
                }
                break;
            }
            case omni::fabric::BaseDataType::eUChar:
            {
                if (messageField.isArray)
                {
                    auto data = *std::static_pointer_cast<const std::vector<uint8_t>>(messageData.at(i));
                    auto outputValue = getAttributeWritableArrayData<uint8_t*>(
                        db.abi_node(), "outputs:" + messageField.name, data.size());
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(uint8_t));
                }
                else
                {
                    auto outputValue = getAttributeWritableData<uint8_t>(db.abi_node(), "outputs:" + messageField.name);
                    *outputValue = *std::static_pointer_cast<const uint8_t>(messageData.at(i));
                }
                break;
            }
            case omni::fabric::BaseDataType::eInt:
            {
                if (messageField.isArray)
                {
                    auto data = *std::static_pointer_cast<const std::vector<int32_t>>(messageData.at(i));
                    auto outputValue = getAttributeWritableArrayData<int32_t*>(
                        db.abi_node(), "outputs:" + messageField.name, data.size());
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(int32_t));
                }
                else
                {
                    auto outputValue = getAttributeWritableData<int32_t>(db.abi_node(), "outputs:" + messageField.name);
                    *outputValue = *std::static_pointer_cast<const int32_t>(messageData.at(i));
                }
                break;
            }
            case omni::fabric::BaseDataType::eUInt:
            {
                if (messageField.isArray)
                {
                    auto data = *std::static_pointer_cast<const std::vector<uint32_t>>(messageData.at(i));
                    auto outputValue = getAttributeWritableArrayData<uint32_t*>(
                        db.abi_node(), "outputs:" + messageField.name, data.size());
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(uint32_t));
                }
                else
                {
                    auto outputValue = getAttributeWritableData<uint32_t>(db.abi_node(), "outputs:" + messageField.name);
                    *outputValue = *std::static_pointer_cast<const uint32_t>(messageData.at(i));
                }
                break;
            }
            case omni::fabric::BaseDataType::eInt64:
            {
                if (messageField.isArray)
                {
                    auto data = *std::static_pointer_cast<const std::vector<int64_t>>(messageData.at(i));
                    auto outputValue = getAttributeWritableArrayData<int64_t*>(
                        db.abi_node(), "outputs:" + messageField.name, data.size());
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(int64_t));
                }
                else
                {
                    auto outputValue = getAttributeWritableData<int64_t>(db.abi_node(), "outputs:" + messageField.name);
                    *outputValue = *std::static_pointer_cast<const int64_t>(messageData.at(i));
                }
                break;
            }
            case omni::fabric::BaseDataType::eUInt64:
            {
                if (messageField.isArray)
                {
                    auto data = *std::static_pointer_cast<const std::vector<uint64_t>>(messageData.at(i));
                    auto outputValue = getAttributeWritableArrayData<uint64_t*>(
                        db.abi_node(), "outputs:" + messageField.name, data.size());
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(uint64_t));
                }
                else
                {
                    auto outputValue = getAttributeWritableData<uint64_t>(db.abi_node(), "outputs:" + messageField.name);
                    *outputValue = *std::static_pointer_cast<const uint64_t>(messageData.at(i));
                }
                break;
            }
            case omni::fabric::BaseDataType::eHalf:
            {
                // no half-precision floating point number in types for ROS message fields
                break;
            }
            case omni::fabric::BaseDataType::eFloat:
            {
                if (messageField.isArray)
                {
                    auto data = *std::static_pointer_cast<const std::vector<float>>(messageData.at(i));
                    auto outputValue = getAttributeWritableArrayData<float*>(
                        db.abi_node(), "outputs:" + messageField.name, data.size());
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(float));
                }
                else
                {
                    auto outputValue = getAttributeWritableData<float>(db.abi_node(), "outputs:" + messageField.name);
                    *outputValue = *std::static_pointer_cast<const float>(messageData.at(i));
                }
                break;
            }
            case omni::fabric::BaseDataType::eDouble:
            {
                if (messageField.isArray)
                {
                    auto data = *std::static_pointer_cast<const std::vector<double>>(messageData.at(i));
                    auto outputValue = getAttributeWritableArrayData<double*>(
                        db.abi_node(), "outputs:" + messageField.name, data.size());
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(double));
                }
                else
                {
                    auto outputValue = getAttributeWritableData<double>(db.abi_node(), "outputs:" + messageField.name);
                    *outputValue = *std::static_pointer_cast<const double>(messageData.at(i));
                }
                break;
            }
            case omni::fabric::BaseDataType::eToken:
            {
                if (messageField.isArray)
                {
                    auto stringValues = *std::static_pointer_cast<const std::vector<std::string>>(messageData.at(i));
                    auto outputValue = getAttributeWritableArrayData<NameToken*>(
                        db.abi_node(), "outputs:" + messageField.name, stringValues.size());
                    for (size_t j = 0; j < stringValues.size(); ++j)
                        *((*outputValue) + j) = db.stringToToken(stringValues.at(j).c_str());
                }
                else
                {
                    auto stringValue = *std::static_pointer_cast<const std::string>(messageData.at(i));
                    auto outputValue = getAttributeWritableData<NameToken>(db.abi_node(), "outputs:" + messageField.name);
                    *outputValue = db.stringToToken(stringValue.c_str());
                }
                break;
            }
            case omni::fabric::BaseDataType::eUnknown:
            {
                if (messageField.isArray)
                {
                    auto array = *std::static_pointer_cast<const std::vector<nlohmann::json>>(messageData.at(i));
                    auto outputValue = getAttributeWritableArrayData<NameToken*>(
                        db.abi_node(), "outputs:" + messageField.name, array.size());
                    for (size_t j = 0; j < array.size(); ++j)
                        *((*outputValue) + j) = db.stringToToken(array.at(j).dump().c_str());
                }
                break;
            }
            default:
                break;
            }
        }

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    NodeObj mNodeObj;
    bool mIsSubscriberUpdateNeeded = false;
    bool mIsMessageUpdateNeeded = false;

    std::shared_ptr<Ros2Subscriber> mSubscriber = nullptr;
    std::shared_ptr<Ros2Message> mMessage = nullptr;

    std::string mMessagePackage;
    std::string mMessageSubfolder;
    std::string mMessageName;
    std::string mTopicName;
    uint64_t mQueueSize;

    // OGN utils

    static AttributeObj getAttributeObj(const NodeObj& nodeObj, const std::string& attrName)
    {
        AttributeObj attrObj = nodeObj.iNode->getAttribute(nodeObj, attrName.c_str());
        CARB_ASSERT(attrObj.isValid());
        return attrObj;
    }

    template <typename T>
    static T* getAttributeWritableData(const NodeObj& nodeObj, const std::string& attrName)
    {
        GraphObj graphObj = nodeObj.iNode->getGraph(nodeObj);
        GraphContextObj context = graphObj.iGraph->getDefaultGraphContext(graphObj);
        AttributeDataHandle handle =
            getAttributeW(context, nodeObj.nodeContextHandle, Token(attrName.c_str()), kAccordingToContextIndex);
        T* value = getDataW<T>(context, handle);
        return value;
    }

    template <typename T>
    static T* getAttributeWritableArrayData(const NodeObj& nodeObj, const std::string& attrName, size_t newCount)
    {
        GraphObj graphObj = nodeObj.iNode->getGraph(nodeObj);
        GraphContextObj context = graphObj.iGraph->getDefaultGraphContext(graphObj);
        AttributeDataHandle handle =
            getAttributeW(context, nodeObj.nodeContextHandle, Token(attrName.c_str()), kAccordingToContextIndex);
        // resize first
        context.iAttributeData->setElementCount(context, handle, newCount);
        // get writable data
        T* value = getDataW<T>(context, handle);
        return value;
    }

    static const char* getTokenText(AttributeObj const& attrObj)
    {
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        GraphObj graphObj = nodeObj.iNode->getGraph(nodeObj);
        GraphContextObj context = graphObj.iGraph->getDefaultGraphContext(graphObj);

        ConstAttributeDataHandle handle =
            attrObj.iAttribute->getConstAttributeDataHandle(attrObj, kAccordingToContextIndex);
        auto const token = getDataR<NameToken>(context, handle);
        return context.iToken->getText(*token);
    }

    static const char* getTokenText(const NodeObj& nodeObj, const std::string& attrName)
    {
        return getTokenText(getAttributeObj(nodeObj, attrName));
    }

    static const char* getTokenText(const NodeObj& nodeObj, const omni::graph::core::NameToken& token)
    {
        GraphObj graphObj = nodeObj.iNode->getGraph(nodeObj);
        GraphContextObj context = graphObj.iGraph->getDefaultGraphContext(graphObj);
        return context.iToken->getText(token);
    }

    static bool setAllowedTokens(const NodeObj& nodeObj,
                                 const std::string& attrName,
                                 const std::vector<std::string>& allowedTokens)
    {
        // OGN
        std::stringstream stream;
        copy(allowedTokens.begin(), allowedTokens.end(), std::ostream_iterator<std::string>(stream, ","));
        std::string ognAllowedTokens = stream.str();
        AttributeObj attrObj = getAttributeObj(nodeObj, attrName);
        attrObj.iAttribute->setMetadata(attrObj, kOgnMetadataAllowedTokens, ognAllowedTokens.c_str());
        // USD
        pxr::UsdStagePtr stage = omni::usd::UsdContext::getContext()->getStage();
        if (!stage)
            return false;
        const pxr::UsdPrim prim = stage->GetPrimAtPath(pxr::SdfPath(nodeObj.iNode->getPrimPath(nodeObj)));
        const pxr::UsdAttribute attr = prim.GetAttribute(pxr::TfToken(attrName));
        if (!attr.IsValid())
            return false;
        attr.SetMetadata(pxr::TfToken(kOgnMetadataAllowedTokens), allowedTokens);
        return true;
    }

    static bool removeDynamicAttributes(const NodeObj& nodeObj, AttributePortType portType)
    {
        // get node attributes
        auto attrCount = nodeObj.iNode->getAttributeCount(nodeObj);
        std::vector<AttributeObj> attrObjects(attrCount);
        nodeObj.iNode->getAttributes(nodeObj, attrObjects.data(), attrCount);
        // iterate and delete requested attributes
        bool status = true;
        for (auto const& attrObj : attrObjects)
            if (attrObj.iAttribute->isDynamic(attrObj))
                if (attrObj.iAttribute->getPortType(attrObj) == portType)
                {
                    // disconnect attribute if connected
                    if (attrObj.iAttribute->getDownstreamConnectionCount(attrObj))
                    {
                        ConnectionInfo connectionInfo;
                        attrObj.iAttribute->getDownstreamConnectionsInfo(attrObj, &connectionInfo, 1);
                        status = status && attrObj.iAttribute->disconnectAttrs(attrObj, connectionInfo.attrObj, true);
                    }
                    // remove attribute
                    char const* attrName = attrObj.iAttribute->getName(attrObj);
                    status = status && nodeObj.iNode->removeAttribute(nodeObj, attrName);
                }
        return status;
    }

    // node

    static bool createMessageAndAttributes(const NodeObj& nodeObj,
                                           const std::string& messagePackage,
                                           const std::string& messageSubfolder,
                                           const std::string& messageName)
    {
        auto db = OgnROS2SubscriberDatabase(nodeObj);
        auto& state = db.perInstanceState<OgnROS2Subscriber>();
        std::string messageType = messagePackage + "/" + messageSubfolder + "/" + messageName;
        // naive check on inputs
        if (messagePackage.empty() || messageSubfolder.empty() || messageName.empty())
            return false;
        // create message
        CARB_LOG_INFO("OgnROS2Subscriber: create message for %s", messageType.c_str());
        state.mMessage = state.mFactory->createDynamicMessage(messagePackage, messageSubfolder, messageName);
        auto messageFields = std::static_pointer_cast<Ros2DynamicMessage>(state.mMessage)->getMessageFields();
        bool status = std::static_pointer_cast<Ros2DynamicMessage>(state.mMessage)->isValid();
        if (!status)
        {
            db.logWarning((messageType + " does not exist or is not available in the ROS 2 environment").c_str());
            state.mMessage.reset();
            return false;
        }
        // check if existing dynamic attributes match the message
        if (checkForMatchingAttributes(nodeObj, messageFields))
        {
            CARB_LOG_INFO("OgnROS2Subscriber: reuse of existing dynamic attributes: %s", messageType.c_str());
            return true;
        }
        // remove dynamic attributes
        CARB_LOG_INFO("OgnROS2Subscriber: remove dynamic attributes: %s", messageType.c_str());
        status = removeDynamicAttributes(nodeObj, AttributePortType::kAttributePortType_Output);
        if (!status)
        {
            db.logWarning("Unable to remove existing attributes from the node");
            return false;
        }
        // create dynamic attributes
        CARB_LOG_INFO("OgnROS2Subscriber: create dynamic attributes: %s", messageType.c_str());
        for (auto const& messageField : messageFields)
        {
            CARB_LOG_INFO("OgnROS2Subscriber: |-- %s (OGN type name: %s, fabric type: %d, ROS type: %d)",
                          messageField.name.c_str(), messageField.ognType.c_str(),
                          static_cast<int>(messageField.dataType), messageField.rosType);
            status = status &&
                     nodeObj.iNode->createAttribute(nodeObj, ("outputs:" + messageField.name).c_str(),
                                                    db.typeFromName(db.stringToToken(messageField.ognType.c_str())),
                                                    nullptr, nullptr, AttributePortType::kAttributePortType_Output,
                                                    ExtendedAttributeType::kExtendedAttributeType_Regular, nullptr);
            if (!status)
            {
                db.logWarning(
                    ("Unable to create attribute " + messageField.name + " of type " + messageField.ognType).c_str());
                removeDynamicAttributes(nodeObj, AttributePortType::kAttributePortType_Output);
                return false;
            }
        }
        return status;
    }

    static bool checkForMatchingAttributes(const NodeObj& nodeObj, std::vector<MessageField> messageFields)
    {
        auto db = OgnROS2SubscriberDatabase(nodeObj);
        auto dynamicOutputs = db.getDynamicOutputs();
        // check for the number of attributes
        if (dynamicOutputs.size() != messageFields.size())
            return false;
        // check for attribute name and type
        for (auto const& dynamicOutput : dynamicOutputs)
        {
            bool status = false;
            for (auto const& messageField : messageFields)
                if (db.tokenToString(dynamicOutput().name()) == ("outputs:" + messageField.name))
                {
                    status = dynamicOutput().typeName() == messageField.ognType;
                    break;
                }
            if (!status)
                return false;
        }
        return true;
    }

    // node events

    static void onMessagePackageChanged(AttributeObj const& attrObj, void const* userData)
    {
        // get message package, subfolder and name
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        auto db = OgnROS2SubscriberDatabase(nodeObj);
        std::string messagePackage = std::string(db.inputs.messagePackage());
        std::string messageSubfolder = std::string(db.inputs.messageSubfolder());
        std::string messageName = std::string(db.inputs.messageName());
        // build message attributes
        createMessageAndAttributes(nodeObj, messagePackage, messageSubfolder, messageName);
    }

    static void onMessageSubfolderChanged(const AttributeObj& attrObj, void const* userData)
    {
        // get message package, subfolder and name
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        auto db = OgnROS2SubscriberDatabase(nodeObj);
        std::string messagePackage = std::string(db.inputs.messagePackage());
        std::string messageSubfolder = std::string(db.inputs.messageSubfolder());
        std::string messageName = std::string(db.inputs.messageName());
        // build message attributes
        createMessageAndAttributes(nodeObj, messagePackage, messageSubfolder, messageName);
    }

    static void onMessageNameChanged(const AttributeObj& attrObj, void const* userData)
    {
        // get message package, subfolder and name
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        auto db = OgnROS2SubscriberDatabase(nodeObj);
        std::string messagePackage = std::string(db.inputs.messagePackage());
        std::string messageSubfolder = std::string(db.inputs.messageSubfolder());
        std::string messageName = std::string(db.inputs.messageName());
        // build message attributes
        createMessageAndAttributes(nodeObj, messagePackage, messageSubfolder, messageName);
    }
};

REGISTER_OGN_NODE()
