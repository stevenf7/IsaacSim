// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBox.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__TRAITS_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__TRAITS_HPP_

#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__struct.hpp"
#include <rosidl_runtime_cpp/traits.hpp>
#include <stdint.h>
#include <type_traits>

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<isaac_ros2_messages::msg::IsaacBoundingBox>()
{
  return "isaac_ros2_messages::msg::IsaacBoundingBox";
}

template<>
inline const char * name<isaac_ros2_messages::msg::IsaacBoundingBox>()
{
  return "isaac_ros2_messages/msg/IsaacBoundingBox";
}

template<>
struct has_fixed_size<isaac_ros2_messages::msg::IsaacBoundingBox>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<isaac_ros2_messages::msg::IsaacBoundingBox>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<isaac_ros2_messages::msg::IsaacBoundingBox>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__TRAITS_HPP_
