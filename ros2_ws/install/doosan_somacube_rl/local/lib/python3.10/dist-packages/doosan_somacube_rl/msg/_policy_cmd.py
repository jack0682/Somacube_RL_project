# generated from rosidl_generator_py/resource/_idl.py.em
# with input from doosan_somacube_rl:msg/PolicyCmd.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_PolicyCmd(type):
    """Metaclass of message 'PolicyCmd'."""

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
                'doosan_somacube_rl.msg.PolicyCmd')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__policy_cmd
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__policy_cmd
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__policy_cmd
            cls._TYPE_SUPPORT = module.type_support_msg__msg__policy_cmd
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__policy_cmd

            from std_msgs.msg import Header
            if Header.__class__._TYPE_SUPPORT is None:
                Header.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class PolicyCmd(metaclass=Metaclass_PolicyCmd):
    """Message class 'PolicyCmd'."""

    __slots__ = [
        '_dx',
        '_dy',
        '_dz',
        '_droll',
        '_dpitch',
        '_dyaw',
        '_d_kp',
        '_d_kd',
        '_header',
    ]

    _fields_and_field_types = {
        'dx': 'float',
        'dy': 'float',
        'dz': 'float',
        'droll': 'float',
        'dpitch': 'float',
        'dyaw': 'float',
        'd_kp': 'float',
        'd_kd': 'float',
        'header': 'std_msgs/Header',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['std_msgs', 'msg'], 'Header'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.dx = kwargs.get('dx', float())
        self.dy = kwargs.get('dy', float())
        self.dz = kwargs.get('dz', float())
        self.droll = kwargs.get('droll', float())
        self.dpitch = kwargs.get('dpitch', float())
        self.dyaw = kwargs.get('dyaw', float())
        self.d_kp = kwargs.get('d_kp', float())
        self.d_kd = kwargs.get('d_kd', float())
        from std_msgs.msg import Header
        self.header = kwargs.get('header', Header())

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
        if self.dx != other.dx:
            return False
        if self.dy != other.dy:
            return False
        if self.dz != other.dz:
            return False
        if self.droll != other.droll:
            return False
        if self.dpitch != other.dpitch:
            return False
        if self.dyaw != other.dyaw:
            return False
        if self.d_kp != other.d_kp:
            return False
        if self.d_kd != other.d_kd:
            return False
        if self.header != other.header:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def dx(self):
        """Message field 'dx'."""
        return self._dx

    @dx.setter
    def dx(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'dx' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'dx' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._dx = value

    @builtins.property
    def dy(self):
        """Message field 'dy'."""
        return self._dy

    @dy.setter
    def dy(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'dy' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'dy' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._dy = value

    @builtins.property
    def dz(self):
        """Message field 'dz'."""
        return self._dz

    @dz.setter
    def dz(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'dz' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'dz' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._dz = value

    @builtins.property
    def droll(self):
        """Message field 'droll'."""
        return self._droll

    @droll.setter
    def droll(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'droll' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'droll' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._droll = value

    @builtins.property
    def dpitch(self):
        """Message field 'dpitch'."""
        return self._dpitch

    @dpitch.setter
    def dpitch(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'dpitch' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'dpitch' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._dpitch = value

    @builtins.property
    def dyaw(self):
        """Message field 'dyaw'."""
        return self._dyaw

    @dyaw.setter
    def dyaw(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'dyaw' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'dyaw' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._dyaw = value

    @builtins.property
    def d_kp(self):
        """Message field 'd_kp'."""
        return self._d_kp

    @d_kp.setter
    def d_kp(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'd_kp' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'd_kp' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._d_kp = value

    @builtins.property
    def d_kd(self):
        """Message field 'd_kd'."""
        return self._d_kd

    @d_kd.setter
    def d_kd(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'd_kd' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'd_kd' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._d_kd = value

    @builtins.property
    def header(self):
        """Message field 'header'."""
        return self._header

    @header.setter
    def header(self, value):
        if __debug__:
            from std_msgs.msg import Header
            assert \
                isinstance(value, Header), \
                "The 'header' field must be a sub message of type 'Header'"
        self._header = value
