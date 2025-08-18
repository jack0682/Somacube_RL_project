// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from doosan_somacube_rl:msg/PolicyCmd.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__STRUCT_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__doosan_somacube_rl__msg__PolicyCmd __attribute__((deprecated))
#else
# define DEPRECATED__doosan_somacube_rl__msg__PolicyCmd __declspec(deprecated)
#endif

namespace doosan_somacube_rl
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct PolicyCmd_
{
  using Type = PolicyCmd_<ContainerAllocator>;

  explicit PolicyCmd_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->dx = 0.0f;
      this->dy = 0.0f;
      this->dz = 0.0f;
      this->droll = 0.0f;
      this->dpitch = 0.0f;
      this->dyaw = 0.0f;
      this->d_kp = 0.0f;
      this->d_kd = 0.0f;
    }
  }

  explicit PolicyCmd_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->dx = 0.0f;
      this->dy = 0.0f;
      this->dz = 0.0f;
      this->droll = 0.0f;
      this->dpitch = 0.0f;
      this->dyaw = 0.0f;
      this->d_kp = 0.0f;
      this->d_kd = 0.0f;
    }
  }

  // field types and members
  using _dx_type =
    float;
  _dx_type dx;
  using _dy_type =
    float;
  _dy_type dy;
  using _dz_type =
    float;
  _dz_type dz;
  using _droll_type =
    float;
  _droll_type droll;
  using _dpitch_type =
    float;
  _dpitch_type dpitch;
  using _dyaw_type =
    float;
  _dyaw_type dyaw;
  using _d_kp_type =
    float;
  _d_kp_type d_kp;
  using _d_kd_type =
    float;
  _d_kd_type d_kd;
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;

  // setters for named parameter idiom
  Type & set__dx(
    const float & _arg)
  {
    this->dx = _arg;
    return *this;
  }
  Type & set__dy(
    const float & _arg)
  {
    this->dy = _arg;
    return *this;
  }
  Type & set__dz(
    const float & _arg)
  {
    this->dz = _arg;
    return *this;
  }
  Type & set__droll(
    const float & _arg)
  {
    this->droll = _arg;
    return *this;
  }
  Type & set__dpitch(
    const float & _arg)
  {
    this->dpitch = _arg;
    return *this;
  }
  Type & set__dyaw(
    const float & _arg)
  {
    this->dyaw = _arg;
    return *this;
  }
  Type & set__d_kp(
    const float & _arg)
  {
    this->d_kp = _arg;
    return *this;
  }
  Type & set__d_kd(
    const float & _arg)
  {
    this->d_kd = _arg;
    return *this;
  }
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator> *;
  using ConstRawPtr =
    const doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__doosan_somacube_rl__msg__PolicyCmd
    std::shared_ptr<doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__doosan_somacube_rl__msg__PolicyCmd
    std::shared_ptr<doosan_somacube_rl::msg::PolicyCmd_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const PolicyCmd_ & other) const
  {
    if (this->dx != other.dx) {
      return false;
    }
    if (this->dy != other.dy) {
      return false;
    }
    if (this->dz != other.dz) {
      return false;
    }
    if (this->droll != other.droll) {
      return false;
    }
    if (this->dpitch != other.dpitch) {
      return false;
    }
    if (this->dyaw != other.dyaw) {
      return false;
    }
    if (this->d_kp != other.d_kp) {
      return false;
    }
    if (this->d_kd != other.d_kd) {
      return false;
    }
    if (this->header != other.header) {
      return false;
    }
    return true;
  }
  bool operator!=(const PolicyCmd_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct PolicyCmd_

// alias to use template instance with default allocator
using PolicyCmd =
  doosan_somacube_rl::msg::PolicyCmd_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace doosan_somacube_rl

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__STRUCT_HPP_
