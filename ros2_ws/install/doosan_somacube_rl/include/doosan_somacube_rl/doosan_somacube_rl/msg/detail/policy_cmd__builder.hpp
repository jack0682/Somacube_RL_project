// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from doosan_somacube_rl:msg/PolicyCmd.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__BUILDER_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "doosan_somacube_rl/msg/detail/policy_cmd__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace doosan_somacube_rl
{

namespace msg
{

namespace builder
{

class Init_PolicyCmd_header
{
public:
  explicit Init_PolicyCmd_header(::doosan_somacube_rl::msg::PolicyCmd & msg)
  : msg_(msg)
  {}
  ::doosan_somacube_rl::msg::PolicyCmd header(::doosan_somacube_rl::msg::PolicyCmd::_header_type arg)
  {
    msg_.header = std::move(arg);
    return std::move(msg_);
  }

private:
  ::doosan_somacube_rl::msg::PolicyCmd msg_;
};

class Init_PolicyCmd_d_kd
{
public:
  explicit Init_PolicyCmd_d_kd(::doosan_somacube_rl::msg::PolicyCmd & msg)
  : msg_(msg)
  {}
  Init_PolicyCmd_header d_kd(::doosan_somacube_rl::msg::PolicyCmd::_d_kd_type arg)
  {
    msg_.d_kd = std::move(arg);
    return Init_PolicyCmd_header(msg_);
  }

private:
  ::doosan_somacube_rl::msg::PolicyCmd msg_;
};

class Init_PolicyCmd_d_kp
{
public:
  explicit Init_PolicyCmd_d_kp(::doosan_somacube_rl::msg::PolicyCmd & msg)
  : msg_(msg)
  {}
  Init_PolicyCmd_d_kd d_kp(::doosan_somacube_rl::msg::PolicyCmd::_d_kp_type arg)
  {
    msg_.d_kp = std::move(arg);
    return Init_PolicyCmd_d_kd(msg_);
  }

private:
  ::doosan_somacube_rl::msg::PolicyCmd msg_;
};

class Init_PolicyCmd_dyaw
{
public:
  explicit Init_PolicyCmd_dyaw(::doosan_somacube_rl::msg::PolicyCmd & msg)
  : msg_(msg)
  {}
  Init_PolicyCmd_d_kp dyaw(::doosan_somacube_rl::msg::PolicyCmd::_dyaw_type arg)
  {
    msg_.dyaw = std::move(arg);
    return Init_PolicyCmd_d_kp(msg_);
  }

private:
  ::doosan_somacube_rl::msg::PolicyCmd msg_;
};

class Init_PolicyCmd_dpitch
{
public:
  explicit Init_PolicyCmd_dpitch(::doosan_somacube_rl::msg::PolicyCmd & msg)
  : msg_(msg)
  {}
  Init_PolicyCmd_dyaw dpitch(::doosan_somacube_rl::msg::PolicyCmd::_dpitch_type arg)
  {
    msg_.dpitch = std::move(arg);
    return Init_PolicyCmd_dyaw(msg_);
  }

private:
  ::doosan_somacube_rl::msg::PolicyCmd msg_;
};

class Init_PolicyCmd_droll
{
public:
  explicit Init_PolicyCmd_droll(::doosan_somacube_rl::msg::PolicyCmd & msg)
  : msg_(msg)
  {}
  Init_PolicyCmd_dpitch droll(::doosan_somacube_rl::msg::PolicyCmd::_droll_type arg)
  {
    msg_.droll = std::move(arg);
    return Init_PolicyCmd_dpitch(msg_);
  }

private:
  ::doosan_somacube_rl::msg::PolicyCmd msg_;
};

class Init_PolicyCmd_dz
{
public:
  explicit Init_PolicyCmd_dz(::doosan_somacube_rl::msg::PolicyCmd & msg)
  : msg_(msg)
  {}
  Init_PolicyCmd_droll dz(::doosan_somacube_rl::msg::PolicyCmd::_dz_type arg)
  {
    msg_.dz = std::move(arg);
    return Init_PolicyCmd_droll(msg_);
  }

private:
  ::doosan_somacube_rl::msg::PolicyCmd msg_;
};

class Init_PolicyCmd_dy
{
public:
  explicit Init_PolicyCmd_dy(::doosan_somacube_rl::msg::PolicyCmd & msg)
  : msg_(msg)
  {}
  Init_PolicyCmd_dz dy(::doosan_somacube_rl::msg::PolicyCmd::_dy_type arg)
  {
    msg_.dy = std::move(arg);
    return Init_PolicyCmd_dz(msg_);
  }

private:
  ::doosan_somacube_rl::msg::PolicyCmd msg_;
};

class Init_PolicyCmd_dx
{
public:
  Init_PolicyCmd_dx()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PolicyCmd_dy dx(::doosan_somacube_rl::msg::PolicyCmd::_dx_type arg)
  {
    msg_.dx = std::move(arg);
    return Init_PolicyCmd_dy(msg_);
  }

private:
  ::doosan_somacube_rl::msg::PolicyCmd msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::doosan_somacube_rl::msg::PolicyCmd>()
{
  return doosan_somacube_rl::msg::builder::Init_PolicyCmd_dx();
}

}  // namespace doosan_somacube_rl

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__BUILDER_HPP_
