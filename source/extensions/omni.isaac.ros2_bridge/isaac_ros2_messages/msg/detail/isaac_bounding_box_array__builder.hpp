// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBoxArray.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__BUILDER_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__BUILDER_HPP_

#include "isaac_ros2_messages/msg/detail/isaac_bounding_box_array__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace isaac_ros2_messages
{

namespace msg
{

namespace builder
{

class Init_IsaacBoundingBoxArray_bboxes
{
public:
  explicit Init_IsaacBoundingBoxArray_bboxes(::isaac_ros2_messages::msg::IsaacBoundingBoxArray & msg)
  : msg_(msg)
  {}
  ::isaac_ros2_messages::msg::IsaacBoundingBoxArray bboxes(::isaac_ros2_messages::msg::IsaacBoundingBoxArray::_bboxes_type arg)
  {
    msg_.bboxes = std::move(arg);
    return std::move(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacBoundingBoxArray msg_;
};

class Init_IsaacBoundingBoxArray_header
{
public:
  Init_IsaacBoundingBoxArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_IsaacBoundingBoxArray_bboxes header(::isaac_ros2_messages::msg::IsaacBoundingBoxArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_IsaacBoundingBoxArray_bboxes(msg_);
  }

private:
  ::isaac_ros2_messages::msg::IsaacBoundingBoxArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::isaac_ros2_messages::msg::IsaacBoundingBoxArray>()
{
  return isaac_ros2_messages::msg::builder::Init_IsaacBoundingBoxArray_header();
}

}  // namespace isaac_ros2_messages

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__BUILDER_HPP_
