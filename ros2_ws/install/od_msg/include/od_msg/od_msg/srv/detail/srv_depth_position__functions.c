// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from od_msg:srv/SrvDepthPosition.idl
// generated code does not contain a copyright notice
#include "od_msg/srv/detail/srv_depth_position__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `target`
#include "rosidl_runtime_c/string_functions.h"

bool
od_msg__srv__SrvDepthPosition_Request__init(od_msg__srv__SrvDepthPosition_Request * msg)
{
  if (!msg) {
    return false;
  }
  // target
  if (!rosidl_runtime_c__String__init(&msg->target)) {
    od_msg__srv__SrvDepthPosition_Request__fini(msg);
    return false;
  }
  return true;
}

void
od_msg__srv__SrvDepthPosition_Request__fini(od_msg__srv__SrvDepthPosition_Request * msg)
{
  if (!msg) {
    return;
  }
  // target
  rosidl_runtime_c__String__fini(&msg->target);
}

bool
od_msg__srv__SrvDepthPosition_Request__are_equal(const od_msg__srv__SrvDepthPosition_Request * lhs, const od_msg__srv__SrvDepthPosition_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // target
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->target), &(rhs->target)))
  {
    return false;
  }
  return true;
}

bool
od_msg__srv__SrvDepthPosition_Request__copy(
  const od_msg__srv__SrvDepthPosition_Request * input,
  od_msg__srv__SrvDepthPosition_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // target
  if (!rosidl_runtime_c__String__copy(
      &(input->target), &(output->target)))
  {
    return false;
  }
  return true;
}

