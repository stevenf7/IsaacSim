// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/tokens/TokensUtils.h>

#include <include/Ros2Node.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/graph/core/OgnHelpers.h>
#include <omni/graph/core/Type.h>
#include <omni/graph/core/ogn/ArrayAttribute.h>
#include <omni/graph/core/ogn/SimpleAttribute.h>
#include <omni/isaac/utils/Math.h>

using omni::graph::core::ogn::OmniGraphDatabase;

namespace OgnDynamicMesssageUtils
{

inline std::string InputOutput(bool isOutput)
{
    return isOutput ? "outputs" : "inputs";
};

inline bool checkCondition(const void* val, std::string message)
{
    if (!val)
        CARB_LOG_ERROR("%s %p", message.c_str(), val);
    return val;
}

template <typename T>
inline T* getAttributeWritableData(const NodeObj& nodeObj, const std::string& attrName)
{
    GraphObj graphObj = nodeObj.iNode->getGraph(nodeObj);
    GraphContextObj context = graphObj.iGraph->getDefaultGraphContext(graphObj);
    AttributeDataHandle handle =
        getAttributeW(context, nodeObj.nodeContextHandle, Token(attrName.c_str()), kAccordingToContextIndex);
    T* value = getDataW<T>(context, handle);
    return value;
}

template <typename T>
inline T* getAttributeWritableArrayData(const NodeObj& nodeObj, const std::string& attrName, size_t newCount)
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


template <typename T>
inline T const* getAttributeReadableData(const NodeObj& nodeObj, const std::string& attrName)
{
    GraphObj graphObj = nodeObj.iNode->getGraph(nodeObj);
    GraphContextObj context = graphObj.iGraph->getDefaultGraphContext(graphObj);
    const ConstAttributeDataHandle handle =
        getAttributeR(context, nodeObj.nodeContextHandle, Token(attrName.c_str()), kAccordingToContextIndex);
    T const* value = getDataR<T>(context, handle);
    return value;
}

template <typename T>
inline T const* getAttributeReadableArrayData(const NodeObj& nodeObj, const std::string& attrName, size_t& newCount)
{
    GraphObj graphObj = nodeObj.iNode->getGraph(nodeObj);
    GraphContextObj context = graphObj.iGraph->getDefaultGraphContext(graphObj);
    const ConstAttributeDataHandle const_handle =
        getAttributeR(context, nodeObj.nodeContextHandle, Token(attrName.c_str()), kAccordingToContextIndex);
    context.iAttributeData->getElementCount(&newCount, context, &const_handle, 1);
    T const* value = getDataR<T>(context, const_handle);
    return value;
}


template <bool removeInputs = false, bool removeOutputs = false>
inline bool removeDynamicAttributes(const NodeObj& nodeObj)
{
    // get node attributes
    auto attrCount = nodeObj.iNode->getAttributeCount(nodeObj);
    std::vector<AttributeObj> attrObjects(attrCount);
    nodeObj.iNode->getAttributes(nodeObj, attrObjects.data(), attrCount);
    // iterate and delete requested attributes
    bool status = true;
    for (auto const& attrObj : attrObjects)
    {
        char const* attrName = attrObj.iAttribute->getName(attrObj);
        if (attrObj.iAttribute->isDynamic(attrObj))
        {
            if (attrObj.iAttribute->getPortType(attrObj) == AttributePortType::kAttributePortType_Output && removeOutputs)
            {
                // disconnect attribute if connected
                if (attrObj.iAttribute->getDownstreamConnectionCount(attrObj))
                {
                    ConnectionInfo connectionInfo;
                    attrObj.iAttribute->getDownstreamConnectionsInfo(attrObj, &connectionInfo, 1);
                    status = status && attrObj.iAttribute->disconnectAttrs(attrObj, connectionInfo.attrObj, true);
                }
                // remove attribute
                status = status && nodeObj.iNode->removeAttribute(nodeObj, attrName);
            }
            else if (attrObj.iAttribute->getPortType(attrObj) == AttributePortType::kAttributePortType_Input &&
                     removeInputs)
            {
                // disconnect attribute if connected
                if (attrObj.iAttribute->getUpstreamConnectionCount(attrObj))
                {
                    ConnectionInfo connectionInfo;
                    attrObj.iAttribute->getUpstreamConnectionsInfo(attrObj, &connectionInfo, 1);
                    status = status && attrObj.iAttribute->disconnectAttrs(connectionInfo.attrObj, attrObj, true);
                    // status = status && attrObj.iAttribute->disconnectAttrs(attrObj, connectionInfo.attrObj, true);
                }
                // remove attribute
                status = status && nodeObj.iNode->removeAttribute(nodeObj, attrName);
            }
        }
    }
    return status;
}

template <class OgnROS2DatabaseDerivedType, bool isOutput, bool clearExistingAttrs>
inline bool findMatchingAttribute(OgnROS2DatabaseDerivedType& db,
                                  const NodeObj& nodeObj,
                                  std::vector<MessageField> messageFields,
                                  const std::string prependStr)
{
    if (isOutput)
    {
        auto dynamicAttributes = db.getDynamicOutputs();
        if (dynamicAttributes.size() != messageFields.size() && clearExistingAttrs)
            return false;
        // check for attribute name and type
        for (auto const& messageField : messageFields)
        {
            bool status = false;
            for (auto const& attribute : dynamicAttributes)
            {
                if (db.tokenToString(attribute().name()) == (InputOutput(isOutput) + ":" + prependStr + messageField.name))
                {
                    status = attribute().typeName() == messageField.ognType;
                    break;
                }
            }
            if (!status)
                return false;
        }
    }
    else
    {
        auto dynamicAttributes = db.getDynamicInputs();
        if (dynamicAttributes.size() != messageFields.size() && clearExistingAttrs)
            return false;
        // check for attribute name and type
        for (auto const& messageField : messageFields)
        {
            bool status = false;
            for (auto const& attribute : dynamicAttributes)
                if (db.tokenToString(attribute().name()) == (InputOutput(isOutput) + ":" + prependStr + messageField.name))
                {
                    status = attribute().typeName() == messageField.ognType;
                    break;
                }
            if (!status)
                return false;
        }
    }
    return true;
}

template <typename OgnROS2DatabaseDerivedType, bool isOutput, bool clearExistingAttrs>
inline bool createOgAttributesForFields(OgnROS2DatabaseDerivedType& db,
                                        const NodeObj& nodeObj,
                                        std::vector<MessageField> messageFields,
                                        const std::string prependStr,
                                        std::string messageType)
{
    // return if all message fields have a corresponding OGN attribute
    if (findMatchingAttribute<OgnROS2DatabaseDerivedType, isOutput, clearExistingAttrs>(
            db, nodeObj, messageFields, prependStr))
    {
        // CARB_LOG_WARN("OgnDynamicMesssageUtils reuse of all existing %s dynamic attribute for package %s",
        //               InputOutput(isOutput).c_str(), messageType.c_str());
        return true;
    }

    if (clearExistingAttrs)
    {
        db.logWarning("removing existing %s attributes ", InputOutput(isOutput).c_str());
        // remove existing dynamic attributes and add new ones based the message fields
        bool status = removeDynamicAttributes<!isOutput, isOutput>(nodeObj);
        if (!status)
        {
            db.logWarning("Unable to remove existing attributes from the node");
            return false;
        }
    }

    auto attrFlag = isOutput ? AttributePortType::kAttributePortType_Output : AttributePortType::kAttributePortType_Input;
    for (auto const& messageField : messageFields)
    {
        // CARB_LOG_ERROR("OgnDynamicMesssageUtils: |-- %s (OGN %s type name: %s, fabric type: %d, ROS type: %d)",
        //                InputOutput(isOutput).c_str(), messageField.name.c_str(), messageField.ognType.c_str(),
        //                static_cast<int>(messageField.dataType), messageField.rosType);
        bool status = nodeObj.iNode->createAttribute(
            nodeObj, (InputOutput(isOutput) + ":" + prependStr + messageField.name).c_str(),
            db.typeFromName(db.stringToToken(messageField.ognType.c_str())), nullptr, nullptr, attrFlag,
            ExtendedAttributeType::kExtendedAttributeType_Regular, nullptr);
        if (!status)
        {
            CARB_LOG_ERROR(
                ("Unable to create attribute " + messageField.name + " of type " + messageField.ognType).c_str());
            removeDynamicAttributes<!isOutput && clearExistingAttrs, isOutput && clearExistingAttrs>(nodeObj);
            return false;
        }
    }
    return true;
}

template <typename OgnROS2DatabaseDerivedType, bool isOutput, bool clearExistingAttrs = true>
inline bool createOgAttributesForMessage(OgnROS2DatabaseDerivedType& db,
                                         const NodeObj& nodeObj,
                                         const std::string& messagePackage,
                                         const std::string& messageSubfolder,
                                         const std::string& MessageName,
                                         std::shared_ptr<Ros2Message> message,
                                         const std::string prependStr)
{
    std::string messageType = messagePackage + "/" + messageSubfolder + "/" + MessageName;
    // naive check on inputs
    if (messagePackage.empty() || messageSubfolder.empty() || MessageName.empty())
        return false;
    // create message

    auto messageFields = std::static_pointer_cast<Ros2DynamicMessage>(message)->getMessageFields();
    bool status = std::static_pointer_cast<Ros2DynamicMessage>(message)->isValid();
    if (!status)
    {
        CARB_LOG_ERROR((messageType + " does not exist or is not available in the ROS 2 environment").c_str());
        message.reset();
        return false;
    }

    return createOgAttributesForFields<OgnROS2DatabaseDerivedType, isOutput, clearExistingAttrs>(
        db, nodeObj, messageFields, prependStr, messageType);
}

// write OGN attribute data to message data
inline bool writeMessageDataFromNode(OmniGraphDatabase& db,
                                     std::shared_ptr<Ros2Message> message,
                                     std::string prependStr,
                                     bool isOutput)
{
    // CARB_LOG_WARN("Server: Filling Response ...");
    auto messageFields = std::static_pointer_cast<Ros2DynamicMessage>(message)->getMessageFields();
    std::vector<std::shared_ptr<void>> messageData;
    for (size_t i = 0; i < messageFields.size(); ++i)
    {
        auto messageField = messageFields.at(i);
        switch (messageField.dataType)
        {
        case omni::fabric::BaseDataType::eBool:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<bool*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<bool> data(inputSize);
                if (checkCondition(inputValue, "unable to read bool array"))
                {
                    for (size_t j = 0; j < data.size(); ++j) // std::vector<bool> is a specialization that has no ::data
                        data[j] = *(*inputValue + j);
                }
                messageData.push_back(std::make_shared<std::vector<bool>>(data));
            }
            else
            {
                auto inputValue = getAttributeReadableData<bool>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(inputValue, "unable to read bool value"))
                    messageData.push_back(std::make_shared<bool>(inputValue ? *inputValue : false));
            }
            break;
        }
        case omni::fabric::BaseDataType::eUChar:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<uint8_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<uint8_t> data(inputSize);
                if (checkCondition(inputValue, "unable to read uchar array"))
                {
                    std::memcpy(data.data(), *inputValue, inputSize * sizeof(uint8_t));
                }
                messageData.push_back(std::make_shared<std::vector<uint8_t>>(data));
            }
            else
            {
                auto inputValue = getAttributeReadableData<uint8_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(inputValue, "unable to read uchar value"))
                    messageData.push_back(std::make_shared<uint8_t>(inputValue ? *inputValue : 0));
            }
            break;
        }
        case omni::fabric::BaseDataType::eInt:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<int32_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<int32_t> data(inputSize);
                if (checkCondition(inputValue, "unable to read int array"))
                {
                    std::memcpy(data.data(), *inputValue, inputSize * sizeof(int32_t));
                }
                messageData.push_back(std::make_shared<std::vector<int32_t>>(data));
            }
            else
            {
                auto inputValue = getAttributeReadableData<int32_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(inputValue, "unable to read int value"))
                    messageData.push_back(std::make_shared<int32_t>(inputValue ? *inputValue : 0));
            }
            break;
        }
        case omni::fabric::BaseDataType::eUInt:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<uint32_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<uint32_t> data(inputSize);
                if (checkCondition(inputValue, "unable to read uint array"))
                {
                    std::memcpy(data.data(), *inputValue, inputSize * sizeof(uint32_t));
                }
                messageData.push_back(std::make_shared<std::vector<uint32_t>>(data));
            }
            else
            {
                auto inputValue = getAttributeReadableData<uint32_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(inputValue, "unable to read uint value"))
                    messageData.push_back(std::make_shared<uint32_t>(inputValue ? *inputValue : 0));
            }
            break;
        }
        case omni::fabric::BaseDataType::eInt64:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<int64_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<int64_t> data(inputSize);
                if (checkCondition(inputValue, "unable to read int64 array"))
                {
                    std::memcpy(data.data(), *inputValue, inputSize * sizeof(int64_t));
                }
                messageData.push_back(std::make_shared<std::vector<int64_t>>(data));
            }
            else
            {
                auto inputValue = getAttributeReadableData<int64_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(inputValue, "unable to read int64 value"))
                    messageData.push_back(std::make_shared<int64_t>(inputValue ? *inputValue : 0));
            }
            break;
        }
        case omni::fabric::BaseDataType::eUInt64:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<uint64_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<uint64_t> data(inputSize);
                if (checkCondition(inputValue, "unable to read uint64 array"))
                {
                    std::memcpy(data.data(), *inputValue, inputSize * sizeof(uint64_t));
                }
                messageData.push_back(std::make_shared<std::vector<uint64_t>>(data));
            }
            else
            {
                auto inputValue = getAttributeReadableData<uint64_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(inputValue, "unable to read uint64 value"))
                    messageData.push_back(std::make_shared<uint64_t>(inputValue ? *inputValue : 0));
            }
            break;
        }
        case omni::fabric::BaseDataType::eFloat:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<float*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<float> data(inputSize);
                if (checkCondition(inputValue, "unable to read float array"))
                {
                    std::memcpy(data.data(), *inputValue, inputSize * sizeof(float));
                }
                messageData.push_back(std::make_shared<std::vector<float>>(data));
            }
            else
            {
                auto inputValue = getAttributeReadableData<float>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(inputValue, "unable to read float value"))
                    messageData.push_back(std::make_shared<float>(inputValue ? *inputValue : 0.0));
            }
            break;
        }

        case omni::fabric::BaseDataType::eDouble:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<double*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<double> data(inputSize);
                if (checkCondition(inputValue, "unable to read double array"))
                {
                    std::memcpy(data.data(), *inputValue, inputSize * sizeof(double));
                }
                messageData.push_back(std::make_shared<std::vector<double>>(data));
            }
            else
            {
                auto inputValue = getAttributeReadableData<double>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(inputValue, "unable to read double value"))
                    messageData.push_back(std::make_shared<double>(inputValue ? *inputValue : 0.0));
            }
            break;
        }

        case omni::fabric::BaseDataType::eToken:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<NameToken*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<std::string> data(inputSize);
                if (checkCondition(inputValue, "unable to read token array"))
                {
                    for (size_t j = 0; j < data.size(); ++j)
                        data[j] = db.tokenToString(*(*inputValue + j));
                }
                messageData.push_back(std::make_shared<std::vector<std::string>>(data));
            }
            else
            {
                auto inputValue = getAttributeReadableData<NameToken>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                std::string str = inputValue ? db.tokenToString(*inputValue) : "";
                if (checkCondition(inputValue, "unable to read token value"))
                    messageData.push_back(std::make_shared<std::string>(str));
            }
            break;
        }
        case omni::fabric::BaseDataType::eUnknown:
        {
            if (messageField.isArray)
            {
                size_t inputSize;
                auto inputValue = getAttributeReadableArrayData<NameToken*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, inputSize);
                std::vector<nlohmann::json> data(inputSize);
                if (checkCondition(inputValue, "unable to read message array"))
                {
                    for (size_t j = 0; j < data.size(); ++j)
                        data[j] = db.tokenToString(*(*inputValue + j));
                }
                messageData.push_back(std::make_shared<std::vector<nlohmann::json>>(data));
            }
            break;
        }

        default:
        {
            CARB_LOG_ERROR("writeMessageDataFromNode data type %d didn't match any of the implemented type.",
                           int(messageField.dataType));
            return false;
            break;
        }
        }
    }

    std::static_pointer_cast<Ros2DynamicMessage>(message)->setData(messageData, true);
    return true;
}

