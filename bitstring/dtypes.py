from __future__ import annotations

import functools
from bitstring.utils import parse_name_length_token, SIGNED_INTEGER_NAMES, UNSIGNED_INTEGER_NAMES, FLOAT_NAMES, ALWAYS_FIXED_LENGTH_TOKENS, VARIABLE_LENGTH_TOKENS
from bitstring.exceptions import InterpretError
from bitstring.bits import Bits
from bitstring.bitarray import BitArray
from typing import Optional, Dict


INTEGER_NAMES = SIGNED_INTEGER_NAMES + UNSIGNED_INTEGER_NAMES
SIGNED_NAMES = SIGNED_INTEGER_NAMES + FLOAT_NAMES


class Dtype:

    # __slots__ = ('name', 'length', 'set', 'get', 'is_integer', 'is_signed', 'is_float', 'is_fixed_length', 'is_variable_length', 'min_value', 'max_value')

    def __init__(self, fmt: Optional[str] = None) -> None:
        if fmt is None:
            return  # Empty
        name, length = parse_name_length_token(fmt)
        self._init_from_register(name, length)


    def _init_from_register(self, name, length):
        d = register.getType(name, length)
        # Test if the length makes sense by trying out the getter.
        if length != 0:
            temp = BitArray(length)
            try:
                _ = d.get(temp, 0)
            except InterpretError as e:
                raise ValueError(f"Invalid Dtype: {e.msg}")
        self.__dict__.update(d.__dict__)

    def _init_old(self, name, length) -> None:
        self.name = name
        self.length = length
        try:
            self.set = functools.partial(Bits._setfunc[self.name], length=self.length)
        except KeyError:
            raise ValueError(f"The token '{self.name}' is not a valid Dtype name.")
        try:
            self.get = functools.partial(Bits._name_to_read[self.name], length=self.length)
        except KeyError:
            raise ValueError(f"The token '{self.name}' is not a valid Dtype name.")

        # Test if the length makes sense by trying out the getter.
        if self.length != 0:
            temp = BitArray(self.length)
            try:
                _ = self.get(temp, 0)
            except InterpretError as e:
                raise ValueError(f"Invalid Dtype: {e.msg}")

        # Some useful information about the type we're creating
        self.is_integer = self.name in INTEGER_NAMES
        self.is_signed = self.name in SIGNED_NAMES
        self.is_float = self.name in FLOAT_NAMES
        self.is_fixed_length = self.name in ALWAYS_FIXED_LENGTH_TOKENS.keys()
        self.is_variable_length = self.name in VARIABLE_LENGTH_TOKENS

        self.max_value = None
        self.min_value = None
        if self.is_integer:
            if self.is_signed:
                self.max_value = (1 << (self.length - 1)) - 1
                self.min_value = -(1 << (self.length - 1))
            else:
                self.max_value = (1 << self.length) - 1
                self.min_value = 0

    @classmethod
    def create(cls, name: str, length: Optional[int], set, get, is_integer, is_float, is_signed,
               is_variable_length, is_fixed_length) -> Dtype:
        dtype = cls()
        dtype.name = name
        dtype.length = length
        dtype.get = functools.partial(get, length=length)
        dtype.set = functools.partial(set, length=length)
        dtype.is_integer = is_integer
        dtype.is_signed = is_signed
        dtype.is_float = is_float
        dtype.is_fixed_length = is_fixed_length
        dtype.is_variable_length = is_variable_length
        return dtype

    def __str__(self) -> str:
        length_str = '' if (self.length == 0 or self.is_fixed_length) else str(self.length)
        return f"{self.name}{length_str}"

    def __repr__(self) -> str:
        s = self.__str__()
        return f"{self.__class__.__name__}('{s}')"


