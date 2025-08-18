// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from od_msg:srv/SrvDepthPosition.idl
// generated code does not contain a copyright notice

#ifndef OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__BUILDER_HPP_
#define OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "od_msg/srv/detail/srv_depth_position__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace od_msg
{

namespace srv
{

namespace builder
{

class Init_SrvDepthPosition_Request_target
{
public:
  Init_SrvDepthPosition_Request_target()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::od_msg::srv::SrvDepthPosition_Request target(::od_msg::srv::SrvDepthPosition_Request::_target_type arg)
  {
    msg_.target = std::move(arg);
    return std::move(msg_);
  }

private:
  ::od_msg::srv::SrvDepthPosition_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::od_msg::srv::SrvDepthPosition_Request>()
{
  return od_msg::srv::builder::Init_SrvDepthPosition_Request_target();
}

}  // namespace od_msg


namespace od_msg
{

namespace srv
{

namespace builder
{

class Init_SrvDepthPosition_Response_depth_position
{
public:
  Init_SrvDepthPosition_Response_depth_position()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::od_msg::srv::SrvDepthPosition_Response depth_position(::od_msg::srv::SrvDepthPosition_Response::_depth_position_type arg)
  {
    msg_.depth_position = std::move(arg);
    return std::move(msg_);
  }

private:
  ::od_msg::srv::SrvDepthPosition_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::od_msg::srv::SrvDepthPosition_Response>()
{
  return od_msg::srv::builder::Init_SrvDepthPosition_Response_depth_position();
}

}  // namespace od_msg

#endif  // OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__BUILDER_HPP_
