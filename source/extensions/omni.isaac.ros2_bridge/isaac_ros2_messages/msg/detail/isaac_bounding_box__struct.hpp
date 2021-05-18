// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBox.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__STRUCT_HPP_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


#ifndef _WIN32
# define DEPRECATED__isaac_ros2_messages__msg__IsaacBoundingBox __attribute__((deprecated))
#else
# define DEPRECATED__isaac_ros2_messages__msg__IsaacBoundingBox __declspec(deprecated)
#endif

namespace isaac_ros2_messages
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct IsaacBoundingBox_
{
  using Type = IsaacBoundingBox_<ContainerAllocator>;

  explicit IsaacBoundingBox_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
      this->confidence = 0.0;
      this->xmin = 0ll;
      this->ymin = 0ll;
      this->xmax = 0ll;
      this->ymax = 0ll;
    }
  }

  explicit IsaacBoundingBox_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
      this->confidence = 0.0;
      this->xmin = 0ll;
      this->ymin = 0ll;
      this->xmax = 0ll;
      this->ymax = 0ll;
    }
  }

  // field types and members
  using _name_type =
    std::basic_string<char, std::char_traits<char>, typename ContainerAllocator::template rebind<char>::other>;
  _name_type name;
  using _confidence_type =
    double;
  _confidence_type confidence;
  using _xmin_type =
    int64_t;
  _xmin_type xmin;
  using _ymin_type =
    int64_t;
  _ymin_type ymin;
  using _xmax_type =
    int64_t;
  _xmax_type xmax;
  using _ymax_type =
    int64_t;
  _ymax_type ymax;

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
  Type & set__xmin(
    const int64_t & _arg)
  {
    this->xmin = _arg;
    return *this;
  }
  Type & set__ymin(
    const int64_t & _arg)
  {
    this->ymin = _arg;
    return *this;
  }
  Type & set__xmax(
    const int64_t & _arg)
  {
    this->xmax = _arg;
    return *this;
  }
  Type & set__ymax(
    const int64_t & _arg)
  {
    this->ymax = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator> *;
  using ConstRawPtr =
    const isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__isaac_ros2_messages__msg__IsaacBoundingBox
    std::shared_ptr<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__isaac_ros2_messages__msg__IsaacBoundingBox
    std::shared_ptr<isaac_ros2_messages::msg::IsaacBoundingBox_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const IsaacBoundingBox_ & other) const
  {
    if (this->name != other.name) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->xmin != other.xmin) {
      return false;
    }
    if (this->ymin != other.ymin) {
      return false;
    }
    if (this->xmax != other.xmax) {
      return false;
    }
    if (this->ymax != other.ymax) {
      return false;
    }
    return true;
  }
  bool operator!=(const IsaacBoundingBox_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct IsaacBoundingBox_

// alias to use template instance with default allocator
using IsaacBoundingBox =
  isaac_ros2_messages::msg::IsaacBoundingBox_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace isaac_ros2_messages

#endif  // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__STRUCT_HPP_
