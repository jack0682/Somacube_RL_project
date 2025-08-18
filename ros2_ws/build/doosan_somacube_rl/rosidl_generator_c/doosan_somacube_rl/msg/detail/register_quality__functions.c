// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from doosan_somacube_rl:msg/RegisterQuality.idl
// generated code does not contain a copyright notice
#include "doosan_somacube_rl/msg/detail/register_quality__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
doosan_somacube_rl__msg__RegisterQuality__init(doosan_somacube_rl__msg__RegisterQuality * msg)
{
  if (!msg) {
    return false;
  }
  // mean_point2plane_m
  // chamfer_bidir_m
  // inlier_ratio
  // icp_residual_std
  // geodesic_deg
  // stamp
  if (!builtin_interfaces__msg__Time__init(&msg->stamp)) {
    doosan_somacube_rl__msg__RegisterQuality__fini(msg);
    return false;
  }
  return true;
}

void
doosan_somacube_rl__msg__RegisterQuality__fini(doosan_somacube_rl__msg__RegisterQuality * msg)
{
  if (!msg) {
    return;
  }
  // mean_point2plane_m
  // chamfer_bidir_m
  // inlier_ratio
  // icp_residual_std
  // geodesic_deg
  // stamp
  builtin_interfaces__msg__Time__fini(&msg->stamp);
}

bool
doosan_somacube_rl__msg__RegisterQuality__are_equal(const doosan_somacube_rl__msg__RegisterQuality * lhs, const doosan_somacube_rl__msg__RegisterQuality * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // mean_point2plane_m
  if (lhs->mean_point2plane_m != rhs->mean_point2plane_m) {
    return false;
  }
  // chamfer_bidir_m
  if (lhs->chamfer_bidir_m != rhs->chamfer_bidir_m) {
    return false;
  }
  // inlier_ratio
  if (lhs->inlier_ratio != rhs->inlier_ratio) {
    return false;
  }
  // icp_residual_std
  if (lhs->icp_residual_std != rhs->icp_residual_std) {
    return false;
  }
  // geodesic_deg
  if (lhs->geodesic_deg != rhs->geodesic_deg) {
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
doosan_somacube_rl__msg__RegisterQuality__copy(
  const doosan_somacube_rl__msg__RegisterQuality * input,
  doosan_somacube_rl__msg__RegisterQuality * output)
{
  if (!input || !output) {
    return false;
  }
  // mean_point2plane_m
  output->mean_point2plane_m = input->mean_point2plane_m;
  // chamfer_bidir_m
  output->chamfer_bidir_m = input->chamfer_bidir_m;
  // inlier_ratio
  output->inlier_ratio = input->inlier_ratio;
  // icp_residual_std
  output->icp_residual_std = input->icp_residual_std;
  // geodesic_deg
  output->geodesic_deg = input->geodesic_deg;
  // stamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->stamp), &(output->stamp)))
  {
    return false;
  }
  return true;
}

doosan_somacube_rl__msg__RegisterQuality *
doosan_somacube_rl__msg__RegisterQuality__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  doosan_somacube_rl__msg__RegisterQuality * msg = (doosan_somacube_rl__msg__RegisterQuality *)allocator.allocate(sizeof(doosan_somacube_rl__msg__RegisterQuality), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(doosan_somacube_rl__msg__RegisterQuality));
  bool success = doosan_somacube_rl__msg__RegisterQuality__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
doosan_somacube_rl__msg__RegisterQuality__destroy(doosan_somacube_rl__msg__RegisterQuality * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    doosan_somacube_rl__msg__RegisterQuality__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
doosan_somacube_rl__msg__RegisterQuality__Sequence__init(doosan_somacube_rl__msg__RegisterQuality__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  doosan_somacube_rl__msg__RegisterQuality * data = NULL;

  if (size) {
    data = (doosan_somacube_rl__msg__RegisterQuality *)allocator.zero_allocate(size, sizeof(doosan_somacube_rl__msg__RegisterQuality), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = doosan_somacube_rl__msg__RegisterQuality__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        doosan_somacube_rl__msg__RegisterQuality__fini(&data[i - 1]);
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
doosan_somacube_rl__msg__RegisterQuality__Sequence__fini(doosan_somacube_rl__msg__RegisterQuality__Sequence * array)
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
      doosan_somacube_rl__msg__RegisterQuality__fini(&array->data[i]);
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

doosan_somacube_rl__msg__RegisterQuality__Sequence *
doosan_somacube_rl__msg__RegisterQuality__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  doosan_somacube_rl__msg__RegisterQuality__Sequence * array = (doosan_somacube_rl__msg__RegisterQuality__Sequence *)allocator.allocate(sizeof(doosan_somacube_rl__msg__RegisterQuality__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = doosan_somacube_rl__msg__RegisterQuality__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
doosan_somacube_rl__msg__RegisterQuality__Sequence__destroy(doosan_somacube_rl__msg__RegisterQuality__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    doosan_somacube_rl__msg__RegisterQuality__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
doosan_somacube_rl__msg__RegisterQuality__Sequence__are_equal(const doosan_somacube_rl__msg__RegisterQuality__Sequence * lhs, const doosan_somacube_rl__msg__RegisterQuality__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!doosan_somacube_rl__msg__RegisterQuality__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
doosan_somacube_rl__msg__RegisterQuality__Sequence__copy(
  const doosan_somacube_rl__msg__RegisterQuality__Sequence * input,
  doosan_somacube_rl__msg__RegisterQuality__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(doosan_somacube_rl__msg__RegisterQuality);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    doosan_somacube_rl__msg__RegisterQuality * data =
      (doosan_somacube_rl__msg__RegisterQuality *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!doosan_somacube_rl__msg__RegisterQuality__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          doosan_somacube_rl__msg__RegisterQuality__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!doosan_somacube_rl__msg__RegisterQuality__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