od_msg__srv__SrvDepthPosition_Request *
od_msg__srv__SrvDepthPosition_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  od_msg__srv__SrvDepthPosition_Request * msg = (od_msg__srv__SrvDepthPosition_Request *)allocator.allocate(sizeof(od_msg__srv__SrvDepthPosition_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(od_msg__srv__SrvDepthPosition_Request));
  bool success = od_msg__srv__SrvDepthPosition_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
od_msg__srv__SrvDepthPosition_Request__destroy(od_msg__srv__SrvDepthPosition_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    od_msg__srv__SrvDepthPosition_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
od_msg__srv__SrvDepthPosition_Request__Sequence__init(od_msg__srv__SrvDepthPosition_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  od_msg__srv__SrvDepthPosition_Request * data = NULL;

  if (size) {
    data = (od_msg__srv__SrvDepthPosition_Request *)allocator.zero_allocate(size, sizeof(od_msg__srv__SrvDepthPosition_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = od_msg__srv__SrvDepthPosition_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        od_msg__srv__SrvDepthPosition_Request__fini(&data[i - 1]);
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
od_msg__srv__SrvDepthPosition_Request__Sequence__fini(od_msg__srv__SrvDepthPosition_Request__Sequence * array)
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
      od_msg__srv__SrvDepthPosition_Request__fini(&array->data[i]);
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

od_msg__srv__SrvDepthPosition_Request__Sequence *
od_msg__srv__SrvDepthPosition_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  od_msg__srv__SrvDepthPosition_Request__Sequence * array = (od_msg__srv__SrvDepthPosition_Request__Sequence *)allocator.allocate(sizeof(od_msg__srv__SrvDepthPosition_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = od_msg__srv__SrvDepthPosition_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
od_msg__srv__SrvDepthPosition_Request__Sequence__destroy(od_msg__srv__SrvDepthPosition_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    od_msg__srv__SrvDepthPosition_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
od_msg__srv__SrvDepthPosition_Request__Sequence__are_equal(const od_msg__srv__SrvDepthPosition_Request__Sequence * lhs, const od_msg__srv__SrvDepthPosition_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!od_msg__srv__SrvDepthPosition_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
od_msg__srv__SrvDepthPosition_Request__Sequence__copy(
  const od_msg__srv__SrvDepthPosition_Request__Sequence * input,
  od_msg__srv__SrvDepthPosition_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(od_msg__srv__SrvDepthPosition_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    od_msg__srv__SrvDepthPosition_Request * data =
      (od_msg__srv__SrvDepthPosition_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!od_msg__srv__SrvDepthPosition_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          od_msg__srv__SrvDepthPosition_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!od_msg__srv__SrvDepthPosition_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `depth_position`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
od_msg__srv__SrvDepthPosition_Response__init(od_msg__srv__SrvDepthPosition_Response * msg)
{
  if (!msg) {
    return false;
  }
  // depth_position
  if (!rosidl_runtime_c__double__Sequence__init(&msg->depth_position, 0)) {
    od_msg__srv__SrvDepthPosition_Response__fini(msg);
    return false;
  }
  return true;
}

void
od_msg__srv__SrvDepthPosition_Response__fini(od_msg__srv__SrvDepthPosition_Response * msg)
{
  if (!msg) {
    return;
  }
  // depth_position
  rosidl_runtime_c__double__Sequence__fini(&msg->depth_position);
}

bool
od_msg__srv__SrvDepthPosition_Response__are_equal(const od_msg__srv__SrvDepthPosition_Response * lhs, const od_msg__srv__SrvDepthPosition_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // depth_position
  if (!rosidl_runtime_c__double__Sequence__are_equal(
      &(lhs->depth_position), &(rhs->depth_position)))
  {
    return false;
  }
  return true;
}

bool
od_msg__srv__SrvDepthPosition_Response__copy(
  const od_msg__srv__SrvDepthPosition_Response * input,
  od_msg__srv__SrvDepthPosition_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // depth_position
  if (!rosidl_runtime_c__double__Sequence__copy(
      &(input->depth_position), &(output->depth_position)))
  {
    return false;
  }
  return true;
}

od_msg__srv__SrvDepthPosition_Response *
od_msg__srv__SrvDepthPosition_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  od_msg__srv__SrvDepthPosition_Response * msg = (od_msg__srv__SrvDepthPosition_Response *)allocator.allocate(sizeof(od_msg__srv__SrvDepthPosition_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(od_msg__srv__SrvDepthPosition_Response));
  bool success = od_msg__srv__SrvDepthPosition_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
od_msg__srv__SrvDepthPosition_Response__destroy(od_msg__srv__SrvDepthPosition_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    od_msg__srv__SrvDepthPosition_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
od_msg__srv__SrvDepthPosition_Response__Sequence__init(od_msg__srv__SrvDepthPosition_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  od_msg__srv__SrvDepthPosition_Response * data = NULL;

  if (size) {
    data = (od_msg__srv__SrvDepthPosition_Response *)allocator.zero_allocate(size, sizeof(od_msg__srv__SrvDepthPosition_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = od_msg__srv__SrvDepthPosition_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        od_msg__srv__SrvDepthPosition_Response__fini(&data[i - 1]);
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
od_msg__srv__SrvDepthPosition_Response__Sequence__fini(od_msg__srv__SrvDepthPosition_Response__Sequence * array)
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
      od_msg__srv__SrvDepthPosition_Response__fini(&array->data[i]);
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

od_msg__srv__SrvDepthPosition_Response__Sequence *
od_msg__srv__SrvDepthPosition_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  od_msg__srv__SrvDepthPosition_Response__Sequence * array = (od_msg__srv__SrvDepthPosition_Response__Sequence *)allocator.allocate(sizeof(od_msg__srv__SrvDepthPosition_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = od_msg__srv__SrvDepthPosition_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
od_msg__srv__SrvDepthPosition_Response__Sequence__destroy(od_msg__srv__SrvDepthPosition_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    od_msg__srv__SrvDepthPosition_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
od_msg__srv__SrvDepthPosition_Response__Sequence__are_equal(const od_msg__srv__SrvDepthPosition_Response__Sequence * lhs, const od_msg__srv__SrvDepthPosition_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!od_msg__srv__SrvDepthPosition_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
od_msg__srv__SrvDepthPosition_Response__Sequence__copy(
  const od_msg__srv__SrvDepthPosition_Response__Sequence * input,
  od_msg__srv__SrvDepthPosition_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(od_msg__srv__SrvDepthPosition_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    od_msg__srv__SrvDepthPosition_Response * data =
      (od_msg__srv__SrvDepthPosition_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!od_msg__srv__SrvDepthPosition_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          od_msg__srv__SrvDepthPosition_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!od_msg__srv__SrvDepthPosition_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
