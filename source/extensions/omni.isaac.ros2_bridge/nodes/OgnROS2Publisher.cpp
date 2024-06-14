// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
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

#include <include/Ros2Node.h>

#include <OgnROS2PublisherDatabase.h>


class OgnROS2Publisher : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublisherDatabase::sPerInstanceState<OgnROS2Publisher>(nodeObj, instanceId);
        state.mNodeObj = nodeObj;

        // register change event for message type
        AttributeObj attrMessagePackageObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messagePackage");
        AttributeObj attrMessageSubfolderObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageSubfolder");
        AttributeObj attrMessageNameObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageName");
        attrMessagePackageObj.iAttribute->registerValueChangedCallback(attrMessagePackageObj, onMessageChanged, true);
        attrMessageSubfolderObj.iAttribute->registerValueChangedCallback(attrMessageSubfolderObj, onMessageChanged, true);
        attrMessageNameObj.iAttribute->registerValueChangedCallback(attrMessageNameObj, onMessageChanged, true);
    }

    static bool compute(OgnROS2PublisherDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2Publisher>();

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
            state.mIsPublisherUpdateNeeded = true;
            return false;
        }

        // check for changes in publisher
        std::string topicName = std::string(db.inputs.topicName());
        uint64_t queueSize = db.inputs.queueSize();
        std::string qosProfile = db.inputs.qosProfile();
        if (topicName != state.mTopicName)
        {
            state.mIsPublisherUpdateNeeded = true;
            state.mTopicName = topicName;
        }
        if (queueSize != state.mQueueSize)
        {
            state.mIsPublisherUpdateNeeded = true;
            state.mQueueSize = queueSize;
        }
        if (qosProfile != state.mQosProfile)
        {
            state.mIsPublisherUpdateNeeded = true;
            state.mQosProfile = qosProfile;
        }
        // update publisher
        if (state.mIsPublisherUpdateNeeded)
        {
            // destroy previous publisher
            state.mPublisher.reset();
            // get topic name
            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, state.mTopicName);
            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }
            // create publisher
            std::string messageType = messagePackage + "/" + messageSubfolder + "/" + messageName;
            CARB_LOG_INFO("OgnROS2Publisher: creating publisher: %s (%s)", fullTopicName.c_str(), messageType.c_str());
            Ros2QoSProfile qos;
            const std::string& qosProfile = db.inputs.qosProfile();
            if (qosProfile == "")
            {
                qos.depth = state.mQueueSize;
            }
            else
            {
                if (!jsonToRos2QoSProfile(qos, state.mQosProfile))
                {
                    return false;
                }
            }
            state.mPublisher = state.mFactory->CreatePublisher(
                state.mNodeHandle.get(), fullTopicName.c_str(), state.mMessage->getTypeSupportHandle(), qos);
            if (!state.mPublisher->isValid())
            {
                db.logWarning(
                    ("Invalid publication to the topic " + fullTopicName + " for the message type " + messageType).c_str());
                state.mPublisher.reset();
                return false;
            }
            state.mIsPublisherUpdateNeeded = false;
            return true;
        }

        return state.publisherCallback(db);
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublisherDatabase::sPerInstanceState<OgnROS2Publisher>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mIsPublisherUpdateNeeded = false;
        mIsMessageUpdateNeeded = false;

        mMessagePackage.clear();
        mMessageSubfolder.clear();
        mMessageName.clear();
        mTopicName.clear();
        mQosProfile.clear();
        mQueueSize = 0;

        mMessage.reset();
        mPublisher.reset(); // this should be reset before reset the handle

        Ros2Node::reset();
    }

    bool publisherCallback(OgnROS2PublisherDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2Publisher>();
        if (!state.mPublisher)
            return false;

        auto messageData = std::static_pointer_cast<Ros2DynamicMessage>(state.mMessage)->getVectorContainer(true);
        auto messageFields = std::static_pointer_cast<Ros2DynamicMessage>(state.mMessage)->getMessageFields();

        size_t arraySize;
        for (size_t i = 0; i < messageFields.size(); ++i)
        {
            auto messageField = messageFields.at(i);
            switch (messageField.dataType)
            {
            case omni::fabric::BaseDataType::eBool:
            {
                if (messageField.isArray)
                {
                    auto inputValue =
                        getAttributeReadableArrayData<bool*>(db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<bool>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    for (size_t j = 0; j < arraySize; ++j) // std::vector<bool> is a specialization that has no ::data
                        (*data)[j] = *((*inputValue) + j);
                }
                else
                {
                    auto inputValue = getAttributeReadableData<bool>(db.abi_node(), "inputs:" + messageField.name);
                    *std::static_pointer_cast<bool>(messageData[i]) = *inputValue;
                }
                break;
            }
            case omni::fabric::BaseDataType::eUChar:
            {
                if (messageField.isArray)
                {
                    auto inputValue =
                        getAttributeReadableArrayData<uint8_t*>(db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<uint8_t>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    std::memcpy(data->data(), *inputValue, arraySize * sizeof(uint8_t));
                }
                else
                {
                    auto inputValue = getAttributeReadableData<uint8_t>(db.abi_node(), "inputs:" + messageField.name);
                    *std::static_pointer_cast<uint8_t>(messageData[i]) = *inputValue;
                }
                break;
            }
            case omni::fabric::BaseDataType::eInt:
            {
                if (messageField.isArray)
                {
                    auto inputValue =
                        getAttributeReadableArrayData<int32_t*>(db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<int32_t>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    std::memcpy(data->data(), *inputValue, arraySize * sizeof(int32_t));
                }
                else
                {
                    auto inputValue = getAttributeReadableData<int32_t>(db.abi_node(), "inputs:" + messageField.name);
                    *std::static_pointer_cast<int32_t>(messageData[i]) = *inputValue;
                }
                break;
            }
            case omni::fabric::BaseDataType::eUInt:
            {
                if (messageField.isArray)
                {
                    auto inputValue = getAttributeReadableArrayData<uint32_t*>(
                        db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<uint32_t>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    std::memcpy(data->data(), *inputValue, arraySize * sizeof(uint32_t));
                }
                else
                {
                    auto inputValue = getAttributeReadableData<uint32_t>(db.abi_node(), "inputs:" + messageField.name);
                    *std::static_pointer_cast<uint32_t>(messageData[i]) = *inputValue;
                }
                break;
            }
            case omni::fabric::BaseDataType::eInt64:
            {
                if (messageField.isArray)
                {
                    auto inputValue =
                        getAttributeReadableArrayData<int64_t*>(db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<int64_t>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    std::memcpy(data->data(), *inputValue, arraySize * sizeof(int64_t));
                }
                else
                {
                    auto inputValue = getAttributeReadableData<int64_t>(db.abi_node(), "inputs:" + messageField.name);
                    *std::static_pointer_cast<int64_t>(messageData[i]) = *inputValue;
                }
                break;
            }
            case omni::fabric::BaseDataType::eUInt64:
            {
                if (messageField.isArray)
                {
                    auto inputValue = getAttributeReadableArrayData<uint64_t*>(
                        db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<uint64_t>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    std::memcpy(data->data(), *inputValue, arraySize * sizeof(uint64_t));
                }
                else
                {
                    auto inputValue = getAttributeReadableData<uint64_t>(db.abi_node(), "inputs:" + messageField.name);
                    *std::static_pointer_cast<uint64_t>(messageData[i]) = *inputValue;
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
                    auto inputValue =
                        getAttributeReadableArrayData<float*>(db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<float>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    std::memcpy(data->data(), *inputValue, arraySize * sizeof(float));
                }
                else
                {
                    auto inputValue = getAttributeReadableData<float>(db.abi_node(), "inputs:" + messageField.name);
                    *std::static_pointer_cast<float>(messageData[i]) = *inputValue;
                }
                break;
            }
            case omni::fabric::BaseDataType::eDouble:
            {
                if (messageField.isArray)
                {
                    auto inputValue =
                        getAttributeReadableArrayData<double*>(db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<double>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    std::memcpy(data->data(), *inputValue, arraySize * sizeof(double));
                }
                else
                {
                    auto inputValue = getAttributeReadableData<double>(db.abi_node(), "inputs:" + messageField.name);
                    *std::static_pointer_cast<double>(messageData[i]) = *inputValue;
                }
                break;
            }
            case omni::fabric::BaseDataType::eToken:
            {
                if (messageField.isArray)
                {
                    auto inputValue = getAttributeReadableArrayData<NameToken*>(
                        db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<std::string>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    for (size_t j = 0; j < arraySize; ++j)
                        (*data)[j] = db.tokenToString(*((*inputValue) + j));
                }
                else
                {
                    auto inputValue = getAttributeReadableData<NameToken>(db.abi_node(), "inputs:" + messageField.name);
                    *std::static_pointer_cast<std::string>(messageData[i]) = db.tokenToString(*inputValue);
                }
                break;
            }
            case omni::fabric::BaseDataType::eUnknown:
            {
                if (messageField.isArray)
                {
                    auto inputValue = getAttributeReadableArrayData<NameToken*>(
                        db.abi_node(), "inputs:" + messageField.name, arraySize);
                    auto data = std::static_pointer_cast<std::vector<nlohmann::json>>(messageData[i]);
                    data->clear();
                    data->resize(arraySize);
                    for (size_t j = 0; j < arraySize; ++j)
                        (*data)[j] = nlohmann::json::parse(db.tokenToString(*((*inputValue) + j)));
                }
                break;
            }
            default:
                break;
            }
        }

        std::static_pointer_cast<Ros2DynamicMessage>(state.mMessage)->setData(messageData, true);
        state.mPublisher->publish(state.mMessage->ptr());

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    NodeObj mNodeObj;
    bool mIsPublisherUpdateNeeded = false;
    bool mIsMessageUpdateNeeded = false;

    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2Message> mMessage = nullptr;

    std::string mMessagePackage;
    std::string mMessageSubfolder;
    std::string mMessageName;
    std::string mTopicName;
    uint64_t mQueueSize;
    std::string mQosProfile;

    // OGN utils

    static AttributeObj getAttributeObj(const NodeObj& nodeObj, const std::string& attrName)
    {
        AttributeObj attrObj = nodeObj.iNode->getAttribute(nodeObj, attrName.c_str());
        CARB_ASSERT(attrObj.isValid());
        return attrObj;
    }

    template <typename T>
    static const T* getAttributeReadableData(const NodeObj& nodeObj, const std::string& attrName)
    {
        GraphObj graphObj = nodeObj.iNode->getGraph(nodeObj);
        GraphContextObj context = graphObj.iGraph->getDefaultGraphContext(graphObj);
        ConstAttributeDataHandle handle =
            getAttributeR(context, nodeObj.nodeContextHandle, Token(attrName.c_str()), kAccordingToContextIndex);
        const T* value = getDataR<T>(context, handle);
        return value;
    }

    template <typename T>
    static T const* getAttributeReadableArrayData(const NodeObj& nodeObj, const std::string& attrName, size_t& countOut)
    {
        GraphObj graphObj = nodeObj.iNode->getGraph(nodeObj);
        GraphContextObj context = graphObj.iGraph->getDefaultGraphContext(graphObj);
        ConstAttributeDataHandle handle =
            getAttributeR(context, nodeObj.nodeContextHandle, Token(attrName.c_str()), kAccordingToContextIndex);
        // get size
        context.iAttributeData->getElementCount(&countOut, context, &handle, 1u);
        // get readable data
        T const* value = getDataR<T>(context, handle);
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
                    if (attrObj.iAttribute->getUpstreamConnectionCount(attrObj))
                    {
                        ConnectionInfo connectionInfo;
                        attrObj.iAttribute->getUpstreamConnectionsInfo(attrObj, &connectionInfo, 1);
                        status = status && attrObj.iAttribute->disconnectAttrs(connectionInfo.attrObj, attrObj, true);
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
        auto db = OgnROS2PublisherDatabase(nodeObj);
        auto& state = db.perInstanceState<OgnROS2Publisher>();
        std::string messageType = messagePackage + "/" + messageSubfolder + "/" + messageName;
        // naive check on inputs
        if (messagePackage.empty() || messageSubfolder.empty() || messageName.empty())
            return false;
        // create message
        CARB_LOG_INFO("OgnROS2Publisher: create message for %s", messageType.c_str());
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
            CARB_LOG_INFO("OgnROS2Publisher: reuse of existing dynamic attributes: %s", messageType.c_str());
            return true;
        }
        // remove dynamic attributes
        CARB_LOG_INFO("OgnROS2Publisher: remove dynamic attributes: %s", messageType.c_str());
        status = removeDynamicAttributes(nodeObj, AttributePortType::kAttributePortType_Input);
        if (!status)
        {
            db.logWarning("Unable to remove existing attributes from the node");
            return false;
        }
        // create dynamic attributes
        CARB_LOG_INFO("OgnROS2Publisher: create dynamic attributes: %s", messageType.c_str());
        for (auto const& messageField : messageFields)
        {
            CARB_LOG_INFO("OgnROS2Publisher: |-- %s (OGN type name: %s, fabric type: %d, ROS type: %d)",
                          messageField.name.c_str(), messageField.ognType.c_str(),
                          static_cast<int>(messageField.dataType), messageField.rosType);
            status = status &&
                     nodeObj.iNode->createAttribute(nodeObj, ("inputs:" + messageField.name).c_str(),
                                                    db.typeFromName(db.stringToToken(messageField.ognType.c_str())),
                                                    nullptr, nullptr, AttributePortType::kAttributePortType_Input,
                                                    ExtendedAttributeType::kExtendedAttributeType_Regular, nullptr);
            if (!status)
            {
                db.logWarning(
                    ("Unable to create attribute " + messageField.name + " of type " + messageField.ognType).c_str());
                removeDynamicAttributes(nodeObj, AttributePortType::kAttributePortType_Input);
                return false;
            }
        }
        return status;
    }

    static bool checkForMatchingAttributes(const NodeObj& nodeObj, std::vector<MessageField> messageFields)
    {
        auto db = OgnROS2PublisherDatabase(nodeObj);
        auto dynamicInputs = db.getDynamicInputs();
        // check for the number of attributes
        if (dynamicInputs.size() != messageFields.size())
            return false;
        // check for attribute name and type
        for (auto const& dynamicInput : dynamicInputs)
        {
            bool status = false;
            for (auto const& messageField : messageFields)
                if (db.tokenToString(dynamicInput().name()) == ("inputs:" + messageField.name))
                {
                    status = dynamicInput().typeName() == messageField.ognType;
                    break;
                }
            if (!status)
                return false;
        }
        return true;
    }

    // node events

    static void onMessageChanged(AttributeObj const& attrObj, void const* userData)
    {
        // get message package, subfolder and name
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        auto db = OgnROS2PublisherDatabase(nodeObj);
        std::string messagePackage = std::string(db.inputs.messagePackage());
        std::string messageSubfolder = std::string(db.inputs.messageSubfolder());
        std::string messageName = std::string(db.inputs.messageName());
        // build message attributes
        createMessageAndAttributes(nodeObj, messagePackage, messageSubfolder, messageName);
    }
};

REGISTER_OGN_NODE()
