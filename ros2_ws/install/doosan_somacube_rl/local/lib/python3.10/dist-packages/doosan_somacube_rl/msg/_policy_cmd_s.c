// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from doosan_somacube_rl:msg/PolicyCmd.idl
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
#include "doosan_somacube_rl/msg/detail/policy_cmd__struct.h"
#include "doosan_somacube_rl/msg/detail/policy_cmd__functions.h"

ROSIDL_GENERATOR_C_IMPORT
bool std_msgs__msg__header__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * std_msgs__msg__header__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool doosan_somacube_rl__msg__policy_cmd__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[45];
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
    assert(strncmp("doosan_somacube_rl.msg._policy_cmd.PolicyCmd", full_classname_dest, 44) == 0);
  }
  doosan_somacube_rl__msg__PolicyCmd * ros_message = _ros_message;
  {  // dx
    PyObject * field = PyObject_GetAttrString(_pymsg, "dx");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->dx = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // dy
    PyObject * field = PyObject_GetAttrString(_pymsg, "dy");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->dy = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // dz
    PyObject * field = PyObject_GetAttrString(_pymsg, "dz");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->dz = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // droll
    PyObject * field = PyObject_GetAttrString(_pymsg, "droll");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->droll = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // dpitch
    PyObject * field = PyObject_GetAttrString(_pymsg, "dpitch");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->dpitch = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // dyaw
    PyObject * field = PyObject_GetAttrString(_pymsg, "dyaw");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->dyaw = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // d_kp
    PyObject * field = PyObject_GetAttrString(_pymsg, "d_kp");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->d_kp = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // d_kd
    PyObject * field = PyObject_GetAttrString(_pymsg, "d_kd");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->d_kd = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // header
    PyObject * field = PyObject_GetAttrString(_pymsg, "header");
    if (!field) {
      return false;
    }
    if (!std_msgs__msg__header__convert_from_py(field, &ros_message->header)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * doosan_somacube_rl__msg__policy_cmd__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of PolicyCmd */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("doosan_somacube_rl.msg._policy_cmd");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "PolicyCmd");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  doosan_somacube_rl__msg__PolicyCmd * ros_message = (doosan_somacube_rl__msg__PolicyCmd *)raw_ros_message;
  {  // dx
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->dx);
    {
      int rc = PyObject_SetAttrString(_pymessage, "dx", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // dy
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->dy);
    {
      int rc = PyObject_SetAttrString(_pymessage, "dy", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // dz
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->dz);
    {
      int rc = PyObject_SetAttrString(_pymessage, "dz", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // droll
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->droll);
    {
      int rc = PyObject_SetAttrString(_pymessage, "droll", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // dpitch
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->dpitch);
    {
      int rc = PyObject_SetAttrString(_pymessage, "dpitch", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // dyaw
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->dyaw);
    {
      int rc = PyObject_SetAttrString(_pymessage, "dyaw", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // d_kp
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->d_kp);
    {
      int rc = PyObject_SetAttrString(_pymessage, "d_kp", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // d_kd
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->d_kd);
    {
      int rc = PyObject_SetAttrString(_pymessage, "d_kd", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // header
    PyObject * field = NULL;
    field = std_msgs__msg__header__convert_to_py(&ros_message->header);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "header", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
