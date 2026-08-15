from __future__ import annotations

import functools
from typing import Any
from collections.abc import Callable
import inspect
import bitstring
from bitstring import utils

CACHE_SIZE = 256

# Dtypes made from a token string, which is much the most common case.
# Bounded like the lru_caches, and cleared whenever the register changes.
TOKEN_CACHE_SIZE = 256
_token_cache: dict[str, Dtype] = {}


class Dtype:
    """A data type class, representing a concrete interpretation of binary data.

    Dtype instances are immutable. They are often created implicitly elsewhere via a token string.

    >>> u12 = Dtype('u', 12)  # length separate from token string.
    >>> float16 = Dtype('f16')  # length part of token string.

    """

    _name: str
    _read_fn: Callable
    _set_fn: Callable
    _get_fn: Callable
    _return_type: Any
    _is_signed: bool
    _set_fn_needs_length: bool
    _variable_length: bool
    _bitlength: int | None
    _bits_per_item: int
    _length: int | None
    _is_property: bool

    def __new__(cls, token: str | Dtype, /, length: int | None = None) -> Dtype:
        if isinstance(token, cls):
            if length is None:
                return token
            # Re-length an existing dtype. Going back through the register means the
            # new length gets the same validation as any other, rather than the length
            # being silently dropped.
            return dtype_register.get_dtype(token.name, length)
        if type(token) is str:
            # Plain dict lookup for the common case - several times quicker than
            # reaching the lru_caches below, and this is on every read and pack.
            key = token if length is None else (token, length)
            x = _token_cache.get(key)
            if x is None:
                x = (cls._new_from_token(token) if length is None
                     else dtype_register.get_dtype(token, length))
                if len(_token_cache) < TOKEN_CACHE_SIZE:
                    _token_cache[key] = x
            return x
        if length is None:
            return cls._new_from_token(token)
        return dtype_register.get_dtype(token, length)

    @property
    def name(self) -> str:
        """A string giving the name of the data type."""
        return self._name

    @property
    def length(self) -> int | None:
        """The length of the data type, in bits for every dtype except 'bytes', which counts bytes.

        Set to None for variable length dtypes. Use bitlength for a length that is always in bits.
        """
        return self._length

    @property
    def bitlength(self) -> int | None:
        """The number of bits needed to represent a single instance of the data type. Set to None for variable length dtypes."""
        return self._bitlength

    @property
    def variable_length(self) -> bool:
        """If True then the length of the data type depends on the data being interpreted, and must not be specified."""
        return self._variable_length

    @property
    def return_type(self) -> Any:
        """The type of the value returned by the unpack method, such as int, float or str."""
        return self._return_type

    @property
    def is_signed(self) -> bool:
        """If True then the data type represents a signed quantity."""
        return self._is_signed

    @classmethod
    @functools.lru_cache(CACHE_SIZE)
    def _new_from_token(cls, token: str) -> Dtype:
        token = ''.join(token.split())
        return dtype_register.get_dtype(*utils.parse_name_length_token(token))

    def __hash__(self) -> int:
        return hash((self._name, self._length))

    @classmethod
    @functools.lru_cache(CACHE_SIZE)
    def _create(cls, definition: DtypeDefinition, length: int | None) -> Dtype:
        x = super().__new__(cls)
        x._name = definition.name
        x._bitlength = x._length = length
        x._bits_per_item = definition.multiplier
        if x._bitlength is not None:
            x._bitlength *= x._bits_per_item
        x._set_fn_needs_length = definition.set_fn_needs_length
        x._variable_length = definition.variable_length
        if x._variable_length or dtype_register.names[x._name].allowed_lengths.only_one_value():
            x._read_fn = definition.read_fn
        else:
            x._read_fn = functools.partial(definition.read_fn, length=x._bitlength)
        if definition.set_fn is None:
            x._set_fn = None
        else:
            if x._set_fn_needs_length:
                x._set_fn = functools.partial(definition.set_fn, length=x._bitlength)
            else:
                x._set_fn = definition.set_fn
        x._get_fn = definition.get_fn
        x._return_type = definition.return_type
        x._is_signed = definition.is_signed
        x._is_property = definition.is_property
        return x

    def pack(self, value: Any, /) -> bitstring.Bits:
        """Pack a value into a bitstring.

        The value parameter should be of a type appropriate to the dtype.
        """
        b = object.__new__(bitstring.Bits)
        self._set_fn(b, value)
        bitlength = self._bitlength  # The property costs a call, and this is a hot path.
        if bitlength is not None and len(b) != bitlength:
            raise ValueError(f"Dtype has a length of {bitlength} bits, but value '{value}' has {len(b)} bits.")
        return b

    def unpack(self, b: BitsType, /) -> Any:
        """Unpack a bitstring to find its value.

        The b parameter should be a bitstring of the dtype's length, or an object that can be converted to a bitstring."""
        b = bitstring.Bits._create_from_bitstype(b)
        bitlength = self._bitlength  # The property costs a call, and this is a hot path.
        if bitlength is not None and len(b) != bitlength:
            raise ValueError(f"Dtype has a length of {bitlength} bits, but value to unpack has {len(b)} bits.")
        return self._get_fn(b)

    def __str__(self) -> str:
        hide_length = self._variable_length or dtype_register.names[self._name].allowed_lengths.only_one_value() or self._length is None
        length_str = '' if hide_length else str(self._length)
        return f"{self._name}{length_str}"

    def __repr__(self) -> str:
        hide_length = self._variable_length or dtype_register.names[self._name].allowed_lengths.only_one_value() or self._length is None
        length_str = '' if hide_length else ', ' + str(self._length)
        return f"{self.__class__.__name__}('{self._name}'{length_str})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Dtype):
            return self._name == other._name and self._length == other._length
        return False

    def __reduce__(self):
        # Dtypes hold unpicklable function references, but are defined by name and length.
        return Dtype, (self._name, self._length)


