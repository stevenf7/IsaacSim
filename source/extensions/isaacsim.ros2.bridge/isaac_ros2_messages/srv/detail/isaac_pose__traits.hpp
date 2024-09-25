// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from isaac_ros2_messages:srv/IsaacPose.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__SRV__DETAIL__ISAAC_POSE__TRAITS_HPP_
#define ISAAC_ROS2_MESSAGES__SRV__DETAIL__ISAAC_POSE__TRAITS_HPP_

#include "isaac_ros2_messages/srv/detail/isaac_pose__struct.hpp"
#include <rosidl_runtime_cpp/traits.hpp>
#include <stdint.h>
#include <type_traits>

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<isaac_ros2_messages::srv::IsaacPose_Request>()
{
  return "isaac_ros2_messages::srv::IsaacPose_Request";
}

template<>
inline const char * name<isaac_ros2_messages::srv::IsaacPose_Request>()
{
  return "isaac_ros2_messages/srv/IsaacPose_Request";
}

template<>
struct has_fixed_size<isaac_ros2_messages::srv::IsaacPose_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<isaac_ros2_messages::srv::IsaacPose_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<isaac_ros2_messages::srv::IsaacPose_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<isaac_ros2_messages::srv::IsaacPose_Response>()
{
  return "isaac_ros2_messages::srv::IsaacPose_Response";
}

template<>
inline const char * name<isaac_ros2_messages::srv::IsaacPose_Response>()
{
  return "isaac_ros2_messages/srv/IsaacPose_Response";
}

template<>
struct has_fixed_size<isaac_ros2_messages::srv::IsaacPose_Response>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<isaac_ros2_messages::srv::IsaacPose_Response>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<isaac_ros2_messages::srv::IsaacPose_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<isaac_ros2_messages::srv::IsaacPose>()
{
  return "isaac_ros2_messages::srv::IsaacPose";
}

template<>
inline const char * name<isaac_ros2_messages::srv::IsaacPose>()
{
  return "isaac_ros2_messages/srv/IsaacPose";
}

template<>
struct has_fixed_size<isaac_ros2_messages::srv::IsaacPose>
  : std::integral_constant<
    bool,
    has_fixed_size<isaac_ros2_messages::srv::IsaacPose_Request>::value &&
    has_fixed_size<isaac_ros2_messages::srv::IsaacPose_Response>::value
  >
{
};

template<>
struct has_bounded_size<isaac_ros2_messages::srv::IsaacPose>
  : std::integral_constant<
    bool,
    has_bounded_size<isaac_ros2_messages::srv::IsaacPose_Request>::value &&
    has_bounded_size<isaac_ros2_messages::srv::IsaacPose_Response>::value
  >
{
};

template<>
struct is_service<isaac_ros2_messages::srv::IsaacPose>
  : std::true_type
{
};

template<>
struct is_service_request<isaac_ros2_messages::srv::IsaacPose_Request>
  : std::true_type
{
};

template<>
struct is_service_response<isaac_ros2_messages::srv::IsaacPose_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // ISAAC_ROS2_MESSAGES__SRV__DETAIL__ISAAC_POSE__TRAITS_HPP_
