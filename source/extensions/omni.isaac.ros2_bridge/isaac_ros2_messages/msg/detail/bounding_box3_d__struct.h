// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from isaac_ros2_messages:msg/BoundingBox3D.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D__STRUCT_H_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D__STRUCT_H_

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
// Member 'center'
#include "geometry_msgs/msg/detail/pose__struct.h"
// Member 'size'
#include "geometry_msgs/msg/detail/vector3__struct.h"

    // Struct defined in msg/BoundingBox3D in the package isaac_ros2_messages.
    typedef struct isaac_ros2_messages__msg__BoundingBox3D
    {
        rosidl_runtime_c__String name;
        double confidence;
        geometry_msgs__msg__Pose center;
        geometry_msgs__msg__Vector3 size;
    } isaac_ros2_messages__msg__BoundingBox3D;

    // Struct for a sequence of isaac_ros2_messages__msg__BoundingBox3D.
    typedef struct isaac_ros2_messages__msg__BoundingBox3D__Sequence
    {
        isaac_ros2_messages__msg__BoundingBox3D* data;
        /// The number of valid items in data
        size_t size;
        /// The number of allocated items in data
        size_t capacity;
    } isaac_ros2_messages__msg__BoundingBox3D__Sequence;

#ifdef __cplusplus
}
#endif

#endif // ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D__STRUCT_H_
