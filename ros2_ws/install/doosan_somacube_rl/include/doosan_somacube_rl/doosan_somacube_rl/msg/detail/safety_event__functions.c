// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from doosan_somacube_rl:msg/SafetyEvent.idl
// generated code does not contain a copyright notice
#include "doosan_somacube_rl/msg/detail/safety_event__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `type`
// Member `detail`
#include "rosidl_runtime_c/string_functions.h"
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
doosan_somacube_rl__msg__SafetyEvent__init(doosan_somacube_rl__msg__SafetyEvent * msg)
{
  if (!msg) {
    return false;
  }
  // type
  if (!rosidl_runtime_c__String__init(&msg->type)) {
    doosan_somacube_rl__msg__SafetyEvent__fini(msg);
    return false;
  }
  // detail
  if (!rosidl_runtime_c__String__init(&msg->detail)) {
    doosan_somacube_rl__msg__SafetyEvent__fini(msg);
    return false;
  }
  // severity
  // stamp
  if (!builtin_interfaces__msg__Time__init(&msg->stamp)) {
    doosan_somacube_rl__msg__SafetyEvent__fini(msg);
    return false;
  }
  return true;
}

void
doosan_somacube_rl__msg__SafetyEvent__fini(doosan_somacube_rl__msg__SafetyEvent * msg)
{
  if (!msg) {
    return;
  }
  // type
  rosidl_runtime_c__String__fini(&msg->type);
  // detail
  rosidl_runtime_c__String__fini(&msg->detail);
  // severity
  // stamp
  builtin_interfaces__msg__Time__fini(&msg->stamp);
}

bool
doosan_somacube_rl__msg__SafetyEvent__are_equal(const doosan_somacube_rl__msg__SafetyEvent * lhs, const doosan_somacube_rl__msg__SafetyEvent * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // type
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->type), &(rhs->type)))
  {
    return false;
  }
  // detail
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->detail), &(rhs->detail)))
  {
    return false;
  }
  // severity
  if (lhs->severity != rhs->severity) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->stamp), &(rhs->stamp)))
  {
    return false;
  }
  return true;
}

bool
doosan_somacube_rl__msg__SafetyEvent__copy(
  const doosan_somacube_rl__msg__SafetyEvent * input,
  doosan_somacube_rl__msg__SafetyEvent * output)
{
  if (!input || !output) {
    return false;
  }
  // type
  if (!rosidl_runtime_c__String__copy(
      &(input->type), &(output->type)))
  {
    return false;
  }
  // detail
  if (!rosidl_runtime_c__String__copy(
      &(input->detail), &(output->detail)))
  {
    return false;
  }
  // severity
  output->severity = input->severity;
  // stamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->stamp), &(output->stamp)))
  {
    return false;
  }
  return true;
}

doosan_somacube_rl__msg__SafetyEvent *
doosan_somacube_rl__msg__SafetyEvent__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  doosan_somacube_rl__msg__SafetyEvent * msg = (doosan_somacube_rl__msg__SafetyEvent *)allocator.allocate(sizeof(doosan_somacube_rl__msg__SafetyEvent), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(doosan_somacube_rl__msg__SafetyEvent));
  bool success = doosan_somacube_rl__msg__SafetyEvent__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
doosan_somacube_rl__msg__SafetyEvent__destroy(doosan_somacube_rl__msg__SafetyEvent * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    doosan_somacube_rl__msg__SafetyEvent__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
doosan_somacube_rl__msg__SafetyEvent__Sequence__init(doosan_somacube_rl__msg__SafetyEvent__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  doosan_somacube_rl__msg__SafetyEvent * data = NULL;

  if (size) {
    data = (doosan_somacube_rl__msg__SafetyEvent *)allocator.zero_allocate(size, sizeof(doosan_somacube_rl__msg__SafetyEvent), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = doosan_somacube_rl__msg__SafetyEvent__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        doosan_somacube_rl__msg__SafetyEvent__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
doosan_somacube_rl__msg__SafetyEvent__Sequence__fini(doosan_somacube_rl__msg__SafetyEvent__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      doosan_somacube_rl__msg__SafetyEvent__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

doosan_somacube_rl__msg__SafetyEvent__Sequence *
doosan_somacube_rl__msg__SafetyEvent__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  doosan_somacube_rl__msg__SafetyEvent__Sequence * array = (doosan_somacube_rl__msg__SafetyEvent__Sequence *)allocator.allocate(sizeof(doosan_somacube_rl__msg__SafetyEvent__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = doosan_somacube_rl__msg__SafetyEvent__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
doosan_somacube_rl__msg__SafetyEvent__Sequence__destroy(doosan_somacube_rl__msg__SafetyEvent__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    doosan_somacube_rl__msg__SafetyEvent__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
doosan_somacube_rl__msg__SafetyEvent__Sequence__are_equal(const doosan_somacube_rl__msg__SafetyEvent__Sequence * lhs, const doosan_somacube_rl__msg__SafetyEvent__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!doosan_somacube_rl__msg__SafetyEvent__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
doosan_somacube_rl__msg__SafetyEvent__Sequence__copy(
  const doosan_somacube_rl__msg__SafetyEvent__Sequence * input,
  doosan_somacube_rl__msg__SafetyEvent__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(doosan_somacube_rl__msg__SafetyEvent);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    doosan_somacube_rl__msg__SafetyEvent * data =
      (doosan_somacube_rl__msg__SafetyEvent *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!doosan_somacube_rl__msg__SafetyEvent__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          doosan_somacube_rl__msg__SafetyEvent__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!doosan_somacube_rl__msg__SafetyEvent__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
