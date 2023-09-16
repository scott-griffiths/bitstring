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

    def __init__(self, name: str='', length: int=0) -> None:
        if name == '':
            return  # Empty
        self._init_from_register(name, length)

    def _init_from_register(self, name: str, length: int) -> None:
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
        self.is_unknown_length = self.name in VARIABLE_LENGTH_TOKENS

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
               is_unknown_length, is_fixed_length) -> Dtype:
        dtype = cls()
        dtype.name = name
        dtype.length = length
        dtype.get = functools.partial(get, length=length)
        dtype.set = functools.partial(set, length=length)
        dtype.is_integer = is_integer
        dtype.is_signed = is_signed
        dtype.is_float = is_float
        dtype.is_fixed_length = is_fixed_length
        dtype.is_unknown_length = is_unknown_length
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
                 is_unknown_length: bool, length: Optional[int] = None):
        # Consistency checks
        if is_unknown_length and length is not None:
            raise ValueError("Can't set is_variable_length and give a value for fixed_length")
        if is_float and is_integer:
            raise ValueError("Can't have type that is both float and integer.")

        self.name = name
        self.is_float = is_float
        self.is_integer = is_integer
        self.is_signed = is_signed
        self.is_fixed_length = length is not None
        self.is_unknown_length = is_unknown_length
        self.length = length

        self.set = set_fn
        self.get = get_fn

    def getDtype(self, length: Optional[int] = None) -> Dtype:
        if length is None:
            if not self.is_fixed_length:
                raise ValueError("No length given for dtype, and meta type is not fixed length.")
            d = Dtype.create(self.name, None, self.set, self.get, self.is_integer, self.is_float, self.is_signed,
                             self.is_unknown_length, self.is_fixed_length)
            return d
        if self.is_unknown_length:
            raise ValueError("Length shouldn't be supplied for dtypes that are variable length.")
        if self.is_fixed_length:
            if length != 0 and length != self.length:
                raise ValueError  # TODO
            length = self.length
        d = Dtype.create(self.name, length, self.set, self.get, self.is_integer, self.is_float, self.is_signed,
                         self.is_unknown_length, self.is_fixed_length)
        return d


class Register:

    def __init__(self) -> None:
        pass

    def addType(self, meta_dtype: MetaDtype):
        self.name_to_meta_dtype[meta_dtype.name] = meta_dtype

    def addAlias(self, name: str, alias: str):
        self.name_to_meta_dtype[alias] = self.name_to_meta_dtype[name]

    @classmethod
    def getType(cls, name: str, length: Optional[int]) -> Dtype:
        try:
            meta_type = cls.name_to_meta_dtype[name]
        except KeyError:
            raise ValueError
        return meta_type.getDtype(length)

    def __new__(cls):
        cls.name_to_meta_dtype: Dict[str, MetaDtype] = {}
        if not hasattr(cls, 'instance'):
            cls.instance = super(Register, cls).__new__(cls)
        return cls.instance

    @classmethod
    def create_dtype(cls, name: str, length: int) -> Dtype:
        d = cls.getType(name, length)
        # Test if the length makes sense by trying out the getter.  # TODO: Optimise!
        if length != 0:
            temp = Bits(length)
            try:
                _ = d.get(temp, 0)
            except InterpretError as e:
                raise ValueError(f"Invalid Dtype: {e.msg}")
        return d



