// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from doosan_somacube_rl:msg/RegisterQuality.idl
// generated code does not contain a copyright notice

#ifndef DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__FUNCTIONS_H_
#define DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "doosan_somacube_rl/msg/rosidl_generator_c__visibility_control.h"

#include "doosan_somacube_rl/msg/detail/register_quality__struct.h"

/// Initialize msg/RegisterQuality message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * doosan_somacube_rl__msg__RegisterQuality
 * )) before or use
 * doosan_somacube_rl__msg__RegisterQuality__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__RegisterQuality__init(doosan_somacube_rl__msg__RegisterQuality * msg);

/// Finalize msg/RegisterQuality message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
void
doosan_somacube_rl__msg__RegisterQuality__fini(doosan_somacube_rl__msg__RegisterQuality * msg);

/// Create msg/RegisterQuality message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * doosan_somacube_rl__msg__RegisterQuality__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
doosan_somacube_rl__msg__RegisterQuality *
doosan_somacube_rl__msg__RegisterQuality__create();

/// Destroy msg/RegisterQuality message.
/**
 * It calls
 * doosan_somacube_rl__msg__RegisterQuality__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
void
doosan_somacube_rl__msg__RegisterQuality__destroy(doosan_somacube_rl__msg__RegisterQuality * msg);

/// Check for msg/RegisterQuality message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__RegisterQuality__are_equal(const doosan_somacube_rl__msg__RegisterQuality * lhs, const doosan_somacube_rl__msg__RegisterQuality * rhs);

/// Copy a msg/RegisterQuality message.
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
doosan_somacube_rl__msg__RegisterQuality__copy(
  const doosan_somacube_rl__msg__RegisterQuality * input,
  doosan_somacube_rl__msg__RegisterQuality * output);

/// Initialize array of msg/RegisterQuality messages.
/**
 * It allocates the memory for the number of elements and calls
 * doosan_somacube_rl__msg__RegisterQuality__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__RegisterQuality__Sequence__init(doosan_somacube_rl__msg__RegisterQuality__Sequence * array, size_t size);

/// Finalize array of msg/RegisterQuality messages.
/**
 * It calls
 * doosan_somacube_rl__msg__RegisterQuality__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
void
doosan_somacube_rl__msg__RegisterQuality__Sequence__fini(doosan_somacube_rl__msg__RegisterQuality__Sequence * array);

/// Create array of msg/RegisterQuality messages.
/**
 * It allocates the memory for the array and calls
 * doosan_somacube_rl__msg__RegisterQuality__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
doosan_somacube_rl__msg__RegisterQuality__Sequence *
doosan_somacube_rl__msg__RegisterQuality__Sequence__create(size_t size);

/// Destroy array of msg/RegisterQuality messages.
/**
 * It calls
 * doosan_somacube_rl__msg__RegisterQuality__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
void
doosan_somacube_rl__msg__RegisterQuality__Sequence__destroy(doosan_somacube_rl__msg__RegisterQuality__Sequence * array);

/// Check for msg/RegisterQuality message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_doosan_somacube_rl
bool
doosan_somacube_rl__msg__RegisterQuality__Sequence__are_equal(const doosan_somacube_rl__msg__RegisterQuality__Sequence * lhs, const doosan_somacube_rl__msg__RegisterQuality__Sequence * rhs);

/// Copy an array of msg/RegisterQuality messages.
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
doosan_somacube_rl__msg__RegisterQuality__Sequence__copy(
  const doosan_somacube_rl__msg__RegisterQuality__Sequence * input,
  doosan_somacube_rl__msg__RegisterQuality__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // DOOSAN_SOMACUBE_RL__MSG__DETAIL__REGISTER_QUALITY__FUNCTIONS_H_
