// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from od_msg:srv/SrvDepthPosition.idl
// generated code does not contain a copyright notice

#ifndef OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__TRAITS_HPP_
#define OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "od_msg/srv/detail/srv_depth_position__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace od_msg
{

namespace srv
{

inline void to_flow_style_yaml(
  const SrvDepthPosition_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: target
  {
    out << "target: ";
    rosidl_generator_traits::value_to_yaml(msg.target, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const SrvDepthPosition_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: target
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "target: ";
    rosidl_generator_traits::value_to_yaml(msg.target, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const SrvDepthPosition_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace od_msg

namespace rosidl_generator_traits
{

[[deprecated("use od_msg::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const od_msg::srv::SrvDepthPosition_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  od_msg::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use od_msg::srv::to_yaml() instead")]]
inline std::string to_yaml(const od_msg::srv::SrvDepthPosition_Request & msg)
{
  return od_msg::srv::to_yaml(msg);
}

template<>
inline const char * data_type<od_msg::srv::SrvDepthPosition_Request>()
{
  return "od_msg::srv::SrvDepthPosition_Request";
}

template<>
inline const char * name<od_msg::srv::SrvDepthPosition_Request>()
{
  return "od_msg/srv/SrvDepthPosition_Request";
}

template<>
struct has_fixed_size<od_msg::srv::SrvDepthPosition_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<od_msg::srv::SrvDepthPosition_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<od_msg::srv::SrvDepthPosition_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace od_msg
{

namespace srv
{

inline void to_flow_style_yaml(
  const SrvDepthPosition_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: depth_position
  {
    if (msg.depth_position.size() == 0) {
      out << "depth_position: []";
    } else {
      out << "depth_position: [";
      size_t pending_items = msg.depth_position.size();
      for (auto item : msg.depth_position) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const SrvDepthPosition_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: depth_position
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.depth_position.size() == 0) {
      out << "depth_position: []\n";
    } else {
      out << "depth_position:\n";
      for (auto item : msg.depth_position) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const SrvDepthPosition_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace od_msg

namespace rosidl_generator_traits
{

[[deprecated("use od_msg::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const od_msg::srv::SrvDepthPosition_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  od_msg::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use od_msg::srv::to_yaml() instead")]]
inline std::string to_yaml(const od_msg::srv::SrvDepthPosition_Response & msg)
{
  return od_msg::srv::to_yaml(msg);
}

template<>
inline const char * data_type<od_msg::srv::SrvDepthPosition_Response>()
{
  return "od_msg::srv::SrvDepthPosition_Response";
}

template<>
inline const char * name<od_msg::srv::SrvDepthPosition_Response>()
{
  return "od_msg/srv/SrvDepthPosition_Response";
}

template<>
struct has_fixed_size<od_msg::srv::SrvDepthPosition_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<od_msg::srv::SrvDepthPosition_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<od_msg::srv::SrvDepthPosition_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<od_msg::srv::SrvDepthPosition>()
{
  return "od_msg::srv::SrvDepthPosition";
}

template<>
inline const char * name<od_msg::srv::SrvDepthPosition>()
{
  return "od_msg/srv/SrvDepthPosition";
}

template<>
struct has_fixed_size<od_msg::srv::SrvDepthPosition>
  : std::integral_constant<
    bool,
    has_fixed_size<od_msg::srv::SrvDepthPosition_Request>::value &&
    has_fixed_size<od_msg::srv::SrvDepthPosition_Response>::value
  >
{
};

template<>
struct has_bounded_size<od_msg::srv::SrvDepthPosition>
  : std::integral_constant<
    bool,
    has_bounded_size<od_msg::srv::SrvDepthPosition_Request>::value &&
    has_bounded_size<od_msg::srv::SrvDepthPosition_Response>::value
  >
{
};

template<>
struct is_service<od_msg::srv::SrvDepthPosition>
  : std::true_type
{
};

template<>
struct is_service_request<od_msg::srv::SrvDepthPosition_Request>
  : std::true_type
{
};

template<>
struct is_service_response<od_msg::srv::SrvDepthPosition_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__TRAITS_HPP_
