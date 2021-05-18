// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from isaac_ros2_messages:msg/BoundingBox3DArray.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D_ARRAY__BUILDER_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D_ARRAY__BUILDER_HPP_

#include "isaac_ros2_messages/msg/detail/bounding_box3_d_array__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace isaac_ros2_messages
{

namespace msg
{

namespace builder
{

class Init_BoundingBox3DArray_bboxes
{
public:
  explicit Init_BoundingBox3DArray_bboxes(::isaac_ros2_messages::msg::BoundingBox3DArray & msg)
  : msg_(msg)
  {}
  ::isaac_ros2_messages::msg::BoundingBox3DArray bboxes(::isaac_ros2_messages::msg::BoundingBox3DArray::_bboxes_type arg)
  {
    msg_.bboxes = std::move(arg);
    return std::move(msg_);
  }

private:
  ::isaac_ros2_messages::msg::BoundingBox3DArray msg_;
};

class Init_BoundingBox3DArray_header
{
public:
  Init_BoundingBox3DArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_BoundingBox3DArray_bboxes header(::isaac_ros2_messages::msg::BoundingBox3DArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_BoundingBox3DArray_bboxes(msg_);
  }

private:
  ::isaac_ros2_messages::msg::BoundingBox3DArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::isaac_ros2_messages::msg::BoundingBox3DArray>()
{
  return isaac_ros2_messages::msg::builder::Init_BoundingBox3DArray_header();
}

}  // namespace isaac_ros2_messages

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D_ARRAY__BUILDER_HPP_
