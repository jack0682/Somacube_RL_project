// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from od_msg:srv/SrvDepthPosition.idl
// generated code does not contain a copyright notice

#ifndef OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__STRUCT_H_
#define OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'target'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/SrvDepthPosition in the package od_msg.
typedef struct od_msg__srv__SrvDepthPosition_Request
{
  rosidl_runtime_c__String target;
} od_msg__srv__SrvDepthPosition_Request;

// Struct for a sequence of od_msg__srv__SrvDepthPosition_Request.
typedef struct od_msg__srv__SrvDepthPosition_Request__Sequence
{
  od_msg__srv__SrvDepthPosition_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} od_msg__srv__SrvDepthPosition_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'depth_position'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in srv/SrvDepthPosition in the package od_msg.
typedef struct od_msg__srv__SrvDepthPosition_Response
{
  rosidl_runtime_c__double__Sequence depth_position;
} od_msg__srv__SrvDepthPosition_Response;

// Struct for a sequence of od_msg__srv__SrvDepthPosition_Response.
typedef struct od_msg__srv__SrvDepthPosition_Response__Sequence
{
  od_msg__srv__SrvDepthPosition_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} od_msg__srv__SrvDepthPosition_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__STRUCT_H_
