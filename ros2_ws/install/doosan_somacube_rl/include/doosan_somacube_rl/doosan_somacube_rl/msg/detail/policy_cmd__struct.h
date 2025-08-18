// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from doosan_somacube_rl:msg/PolicyCmd.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__STRUCT_H_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in msg/PolicyCmd in the package doosan_somacube_rl.
typedef struct doosan_somacube_rl__msg__PolicyCmd
{
  float dx;
  float dy;
  float dz;
  float droll;
  float dpitch;
  float dyaw;
  float d_kp;
  float d_kd;
  std_msgs__msg__Header header;
} doosan_somacube_rl__msg__PolicyCmd;

// Struct for a sequence of doosan_somacube_rl__msg__PolicyCmd.
typedef struct doosan_somacube_rl__msg__PolicyCmd__Sequence
{
  doosan_somacube_rl__msg__PolicyCmd * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} doosan_somacube_rl__msg__PolicyCmd__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__STRUCT_H_
