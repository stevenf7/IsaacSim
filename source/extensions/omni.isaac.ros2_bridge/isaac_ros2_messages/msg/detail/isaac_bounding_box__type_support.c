// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBox.idl
// generated code does not contain a copyright notice

#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__functions.h"
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__rosidl_typesupport_introspection_c.h"
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__struct.h"
#include "isaac_ros2_messages/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"

#include <stddef.h>


// Include directives for member types
// Member `name`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

    void IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_init_function(
        void* message_memory, enum rosidl_runtime_c__message_initialization _init)
    {
        // TODO(karsten1987): initializers are not yet implemented for typesupport c
        // see https://github.com/ros2/ros2/issues/397
        (void)_init;
        isaac_ros2_messages__msg__IsaacBoundingBox__init(message_memory);
    }

    void IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_fini_function(void* message_memory)
    {
        isaac_ros2_messages__msg__IsaacBoundingBox__fini(message_memory);
    }

    static rosidl_typesupport_introspection_c__MessageMember
        IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_message_member_array[6] = {
            {
                "name", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_STRING, // type
                0, // upper bound of string
                NULL, // members of sub message
                false, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__msg__IsaacBoundingBox, name), // bytes offset in struct
                NULL, // default value
                NULL, // size() function pointer
                NULL, // get_const(index) function pointer
                NULL, // get(index) function pointer
                NULL // resize(index) function pointer
            },
            {
                "confidence", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE, // type
                0, // upper bound of string
                NULL, // members of sub message
                false, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__msg__IsaacBoundingBox, confidence), // bytes offset in struct
                NULL, // default value
                NULL, // size() function pointer
                NULL, // get_const(index) function pointer
                NULL, // get(index) function pointer
                NULL // resize(index) function pointer
            },
            {
                "xmin", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_INT64, // type
                0, // upper bound of string
                NULL, // members of sub message
                false, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__msg__IsaacBoundingBox, xmin), // bytes offset in struct
                NULL, // default value
                NULL, // size() function pointer
                NULL, // get_const(index) function pointer
                NULL, // get(index) function pointer
                NULL // resize(index) function pointer
            },
            {
                "ymin", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_INT64, // type
                0, // upper bound of string
                NULL, // members of sub message
                false, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__msg__IsaacBoundingBox, ymin), // bytes offset in struct
                NULL, // default value
                NULL, // size() function pointer
                NULL, // get_const(index) function pointer
                NULL, // get(index) function pointer
                NULL // resize(index) function pointer
            },
            {
                "xmax", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_INT64, // type
                0, // upper bound of string
                NULL, // members of sub message
                false, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__msg__IsaacBoundingBox, xmax), // bytes offset in struct
                NULL, // default value
                NULL, // size() function pointer
                NULL, // get_const(index) function pointer
                NULL, // get(index) function pointer
                NULL // resize(index) function pointer
            },
            {
                "ymax", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_INT64, // type
                0, // upper bound of string
                NULL, // members of sub message
                false, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__msg__IsaacBoundingBox, ymax), // bytes offset in struct
                NULL, // default value
                NULL, // size() function pointer
                NULL, // get_const(index) function pointer
                NULL, // get(index) function pointer
                NULL // resize(index) function pointer
            }
        };

    static const rosidl_typesupport_introspection_c__MessageMembers
        IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_message_members = {
            "isaac_ros2_messages__msg", // message namespace
            "IsaacBoundingBox", // message name
            6, // number of fields
            sizeof(isaac_ros2_messages__msg__IsaacBoundingBox),
            IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_message_member_array, // message
                                                                                                         // members
            IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_init_function, // function to
                                                                                                  // initialize message
                                                                                                  // memory (memory has
                                                                                                  // to be allocated)
            IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_fini_function // function to
                                                                                                 // terminate message
                                                                                                 // instance (will not
                                                                                                 // free memory)
        };

    // this is not const since it must be initialized on first access
    // since C does not allow non-integral compile-time constants
    static rosidl_message_type_support_t
        IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_message_type_support_handle = {
            0,
            &IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_message_members,
            get_message_typesupport_handle_function,
        };

    ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_isaac_ros2_messages const rosidl_message_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_introspection_c, isaac_ros2_messages, msg, IsaacBoundingBox)()
    {
        if (!IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_message_type_support_handle
                 .typesupport_identifier)
        {
            IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_message_type_support_handle
                .typesupport_identifier = rosidl_typesupport_introspection_c__identifier;
        }
        return &IsaacBoundingBox__rosidl_typesupport_introspection_c__IsaacBoundingBox_message_type_support_handle;
    }
#ifdef __cplusplus
}
#endif
