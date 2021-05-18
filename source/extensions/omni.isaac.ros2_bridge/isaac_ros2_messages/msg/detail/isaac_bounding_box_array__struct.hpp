// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBoxArray.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__STRUCT_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"
// Member 'bboxes'
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__isaac_ros2_messages__msg__IsaacBoundingBoxArray __attribute__((deprecated))
#else
# define DEPRECATED__isaac_ros2_messages__msg__IsaacBoundingBoxArray __declspec(deprecated)
#endif

namespace isaac_ros2_messages
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct IsaacBoundingBoxArray_
{
  using Type = IsaacBoundingBoxArray_<ContainerAllocator>;

  explicit IsaacBoundingBoxArray_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    (void)_init;
  }

  explicit IsaacBoundingBoxArray_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _bboxes_type =
    std::vector<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>, typename ContainerAllocator::template rebind<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>>::other>;
  _bboxes_type bboxes;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__bboxes(
    const std::vector<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>, typename ContainerAllocator::template rebind<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>>::other> & _arg)
  {
    this->bboxes = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator> *;
  using ConstRawPtr =
    const isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__isaac_ros2_messages__msg__IsaacBoundingBoxArray
    std::shared_ptr<isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__isaac_ros2_messages__msg__IsaacBoundingBoxArray
    std::shared_ptr<isaac_ros2_messages::msg::IsaacBoundingBoxArray_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const IsaacBoundingBoxArray_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->bboxes != other.bboxes) {
      return false;
    }
    return true;
  }
  bool operator!=(const IsaacBoundingBoxArray_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct IsaacBoundingBoxArray_

// alias to use template instance with default allocator
using IsaacBoundingBoxArray =
  isaac_ros2_messages::msg::IsaacBoundingBoxArray_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace isaac_ros2_messages

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX_ARRAY__STRUCT_HPP_
