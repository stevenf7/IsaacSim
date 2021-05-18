// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBox.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__BUILDER_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__BUILDER_HPP_

#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace isaac_ros2_messages
{

namespace msg
{

namespace builder
{

class Init_IsaacBoundingBox_ymax
{
public:
  explicit Init_IsaacBoundingBox_ymax(::isaac_ros2_messages::msg::IsaacBoundingBox & msg)
  : msg_(msg)
  {}
  ::isaac_ros2_messages::msg::IsaacBoundingBox ymax(::isaac_ros2_messages::msg::IsaacBoundingBox::_ymax_type arg)
  {
    msg_.ymax = std::move(arg);
    return std::move(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacBoundingBox msg_;
};

class Init_IsaacBoundingBox_xmax
{
public:
  explicit Init_IsaacBoundingBox_xmax(::isaac_ros2_messages::msg::IsaacBoundingBox & msg)
  : msg_(msg)
  {}
  Init_IsaacBoundingBox_ymax xmax(::isaac_ros2_messages::msg::IsaacBoundingBox::_xmax_type arg)
  {
    msg_.xmax = std::move(arg);
    return Init_IsaacBoundingBox_ymax(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacBoundingBox msg_;
};

class Init_IsaacBoundingBox_ymin
{
public:
  explicit Init_IsaacBoundingBox_ymin(::isaac_ros2_messages::msg::IsaacBoundingBox & msg)
  : msg_(msg)
  {}
  Init_IsaacBoundingBox_xmax ymin(::isaac_ros2_messages::msg::IsaacBoundingBox::_ymin_type arg)
  {
    msg_.ymin = std::move(arg);
    return Init_IsaacBoundingBox_xmax(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacBoundingBox msg_;
};

class Init_IsaacBoundingBox_xmin
{
public:
  explicit Init_IsaacBoundingBox_xmin(::isaac_ros2_messages::msg::IsaacBoundingBox & msg)
  : msg_(msg)
  {}
  Init_IsaacBoundingBox_ymin xmin(::isaac_ros2_messages::msg::IsaacBoundingBox::_xmin_type arg)
  {
    msg_.xmin = std::move(arg);
    return Init_IsaacBoundingBox_ymin(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacBoundingBox msg_;
};

class Init_IsaacBoundingBox_confidence
{
public:
  explicit Init_IsaacBoundingBox_confidence(::isaac_ros2_messages::msg::IsaacBoundingBox & msg)
  : msg_(msg)
  {}
  Init_IsaacBoundingBox_xmin confidence(::isaac_ros2_messages::msg::IsaacBoundingBox::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_IsaacBoundingBox_xmin(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacBoundingBox msg_;
};

class Init_IsaacBoundingBox_name
{
public:
  Init_IsaacBoundingBox_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_IsaacBoundingBox_confidence name(::isaac_ros2_messages::msg::IsaacBoundingBox::_name_type arg)
  {
    msg_.name = std::move(arg);
    return Init_IsaacBoundingBox_confidence(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacBoundingBox msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::isaac_ros2_messages::msg::IsaacBoundingBox>()
{
  return isaac_ros2_messages::msg::builder::Init_IsaacBoundingBox_name();
}

}  // namespace isaac_ros2_messages

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__BUILDER_HPP_