// write message data to omnigraph node data
inline bool writeNodeAttributeFromMessage(OmniGraphDatabase& db,
                                          std::shared_ptr<Ros2Message> message,
                                          std::string prependStr,
                                          bool isOutput)
{
    // CARB_LOG_WARN("Server: Process Request ...");
    const std::vector<std::shared_ptr<void>> messageData =
        std::static_pointer_cast<Ros2DynamicMessage>(message)->getData(true);
    auto messageFields = std::static_pointer_cast<Ros2DynamicMessage>(message)->getMessageFields();
    CARB_ASSERT(messageFields.size() == messageData.size());

    for (size_t i = 0; i < messageFields.size(); ++i)
    {
        if (!messageData.at(i))
            continue;
        auto messageField = messageFields.at(i);
        // CARB_LOG_WARN("Server: Evaluating service request field %s", messageField.name.c_str());
        switch (messageField.dataType)
        {
        case omni::fabric::BaseDataType::eBool:
        {
            if (messageField.isArray)
            {
                auto data = *std::static_pointer_cast<std::vector<bool>>(messageData.at(i));
                auto outputValue = getAttributeWritableArrayData<bool*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, data.size());
                if (checkCondition(outputValue, "unable to write bool array"))
                    for (size_t j = 0; j < data.size(); ++j) // std::vector<bool> is a specialization that has no ::data
                        *((*outputValue) + j) = data.at(j);
            }
            else
            {
                auto outputValue = getAttributeWritableData<bool>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(outputValue, "unable to write bool value"))
                    *outputValue = *std::static_pointer_cast<bool>(messageData.at(i));
            }
            break;
        }
        case omni::fabric::BaseDataType::eUChar:
        {
            if (messageField.isArray)
            {

                auto data = *std::static_pointer_cast<std::vector<uint8_t>>(messageData.at(i));
                auto outputValue = getAttributeWritableArrayData<uint8_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, data.size());
                if (checkCondition(outputValue, "unable to write uchar array"))
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(uint8_t));
            }
            else
            {
                auto outputValue = getAttributeWritableData<uint8_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(outputValue, "unable to write uchar value"))
                    *outputValue = *std::static_pointer_cast<uint8_t>(messageData.at(i));
            }
            break;
        }
        case omni::fabric::BaseDataType::eInt:
        {
            if (messageField.isArray)
            {
                auto data = *std::static_pointer_cast<std::vector<int32_t>>(messageData.at(i));
                auto outputValue = getAttributeWritableArrayData<int32_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, data.size());
                if (checkCondition(outputValue, "unable to write int array"))
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(int32_t));
            }
            else
            {
                auto outputValue = getAttributeWritableData<int32_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(outputValue, "unable to write int value"))
                    *outputValue = *std::static_pointer_cast<int32_t>(messageData.at(i));
            }
            break;
        }
        case omni::fabric::BaseDataType::eUInt:
        {
            if (messageField.isArray)
            {
                auto data = *std::static_pointer_cast<std::vector<uint32_t>>(messageData.at(i));
                auto outputValue = getAttributeWritableArrayData<uint32_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, data.size());
                if (checkCondition(outputValue, "unable to write uint array"))
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(uint32_t));
            }
            else
            {
                auto outputValue = getAttributeWritableData<uint32_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(outputValue, "unable to write uint value"))
                    *outputValue = *std::static_pointer_cast<uint32_t>(messageData.at(i));
            }
            break;
        }
        case omni::fabric::BaseDataType::eInt64:
        {
            if (messageField.isArray)
            {
                auto data = *std::static_pointer_cast<std::vector<int64_t>>(messageData.at(i));
                auto outputValue = getAttributeWritableArrayData<int64_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, data.size());
                if (checkCondition(outputValue, "unable to write int64 array"))
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(int64_t));
            }
            else
            {
                auto outputValue = getAttributeWritableData<int64_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(outputValue, "unable to write int64 value"))
                    *outputValue = *std::static_pointer_cast<int64_t>(messageData.at(i));
            }
            break;
        }
        case omni::fabric::BaseDataType::eUInt64:
        {
            if (messageField.isArray)
            {
                auto data = *std::static_pointer_cast<std::vector<uint64_t>>(messageData.at(i));
                auto outputValue = getAttributeWritableArrayData<uint64_t*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, data.size());
                if (checkCondition(outputValue, "unable to write uint64 array"))
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(uint64_t));
            }
            else
            {
                auto outputValue = getAttributeWritableData<uint64_t>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(outputValue, "unable to write uint64 value"))
                    *outputValue = *std::static_pointer_cast<uint64_t>(messageData.at(i));
            }
            break;
        }
        case omni::fabric::BaseDataType::eFloat:
        {
            if (messageField.isArray)
            {
                auto data = *std::static_pointer_cast<std::vector<float>>(messageData.at(i));
                auto outputValue =
                    getAttributeWritableArrayData<float*>(db.abi_node(), "outputs:" + messageField.name, data.size());
                if (checkCondition(outputValue, "unable to write float array"))
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(float));
            }
            else
            {
                auto outputValue = getAttributeWritableData<float>(db.abi_node(), "outputs:" + messageField.name);
                if (checkCondition(outputValue, "unable to write float value"))
                    *outputValue = *std::static_pointer_cast<float>(messageData.at(i));
            }
            break;
        }
        case omni::fabric::BaseDataType::eDouble:
        {
            if (messageField.isArray)
            {

                auto data = *std::static_pointer_cast<std::vector<double>>(messageData.at(i));
                auto outputValue = getAttributeWritableArrayData<double*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, data.size());
                if (checkCondition(outputValue, "unable to write double array"))
                    std::memcpy(*outputValue, data.data(), data.size() * sizeof(double));
            }
            else
            {
                auto outputValue = getAttributeWritableData<double>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(outputValue, "unable to write double value"))
                    *outputValue = *std::static_pointer_cast<double>(messageData.at(i));
            }
            break;
        }
        case omni::fabric::BaseDataType::eToken:
        {
            if (messageField.isArray)
            {
                auto stringValues = *std::static_pointer_cast<std::vector<std::string>>(messageData.at(i));
                auto outputValue = getAttributeWritableArrayData<NameToken*>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name, stringValues.size());
                if (checkCondition(outputValue, "unable to write token array"))
                    for (size_t j = 0; j < stringValues.size(); ++j)
                        *((*outputValue) + j) = db.stringToToken(stringValues.at(j).c_str());
            }
            else
            {
                auto stringValue = *std::static_pointer_cast<std::string>(messageData.at(i));
                auto outputValue = getAttributeWritableData<NameToken>(
                    db.abi_node(), InputOutput(isOutput) + ":" + prependStr + messageField.name);
                if (checkCondition(outputValue, "unable to write token value"))
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
                if (checkCondition(outputValue, "unable to write message array"))
                    for (size_t j = 0; j < array.size(); ++j)
                        *((*outputValue) + j) = db.stringToToken(array.at(j).dump().c_str());
            }
            break;
        }
        default:
        {
            CARB_LOG_ERROR("writeNodeAttributeFromMessage data type %d didn't match any of the implemented type.",
                           int(messageField.dataType));
            return false;
            break;
        }
        }
    }
    return true;
}

}
