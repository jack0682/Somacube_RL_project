// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from doosan_somacube_rl:msg/SafetyEvent.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__STRUCT_H_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'type'
// Member 'detail'
#include "rosidl_runtime_c/string.h"
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in msg/SafetyEvent in the package doosan_somacube_rl.
typedef struct doosan_somacube_rl__msg__SafetyEvent
{
  rosidl_runtime_c__String type;
  rosidl_runtime_c__String detail;
  int32_t severity;
  builtin_interfaces__msg__Time stamp;
} doosan_somacube_rl__msg__SafetyEvent;

// Struct for a sequence of doosan_somacube_rl__msg__SafetyEvent.
typedef struct doosan_somacube_rl__msg__SafetyEvent__Sequence
{
  doosan_somacube_rl__msg__SafetyEvent * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} doosan_somacube_rl__msg__SafetyEvent__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__SAFETY_EVENT__STRUCT_H_
