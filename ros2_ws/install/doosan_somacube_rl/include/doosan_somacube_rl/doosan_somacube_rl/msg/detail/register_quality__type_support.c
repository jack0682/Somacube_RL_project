// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from doosan_somacube_rl:msg/RegisterQuality.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "doosan_somacube_rl/msg/detail/register_quality__rosidl_typesupport_introspection_c.h"
#include "doosan_somacube_rl/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "doosan_somacube_rl/msg/detail/register_quality__functions.h"
#include "doosan_somacube_rl/msg/detail/register_quality__struct.h"


// Include directives for member types
// Member `stamp`
#include "builtin_interfaces/msg/time.h"
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  doosan_somacube_rl__msg__RegisterQuality__init(message_memory);
}

void doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_fini_function(void * message_memory)
{
  doosan_somacube_rl__msg__RegisterQuality__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_message_member_array[6] = {
  {
    "mean_point2plane_m",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(doosan_somacube_rl__msg__RegisterQuality, mean_point2plane_m),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "chamfer_bidir_m",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(doosan_somacube_rl__msg__RegisterQuality, chamfer_bidir_m),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "inlier_ratio",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(doosan_somacube_rl__msg__RegisterQuality, inlier_ratio),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "icp_residual_std",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(doosan_somacube_rl__msg__RegisterQuality, icp_residual_std),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "geodesic_deg",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(doosan_somacube_rl__msg__RegisterQuality, geodesic_deg),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "stamp",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(doosan_somacube_rl__msg__RegisterQuality, stamp),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_message_members = {
  "doosan_somacube_rl__msg",  // message namespace
  "RegisterQuality",  // message name
  6,  // number of fields
  sizeof(doosan_somacube_rl__msg__RegisterQuality),
  doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_message_member_array,  // message members
  doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_init_function,  // function to initialize message memory (memory has to be allocated)
  doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_message_type_support_handle = {
  0,
  &doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_doosan_somacube_rl
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, doosan_somacube_rl, msg, RegisterQuality)() {
  doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_message_member_array[5].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, builtin_interfaces, msg, Time)();
  if (!doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_message_type_support_handle.typesupport_identifier) {
    doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &doosan_somacube_rl__msg__RegisterQuality__rosidl_typesupport_introspection_c__RegisterQuality_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
