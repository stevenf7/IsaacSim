// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from isaac_ros2_messages:msg/BoundingBox3DArray.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D_ARRAY__STRUCT_H_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D_ARRAY__STRUCT_H_

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
#include "isaac_ros2_messages/msg/detail/bounding_box3_d__struct.h"

    // Struct defined in msg/BoundingBox3DArray in the package isaac_ros2_messages.
    typedef struct isaac_ros2_messages__msg__BoundingBox3DArray
    {
        std_msgs__msg__Header header;
        isaac_ros2_messages__msg__BoundingBox3D__Sequence bboxes;
    } isaac_ros2_messages__msg__BoundingBox3DArray;

    // Struct for a sequence of isaac_ros2_messages__msg__BoundingBox3DArray.
    typedef struct isaac_ros2_messages__msg__BoundingBox3DArray__Sequence
    {
        isaac_ros2_messages__msg__BoundingBox3DArray* data;
        /// The number of valid items in data
        size_t size;
        /// The number of allocated items in data
        size_t capacity;
    } isaac_ros2_messages__msg__BoundingBox3DArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif // ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D_ARRAY__STRUCT_H_
