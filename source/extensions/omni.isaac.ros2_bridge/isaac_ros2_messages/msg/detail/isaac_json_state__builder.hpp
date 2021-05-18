// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from isaac_ros2_messages:msg/IsaacJSONState.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_JSON_STATE__BUILDER_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_JSON_STATE__BUILDER_HPP_

#include "isaac_ros2_messages/msg/detail/isaac_json_state__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace isaac_ros2_messages
{

namespace msg
{

namespace builder
{

class Init_IsaacJSONState_json
{
public:
  explicit Init_IsaacJSONState_json(::isaac_ros2_messages::msg::IsaacJSONState & msg)
  : msg_(msg)
  {}
  ::isaac_ros2_messages::msg::IsaacJSONState json(::isaac_ros2_messages::msg::IsaacJSONState::_json_type arg)
  {
    msg_.json = std::move(arg);
    return std::move(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacJSONState msg_;
};

class Init_IsaacJSONState_header
{
public:
  Init_IsaacJSONState_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_IsaacJSONState_json header(::isaac_ros2_messages::msg::IsaacJSONState::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_IsaacJSONState_json(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacJSONState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::isaac_ros2_messages::msg::IsaacJSONState>()
{
  return isaac_ros2_messages::msg::builder::Init_IsaacJSONState_header();
}

}  // namespace isaac_ros2_messages

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_JSON_STATE__BUILDER_HPP_