class MetaDtype:
    # Represents a class of dtypes, such as uint or float, rather than a concrete dtype such as uint8.

    def __init__(self, name: str, set_fn, get_fn, is_integer: bool, is_float: bool, is_signed: bool,
                 is_variable_length: bool, length: Optional[int] = None):
        # Consistency checks
        if is_variable_length and length is not None:
            raise ValueError("Can't set is_variable_length and give a value for fixed_length")
        if is_float and is_integer:
            raise ValueError("Can't have type that is both float and integer.")

        self.name = name
        self.is_float = is_float
        self.is_integer = is_integer
        self.is_signed = is_signed
        self.is_fixed_length = length is not None
        self.is_variable_length = is_variable_length
        self.length = length

        self.set = set_fn
        self.get = get_fn

    def getDtype(self, length: Optional[int] = None) -> Dtype:
        if length is None:
            if not self.is_fixed_length:
                raise ValueError("No length given for dtype, and meta type is not fixed length.")
            d = Dtype.create(self.name, None, self.set, self.get, self.is_integer, self.is_float, self.is_signed,
                             self.is_variable_length, self.is_fixed_length)
            return d
        if self.is_variable_length:
            raise ValueError("Length shouldn't be supplied for dtypes that are variable length.")
        d = Dtype.create(self.name, length, self.set, self.get, self.is_integer, self.is_float, self.is_signed,
                         self.is_variable_length, self.is_fixed_length)
        return d


class Register:

    def __init__(self) -> None:
        self.name_to_meta_dtype: Dict[str, MetaDtype] = {}

    def addType(self, meta_dtype: MetaDtype):
        self.name_to_meta_dtype[meta_dtype.name] = meta_dtype

    def addAlias(self, name: str, alias: str):
        self.name_to_meta_dtype[alias] = self.name_to_meta_dtype[name]

    def getType(self, name: str, length: Optional[int]) -> Dtype:
        try:
            meta_type = self.name_to_meta_dtype[name]
        except KeyError:
            raise ValueError
        return meta_type.getDtype(length)


types = [
    MetaDtype('uint', Bits._setuint, Bits._readuint, True, False, False, False, None),
    MetaDtype('uintle', Bits._setuintle, Bits._readuintle, True, False, False, False, None),
    MetaDtype('uintne', Bits._setuintne, Bits._readuintne, True, False, False, False, None),
    MetaDtype('uintbe', Bits._setuintbe, Bits._readuintbe, True, False, False, False, None),
    MetaDtype('int', Bits._setint, Bits._readint, True, False, True, False, None),
    MetaDtype('intle', Bits._setintle, Bits._readintle, True, False, True, False, None),
    MetaDtype('intne', Bits._setintne, Bits._readintne, True, False, True, False, None),
    MetaDtype('intbe', Bits._setintbe, Bits._readintbe, True, False, True, False, None),
    MetaDtype('float', Bits._setfloatbe, Bits._readfloatbe, False, True, True, False, None),
    MetaDtype('float8_152', Bits._setfloat152, Bits._readfloat152, False, True, True, False, 8),
    MetaDtype('hex', Bits._sethex, Bits._readhex, False, False, False, False, None),
    MetaDtype('bin', Bits._setbin_unsafe, Bits._readbin, False, False, False, False, None),
    MetaDtype('oct', Bits._setoct, Bits._readoct, False, False, False, False, None),
    MetaDtype('bool', Bits._setbool, Bits._readbool, True, False, False, False, 1),
    MetaDtype('float8_143', Bits._setfloat143, Bits._readfloat143, False, True, True, False, 8),
    MetaDtype('floatne', Bits._setfloatne, Bits._readfloatne, False, True, True, False, None),
    MetaDtype('floatle', Bits._setfloatle, Bits._readfloatle, False, True, True, False, None),
    MetaDtype('bfloat', Bits._setbfloatbe, Bits._readbfloatbe, False, True, True, False, 16),
    MetaDtype('bits', Bits._setbits, Bits._readbits, False, False, False, False, None),
    ]


register = Register()
for t in types:
    register.addType(t)
register.addAlias('float', 'floatbe')
