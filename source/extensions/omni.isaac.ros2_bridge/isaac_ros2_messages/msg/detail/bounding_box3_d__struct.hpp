// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from isaac_ros2_messages:msg/BoundingBox3D.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D__STRUCT_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


// Include directives for member types
// Member 'center'
#include "geometry_msgs/msg/detail/pose__struct.hpp"
// Member 'size'
#include "geometry_msgs/msg/detail/vector3__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__isaac_ros2_messages__msg__BoundingBox3D __attribute__((deprecated))
#else
# define DEPRECATED__isaac_ros2_messages__msg__BoundingBox3D __declspec(deprecated)
#endif

namespace isaac_ros2_messages
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct BoundingBox3D_
{
  using Type = BoundingBox3D_<ContainerAllocator>;

  explicit BoundingBox3D_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : center(_init),
    size(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
      this->confidence = 0.0;
    }
  }

  explicit BoundingBox3D_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : name(_alloc),
    center(_alloc, _init),
    size(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
      this->confidence = 0.0;
    }
  }

  // field types and members
  using _name_type =
    std::basic_string<char, std::char_traits<char>, typename ContainerAllocator::template rebind<char>::other>;
  _name_type name;
  using _confidence_type =
    double;
  _confidence_type confidence;
  using _center_type =
    geometry_msgs::msg::Pose_<ContainerAllocator>;
  _center_type center;
  using _size_type =
    geometry_msgs::msg::Vector3_<ContainerAllocator>;
  _size_type size;

  // setters for named parameter idiom
  Type & set__name(
    const std::basic_string<char, std::char_traits<char>, typename ContainerAllocator::template rebind<char>::other> & _arg)
  {
    this->name = _arg;
    return *this;
  }
  Type & set__confidence(
    const double & _arg)
  {
    this->confidence = _arg;
    return *this;
  }
  Type & set__center(
    const geometry_msgs::msg::Pose_<ContainerAllocator> & _arg)
  {
    this->center = _arg;
    return *this;
  }
  Type & set__size(
    const geometry_msgs::msg::Vector3_<ContainerAllocator> & _arg)
  {
    this->size = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator> *;
  using ConstRawPtr =
    const isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__isaac_ros2_messages__msg__BoundingBox3D
    std::shared_ptr<isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__isaac_ros2_messages__msg__BoundingBox3D
    std::shared_ptr<isaac_ros2_messages::msg::BoundingBox3D_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const BoundingBox3D_ & other) const
  {
    if (this->name != other.name) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->center != other.center) {
      return false;
    }
    if (this->size != other.size) {
      return false;
    }
    return true;
  }
  bool operator!=(const BoundingBox3D_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct BoundingBox3D_

// alias to use template instance with default allocator
using BoundingBox3D =
  isaac_ros2_messages::msg::BoundingBox3D_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace isaac_ros2_messages

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__BOUNDING_BOX3_D__STRUCT_HPP_
