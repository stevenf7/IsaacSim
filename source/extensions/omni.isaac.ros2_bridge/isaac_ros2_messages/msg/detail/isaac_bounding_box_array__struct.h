// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBoxArray.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__STRUCT_H_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__STRUCT_H_

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
// Member 'bboxes'
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__struct.h"

    // Struct defined in msg/IsaacBoundingBoxArray in the package isaac_ros2_messages.
    typedef struct isaac_ros2_messages__msg__IsaacBoundingBoxArray
    {
        std_msgs__msg__Header header;
        isaac_ros2_messages__msg__IsaacBoundingBox__Sequence bboxes;
    } isaac_ros2_messages__msg__IsaacBoundingBoxArray;

    // Struct for a sequence of isaac_ros2_messages__msg__IsaacBoundingBoxArray.
    typedef struct isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence
    {
        isaac_ros2_messages__msg__IsaacBoundingBoxArray* data;
        /// The number of valid items in data
        size_t size;
        /// The number of allocated items in data
        size_t capacity;
    } isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__STRUCT_H_
