// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBox.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__STRUCT_H_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'name'
#include "rosidl_runtime_c/string.h"

    // Struct defined in msg/IsaacBoundingBox in the package isaac_ros2_messages.
    typedef struct isaac_ros2_messages__msg__IsaacBoundingBox
    {
        rosidl_runtime_c__String name;
        double confidence;
        int64_t xmin;
        int64_t ymin;
        int64_t xmax;
        int64_t ymax;
    } isaac_ros2_messages__msg__IsaacBoundingBox;

    // Struct for a sequence of isaac_ros2_messages__msg__IsaacBoundingBox.
    typedef struct isaac_ros2_messages__msg__IsaacBoundingBox__Sequence
    {
        isaac_ros2_messages__msg__IsaacBoundingBox* data;
        /// The number of valid items in data
        size_t size;
        /// The number of allocated items in data
        size_t capacity;
    } isaac_ros2_messages__msg__IsaacBoundingBox__Sequence;

#ifdef __cplusplus
}
#endif

#endif // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__STRUCT_H_
