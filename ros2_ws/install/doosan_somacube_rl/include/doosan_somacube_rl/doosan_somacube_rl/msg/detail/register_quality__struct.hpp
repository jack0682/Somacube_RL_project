// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from doosan_somacube_rl:msg/RegisterQuality.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__STRUCT_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__STRUCT_HPP_

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
# define DEPRECATED__doosan_somacube_rl__msg__RegisterQuality __attribute__((deprecated))
#else
# define DEPRECATED__doosan_somacube_rl__msg__RegisterQuality __declspec(deprecated)
#endif

namespace doosan_somacube_rl
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct RegisterQuality_
{
  using Type = RegisterQuality_<ContainerAllocator>;

  explicit RegisterQuality_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : stamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->mean_point2plane_m = 0.0f;
      this->chamfer_bidir_m = 0.0f;
      this->inlier_ratio = 0.0f;
      this->icp_residual_std = 0.0f;
      this->geodesic_deg = 0.0f;
    }
  }

  explicit RegisterQuality_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : stamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->mean_point2plane_m = 0.0f;
      this->chamfer_bidir_m = 0.0f;
      this->inlier_ratio = 0.0f;
      this->icp_residual_std = 0.0f;
      this->geodesic_deg = 0.0f;
    }
  }

  // field types and members
  using _mean_point2plane_m_type =
    float;
  _mean_point2plane_m_type mean_point2plane_m;
  using _chamfer_bidir_m_type =
    float;
  _chamfer_bidir_m_type chamfer_bidir_m;
  using _inlier_ratio_type =
    float;
  _inlier_ratio_type inlier_ratio;
  using _icp_residual_std_type =
    float;
  _icp_residual_std_type icp_residual_std;
  using _geodesic_deg_type =
    float;
  _geodesic_deg_type geodesic_deg;
  using _stamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _stamp_type stamp;

  // setters for named parameter idiom
  Type & set__mean_point2plane_m(
    const float & _arg)
  {
    this->mean_point2plane_m = _arg;
    return *this;
  }
  Type & set__chamfer_bidir_m(
    const float & _arg)
  {
    this->chamfer_bidir_m = _arg;
    return *this;
  }
  Type & set__inlier_ratio(
    const float & _arg)
  {
    this->inlier_ratio = _arg;
    return *this;
  }
  Type & set__icp_residual_std(
    const float & _arg)
  {
    this->icp_residual_std = _arg;
    return *this;
  }
  Type & set__geodesic_deg(
    const float & _arg)
  {
    this->geodesic_deg = _arg;
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
    doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator> *;
  using ConstRawPtr =
    const doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__doosan_somacube_rl__msg__RegisterQuality
    std::shared_ptr<doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__doosan_somacube_rl__msg__RegisterQuality
    std::shared_ptr<doosan_somacube_rl::msg::RegisterQuality_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const RegisterQuality_ & other) const
  {
    if (this->mean_point2plane_m != other.mean_point2plane_m) {
      return false;
    }
    if (this->chamfer_bidir_m != other.chamfer_bidir_m) {
      return false;
    }
    if (this->inlier_ratio != other.inlier_ratio) {
      return false;
    }
    if (this->icp_residual_std != other.icp_residual_std) {
      return false;
    }
    if (this->geodesic_deg != other.geodesic_deg) {
      return false;
    }
    if (this->stamp != other.stamp) {
      return false;
    }
    return true;
  }
  bool operator!=(const RegisterQuality_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct RegisterQuality_

// alias to use template instance with default allocator
using RegisterQuality =
  doosan_somacube_rl::msg::RegisterQuality_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace doosan_somacube_rl

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__STRUCT_HPP_
