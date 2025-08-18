// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from doosan_somacube_rl:msg/RegisterQuality.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__STRUCT_H_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in msg/RegisterQuality in the package doosan_somacube_rl.
typedef struct doosan_somacube_rl__msg__RegisterQuality
{
  float mean_point2plane_m;
  float chamfer_bidir_m;
  float inlier_ratio;
  float icp_residual_std;
  float geodesic_deg;
  builtin_interfaces__msg__Time stamp;
} doosan_somacube_rl__msg__RegisterQuality;

// Struct for a sequence of doosan_somacube_rl__msg__RegisterQuality.
typedef struct doosan_somacube_rl__msg__RegisterQuality__Sequence
{
  doosan_somacube_rl__msg__RegisterQuality * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} doosan_somacube_rl__msg__RegisterQuality__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__STRUCT_H_
