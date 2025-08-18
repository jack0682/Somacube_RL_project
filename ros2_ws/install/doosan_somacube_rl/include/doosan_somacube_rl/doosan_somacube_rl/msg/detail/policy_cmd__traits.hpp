// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from doosan_somacube_rl:msg/PolicyCmd.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__TRAITS_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "doosan_somacube_rl/msg/detail/policy_cmd__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace doosan_somacube_rl
{

namespace msg
{

inline void to_flow_style_yaml(
  const PolicyCmd & msg,
  std::ostream & out)
{
  out << "{";
  // member: dx
  {
    out << "dx: ";
    rosidl_generator_traits::value_to_yaml(msg.dx, out);
    out << ", ";
  }

  // member: dy
  {
    out << "dy: ";
    rosidl_generator_traits::value_to_yaml(msg.dy, out);
    out << ", ";
  }

  // member: dz
  {
    out << "dz: ";
    rosidl_generator_traits::value_to_yaml(msg.dz, out);
    out << ", ";
  }

  // member: droll
  {
    out << "droll: ";
    rosidl_generator_traits::value_to_yaml(msg.droll, out);
    out << ", ";
  }

  // member: dpitch
  {
    out << "dpitch: ";
    rosidl_generator_traits::value_to_yaml(msg.dpitch, out);
    out << ", ";
  }

  // member: dyaw
  {
    out << "dyaw: ";
    rosidl_generator_traits::value_to_yaml(msg.dyaw, out);
    out << ", ";
  }

  // member: d_kp
  {
    out << "d_kp: ";
    rosidl_generator_traits::value_to_yaml(msg.d_kp, out);
    out << ", ";
  }

  // member: d_kd
  {
    out << "d_kd: ";
    rosidl_generator_traits::value_to_yaml(msg.d_kd, out);
    out << ", ";
  }

  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const PolicyCmd & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: dx
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "dx: ";
    rosidl_generator_traits::value_to_yaml(msg.dx, out);
    out << "\n";
  }

  // member: dy
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "dy: ";
    rosidl_generator_traits::value_to_yaml(msg.dy, out);
    out << "\n";
  }

  // member: dz
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "dz: ";
    rosidl_generator_traits::value_to_yaml(msg.dz, out);
    out << "\n";
  }

  // member: droll
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "droll: ";
    rosidl_generator_traits::value_to_yaml(msg.droll, out);
    out << "\n";
  }

  // member: dpitch
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "dpitch: ";
    rosidl_generator_traits::value_to_yaml(msg.dpitch, out);
    out << "\n";
  }

  // member: dyaw
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "dyaw: ";
    rosidl_generator_traits::value_to_yaml(msg.dyaw, out);
    out << "\n";
  }

  // member: d_kp
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "d_kp: ";
    rosidl_generator_traits::value_to_yaml(msg.d_kp, out);
    out << "\n";
  }

  // member: d_kd
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "d_kd: ";
    rosidl_generator_traits::value_to_yaml(msg.d_kd, out);
    out << "\n";
  }

  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const PolicyCmd & msg, bool use_flow_style = false)
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
  const doosan_somacube_rl::msg::PolicyCmd & msg,
  std::ostream & out, size_t indentation = 0)
{
  doosan_somacube_rl::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use doosan_somacube_rl::msg::to_yaml() instead")]]
inline std::string to_yaml(const doosan_somacube_rl::msg::PolicyCmd & msg)
{
  return doosan_somacube_rl::msg::to_yaml(msg);
}

template<>
inline const char * data_type<doosan_somacube_rl::msg::PolicyCmd>()
{
  return "doosan_somacube_rl::msg::PolicyCmd";
}

template<>
inline const char * name<doosan_somacube_rl::msg::PolicyCmd>()
{
  return "doosan_somacube_rl/msg/PolicyCmd";
}

template<>
struct has_fixed_size<doosan_somacube_rl::msg::PolicyCmd>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<doosan_somacube_rl::msg::PolicyCmd>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<doosan_somacube_rl::msg::PolicyCmd>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__TRAITS_HPP_
