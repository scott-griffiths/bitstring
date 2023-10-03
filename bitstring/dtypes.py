from __future__ import annotations

import functools
from bitstring.exceptions import InterpretError, CreationError
from bitstring.bits import Bits
from typing import Optional, Dict, List, Any, Union
from bitstring.utils import parse_name_length_token


class Dtype:

    __slots__ = ('name', 'length', 'bitlength', 'read_fn', 'set_fn', 'get_fn', 'is_integer', 'is_signed', 'is_float', 'is_fixed_length', 'is_unknown_length')

    def __new__(cls, token: Union[str, Dtype, None] = None, length: Optional[int] = None) -> Dtype:
        if isinstance(token, Dtype):
            return token
        if token is not None:
            register = Register()
            token = ''.join(token.split())
            if length is None:
                name, length = parse_name_length_token(token)
            else:
                name = token
            d = register.get_dtype(name, length)
            return d
        else:
            return super(Dtype, cls).__new__(cls)

    def __hash__(self) -> int:
        return 0  # TODO: Optimise :)

    @classmethod
    def create(cls, name: str, length: Optional[int], set_fn, read_fn, get_fn, is_integer: bool, is_float: bool, is_signed: bool,
               is_unknown_length: bool, is_fixed_length: bool, length_multiplier: Optional[int]) -> Dtype:
        x = cls.__new__(cls)
        x.name = name
        x.length = length
        x.bitlength = length
        if length_multiplier is not None:
            x.bitlength *= length_multiplier
        x.read_fn = functools.partial(read_fn, length=x.bitlength)
        if set_fn is None:
            x.set_fn = None
        else:
            x.set_fn = functools.partial(set_fn, length=x.bitlength)
        x.get_fn = get_fn
        x.is_integer = is_integer
        x.is_signed = is_signed
        x.is_float = is_float
        x.is_fixed_length = is_fixed_length
        x.is_unknown_length = is_unknown_length
        return x

    def __str__(self) -> str:
        length_str = '' if (self.length == 0 or self.is_fixed_length) else str(self.length)
        return f"{self.name}{length_str}"

    def __repr__(self) -> str:
        s = self.__str__()
        return f"{self.__class__.__name__}('{s}')"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Dtype):
            return self.name == other.name and self.length == other.length
        return False


class MetaDtype:
    # Represents a class of dtypes, such as uint or float, rather than a concrete dtype such as uint8.

    def __init__(self, name: str, description: str, set_fn, read_fn, get_fn, is_integer: bool, is_float: bool, is_signed: bool,
                 is_unknown_length: bool, length: Optional[int] = None, length_multiplier: Optional[int] = None):
        # Consistency checks
        if is_unknown_length and length is not None:
            raise ValueError("Can't set is_unknown_length and give a value for length.")
        if is_float and is_integer:
            raise ValueError("Can't have type that is both float and integer.")

        self.name = name
        self.description = description
        self.is_float = is_float
        self.is_integer = is_integer
        self.is_signed = is_signed
        self.is_fixed_length = length is not None
        self.is_unknown_length = is_unknown_length
        self.length = length
        self.length_multiplier = length_multiplier

        self.set_fn = set_fn
        self.read_fn = read_fn  # With a start and usually a length
        self.get_fn = get_fn    # Interpret everything

    def getDtype(self, length: Optional[int] = None) -> Dtype:
        if length is None:
            if not self.is_fixed_length and not self.is_unknown_length:
                raise ValueError(f"No length given for dtype '{self.name}', and meta type is not fixed length.")
            d = Dtype.create(self.name, None, self.set_fn, self.read_fn, self.get_fn, self.is_integer, self.is_float, self.is_signed,
                             self.is_unknown_length, self.is_fixed_length, self.length_multiplier)
            return d
        if self.is_unknown_length:
            raise ValueError("Length shouldn't be supplied for dtypes that are variable length.")
        if self.is_fixed_length:
            if length != 0 and length != self.length:
                raise ValueError  # TODO
            length = self.length
        d = Dtype.create(self.name, length, self.set_fn, self.read_fn, self.get_fn, self.is_integer, self.is_float, self.is_signed,
                         self.is_unknown_length, self.is_fixed_length, self.length_multiplier)
        return d


class Register:

    _instance: Optional[Register] = None

    def __new__(cls) -> Register:
        # Singleton. Only one Register instance can ever exist.
        if cls._instance is None:
            cls._instance = super(Register, cls).__new__(cls)
            cls.name_to_meta_dtype: Dict[str, MetaDtype] = {}
        return cls._instance

    @classmethod
    def add_meta_dtype(cls, meta_dtype: MetaDtype):
        cls.name_to_meta_dtype[meta_dtype.name] = meta_dtype

    @classmethod
    def add_meta_dtype_alias(cls, name: str, alias: str):
        cls.name_to_meta_dtype[alias] = cls.name_to_meta_dtype[name]

    @classmethod
    def get_dtype(cls, name: str, length: Optional[int]) -> Dtype:
        try:
            meta_type = cls.name_to_meta_dtype[name]
        except KeyError:
            raise ValueError
        d = meta_type.getDtype(length)
        # Test if the length makes sense by trying out the getter.  # TODO: Optimise!
        if length != 0 and not d.is_unknown_length:
            if meta_type.length_multiplier is not None:
                length *= meta_type.length_multiplier
            try:
                temp = Bits(length)
            except CreationError as e:
                raise ValueError(f"Invalid Dtype: {e}")
            try:
                _ = d.read_fn(temp, 0)
            except InterpretError as e:
                raise ValueError(f"Invalid Dtype: {e}")
        return d

    # TODO: This should be only calculated if the register has been altered since the last time it was called.
    @classmethod
    def unknowable_length_names(cls) -> List[str]:
        return [dt_name for dt_name in cls.name_to_meta_dtype if cls.name_to_meta_dtype[dt_name].is_unknown_length]

    @classmethod
    def always_fixed_length(cls) -> Dict[str, int]:
        d: Dict[str, int] = {}
        for mt in cls.name_to_meta_dtype:
            if cls.name_to_meta_dtype[mt].is_fixed_length:
                d[mt] = cls.name_to_meta_dtype[mt].length
        return d



