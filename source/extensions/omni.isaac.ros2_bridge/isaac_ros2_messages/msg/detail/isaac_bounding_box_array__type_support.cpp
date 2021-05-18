// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBoxArray.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box_array__struct.hpp"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"
#include "string"
#include "vector"

namespace isaac_ros2_messages
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void IsaacBoundingBoxArray_init_function(void* message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
    new (message_memory) isaac_ros2_messages::msg::IsaacBoundingBoxArray(_init);
}

void IsaacBoundingBoxArray_fini_function(void* message_memory)
{
    auto typed_message = static_cast<isaac_ros2_messages::msg::IsaacBoundingBoxArray*>(message_memory);
    typed_message->~IsaacBoundingBoxArray();
}

size_t size_function__IsaacBoundingBoxArray__bboxes(const void* untyped_member)
{
    const auto* member = reinterpret_cast<const std::vector<isaac_ros2_messages::msg::IsaacBoundingBox>*>(untyped_member);
    return member->size();
}

const void* get_const_function__IsaacBoundingBoxArray__bboxes(const void* untyped_member, size_t index)
{
    const auto& member =
        *reinterpret_cast<const std::vector<isaac_ros2_messages::msg::IsaacBoundingBox>*>(untyped_member);
    return &member[index];
}

void* get_function__IsaacBoundingBoxArray__bboxes(void* untyped_member, size_t index)
{
    auto& member = *reinterpret_cast<std::vector<isaac_ros2_messages::msg::IsaacBoundingBox>*>(untyped_member);
    return &member[index];
}

void resize_function__IsaacBoundingBoxArray__bboxes(void* untyped_member, size_t size)
{
    auto* member = reinterpret_cast<std::vector<isaac_ros2_messages::msg::IsaacBoundingBox>*>(untyped_member);
    member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember IsaacBoundingBoxArray_message_member_array[2] = {
    {
        "header", // name
        ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE, // type
        0, // upper bound of string
        ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(), // members of
                                                                                                          // sub message
        false, // is array
        0, // array size
        false, // is upper bound
        offsetof(isaac_ros2_messages::msg::IsaacBoundingBoxArray, header), // bytes offset in struct
        nullptr, // default value
        nullptr, // size() function pointer
        nullptr, // get_const(index) function pointer
        nullptr, // get(index) function pointer
        nullptr // resize(index) function pointer
    },
    {
        "bboxes", // name
        ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE, // type
        0, // upper bound of string
        ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<
            isaac_ros2_messages::msg::IsaacBoundingBox>(), // members of sub message
        true, // is array
        0, // array size
        false, // is upper bound
        offsetof(isaac_ros2_messages::msg::IsaacBoundingBoxArray, bboxes), // bytes offset in struct
        nullptr, // default value
        size_function__IsaacBoundingBoxArray__bboxes, // size() function pointer
        get_const_function__IsaacBoundingBoxArray__bboxes, // get_const(index) function pointer
        get_function__IsaacBoundingBoxArray__bboxes, // get(index) function pointer
        resize_function__IsaacBoundingBoxArray__bboxes // resize(index) function pointer
    }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers IsaacBoundingBoxArray_message_members = {
    "isaac_ros2_messages::msg", // message namespace
    "IsaacBoundingBoxArray", // message name
    2, // number of fields
    sizeof(isaac_ros2_messages::msg::IsaacBoundingBoxArray),
    IsaacBoundingBoxArray_message_member_array, // message members
    IsaacBoundingBoxArray_init_function, // function to initialize message memory (memory has to be allocated)
    IsaacBoundingBoxArray_fini_function // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t IsaacBoundingBoxArray_message_type_support_handle = {
    ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
    &IsaacBoundingBoxArray_message_members,
    get_message_typesupport_handle_function,
};

} // namespace rosidl_typesupport_introspection_cpp

} // namespace msg

} // namespace isaac_ros2_messages


namespace rosidl_typesupport_introspection_cpp
{

template <>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC const rosidl_message_type_support_t* get_message_type_support_handle<
    isaac_ros2_messages::msg::IsaacBoundingBoxArray>()
{
    return &::isaac_ros2_messages::msg::rosidl_typesupport_introspection_cpp::IsaacBoundingBoxArray_message_type_support_handle;
}

} // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

    ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
    const rosidl_message_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_introspection_cpp, isaac_ros2_messages, msg, IsaacBoundingBoxArray)()
    {
        return &::isaac_ros2_messages::msg::rosidl_typesupport_introspection_cpp::IsaacBoundingBoxArray_message_type_support_handle;
    }

#ifdef __cplusplus
}
#endif
