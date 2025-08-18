// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from doosan_somacube_rl:msg/RegisterQuality.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "doosan_somacube_rl/msg/detail/register_quality__struct.h"
#include "doosan_somacube_rl/msg/detail/register_quality__functions.h"

ROSIDL_GENERATOR_C_IMPORT
bool builtin_interfaces__msg__time__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * builtin_interfaces__msg__time__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool doosan_somacube_rl__msg__register_quality__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[57];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("doosan_somacube_rl.msg._register_quality.RegisterQuality", full_classname_dest, 56) == 0);
  }
  doosan_somacube_rl__msg__RegisterQuality * ros_message = _ros_message;
  {  // mean_point2plane_m
    PyObject * field = PyObject_GetAttrString(_pymsg, "mean_point2plane_m");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->mean_point2plane_m = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // chamfer_bidir_m
    PyObject * field = PyObject_GetAttrString(_pymsg, "chamfer_bidir_m");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->chamfer_bidir_m = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // inlier_ratio
    PyObject * field = PyObject_GetAttrString(_pymsg, "inlier_ratio");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->inlier_ratio = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // icp_residual_std
    PyObject * field = PyObject_GetAttrString(_pymsg, "icp_residual_std");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->icp_residual_std = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // geodesic_deg
    PyObject * field = PyObject_GetAttrString(_pymsg, "geodesic_deg");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->geodesic_deg = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // stamp
    PyObject * field = PyObject_GetAttrString(_pymsg, "stamp");
    if (!field) {
      return false;
    }
    if (!builtin_interfaces__msg__time__convert_from_py(field, &ros_message->stamp)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * doosan_somacube_rl__msg__register_quality__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of RegisterQuality */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("doosan_somacube_rl.msg._register_quality");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "RegisterQuality");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  doosan_somacube_rl__msg__RegisterQuality * ros_message = (doosan_somacube_rl__msg__RegisterQuality *)raw_ros_message;
  {  // mean_point2plane_m
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->mean_point2plane_m);
    {
      int rc = PyObject_SetAttrString(_pymessage, "mean_point2plane_m", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // chamfer_bidir_m
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->chamfer_bidir_m);
    {
      int rc = PyObject_SetAttrString(_pymessage, "chamfer_bidir_m", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // inlier_ratio
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->inlier_ratio);
    {
      int rc = PyObject_SetAttrString(_pymessage, "inlier_ratio", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // icp_residual_std
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->icp_residual_std);
    {
      int rc = PyObject_SetAttrString(_pymessage, "icp_residual_std", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // geodesic_deg
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->geodesic_deg);
    {
      int rc = PyObject_SetAttrString(_pymessage, "geodesic_deg", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // stamp
    PyObject * field = NULL;
    field = builtin_interfaces__msg__time__convert_to_py(&ros_message->stamp);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "stamp", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
