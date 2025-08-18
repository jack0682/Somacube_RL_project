// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from doosan_somacube_rl:msg/SafetyEvent.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__STRUCT_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__doosan_somacube_rl__msg__SafetyEvent __attribute__((deprecated))
#else
# define DEPRECATED__doosan_somacube_rl__msg__SafetyEvent __declspec(deprecated)
#endif

namespace doosan_somacube_rl
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct SafetyEvent_
{
  using Type = SafetyEvent_<ContainerAllocator>;

  explicit SafetyEvent_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : stamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->type = "";
      this->detail = "";
      this->severity = 0l;
    }
  }

  explicit SafetyEvent_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : type(_alloc),
    detail(_alloc),
    stamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->type = "";
      this->detail = "";
      this->severity = 0l;
    }
  }

  // field types and members
  using _type_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _type_type type;
  using _detail_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _detail_type detail;
  using _severity_type =
    int32_t;
  _severity_type severity;
  using _stamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _stamp_type stamp;

  // setters for named parameter idiom
  Type & set__type(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->type = _arg;
    return *this;
  }
  Type & set__detail(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->detail = _arg;
    return *this;
  }
  Type & set__severity(
    const int32_t & _arg)
  {
    this->severity = _arg;
    return *this;
  }
  Type & set__stamp(
    const builtin_interfaces::msg::Time_<ContainerAllocator> & _arg)
  {
    this->stamp = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator> *;
  using ConstRawPtr =
    const doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__doosan_somacube_rl__msg__SafetyEvent
    std::shared_ptr<doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__doosan_somacube_rl__msg__SafetyEvent
    std::shared_ptr<doosan_somacube_rl::msg::SafetyEvent_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SafetyEvent_ & other) const
  {
    if (this->type != other.type) {
      return false;
    }
    if (this->detail != other.detail) {
      return false;
    }
    if (this->severity != other.severity) {
      return false;
    }
    if (this->stamp != other.stamp) {
      return false;
    }
    return true;
  }
  bool operator!=(const SafetyEvent_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SafetyEvent_

// alias to use template instance with default allocator
using SafetyEvent =
  doosan_somacube_rl::msg::SafetyEvent_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace doosan_somacube_rl

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__STRUCT_HPP_
