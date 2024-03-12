// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "Ros2Foxy.h"

#include <carb/logging/Log.h>

#include <nlohmann/json.hpp>


Ros2DynamicMessageFoxy::Ros2DynamicMessageFoxy(std::string pkgName, std::string msgSubfolder, std::string msgName)
    : Ros2BackendFoxy(pkgName, msgSubfolder, msgName)
{
    // create message
    msg = create();
    // get message fields
    mMessagesFields.clear();
    void* typeSupportHandle = getTypeSupportIntrospectionHandleDynamic();
    if (typeSupportHandle)
    {
        auto members = static_cast<const rosidl_message_type_support_t*>(typeSupportHandle)->data;
        parseMessageFields("", members);
    }
}

Ros2DynamicMessageFoxy::~Ros2DynamicMessageFoxy()
{
    if (msg)
        destroy(static_cast<void*>(msg));
}

const void* Ros2DynamicMessageFoxy::getTypeSupportHandle()
{
    return getTypeSupportHandleDynamic();
}

void Ros2DynamicMessageFoxy::getData(std::vector<std::shared_ptr<const void>>& data, bool asOgnType)
{
    void* typeSupportHandle = getTypeSupportIntrospectionHandleDynamic();
    if (typeSupportHandle)
    {
        auto members = static_cast<const rosidl_message_type_support_t*>(typeSupportHandle)->data;
        parseMessageValues(members, reinterpret_cast<uint8_t*>(msg), data, asOgnType);
    }
}

void Ros2DynamicMessageFoxy::parseMessageFields(const std::string& parentName, const void* members)
{
    auto messageMembers = reinterpret_cast<const rosidl_typesupport_introspection_c__MessageMembers*>(members);
    for (size_t i = 0; i < messageMembers->member_count_; ++i)
    {
        const rosidl_typesupport_introspection_c__MessageMember* member = messageMembers->members_ + i;
        std::string name = (parentName.length() ? parentName + ":" : "") + member->name_;
        std::string type;
        omni::fabric::BaseDataType dataType = omni::fabric::BaseDataType::eUnknown;
        switch (member->type_id_)
        {
        case rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT:
            type = member->is_array_ ? "float[]" : "float";
            dataType = omni::fabric::BaseDataType::eFloat;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE:
            type = member->is_array_ ? "double[]" : "double";
            dataType = omni::fabric::BaseDataType::eDouble;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_LONG_DOUBLE:
            type = member->is_array_ ? "double[]" : "double";
            dataType = omni::fabric::BaseDataType::eDouble;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_CHAR:
            type = member->is_array_ ? "uchar[]" : "uchar";
            dataType = omni::fabric::BaseDataType::eUChar;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_WCHAR:
            type = member->is_array_ ? "uint[]" : "uint";
            dataType = omni::fabric::BaseDataType::eUInt;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN:
            type = member->is_array_ ? "bool[]" : "bool";
            dataType = omni::fabric::BaseDataType::eBool;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_OCTET:
            type = member->is_array_ ? "uchar[]" : "uchar";
            dataType = omni::fabric::BaseDataType::eUChar;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT8:
            type = member->is_array_ ? "uint[]" : "uint";
            dataType = omni::fabric::BaseDataType::eUInt;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT8:
            type = member->is_array_ ? "int[]" : "int";
            dataType = omni::fabric::BaseDataType::eInt;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT16:
            type = member->is_array_ ? "uint[]" : "uint";
            dataType = omni::fabric::BaseDataType::eUInt;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT16:
            type = member->is_array_ ? "int[]" : "int";
            dataType = omni::fabric::BaseDataType::eInt;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT32:
            type = member->is_array_ ? "uint[]" : "uint";
            dataType = omni::fabric::BaseDataType::eUInt;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT32:
            type = member->is_array_ ? "int[]" : "int";
            dataType = omni::fabric::BaseDataType::eInt;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT64:
            type = member->is_array_ ? "uint64[]" : "uint64";
            dataType = omni::fabric::BaseDataType::eUInt64;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT64:
            type = member->is_array_ ? "int64[]" : "int64";
            dataType = omni::fabric::BaseDataType::eInt64;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_STRING:
            type = member->is_array_ ? "token[]" : "token";
            dataType = omni::fabric::BaseDataType::eToken;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_WSTRING:
            type = member->is_array_ ? "token[]" : "token";
            dataType = omni::fabric::BaseDataType::eToken;
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE:
            if (member->is_array_)
            {
                type = "token[]";
                dataType = omni::fabric::BaseDataType::eToken;
                break;
            }
            // unroll only if not an array
            parseMessageFields(name, member->members_->data);
            continue;
        default:
            break;
        }
        mMessagesFields.push_back({ name, member->type_id_, member->is_array_, type, dataType });
    }
}

