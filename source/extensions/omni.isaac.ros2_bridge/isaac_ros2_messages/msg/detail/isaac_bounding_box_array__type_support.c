// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBoxArray.idl
// generated code does not contain a copyright notice

#include "isaac_ros2_messages/msg/detail/isaac_bounding_box_array__functions.h"
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box_array__rosidl_typesupport_introspection_c.h"
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box_array__struct.h"
#include "isaac_ros2_messages/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"

#include <stddef.h>


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `bboxes`
#include "isaac_ros2_messages/msg/isaac_bounding_box.h"
// Member `bboxes`
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

    void IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_init_function(
        void* message_memory, enum rosidl_runtime_c__message_initialization _init)
    {
        // TODO(karsten1987): initializers are not yet implemented for typesupport c
        // see https://github.com/ros2/ros2/issues/397
        (void)_init;
        isaac_ros2_messages__msg__IsaacBoundingBoxArray__init(message_memory);
    }

    void IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_fini_function(void* message_memory)
    {
        isaac_ros2_messages__msg__IsaacBoundingBoxArray__fini(message_memory);
    }

    size_t IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__size_function__IsaacBoundingBox__bboxes(
        const void* untyped_member)
    {
        const isaac_ros2_messages__msg__IsaacBoundingBox__Sequence* member =
            (const isaac_ros2_messages__msg__IsaacBoundingBox__Sequence*)(untyped_member);
        return member->size;
    }

    const void* IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__get_const_function__IsaacBoundingBox__bboxes(
        const void* untyped_member, size_t index)
    {
        const isaac_ros2_messages__msg__IsaacBoundingBox__Sequence* member =
            (const isaac_ros2_messages__msg__IsaacBoundingBox__Sequence*)(untyped_member);
        return &member->data[index];
    }

    void* IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__get_function__IsaacBoundingBox__bboxes(
        void* untyped_member, size_t index)
    {
        isaac_ros2_messages__msg__IsaacBoundingBox__Sequence* member =
            (isaac_ros2_messages__msg__IsaacBoundingBox__Sequence*)(untyped_member);
        return &member->data[index];
    }

    bool IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__resize_function__IsaacBoundingBox__bboxes(
        void* untyped_member, size_t size)
    {
        isaac_ros2_messages__msg__IsaacBoundingBox__Sequence* member =
            (isaac_ros2_messages__msg__IsaacBoundingBox__Sequence*)(untyped_member);
        isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__fini(member);
        return isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__init(member, size);
    }

    static rosidl_typesupport_introspection_c__MessageMember
        IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_member_array[2] = {
            {
                "header", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE, // type
                0, // upper bound of string
                NULL, // members of sub message (initialized later)
                false, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__msg__IsaacBoundingBoxArray, header), // bytes offset in struct
                NULL, // default value
                NULL, // size() function pointer
                NULL, // get_const(index) function pointer
                NULL, // get(index) function pointer
                NULL // resize(index) function pointer
            },
            {
                "bboxes", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE, // type
                0, // upper bound of string
                NULL, // members of sub message (initialized later)
                true, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__msg__IsaacBoundingBoxArray, bboxes), // bytes offset in struct
                NULL, // default value
                IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__size_function__IsaacBoundingBox__bboxes, // size() function pointer
                IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__get_const_function__IsaacBoundingBox__bboxes, // get_const(index) function pointer
                IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__get_function__IsaacBoundingBox__bboxes, // get(index)
                                                                                                                   // function
                                                                                                                   // pointer
                IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__resize_function__IsaacBoundingBox__bboxes // resize(index) function pointer
            }
        };

    static const rosidl_typesupport_introspection_c__MessageMembers
        IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_members = {
            "isaac_ros2_messages__msg", // message namespace
            "IsaacBoundingBoxArray", // message name
            2, // number of fields
            sizeof(isaac_ros2_messages__msg__IsaacBoundingBoxArray),
            IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_member_array, // message
                                                                                                                   // members
            IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_init_function, // function
                                                                                                            // to
                                                                                                            // initialize
                                                                                                            // message
                                                                                                            // memory
                                                                                                            // (memory
                                                                                                            // has to be
                                                                                                            // allocated)
            IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_fini_function // function
                                                                                                           // to
                                                                                                           // terminate
                                                                                                           // message
                                                                                                           // instance
                                                                                                           // (will not
                                                                                                           // free
                                                                                                           // memory)
        };

    // this is not const since it must be initialized on first access
    // since C does not allow non-integral compile-time constants
    static rosidl_message_type_support_t
        IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_type_support_handle = {
            0,
            &IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_members,
            get_message_typesupport_handle_function,
        };

    ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_isaac_ros2_messages const rosidl_message_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_introspection_c, isaac_ros2_messages, msg, IsaacBoundingBoxArray)()
    {
        IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_member_array[0].members_ =
            ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
        IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_member_array[1].members_ =
            ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, isaac_ros2_messages, msg, IsaacBoundingBox)();
        if (!IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_type_support_handle
                 .typesupport_identifier)
        {
            IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_type_support_handle
                .typesupport_identifier = rosidl_typesupport_introspection_c__identifier;
        }
        return &IsaacBoundingBoxArray__rosidl_typesupport_introspection_c__IsaacBoundingBoxArray_message_type_support_handle;
    }
#ifdef __cplusplus
}
#endif