class AllowedLengths:
    def __init__(self, value: tuple[int, ...] = tuple()) -> None:
        if len(value) >= 3 and value[-1] is Ellipsis:
            step = value[1] - value[0]
            for i in range(1, len(value) - 1):
                if value[i] - value[i - 1] != step:
                    raise ValueError(f"Allowed length tuples must be equally spaced when final element is Ellipsis, but got {value}.")
            self.values = (value[0], value[1], Ellipsis)
        else:
            self.values = value

    def __str__(self) -> str:
        if self.values and self.values[-1] is Ellipsis:
            return f"({self.values[0]}, {self.values[1]}, ...)"
        return str(self.values)

    def __contains__(self, other: Any) -> bool:
        if not self.values:
            return True
        if self.values[-1] is Ellipsis:
            start = self.values[0]
            step = self.values[1] - self.values[0]
            return other >= start and (other - start) % step == 0
        return other in self.values

    def only_one_value(self) -> bool:
        return self.values and len(self.values) == 1


class DtypeDefinition:
    """Represents a class of dtypes, such as uint or float, rather than a concrete dtype such as uint8.
    Not (yet) part of the public interface."""

    def __init__(self, name: str, set_fn, get_fn, return_type: Any = Any, is_signed: bool = False, bitlength2chars_fn=None,
                 variable_length: bool = False, allowed_lengths: tuple[int, ...] = tuple(), multiplier: int = 1,
                 description: str = '', read_fn=None, is_property: bool = True):

        # Consistency checks
        if int(multiplier) != multiplier or multiplier <= 0:
            raise ValueError("multiplier must be an positive integer")
        if variable_length and allowed_lengths:
            raise ValueError("A variable length dtype can't have allowed lengths.")
        if variable_length and set_fn is not None and 'length' in inspect.signature(set_fn).parameters:
            raise ValueError("A variable length dtype can't have a set_fn which takes a length.")

        self.name = name
        self.description = description
        self.return_type = return_type
        self.is_signed = is_signed
        self.variable_length = variable_length
        self.allowed_lengths = AllowedLengths(allowed_lengths)
        # Most dtypes are also an interpretation of a whole bitstring, and so become a
        # property on Bits and BitArray. The exceptions are 'pad', which is a format
        # string directive rather than an interpretation, and 'bits', whose property
        # form would just be the identity.
        self.is_property = is_property

        self.multiplier = multiplier

        # Can work out if set_fn needs length based on its signature.
        self.set_fn_needs_length = set_fn is not None and 'length' in inspect.signature(set_fn).parameters
        self.set_fn = set_fn

        # The interpretation without any length checking around it, so that the attribute
        # getters built in _property_getter can do their own check in a single call.
        self.raw_get_fn = get_fn

        if self.allowed_lengths.values:
            def allowed_length_checked_get_fn(bs):
                if len(bs) not in self.allowed_lengths:
                    if self.allowed_lengths.only_one_value():
                        raise ValueError(f"'{self.name}' dtypes must have a length of {self.allowed_lengths.values[0]}, but received a length of {len(bs)}.")
                    else:
                        raise ValueError(f"'{self.name}' dtypes must have a length in {self.allowed_lengths}, but received a length of {len(bs)}.")
                return get_fn(bs)
            self.get_fn = allowed_length_checked_get_fn  # Interpret everything and check the length
        else:
            self.get_fn = get_fn  # Interpret everything

        # Create a reading function from the get_fn.
        if not self.variable_length:
            if read_fn is not None:
                direct_read_fn = read_fn
                if self.allowed_lengths.only_one_value():
                    def read_fn(bs, start):
                        length = self.allowed_lengths.values[0]
                        if len(bs) < start + length:
                            raise bitstring.ReadError(f"Needed a length of at least {length} bits, but only {len(bs) - start} bits were available.")
                        return direct_read_fn(bs, start, length)
                else:
                    def read_fn(bs, start, length):
                        if len(bs) < start + length:
                            raise bitstring.ReadError(f"Needed a length of at least {length} bits, but only {len(bs) - start} bits were available.")
                        return direct_read_fn(bs, start, length)
            else:
                if self.allowed_lengths.only_one_value():
                    def read_fn(bs, start):
                        return self.get_fn(bs[start:start + self.allowed_lengths.values[0]])
                else:
                    def read_fn(bs, start, length):
                        if len(bs) < start + length:
                            raise bitstring.ReadError(f"Needed a length of at least {length} bits, but only {len(bs) - start} bits were available.")
                        return self.get_fn(bs[start:start + length])
            self.read_fn = read_fn
        else:
            # We only find out the length when we read/get.
            def length_checked_get_fn(bs):
                x, length = get_fn(bs)
                if length != len(bs):
                    raise ValueError(f"Bitstring is not a single '{self.name}' code: it is "
                                     f"{len(bs)} bits long but the code read uses {length}.")
                return x
            self.get_fn = length_checked_get_fn

            def read_fn(bs, start):
                try:
                    x, length = get_fn(bs[start:])
                except ValueError:
                    raise bitstring.ReadError(f"Cannot read a '{self.name}' code at bit position "
                                              f"{start}: the data there isn't a valid code.")
                return x, start + length
            self.read_fn = read_fn
        self.bitlength2chars_fn = bitlength2chars_fn

    def get_dtype(self, length: int | None = None) -> Dtype:
        if self.allowed_lengths:
            if length is None:
                if self.allowed_lengths.only_one_value():
                    length = self.allowed_lengths.values[0]
            else:
                if length not in self.allowed_lengths:
                    if self.allowed_lengths.only_one_value():
                        raise ValueError(f"A length of {length} was supplied for the '{self.name}' dtype, but its only allowed length is {self.allowed_lengths.values[0]}.")
                    else:
                        raise ValueError(f"A length of {length} was supplied for the '{self.name}' dtype which is not one of its possible lengths (must be one of {self.allowed_lengths}).")
        if length is None:
            d = Dtype._create(self, None)
            return d
        if self.variable_length:
            raise ValueError(f"A length ({length}) shouldn't be supplied for the variable length dtype '{self.name}'.")
        d = Dtype._create(self, length)
        return d

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}(name='{self.name}', description='{self.description}', return_type={self.return_type.__name__}, "
        s += f"is_signed={self.is_signed}, set_fn_needs_length={self.set_fn_needs_length}, allowed_lengths={self.allowed_lengths!s}, multiplier={self.multiplier})"
        return s


def _interpretation_error(definition: DtypeDefinition, length: int, attribute: str,
                          classname: str) -> bitstring.InterpretationError:
    return bitstring.InterpretationError(
        f"'{classname}' object has no attribute '{attribute}': a length of {length} bits "
        f"is not one the '{definition.name}' dtype can interpret.")


def check_interpretation_length(definition: DtypeDefinition, length: int, attribute: str, classname: str) -> None:
    """Raise if a bitstring of this length has no interpretation as the given dtype.

    Only for the cold path in Bits.__getattr__; the properties themselves check inline.
    """
    if length not in definition.allowed_lengths or length % definition.multiplier:
        raise _interpretation_error(definition, length, attribute, classname)


def _property_getter(definition: DtypeDefinition, name: str) -> Callable:
    """Build the attribute getter for a dtype, so a length mismatch is an AttributeError too.

    A bitstring of the wrong length simply doesn't have the property, which is the rule
    Bits.__getattr__ already uses for the names that carry a length, such as 'u16'. A
    plain ValueError would break hasattr() and getattr() with a default, as neither of
    those catches it.

    This wraps the unchecked get_fn and does the length check itself, rather than sitting
    on top of the checked one, so that a property read still costs a single call.
    """
    allowed = definition.allowed_lengths
    multiplier = definition.multiplier
    if not allowed.values and multiplier == 1:
        return definition.get_fn  # No length constraint, so nothing to check.
    get_fn = definition.raw_get_fn

    if multiplier == 1:
        @functools.wraps(get_fn)
        def getter(self):
            length = len(self)
            if length not in allowed:
                raise _interpretation_error(definition, length, name, type(self).__name__)
            return get_fn(self)
    else:
        @functools.wraps(get_fn)
        def getter(self):
            length = len(self)
            if length not in allowed or length % multiplier:
                raise _interpretation_error(definition, length, name, type(self).__name__)
            return get_fn(self)
    return getter


def _mutable_property_setter(set_fn: Callable) -> Callable:
    """Wrap a Bits setter so that assigning to it leaves a BitArray still mutable.

    The setters all replace the store outright, and nearly all of them build an
    immutable one - which is what _initialise converts after construction. A property
    assignment doesn't go through _initialise, so it does the same conversion here.
    """
    @functools.wraps(set_fn)
    def setter(self, value, /) -> None:
        set_fn(self, value)
        self._bitstore = self._bitstore._mutable_copy()
    return setter


class Register:
    """A singleton class that holds all the DtypeDefinitions. Not (yet) part of the public interface."""

    _instance: Register | None = None
    names: dict[str, DtypeDefinition] = {}

    def __new__(cls) -> Register:
        # Singleton. Only one Register instance can ever exist.
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def add_dtype(cls, definition: DtypeDefinition):
        cls.names[definition.name] = definition
        _token_cache.clear()
        if not definition.is_property:
            return
        get_fn = None if definition.get_fn is None else _property_getter(definition, definition.name)
        if get_fn is not None:
            setattr(bitstring.bits.Bits, definition.name, property(fget=get_fn, doc=f"The bitstring as {definition.description}. Read only."))
        if definition.set_fn is not None:
            setattr(bitstring.bitarray_.BitArray, definition.name, property(fget=get_fn, fset=_mutable_property_setter(definition.set_fn), doc=f"The bitstring as {definition.description}. Read and write."))

    @classmethod
    def add_dtype_alias(cls, name: str, alias: str):
        cls.names[alias] = cls.names[name]
        _token_cache.clear()
        definition = cls.names[alias]
        if not definition.is_property:
            return
        get_fn = None if definition.get_fn is None else _property_getter(definition, alias)
        if get_fn is not None:
            setattr(bitstring.bits.Bits, alias, property(fget=get_fn, doc=f"An alias for '{name}'. Read only."))
        if definition.set_fn is not None:
            setattr(bitstring.bitarray_.BitArray, alias, property(fget=get_fn, fset=_mutable_property_setter(definition.set_fn), doc=f"An alias for '{name}'. Read and write."))

    @classmethod
    def get_dtype(cls, name: str, length: int | None) -> Dtype:
        try:
            definition = cls.names[name]
        except KeyError:
            raise ValueError(f"Unknown Dtype name '{name}'. Names available: {list(cls.names.keys())}.")
        else:
            return definition.get_dtype(length)

    @classmethod
    def __getitem__(cls, name: str) -> DtypeDefinition:
        return cls.names[name]

    @classmethod
    def __delitem__(cls, name: str) -> None:
        del cls.names[name]
        _token_cache.clear()

    def __repr__(self) -> str:
        s = [f"{'key':<12}:{'name':^12}{'signed':^8}{'set_fn_needs_length':^23}{'allowed_lengths':^16}{'multiplier':^12}{'return_type':<13}"]
        s.append('-' * 85)
        for key in self.names:
            m = self.names[key]
            allowed = '' if not m.allowed_lengths else m.allowed_lengths
            ret = 'None' if m.return_type is None else m.return_type.__name__
            s.append(f"{key:<12}:{m.name:>12}{m.is_signed:^8}{m.set_fn_needs_length:^16}{allowed!s:^16}{m.multiplier:^12}{ret:<13} # {m.description}")
        return '\n'.join(s)


# Create the Register singleton
dtype_register = Register()
