// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from isaac_ros2_messages:msg/BoundingBox3DArray.idl
// generated code does not contain a copyright notice

#include "isaac_ros2_messages/msg/detail/bounding_box3_d_array__functions.h"
#include "isaac_ros2_messages/msg/detail/bounding_box3_d_array__rosidl_typesupport_introspection_c.h"
#include "isaac_ros2_messages/msg/detail/bounding_box3_d_array__struct.h"
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
#include "isaac_ros2_messages/msg/bounding_box3_d.h"
// Member `bboxes`
#include "isaac_ros2_messages/msg/detail/bounding_box3_d__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

    void BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_init_function(
        void* message_memory, enum rosidl_runtime_c__message_initialization _init)
    {
        // TODO(karsten1987): initializers are not yet implemented for typesupport c
        // see https://github.com/ros2/ros2/issues/397
        (void)_init;
        isaac_ros2_messages__msg__BoundingBox3DArray__init(message_memory);
    }

    void BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_fini_function(void* message_memory)
    {
        isaac_ros2_messages__msg__BoundingBox3DArray__fini(message_memory);
    }

    size_t BoundingBox3DArray__rosidl_typesupport_introspection_c__size_function__BoundingBox3D__bboxes(
        const void* untyped_member)
    {
        const isaac_ros2_messages__msg__BoundingBox3D__Sequence* member =
            (const isaac_ros2_messages__msg__BoundingBox3D__Sequence*)(untyped_member);
        return member->size;
    }

    const void* BoundingBox3DArray__rosidl_typesupport_introspection_c__get_const_function__BoundingBox3D__bboxes(
        const void* untyped_member, size_t index)
    {
        const isaac_ros2_messages__msg__BoundingBox3D__Sequence* member =
            (const isaac_ros2_messages__msg__BoundingBox3D__Sequence*)(untyped_member);
        return &member->data[index];
    }

    void* BoundingBox3DArray__rosidl_typesupport_introspection_c__get_function__BoundingBox3D__bboxes(void* untyped_member,
                                                                                                      size_t index)
    {
        isaac_ros2_messages__msg__BoundingBox3D__Sequence* member =
            (isaac_ros2_messages__msg__BoundingBox3D__Sequence*)(untyped_member);
        return &member->data[index];
    }

    bool BoundingBox3DArray__rosidl_typesupport_introspection_c__resize_function__BoundingBox3D__bboxes(void* untyped_member,
                                                                                                        size_t size)
    {
        isaac_ros2_messages__msg__BoundingBox3D__Sequence* member =
            (isaac_ros2_messages__msg__BoundingBox3D__Sequence*)(untyped_member);
        isaac_ros2_messages__msg__BoundingBox3D__Sequence__fini(member);
        return isaac_ros2_messages__msg__BoundingBox3D__Sequence__init(member, size);
    }

    static rosidl_typesupport_introspection_c__MessageMember
        BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_member_array[2] = {
            {
                "header", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE, // type
                0, // upper bound of string
                NULL, // members of sub message (initialized later)
                false, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__msg__BoundingBox3DArray, header), // bytes offset in struct
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
                offsetof(isaac_ros2_messages__msg__BoundingBox3DArray, bboxes), // bytes offset in struct
                NULL, // default value
                BoundingBox3DArray__rosidl_typesupport_introspection_c__size_function__BoundingBox3D__bboxes, // size()
                                                                                                              // function
                                                                                                              // pointer
                BoundingBox3DArray__rosidl_typesupport_introspection_c__get_const_function__BoundingBox3D__bboxes, // get_const(index)
                                                                                                                   // function
                                                                                                                   // pointer
                BoundingBox3DArray__rosidl_typesupport_introspection_c__get_function__BoundingBox3D__bboxes, // get(index)
                                                                                                             // function
                                                                                                             // pointer
                BoundingBox3DArray__rosidl_typesupport_introspection_c__resize_function__BoundingBox3D__bboxes // resize(index)
                                                                                                               // function
                                                                                                               // pointer
            }
        };

    static const rosidl_typesupport_introspection_c__MessageMembers
        BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_members = {
            "isaac_ros2_messages__msg", // message namespace
            "BoundingBox3DArray", // message name
            2, // number of fields
            sizeof(isaac_ros2_messages__msg__BoundingBox3DArray),
            BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_member_array, // message
                                                                                                             // members
            BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_init_function, // function to
                                                                                                      // initialize
                                                                                                      // message memory
                                                                                                      // (memory has to
                                                                                                      // be allocated)
            BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_fini_function // function to
                                                                                                     // terminate
                                                                                                     // message instance
                                                                                                     // (will not free
                                                                                                     // memory)
        };

    // this is not const since it must be initialized on first access
    // since C does not allow non-integral compile-time constants
    static rosidl_message_type_support_t
        BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_type_support_handle = {
            0,
            &BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_members,
            get_message_typesupport_handle_function,
        };

    ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_isaac_ros2_messages const rosidl_message_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_introspection_c, isaac_ros2_messages, msg, BoundingBox3DArray)()
    {
        BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_member_array[0].members_ =
            ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
        BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_member_array[1].members_ =
            ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, isaac_ros2_messages, msg, BoundingBox3D)();
        if (!BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_type_support_handle
                 .typesupport_identifier)
        {
            BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_type_support_handle
                .typesupport_identifier = rosidl_typesupport_introspection_c__identifier;
        }
        return &BoundingBox3DArray__rosidl_typesupport_introspection_c__BoundingBox3DArray_message_type_support_handle;
    }
#ifdef __cplusplus
}
#endif
