// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from doosan_somacube_rl:msg/RegisterQuality.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__TRAITS_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "doosan_somacube_rl/msg/detail/register_quality__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace doosan_somacube_rl
{

namespace msg
{

inline void to_flow_style_yaml(
  const RegisterQuality & msg,
  std::ostream & out)
{
  out << "{";
  // member: mean_point2plane_m
  {
    out << "mean_point2plane_m: ";
    rosidl_generator_traits::value_to_yaml(msg.mean_point2plane_m, out);
    out << ", ";
  }

  // member: chamfer_bidir_m
  {
    out << "chamfer_bidir_m: ";
    rosidl_generator_traits::value_to_yaml(msg.chamfer_bidir_m, out);
    out << ", ";
  }

  // member: inlier_ratio
  {
    out << "inlier_ratio: ";
    rosidl_generator_traits::value_to_yaml(msg.inlier_ratio, out);
    out << ", ";
  }

  // member: icp_residual_std
  {
    out << "icp_residual_std: ";
    rosidl_generator_traits::value_to_yaml(msg.icp_residual_std, out);
    out << ", ";
  }

  // member: geodesic_deg
  {
    out << "geodesic_deg: ";
    rosidl_generator_traits::value_to_yaml(msg.geodesic_deg, out);
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
  const RegisterQuality & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: mean_point2plane_m
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "mean_point2plane_m: ";
    rosidl_generator_traits::value_to_yaml(msg.mean_point2plane_m, out);
    out << "\n";
  }

  // member: chamfer_bidir_m
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "chamfer_bidir_m: ";
    rosidl_generator_traits::value_to_yaml(msg.chamfer_bidir_m, out);
    out << "\n";
  }

  // member: inlier_ratio
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "inlier_ratio: ";
    rosidl_generator_traits::value_to_yaml(msg.inlier_ratio, out);
    out << "\n";
  }

  // member: icp_residual_std
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "icp_residual_std: ";
    rosidl_generator_traits::value_to_yaml(msg.icp_residual_std, out);
    out << "\n";
  }

  // member: geodesic_deg
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "geodesic_deg: ";
    rosidl_generator_traits::value_to_yaml(msg.geodesic_deg, out);
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

inline std::string to_yaml(const RegisterQuality & msg, bool use_flow_style = false)
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
  const doosan_somacube_rl::msg::RegisterQuality & msg,
  std::ostream & out, size_t indentation = 0)
{
  doosan_somacube_rl::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use doosan_somacube_rl::msg::to_yaml() instead")]]
inline std::string to_yaml(const doosan_somacube_rl::msg::RegisterQuality & msg)
{
  return doosan_somacube_rl::msg::to_yaml(msg);
}

template<>
inline const char * data_type<doosan_somacube_rl::msg::RegisterQuality>()
{
  return "doosan_somacube_rl::msg::RegisterQuality";
}

template<>
inline const char * name<doosan_somacube_rl::msg::RegisterQuality>()
{
  return "doosan_somacube_rl/msg/RegisterQuality";
}

template<>
struct has_fixed_size<doosan_somacube_rl::msg::RegisterQuality>
  : std::integral_constant<bool, has_fixed_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct has_bounded_size<doosan_somacube_rl::msg::RegisterQuality>
  : std::integral_constant<bool, has_bounded_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct is_message<doosan_somacube_rl::msg::RegisterQuality>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__TRAITS_HPP_
