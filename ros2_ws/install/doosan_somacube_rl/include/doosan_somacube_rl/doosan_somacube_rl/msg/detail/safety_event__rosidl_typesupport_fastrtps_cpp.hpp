// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__rosidl_typesupport_fastrtps_cpp.hpp.em
// with input from doosan_somacube_rl:msg/SafetyEvent.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_

#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "doosan_somacube_rl/msg/rosidl_typesupport_fastrtps_cpp__visibility_control.h"
#include "doosan_somacube_rl/msg/detail/safety_event__struct.hpp"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

#include "fastcdr/Cdr.h"

namespace doosan_somacube_rl
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_doosan_somacube_rl
cdr_serialize(
  const doosan_somacube_rl::msg::SafetyEvent & ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_doosan_somacube_rl
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  doosan_somacube_rl::msg::SafetyEvent & ros_message);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_doosan_somacube_rl
get_serialized_size(
  const doosan_somacube_rl::msg::SafetyEvent & ros_message,
  size_t current_alignment);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_doosan_somacube_rl
max_serialized_size_SafetyEvent(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace doosan_somacube_rl

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_doosan_somacube_rl
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, doosan_somacube_rl, msg, SafetyEvent)();

#ifdef __cplusplus
}
#endif

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
