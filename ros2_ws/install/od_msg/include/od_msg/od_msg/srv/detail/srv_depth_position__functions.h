// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from od_msg:srv/SrvDepthPosition.idl
// generated code does not contain a copyright notice

#ifndef OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__FUNCTIONS_H_
#define OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "od_msg/msg/rosidl_generator_c__visibility_control.h"

#include "od_msg/srv/detail/srv_depth_position__struct.h"

/// Initialize srv/SrvDepthPosition message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * od_msg__srv__SrvDepthPosition_Request
 * )) before or use
 * od_msg__srv__SrvDepthPosition_Request__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Request__init(od_msg__srv__SrvDepthPosition_Request * msg);

/// Finalize srv/SrvDepthPosition message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
void
od_msg__srv__SrvDepthPosition_Request__fini(od_msg__srv__SrvDepthPosition_Request * msg);

/// Create srv/SrvDepthPosition message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * od_msg__srv__SrvDepthPosition_Request__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
od_msg__srv__SrvDepthPosition_Request *
od_msg__srv__SrvDepthPosition_Request__create();

/// Destroy srv/SrvDepthPosition message.
/**
 * It calls
 * od_msg__srv__SrvDepthPosition_Request__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
void
od_msg__srv__SrvDepthPosition_Request__destroy(od_msg__srv__SrvDepthPosition_Request * msg);

/// Check for srv/SrvDepthPosition message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Request__are_equal(const od_msg__srv__SrvDepthPosition_Request * lhs, const od_msg__srv__SrvDepthPosition_Request * rhs);

/// Copy a srv/SrvDepthPosition message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Request__copy(
  const od_msg__srv__SrvDepthPosition_Request * input,
  od_msg__srv__SrvDepthPosition_Request * output);

/// Initialize array of srv/SrvDepthPosition messages.
/**
 * It allocates the memory for the number of elements and calls
 * od_msg__srv__SrvDepthPosition_Request__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Request__Sequence__init(od_msg__srv__SrvDepthPosition_Request__Sequence * array, size_t size);

/// Finalize array of srv/SrvDepthPosition messages.
/**
 * It calls
 * od_msg__srv__SrvDepthPosition_Request__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
void
od_msg__srv__SrvDepthPosition_Request__Sequence__fini(od_msg__srv__SrvDepthPosition_Request__Sequence * array);

/// Create array of srv/SrvDepthPosition messages.
/**
 * It allocates the memory for the array and calls
 * od_msg__srv__SrvDepthPosition_Request__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
od_msg__srv__SrvDepthPosition_Request__Sequence *
od_msg__srv__SrvDepthPosition_Request__Sequence__create(size_t size);

/// Destroy array of srv/SrvDepthPosition messages.
/**
 * It calls
 * od_msg__srv__SrvDepthPosition_Request__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
void
od_msg__srv__SrvDepthPosition_Request__Sequence__destroy(od_msg__srv__SrvDepthPosition_Request__Sequence * array);

/// Check for srv/SrvDepthPosition message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Request__Sequence__are_equal(const od_msg__srv__SrvDepthPosition_Request__Sequence * lhs, const od_msg__srv__SrvDepthPosition_Request__Sequence * rhs);

/// Copy an array of srv/SrvDepthPosition messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Request__Sequence__copy(
  const od_msg__srv__SrvDepthPosition_Request__Sequence * input,
  od_msg__srv__SrvDepthPosition_Request__Sequence * output);

/// Initialize srv/SrvDepthPosition message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * od_msg__srv__SrvDepthPosition_Response
 * )) before or use
 * od_msg__srv__SrvDepthPosition_Response__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Response__init(od_msg__srv__SrvDepthPosition_Response * msg);

/// Finalize srv/SrvDepthPosition message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
void
od_msg__srv__SrvDepthPosition_Response__fini(od_msg__srv__SrvDepthPosition_Response * msg);

/// Create srv/SrvDepthPosition message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * od_msg__srv__SrvDepthPosition_Response__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
od_msg__srv__SrvDepthPosition_Response *
od_msg__srv__SrvDepthPosition_Response__create();

/// Destroy srv/SrvDepthPosition message.
/**
 * It calls
 * od_msg__srv__SrvDepthPosition_Response__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
void
od_msg__srv__SrvDepthPosition_Response__destroy(od_msg__srv__SrvDepthPosition_Response * msg);

/// Check for srv/SrvDepthPosition message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Response__are_equal(const od_msg__srv__SrvDepthPosition_Response * lhs, const od_msg__srv__SrvDepthPosition_Response * rhs);

/// Copy a srv/SrvDepthPosition message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Response__copy(
  const od_msg__srv__SrvDepthPosition_Response * input,
  od_msg__srv__SrvDepthPosition_Response * output);

/// Initialize array of srv/SrvDepthPosition messages.
/**
 * It allocates the memory for the number of elements and calls
 * od_msg__srv__SrvDepthPosition_Response__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Response__Sequence__init(od_msg__srv__SrvDepthPosition_Response__Sequence * array, size_t size);

/// Finalize array of srv/SrvDepthPosition messages.
/**
 * It calls
 * od_msg__srv__SrvDepthPosition_Response__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
void
od_msg__srv__SrvDepthPosition_Response__Sequence__fini(od_msg__srv__SrvDepthPosition_Response__Sequence * array);

/// Create array of srv/SrvDepthPosition messages.
/**
 * It allocates the memory for the array and calls
 * od_msg__srv__SrvDepthPosition_Response__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
od_msg__srv__SrvDepthPosition_Response__Sequence *
od_msg__srv__SrvDepthPosition_Response__Sequence__create(size_t size);

/// Destroy array of srv/SrvDepthPosition messages.
/**
 * It calls
 * od_msg__srv__SrvDepthPosition_Response__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
void
od_msg__srv__SrvDepthPosition_Response__Sequence__destroy(od_msg__srv__SrvDepthPosition_Response__Sequence * array);

/// Check for srv/SrvDepthPosition message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Response__Sequence__are_equal(const od_msg__srv__SrvDepthPosition_Response__Sequence * lhs, const od_msg__srv__SrvDepthPosition_Response__Sequence * rhs);

/// Copy an array of srv/SrvDepthPosition messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_od_msg
bool
od_msg__srv__SrvDepthPosition_Response__Sequence__copy(
  const od_msg__srv__SrvDepthPosition_Response__Sequence * input,
  od_msg__srv__SrvDepthPosition_Response__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // OD_MSG__SRV__DETAIL__SRV_DEPTH_POSITION__FUNCTIONS_H_
