# generated from rosidl_generator_py/resource/_idl.py.em
# with input from doosan_somacube_rl:msg/RegisterQuality.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_RegisterQuality(type):
    """Metaclass of message 'RegisterQuality'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('doosan_somacube_rl')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'doosan_somacube_rl.msg.RegisterQuality')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__register_quality
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__register_quality
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__register_quality
            cls._TYPE_SUPPORT = module.type_support_msg__msg__register_quality
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__register_quality

            from builtin_interfaces.msg import Time
            if Time.__class__._TYPE_SUPPORT is None:
                Time.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class RegisterQuality(metaclass=Metaclass_RegisterQuality):
    """Message class 'RegisterQuality'."""

    __slots__ = [
        '_mean_point2plane_m',
        '_chamfer_bidir_m',
        '_inlier_ratio',
        '_icp_residual_std',
        '_geodesic_deg',
        '_stamp',
    ]

    _fields_and_field_types = {
        'mean_point2plane_m': 'float',
        'chamfer_bidir_m': 'float',
        'inlier_ratio': 'float',
        'icp_residual_std': 'float',
        'geodesic_deg': 'float',
        'stamp': 'builtin_interfaces/Time',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['builtin_interfaces', 'msg'], 'Time'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.mean_point2plane_m = kwargs.get('mean_point2plane_m', float())
        self.chamfer_bidir_m = kwargs.get('chamfer_bidir_m', float())
        self.inlier_ratio = kwargs.get('inlier_ratio', float())
        self.icp_residual_std = kwargs.get('icp_residual_std', float())
        self.geodesic_deg = kwargs.get('geodesic_deg', float())
        from builtin_interfaces.msg import Time
        self.stamp = kwargs.get('stamp', Time())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.mean_point2plane_m != other.mean_point2plane_m:
            return False
        if self.chamfer_bidir_m != other.chamfer_bidir_m:
            return False
        if self.inlier_ratio != other.inlier_ratio:
            return False
        if self.icp_residual_std != other.icp_residual_std:
            return False
        if self.geodesic_deg != other.geodesic_deg:
            return False
        if self.stamp != other.stamp:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def mean_point2plane_m(self):
        """Message field 'mean_point2plane_m'."""
        return self._mean_point2plane_m

    @mean_point2plane_m.setter
    def mean_point2plane_m(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'mean_point2plane_m' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'mean_point2plane_m' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._mean_point2plane_m = value

    @builtins.property
    def chamfer_bidir_m(self):
        """Message field 'chamfer_bidir_m'."""
        return self._chamfer_bidir_m

    @chamfer_bidir_m.setter
    def chamfer_bidir_m(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'chamfer_bidir_m' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'chamfer_bidir_m' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._chamfer_bidir_m = value

    @builtins.property
    def inlier_ratio(self):
        """Message field 'inlier_ratio'."""
        return self._inlier_ratio

    @inlier_ratio.setter
    def inlier_ratio(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'inlier_ratio' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'inlier_ratio' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._inlier_ratio = value

    @builtins.property
    def icp_residual_std(self):
        """Message field 'icp_residual_std'."""
        return self._icp_residual_std

    @icp_residual_std.setter
    def icp_residual_std(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'icp_residual_std' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'icp_residual_std' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._icp_residual_std = value

    @builtins.property
    def geodesic_deg(self):
        """Message field 'geodesic_deg'."""
        return self._geodesic_deg

    @geodesic_deg.setter
    def geodesic_deg(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'geodesic_deg' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'geodesic_deg' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._geodesic_deg = value

    @builtins.property
    def stamp(self):
        """Message field 'stamp'."""
        return self._stamp

    @stamp.setter
    def stamp(self, value):
        if __debug__:
            from builtin_interfaces.msg import Time
            assert \
                isinstance(value, Time), \
                "The 'stamp' field must be a sub message of type 'Time'"
        self._stamp = value
