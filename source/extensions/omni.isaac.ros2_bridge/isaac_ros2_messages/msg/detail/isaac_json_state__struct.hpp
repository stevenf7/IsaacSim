// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from isaac_ros2_messages:msg/IsaacJSONState.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_JSON_STATE__STRUCT_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_JSON_STATE__STRUCT_HPP_

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

#ifndef _WIN32
# define DEPRECATED__isaac_ros2_messages__msg__IsaacJSONState __attribute__((deprecated))
#else
# define DEPRECATED__isaac_ros2_messages__msg__IsaacJSONState __declspec(deprecated)
#endif

namespace isaac_ros2_messages
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct IsaacJSONState_
{
  using Type = IsaacJSONState_<ContainerAllocator>;

  explicit IsaacJSONState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->json = "";
    }
  }

  explicit IsaacJSONState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    json(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->json = "";
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _json_type =
    std::basic_string<char, std::char_traits<char>, typename ContainerAllocator::template rebind<char>::other>;
  _json_type json;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__json(
    const std::basic_string<char, std::char_traits<char>, typename ContainerAllocator::template rebind<char>::other> & _arg)
  {
    this->json = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator> *;
  using ConstRawPtr =
    const isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__isaac_ros2_messages__msg__IsaacJSONState
    std::shared_ptr<isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__isaac_ros2_messages__msg__IsaacJSONState
    std::shared_ptr<isaac_ros2_messages::msg::IsaacJSONState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const IsaacJSONState_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->json != other.json) {
      return false;
    }
    return true;
  }
  bool operator!=(const IsaacJSONState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct IsaacJSONState_

// alias to use template instance with default allocator
using IsaacJSONState =
  isaac_ros2_messages::msg::IsaacJSONState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace isaac_ros2_messages

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_JSON_STATE__STRUCT_HPP_
