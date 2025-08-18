// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from od_msg:srv/SrvDepthPosition.idl
// generated code does not contain a copyright notice

#ifndef OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__STRUCT_HPP_
#define OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__od_msg__srv__SrvDepthPosition_Request __attribute__((deprecated))
#else
# define DEPRECATED__od_msg__srv__SrvDepthPosition_Request __declspec(deprecated)
#endif

namespace od_msg
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct SrvDepthPosition_Request_
{
  using Type = SrvDepthPosition_Request_<ContainerAllocator>;

  explicit SrvDepthPosition_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->target = "";
    }
  }

  explicit SrvDepthPosition_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : target(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->target = "";
    }
  }

  // field types and members
  using _target_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _target_type target;

  // setters for named parameter idiom
  Type & set__target(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->target = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__od_msg__srv__SrvDepthPosition_Request
    std::shared_ptr<od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__od_msg__srv__SrvDepthPosition_Request
    std::shared_ptr<od_msg::srv::SrvDepthPosition_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SrvDepthPosition_Request_ & other) const
  {
    if (this->target != other.target) {
      return false;
    }
    return true;
  }
  bool operator!=(const SrvDepthPosition_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SrvDepthPosition_Request_

// alias to use template instance with default allocator
using SrvDepthPosition_Request =
  od_msg::srv::SrvDepthPosition_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace od_msg


#ifndef _WIN32
# define DEPRECATED__od_msg__srv__SrvDepthPosition_Response __attribute__((deprecated))
#else
# define DEPRECATED__od_msg__srv__SrvDepthPosition_Response __declspec(deprecated)
#endif

namespace od_msg
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct SrvDepthPosition_Response_
{
  using Type = SrvDepthPosition_Response_<ContainerAllocator>;

  explicit SrvDepthPosition_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
  }

  explicit SrvDepthPosition_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
    (void)_alloc;
  }

  // field types and members
  using _depth_position_type =
    std::vector<double, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<double>>;
  _depth_position_type depth_position;

  // setters for named parameter idiom
  Type & set__depth_position(
    const std::vector<double, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<double>> & _arg)
  {
    this->depth_position = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__od_msg__srv__SrvDepthPosition_Response
    std::shared_ptr<od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__od_msg__srv__SrvDepthPosition_Response
    std::shared_ptr<od_msg::srv::SrvDepthPosition_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SrvDepthPosition_Response_ & other) const
  {
    if (this->depth_position != other.depth_position) {
      return false;
    }
    return true;
  }
  bool operator!=(const SrvDepthPosition_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SrvDepthPosition_Response_

// alias to use template instance with default allocator
using SrvDepthPosition_Response =
  od_msg::srv::SrvDepthPosition_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace od_msg

namespace od_msg
{

namespace srv
{

struct SrvDepthPosition
{
  using Request = od_msg::srv::SrvDepthPosition_Request;
  using Response = od_msg::srv::SrvDepthPosition_Response;
};

}  // namespace srv

}  // namespace od_msg

#endif  // OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__STRUCT_HPP_
