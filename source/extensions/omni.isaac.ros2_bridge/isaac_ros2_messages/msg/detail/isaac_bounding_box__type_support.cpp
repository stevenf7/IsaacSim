// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBox.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__struct.hpp"
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

void IsaacBoundingBox_init_function(void* message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
    new (message_memory) isaac_ros2_messages::msg::IsaacBoundingBox(_init);
}

void IsaacBoundingBox_fini_function(void* message_memory)
{
    auto typed_message = static_cast<isaac_ros2_messages::msg::IsaacBoundingBox*>(message_memory);
    typed_message->~IsaacBoundingBox();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember IsaacBoundingBox_message_member_array[6] = {
    {
        "name", // name
        ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING, // type
        0, // upper bound of string
        nullptr, // members of sub message
        false, // is array
        0, // array size
        false, // is upper bound
        offsetof(isaac_ros2_messages::msg::IsaacBoundingBox, name), // bytes offset in struct
        nullptr, // default value
        nullptr, // size() function pointer
        nullptr, // get_const(index) function pointer
        nullptr, // get(index) function pointer
        nullptr // resize(index) function pointer
    },
    {
        "confidence", // name
        ::rosidl_typesupport_introspection_cpp::ROS_TYPE_DOUBLE, // type
        0, // upper bound of string
        nullptr, // members of sub message
        false, // is array
        0, // array size
        false, // is upper bound
        offsetof(isaac_ros2_messages::msg::IsaacBoundingBox, confidence), // bytes offset in struct
        nullptr, // default value
        nullptr, // size() function pointer
        nullptr, // get_const(index) function pointer
        nullptr, // get(index) function pointer
        nullptr // resize(index) function pointer
    },
    {
        "xmin", // name
        ::rosidl_typesupport_introspection_cpp::ROS_TYPE_INT64, // type
        0, // upper bound of string
        nullptr, // members of sub message
        false, // is array
        0, // array size
        false, // is upper bound
        offsetof(isaac_ros2_messages::msg::IsaacBoundingBox, xmin), // bytes offset in struct
        nullptr, // default value
        nullptr, // size() function pointer
        nullptr, // get_const(index) function pointer
        nullptr, // get(index) function pointer
        nullptr // resize(index) function pointer
    },
    {
        "ymin", // name
        ::rosidl_typesupport_introspection_cpp::ROS_TYPE_INT64, // type
        0, // upper bound of string
        nullptr, // members of sub message
        false, // is array
        0, // array size
        false, // is upper bound
        offsetof(isaac_ros2_messages::msg::IsaacBoundingBox, ymin), // bytes offset in struct
        nullptr, // default value
        nullptr, // size() function pointer
        nullptr, // get_const(index) function pointer
        nullptr, // get(index) function pointer
        nullptr // resize(index) function pointer
    },
    {
        "xmax", // name
        ::rosidl_typesupport_introspection_cpp::ROS_TYPE_INT64, // type
        0, // upper bound of string
        nullptr, // members of sub message
        false, // is array
        0, // array size
        false, // is upper bound
        offsetof(isaac_ros2_messages::msg::IsaacBoundingBox, xmax), // bytes offset in struct
        nullptr, // default value
        nullptr, // size() function pointer
        nullptr, // get_const(index) function pointer
        nullptr, // get(index) function pointer
        nullptr // resize(index) function pointer
    },
    {
        "ymax", // name
        ::rosidl_typesupport_introspection_cpp::ROS_TYPE_INT64, // type
        0, // upper bound of string
        nullptr, // members of sub message
        false, // is array
        0, // array size
        false, // is upper bound
        offsetof(isaac_ros2_messages::msg::IsaacBoundingBox, ymax), // bytes offset in struct
        nullptr, // default value
        nullptr, // size() function pointer
        nullptr, // get_const(index) function pointer
        nullptr, // get(index) function pointer
        nullptr // resize(index) function pointer
    }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers IsaacBoundingBox_message_members = {
    "isaac_ros2_messages::msg", // message namespace
    "IsaacBoundingBox", // message name
    6, // number of fields
    sizeof(isaac_ros2_messages::msg::IsaacBoundingBox),
    IsaacBoundingBox_message_member_array, // message members
    IsaacBoundingBox_init_function, // function to initialize message memory (memory has to be allocated)
    IsaacBoundingBox_fini_function // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t IsaacBoundingBox_message_type_support_handle = {
    ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
    &IsaacBoundingBox_message_members,
    get_message_typesupport_handle_function,
};

} // namespace rosidl_typesupport_introspection_cpp

} // namespace msg

} // namespace isaac_ros2_messages


namespace rosidl_typesupport_introspection_cpp
{

template <>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC const rosidl_message_type_support_t* get_message_type_support_handle<
    isaac_ros2_messages::msg::IsaacBoundingBox>()
{
    return &::isaac_ros2_messages::msg::rosidl_typesupport_introspection_cpp::IsaacBoundingBox_message_type_support_handle;
}

} // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

    ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
    const rosidl_message_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_introspection_cpp, isaac_ros2_messages, msg, IsaacBoundingBox)()
    {
        return &::isaac_ros2_messages::msg::rosidl_typesupport_introspection_cpp::IsaacBoundingBox_message_type_support_handle;
    }

#ifdef __cplusplus
}
#endif
