// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from doosan_somacube_rl:msg/SafetyEvent.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__TRAITS_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "doosan_somacube_rl/msg/detail/safety_event__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace doosan_somacube_rl
{

namespace msg
{

inline void to_flow_style_yaml(
  const SafetyEvent & msg,
  std::ostream & out)
{
  out << "{";
  // member: type
  {
    out << "type: ";
    rosidl_generator_traits::value_to_yaml(msg.type, out);
    out << ", ";
  }

  // member: detail
  {
    out << "detail: ";
    rosidl_generator_traits::value_to_yaml(msg.detail, out);
    out << ", ";
  }

  // member: severity
  {
    out << "severity: ";
    rosidl_generator_traits::value_to_yaml(msg.severity, out);
    out << ", ";
  }

  // member: stamp
  {
    out << "stamp: ";
    to_flow_style_yaml(msg.stamp, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const SafetyEvent & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: type
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "type: ";
    rosidl_generator_traits::value_to_yaml(msg.type, out);
    out << "\n";
  }

  // member: detail
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "detail: ";
    rosidl_generator_traits::value_to_yaml(msg.detail, out);
    out << "\n";
  }

  // member: severity
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "severity: ";
    rosidl_generator_traits::value_to_yaml(msg.severity, out);
    out << "\n";
  }

  // member: stamp
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "stamp:\n";
    to_block_style_yaml(msg.stamp, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const SafetyEvent & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace doosan_somacube_rl

namespace rosidl_generator_traits
{

[[deprecated("use doosan_somacube_rl::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const doosan_somacube_rl::msg::SafetyEvent & msg,
  std::ostream & out, size_t indentation = 0)
{
  doosan_somacube_rl::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use doosan_somacube_rl::msg::to_yaml() instead")]]
inline std::string to_yaml(const doosan_somacube_rl::msg::SafetyEvent & msg)
{
  return doosan_somacube_rl::msg::to_yaml(msg);
}

template<>
inline const char * data_type<doosan_somacube_rl::msg::SafetyEvent>()
{
  return "doosan_somacube_rl::msg::SafetyEvent";
}

template<>
inline const char * name<doosan_somacube_rl::msg::SafetyEvent>()
{
  return "doosan_somacube_rl/msg/SafetyEvent";
}

template<>
struct has_fixed_size<doosan_somacube_rl::msg::SafetyEvent>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<doosan_somacube_rl::msg::SafetyEvent>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<doosan_somacube_rl::msg::SafetyEvent>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__TRAITS_HPP_