template <typename ArrayType, typename RosType, typename OgnType>
std::shared_ptr<const void> Ros2DynamicMessageFoxy::getArray(
    const rosidl_typesupport_introspection_c__MessageMember* member, uint8_t* data, bool asOgnType)
{
    // OGN data type array
    if (asOgnType)
    {
        auto ognArray = std::make_shared<std::vector<OgnType>>();
        // non-fixed size array
        if (member->is_upper_bound_ || !member->array_size_)
        {
            const ArrayType* source = reinterpret_cast<const ArrayType*>(data);
            for (size_t i = 0; i < source->size; ++i)
            {
                auto sourceData = reinterpret_cast<const RosType*>(&source->data[i]);
                ognArray->push_back(static_cast<OgnType>(*sourceData));
            }
        }
        // fixed size array
        else
            for (size_t i = 0; i < member->array_size_; ++i)
            {
                auto sourceData = reinterpret_cast<const RosType*>(&data[i * sizeof(RosType)]);
                ognArray->push_back(static_cast<OgnType>(*sourceData));
            }
        return ognArray;
    }
    // ROS data type array
    auto rosArray = std::make_shared<std::vector<RosType>>();
    // non-fixed size array
    if (member->is_upper_bound_ || !member->array_size_)
    {
        const ArrayType* source = reinterpret_cast<const ArrayType*>(data);
        for (size_t i = 0; i < source->size; ++i)
        {
            const uint8_t* sourceData = reinterpret_cast<const uint8_t*>(&source->data[i]);
            rosArray->push_back(*reinterpret_cast<const RosType*>(sourceData));
        }
    }
    // fixed size array
    else
        for (size_t i = 0; i < member->array_size_; ++i)
            rosArray->push_back(*reinterpret_cast<const RosType*>(&data[i * sizeof(RosType)]));
    return rosArray;
}

template <typename RosType, typename OgnType>
std::shared_ptr<const void> Ros2DynamicMessageFoxy::getSingleValue(uint8_t* data, bool asOgnType)
{
    auto value = reinterpret_cast<const RosType*>(data);
    if (asOgnType)
        return std::make_shared<OgnType>(static_cast<OgnType>(*value));
    return std::make_shared<RosType>(*value);
}


