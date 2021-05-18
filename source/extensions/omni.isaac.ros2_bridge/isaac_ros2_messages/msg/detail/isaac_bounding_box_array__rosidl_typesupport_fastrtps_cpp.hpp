// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__rosidl_typesupport_fastrtps_cpp.hpp.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBoxArray.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_

#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "isaac_ros2_messages/msg/rosidl_typesupport_fastrtps_cpp__visibility_control.h"
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box_array__struct.hpp"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

#include "fastcdr/Cdr.h"

namespace isaac_ros2_messages
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_isaac_ros2_messages
cdr_serialize(
  const isaac_ros2_messages::msg::IsaacBoundingBoxArray & ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_isaac_ros2_messages
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  isaac_ros2_messages::msg::IsaacBoundingBoxArray & ros_message);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_isaac_ros2_messages
get_serialized_size(
  const isaac_ros2_messages::msg::IsaacBoundingBoxArray & ros_message,
  size_t current_alignment);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_isaac_ros2_messages
max_serialized_size_IsaacBoundingBoxArray(
  bool & full_bounded,
  size_t current_alignment);

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace isaac_ros2_messages

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_isaac_ros2_messages
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, isaac_ros2_messages, msg, IsaacBoundingBoxArray)();

#ifdef __cplusplus
}
#endif

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
