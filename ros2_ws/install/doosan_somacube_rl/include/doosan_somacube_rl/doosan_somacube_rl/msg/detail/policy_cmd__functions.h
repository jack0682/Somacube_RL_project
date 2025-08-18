// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from doosan_somacube_rl:msg/PolicyCmd.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__FUNCTIONS_H_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "doosan_somacube_rl/msg/rosidl_generator_c__visibility_control.h"

#include "doosan_somacube_rl/msg/detail/policy_cmd__struct.h"

/// Initialize msg/PolicyCmd message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * doosan_somacube_rl__msg__PolicyCmd
 * )) before or use
 * doosan_somacube_rl__msg__PolicyCmd__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__PolicyCmd__init(doosan_somacube_rl__msg__PolicyCmd * msg);

/// Finalize msg/PolicyCmd message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
void
doosan_somacube_rl__msg__PolicyCmd__fini(doosan_somacube_rl__msg__PolicyCmd * msg);

/// Create msg/PolicyCmd message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * doosan_somacube_rl__msg__PolicyCmd__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
doosan_somacube_rl__msg__PolicyCmd *
doosan_somacube_rl__msg__PolicyCmd__create();

/// Destroy msg/PolicyCmd message.
/**
 * It calls
 * doosan_somacube_rl__msg__PolicyCmd__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
void
doosan_somacube_rl__msg__PolicyCmd__destroy(doosan_somacube_rl__msg__PolicyCmd * msg);

/// Check for msg/PolicyCmd message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__PolicyCmd__are_equal(const doosan_somacube_rl__msg__PolicyCmd * lhs, const doosan_somacube_rl__msg__PolicyCmd * rhs);

/// Copy a msg/PolicyCmd message.
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
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__PolicyCmd__copy(
  const doosan_somacube_rl__msg__PolicyCmd * input,
  doosan_somacube_rl__msg__PolicyCmd * output);

/// Initialize array of msg/PolicyCmd messages.
/**
 * It allocates the memory for the number of elements and calls
 * doosan_somacube_rl__msg__PolicyCmd__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__PolicyCmd__Sequence__init(doosan_somacube_rl__msg__PolicyCmd__Sequence * array, size_t size);

/// Finalize array of msg/PolicyCmd messages.
/**
 * It calls
 * doosan_somacube_rl__msg__PolicyCmd__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
void
doosan_somacube_rl__msg__PolicyCmd__Sequence__fini(doosan_somacube_rl__msg__PolicyCmd__Sequence * array);

/// Create array of msg/PolicyCmd messages.
/**
 * It allocates the memory for the array and calls
 * doosan_somacube_rl__msg__PolicyCmd__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
doosan_somacube_rl__msg__PolicyCmd__Sequence *
doosan_somacube_rl__msg__PolicyCmd__Sequence__create(size_t size);

/// Destroy array of msg/PolicyCmd messages.
/**
 * It calls
 * doosan_somacube_rl__msg__PolicyCmd__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
void
doosan_somacube_rl__msg__PolicyCmd__Sequence__destroy(doosan_somacube_rl__msg__PolicyCmd__Sequence * array);

/// Check for msg/PolicyCmd message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__PolicyCmd__Sequence__are_equal(const doosan_somacube_rl__msg__PolicyCmd__Sequence * lhs, const doosan_somacube_rl__msg__PolicyCmd__Sequence * rhs);

/// Copy an array of msg/PolicyCmd messages.
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
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__PolicyCmd__Sequence__copy(
  const doosan_somacube_rl__msg__PolicyCmd__Sequence * input,
  doosan_somacube_rl__msg__PolicyCmd__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__POLICY_CMD__FUNCTIONS_H_