void Ros2DynamicMessageFoxy::messageValuesToJson(const void* members,
                                                 uint8_t* messageData,
                                                 const std::shared_ptr<std::vector<std::string>> messageValues)
{
    nlohmann::json jsonObj;
    auto messageMembers = reinterpret_cast<const rosidl_typesupport_introspection_c__MessageMembers*>(members);
    for (size_t i = 0; i < messageMembers->member_count_; ++i)
    {
        const rosidl_typesupport_introspection_c__MessageMember* member = messageMembers->members_ + i;
        auto data = &messageData[member->offset_];
        switch (member->type_id_)
        {
        case rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<float>>(
                    getArray<rosidl_runtime_c__float__Sequence, float, float>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const float*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<double>>(
                    getArray<rosidl_runtime_c__double__Sequence, double, double>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const double*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_LONG_DOUBLE:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<long double>>(
                    getArray<rosidl_runtime_c__long_double__Sequence, long double, long double>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const long double*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_CHAR:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<uint8_t>>(
                    getArray<rosidl_runtime_c__char__Sequence, uint8_t, uint8_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const uint8_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_WCHAR:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<uint16_t>>(
                    getArray<rosidl_runtime_c__wchar__Sequence, uint16_t, uint16_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const uint16_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<bool>>(
                    getArray<rosidl_runtime_c__boolean__Sequence, bool, bool>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const bool*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_OCTET:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<uint8_t>>(
                    getArray<rosidl_runtime_c__octet__Sequence, uint8_t, uint8_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const uint8_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT8:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<uint8_t>>(
                    getArray<rosidl_runtime_c__uint8__Sequence, uint8_t, uint8_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const uint8_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT8:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<int8_t>>(
                    getArray<rosidl_runtime_c__int8__Sequence, int8_t, int8_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const int8_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT16:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<uint16_t>>(
                    getArray<rosidl_runtime_c__uint16__Sequence, uint16_t, uint16_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const uint16_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT16:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<int16_t>>(
                    getArray<rosidl_runtime_c__int16__Sequence, int16_t, int16_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const int16_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT32:
        {
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<uint32_t>>(
                    getArray<rosidl_runtime_c__uint32__Sequence, uint32_t, uint32_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const uint32_t*>(data);
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT32:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<int32_t>>(
                    getArray<rosidl_runtime_c__int32__Sequence, int32_t, int32_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const int32_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT64:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<uint64_t>>(
                    getArray<rosidl_runtime_c__uint64__Sequence, uint64_t, uint64_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const uint64_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT64:
            if (member->is_array_)
                jsonObj[member->name_] = *std::static_pointer_cast<const std::vector<int64_t>>(
                    getArray<rosidl_runtime_c__int64__Sequence, int64_t, int64_t>(member, data, false));
            else
                jsonObj[member->name_] = *reinterpret_cast<const int64_t*>(data);
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_STRING:
        {
            if (member->is_array_)
            {
                auto value =
                    getArray<rosidl_runtime_c__String__Sequence, rosidl_runtime_c__String, rosidl_runtime_c__String>(
                        member, data, false);
                std::vector<std::string> stringValue;
                for (auto const& v : *std::static_pointer_cast<const std::vector<rosidl_runtime_c__String>>(value))
                    stringValue.push_back(std::string(v.data));
                jsonObj[member->name_] = stringValue;
            }
            else
                jsonObj[member->name_] = std::string(reinterpret_cast<const rosidl_runtime_c__String*>(data)->data);
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_WSTRING:
            // TODO: proccess WSTRING (no messages with 'path:*/msgs/*.msg "wstring"')
            jsonObj[member->name_] = std::string();
            break;
        case rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE:
        {
            if (member->is_array_)
            {
                auto stringValue = std::make_shared<std::vector<std::string>>();
                embeddedMessageArrayToJson(member, data, stringValue);
                jsonObj[member->name_] = *stringValue;
            }
            else
            {
                auto embeddedMessageContainer = std::make_shared<std::vector<std::string>>();
                messageValuesToJson(member->members_->data, data, embeddedMessageContainer);
                jsonObj[member->name_] = embeddedMessageContainer->at(0);
            }
            break;
        }
        default:
            break;
        }
    }
    messageValues->push_back(jsonObj.dump());
}

void Ros2DynamicMessageFoxy::embeddedMessageArrayToJson(const rosidl_typesupport_introspection_c__MessageMember* member,
                                                        uint8_t* data,
                                                        const std::shared_ptr<std::vector<std::string>> messageValues)
{
    // non-fixed size array
    if (member->is_upper_bound_ || !member->array_size_)
    {
        uint8_t* memberData;
        memcpy(&memberData, data, sizeof(void*));
        size_t memberCount = static_cast<size_t>(data[sizeof(void*)]);
        auto embeddedMembers =
            reinterpret_cast<const rosidl_typesupport_introspection_c__MessageMembers*>(member->members_->data);
        for (size_t i = 0; i < memberCount; ++i)
        {
            auto embeddedData = memberData + i * embeddedMembers->size_of_;
            messageValuesToJson(embeddedMembers, embeddedData, messageValues);
        }
    }
    // fixed size array
    else
    {
        auto embeddedMembers =
            reinterpret_cast<const rosidl_typesupport_introspection_c__MessageMembers*>(member->members_->data);
        for (size_t i = 0; i < member->array_size_; ++i)
            messageValuesToJson(embeddedMembers, &data[i * embeddedMembers->size_of_], messageValues);
    }
}


void Ros2DynamicMessageFoxy::parseMessageValues(const void* members,
                                                uint8_t* messageData,
                                                std::vector<std::shared_ptr<const void>>& messageValues,
                                                bool asOgnType)
{
    auto messageMembers = reinterpret_cast<const rosidl_typesupport_introspection_c__MessageMembers*>(members);
    for (size_t i = 0; i < messageMembers->member_count_; ++i)
    {
        const rosidl_typesupport_introspection_c__MessageMember* member = messageMembers->members_ + i;
        auto data = &messageData[member->offset_];
        switch (member->type_id_)
        {
        case rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT:
        {
            if (member->is_array_)
                messageValues.push_back(getArray<rosidl_runtime_c__float__Sequence, float, float>(member, data, false));
            else
                messageValues.push_back(getSingleValue<float, float>(data, false));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE:
        {
            if (member->is_array_)
                messageValues.push_back(getArray<rosidl_runtime_c__double__Sequence, double, double>(member, data, false));
            else
                messageValues.push_back(getSingleValue<double, double>(data, false));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_LONG_DOUBLE:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__long_double__Sequence, long double, double>(member, data, asOgnType));
            else
                messageValues.push_back(getSingleValue<long double, double>(data, asOgnType));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_CHAR:
        {
            if (member->is_array_)
                messageValues.push_back(getArray<rosidl_runtime_c__char__Sequence, uint8_t, uint8_t>(member, data, false));
            else
                messageValues.push_back(getSingleValue<uint8_t, uint8_t>(data, false));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_WCHAR:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__wchar__Sequence, uint16_t, uint32_t>(member, data, asOgnType));
            else
                messageValues.push_back(getSingleValue<uint16_t, uint32_t>(data, asOgnType));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN:
        {
            if (member->is_array_)
                messageValues.push_back(getArray<rosidl_runtime_c__boolean__Sequence, bool, bool>(member, data, false));
            else
                messageValues.push_back(getSingleValue<bool, bool>(data, false));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_OCTET:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__octet__Sequence, uint8_t, uint8_t>(member, data, false));
            else
                messageValues.push_back(getSingleValue<uint8_t, uint8_t>(data, false));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT8:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__uint8__Sequence, uint8_t, uint32_t>(member, data, asOgnType));
            else
                messageValues.push_back(getSingleValue<uint8_t, uint32_t>(data, asOgnType));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT8:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__int8__Sequence, int8_t, int32_t>(member, data, asOgnType));
            else
                messageValues.push_back(getSingleValue<int8_t, int32_t>(data, asOgnType));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT16:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__uint16__Sequence, uint16_t, uint32_t>(member, data, asOgnType));
            else
                messageValues.push_back(getSingleValue<uint16_t, uint32_t>(data, asOgnType));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT16:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__int16__Sequence, int16_t, int32_t>(member, data, asOgnType));
            else
                messageValues.push_back(getSingleValue<int16_t, int32_t>(data, asOgnType));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT32:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__uint32__Sequence, uint32_t, uint32_t>(member, data, false));
            else
                messageValues.push_back(getSingleValue<uint32_t, uint32_t>(data, false));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT32:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__int32__Sequence, int32_t, int32_t>(member, data, false));
            else
                messageValues.push_back(getSingleValue<int32_t, int32_t>(data, false));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_UINT64:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__uint64__Sequence, uint64_t, uint64_t>(member, data, false));
            else
                messageValues.push_back(getSingleValue<uint64_t, uint64_t>(data, false));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_INT64:
        {
            if (member->is_array_)
                messageValues.push_back(
                    getArray<rosidl_runtime_c__int64__Sequence, int64_t, int64_t>(member, data, false));
            else
                messageValues.push_back(getSingleValue<int64_t, int64_t>(data, false));
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_STRING:
        {
            if (member->is_array_)
            {
                auto value =
                    getArray<rosidl_runtime_c__String__Sequence, rosidl_runtime_c__String, rosidl_runtime_c__String>(
                        member, data, false);
                auto stringValue = std::make_shared<std::vector<std::string>>();
                for (auto const& v : *(std::static_pointer_cast<const std::vector<rosidl_runtime_c__String>>(value)))
                    stringValue->push_back(std::string(v.data));
                messageValues.push_back(stringValue);
            }
            else
            {
                auto value = reinterpret_cast<const rosidl_runtime_c__String*>(data);
                messageValues.push_back(std::make_shared<std::string>(std::string(value->data)));
            }
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_WSTRING:
        {
            // TODO: proccess WSTRING (no messages with 'path:*/msgs/*.msg "wstring"')
            if (member->is_array_)
            {
                auto stringValue = std::make_shared<std::vector<std::string>>();
                messageValues.push_back(stringValue);
            }
            else
            {
                messageValues.push_back(std::make_shared<std::string>());
            }
            break;
        }
        case rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE:
        {
            if (member->is_array_)
            {
                auto stringValue = std::make_shared<std::vector<std::string>>();
                embeddedMessageArrayToJson(member, data, stringValue);
                messageValues.push_back(stringValue);
            }
            else
            {
                parseMessageValues(member->members_->data, data, messageValues, asOgnType);
                continue;
            }
            break;
        }
        default:
            break;
        }
    }
}
