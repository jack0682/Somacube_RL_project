// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from doosan_somacube_rl:msg/PolicyCmd.idl
// generated code does not contain a copyright notice
#include "doosan_somacube_rl/msg/detail/policy_cmd__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
doosan_somacube_rl__msg__PolicyCmd__init(doosan_somacube_rl__msg__PolicyCmd * msg)
{
  if (!msg) {
    return false;
  }
  // dx
  // dy
  // dz
  // droll
  // dpitch
  // dyaw
  // d_kp
  // d_kd
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    doosan_somacube_rl__msg__PolicyCmd__fini(msg);
    return false;
  }
  return true;
}

void
doosan_somacube_rl__msg__PolicyCmd__fini(doosan_somacube_rl__msg__PolicyCmd * msg)
{
  if (!msg) {
    return;
  }
  // dx
  // dy
  // dz
  // droll
  // dpitch
  // dyaw
  // d_kp
  // d_kd
  // header
  std_msgs__msg__Header__fini(&msg->header);
}

bool
doosan_somacube_rl__msg__PolicyCmd__are_equal(const doosan_somacube_rl__msg__PolicyCmd * lhs, const doosan_somacube_rl__msg__PolicyCmd * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // dx
  if (lhs->dx != rhs->dx) {
    return false;
  }
  // dy
  if (lhs->dy != rhs->dy) {
    return false;
  }
  // dz
  if (lhs->dz != rhs->dz) {
    return false;
  }
  // droll
  if (lhs->droll != rhs->droll) {
    return false;
  }
  // dpitch
  if (lhs->dpitch != rhs->dpitch) {
    return false;
  }
  // dyaw
  if (lhs->dyaw != rhs->dyaw) {
    return false;
  }
  // d_kp
  if (lhs->d_kp != rhs->d_kp) {
    return false;
  }
  // d_kd
  if (lhs->d_kd != rhs->d_kd) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  return true;
}

bool
doosan_somacube_rl__msg__PolicyCmd__copy(
  const doosan_somacube_rl__msg__PolicyCmd * input,
  doosan_somacube_rl__msg__PolicyCmd * output)
{
  if (!input || !output) {
    return false;
  }
  // dx
  output->dx = input->dx;
  // dy
  output->dy = input->dy;
  // dz
  output->dz = input->dz;
  // droll
  output->droll = input->droll;
  // dpitch
  output->dpitch = input->dpitch;
  // dyaw
  output->dyaw = input->dyaw;
  // d_kp
  output->d_kp = input->d_kp;
  // d_kd
  output->d_kd = input->d_kd;
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  return true;
}

doosan_somacube_rl__msg__PolicyCmd *
doosan_somacube_rl__msg__PolicyCmd__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  doosan_somacube_rl__msg__PolicyCmd * msg = (doosan_somacube_rl__msg__PolicyCmd *)allocator.allocate(sizeof(doosan_somacube_rl__msg__PolicyCmd), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(doosan_somacube_rl__msg__PolicyCmd));
  bool success = doosan_somacube_rl__msg__PolicyCmd__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
doosan_somacube_rl__msg__PolicyCmd__destroy(doosan_somacube_rl__msg__PolicyCmd * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    doosan_somacube_rl__msg__PolicyCmd__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
doosan_somacube_rl__msg__PolicyCmd__Sequence__init(doosan_somacube_rl__msg__PolicyCmd__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  doosan_somacube_rl__msg__PolicyCmd * data = NULL;

  if (size) {
    data = (doosan_somacube_rl__msg__PolicyCmd *)allocator.zero_allocate(size, sizeof(doosan_somacube_rl__msg__PolicyCmd), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = doosan_somacube_rl__msg__PolicyCmd__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        doosan_somacube_rl__msg__PolicyCmd__fini(&data[i - 1]);
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
doosan_somacube_rl__msg__PolicyCmd__Sequence__fini(doosan_somacube_rl__msg__PolicyCmd__Sequence * array)
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
      doosan_somacube_rl__msg__PolicyCmd__fini(&array->data[i]);
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

doosan_somacube_rl__msg__PolicyCmd__Sequence *
doosan_somacube_rl__msg__PolicyCmd__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  doosan_somacube_rl__msg__PolicyCmd__Sequence * array = (doosan_somacube_rl__msg__PolicyCmd__Sequence *)allocator.allocate(sizeof(doosan_somacube_rl__msg__PolicyCmd__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = doosan_somacube_rl__msg__PolicyCmd__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
doosan_somacube_rl__msg__PolicyCmd__Sequence__destroy(doosan_somacube_rl__msg__PolicyCmd__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    doosan_somacube_rl__msg__PolicyCmd__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
doosan_somacube_rl__msg__PolicyCmd__Sequence__are_equal(const doosan_somacube_rl__msg__PolicyCmd__Sequence * lhs, const doosan_somacube_rl__msg__PolicyCmd__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!doosan_somacube_rl__msg__PolicyCmd__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
doosan_somacube_rl__msg__PolicyCmd__Sequence__copy(
  const doosan_somacube_rl__msg__PolicyCmd__Sequence * input,
  doosan_somacube_rl__msg__PolicyCmd__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(doosan_somacube_rl__msg__PolicyCmd);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    doosan_somacube_rl__msg__PolicyCmd * data =
      (doosan_somacube_rl__msg__PolicyCmd *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!doosan_somacube_rl__msg__PolicyCmd__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          doosan_somacube_rl__msg__PolicyCmd__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!doosan_somacube_rl__msg__PolicyCmd__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
