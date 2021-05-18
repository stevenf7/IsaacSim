// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from isaac_ros2_messages:msg/IsaacJSONState.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_JSON_STATE__STRUCT_H_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_JSON_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'json'
#include "rosidl_runtime_c/string.h"

    // Struct defined in msg/IsaacJSONState in the package isaac_ros2_messages.
    typedef struct isaac_ros2_messages__msg__IsaacJSONState
    {
        std_msgs__msg__Header header;
        rosidl_runtime_c__String json;
    } isaac_ros2_messages__msg__IsaacJSONState;

    // Struct for a sequence of isaac_ros2_messages__msg__IsaacJSONState.
    typedef struct isaac_ros2_messages__msg__IsaacJSONState__Sequence
    {
        isaac_ros2_messages__msg__IsaacJSONState* data;
        /// The number of valid items in data
        size_t size;
        /// The number of allocated items in data
        size_t capacity;
    } isaac_ros2_messages__msg__IsaacJSONState__Sequence;

#ifdef __cplusplus
}
#endif

#endif // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_JSON_STATE__STRUCT_H_
