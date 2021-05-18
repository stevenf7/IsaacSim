// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from isaac_ros2_messages:msg/BoundingBox3D.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D__BUILDER_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D__BUILDER_HPP_

#include "isaac_ros2_messages/msg/detail/bounding_box3_d__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace isaac_ros2_messages
{

namespace msg
{

namespace builder
{

class Init_BoundingBox3D_size
{
public:
  explicit Init_BoundingBox3D_size(::isaac_ros2_messages::msg::BoundingBox3D & msg)
  : msg_(msg)
  {}
  ::isaac_ros2_messages::msg::BoundingBox3D size(::isaac_ros2_messages::msg::BoundingBox3D::_size_type arg)
  {
    msg_.size = std::move(arg);
    return std::move(msg_);
  }

private:
  ::isaac_ros2_messages::msg::BoundingBox3D msg_;
};

class Init_BoundingBox3D_center
{
public:
  explicit Init_BoundingBox3D_center(::isaac_ros2_messages::msg::BoundingBox3D & msg)
  : msg_(msg)
  {}
  Init_BoundingBox3D_size center(::isaac_ros2_messages::msg::BoundingBox3D::_center_type arg)
  {
    msg_.center = std::move(arg);
    return Init_BoundingBox3D_size(msg_);
  }

private:
  ::isaac_ros2_messages::msg::BoundingBox3D msg_;
};

class Init_BoundingBox3D_confidence
{
public:
  explicit Init_BoundingBox3D_confidence(::isaac_ros2_messages::msg::BoundingBox3D & msg)
  : msg_(msg)
  {}
  Init_BoundingBox3D_center confidence(::isaac_ros2_messages::msg::BoundingBox3D::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_BoundingBox3D_center(msg_);
  }

private:
  ::isaac_ros2_messages::msg::BoundingBox3D msg_;
};

class Init_BoundingBox3D_name
{
public:
  Init_BoundingBox3D_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_BoundingBox3D_confidence name(::isaac_ros2_messages::msg::BoundingBox3D::_name_type arg)
  {
    msg_.name = std::move(arg);
    return Init_BoundingBox3D_confidence(msg_);
  }

private:
  ::isaac_ros2_messages::msg::BoundingBox3D msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::isaac_ros2_messages::msg::BoundingBox3D>()
{
  return isaac_ros2_messages::msg::builder::Init_BoundingBox3D_name();
}

}  // namespace isaac_ros2_messages

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D__BUILDER_HPP_
