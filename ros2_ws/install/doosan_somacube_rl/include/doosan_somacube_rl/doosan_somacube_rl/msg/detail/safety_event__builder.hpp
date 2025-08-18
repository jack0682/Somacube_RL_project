// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from doosan_somacube_rl:msg/SafetyEvent.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__BUILDER_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "doosan_somacube_rl/msg/detail/safety_event__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace doosan_somacube_rl
{

namespace msg
{

namespace builder
{

class Init_SafetyEvent_stamp
{
public:
  explicit Init_SafetyEvent_stamp(::doosan_somacube_rl::msg::SafetyEvent & msg)
  : msg_(msg)
  {}
  ::doosan_somacube_rl::msg::SafetyEvent stamp(::doosan_somacube_rl::msg::SafetyEvent::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::doosan_somacube_rl::msg::SafetyEvent msg_;
};

class Init_SafetyEvent_severity
{
public:
  explicit Init_SafetyEvent_severity(::doosan_somacube_rl::msg::SafetyEvent & msg)
  : msg_(msg)
  {}
  Init_SafetyEvent_stamp severity(::doosan_somacube_rl::msg::SafetyEvent::_severity_type arg)
  {
    msg_.severity = std::move(arg);
    return Init_SafetyEvent_stamp(msg_);
  }

private:
  ::doosan_somacube_rl::msg::SafetyEvent msg_;
};

class Init_SafetyEvent_detail
{
public:
  explicit Init_SafetyEvent_detail(::doosan_somacube_rl::msg::SafetyEvent & msg)
  : msg_(msg)
  {}
  Init_SafetyEvent_severity detail(::doosan_somacube_rl::msg::SafetyEvent::_detail_type arg)
  {
    msg_.detail = std::move(arg);
    return Init_SafetyEvent_severity(msg_);
  }

private:
  ::doosan_somacube_rl::msg::SafetyEvent msg_;
};

class Init_SafetyEvent_type
{
public:
  Init_SafetyEvent_type()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SafetyEvent_detail type(::doosan_somacube_rl::msg::SafetyEvent::_type_type arg)
  {
    msg_.type = std::move(arg);
    return Init_SafetyEvent_detail(msg_);
  }

private:
  ::doosan_somacube_rl::msg::SafetyEvent msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::doosan_somacube_rl::msg::SafetyEvent>()
{
  return doosan_somacube_rl::msg::builder::Init_SafetyEvent_type();
}

}  // namespace doosan_somacube_rl

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__BUILDER_HPP_
