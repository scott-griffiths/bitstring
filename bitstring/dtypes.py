from __future__ import annotations

import functools
from typing import Optional, Dict, Any, Union, Tuple
from bitstring.utils import parse_name_length_token
from collections.abc import Iterable
from bitstring.bits import Bits
from bitstring.bitarray_ import BitArray
from bitstring.exceptions import ReadError, InterpretError

CACHE_SIZE = 256


class Dtype:

    def __new__(cls, token: Union[str, Dtype, None] = None, /, length: Optional[int] = None) -> Dtype:
        if isinstance(token, cls):
            return token
        if token is not None:
            return cls._new_from_token(token, length)
        return super(Dtype, cls).__new__(cls)

    @classmethod
    @functools.lru_cache(CACHE_SIZE)
    def _new_from_token(cls, token: str, length: Optional[int] = None) -> Dtype:
        token = ''.join(token.split())
        if length is None:
            name, length = parse_name_length_token(token)
        else:
            name = token
        d = dtype_register.get_dtype(name, length)
        return d

    def __hash__(self) -> int:
        return 0  # TODO: Optimise :)

    @classmethod
    @functools.lru_cache(CACHE_SIZE)
    def create(cls, definition: DtypeDefinition, length: Optional[int]) -> Dtype:
        x = cls.__new__(cls)
        x.name = definition.name
        x.bitlength = x.length = length
        x.bits_per_item = definition.multiplier
        if x.bitlength is not None:
            x.bitlength *= x.bits_per_item
        x.is_unknown_length = definition.is_unknown_length
        if x.is_unknown_length or len(dtype_register.names[x.name].fixed_length) == 1:
            x.read_fn = definition.read_fn
        else:
            x.read_fn = functools.partial(definition.read_fn, length=x.bitlength)
        if definition.set_fn is None:
            x.set_fn = None
        else:
            x.set_fn = functools.partial(definition.set_fn, length=x.bitlength)
        x.get_fn = definition.get_fn
        x.return_type = definition.return_type
        x.is_signed = definition.is_signed
        return x

    def __str__(self) -> str:
        hide_length = self.is_unknown_length or len(dtype_register.names[self.name].fixed_length) == 1
        length_str = '' if hide_length else str(self.length)
        return f"{self.name}{length_str}"

    def __repr__(self) -> str:
        s = self.__str__()
        return f"{self.__class__.__name__}('{s}')"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Dtype):
            return self.name == other.name and self.length == other.length
        return False


class DtypeDefinition:
    # Represents a class of dtypes, such as uint or float, rather than a concrete dtype such as uint8.

    def __init__(self, name: str, set_fn, get_fn, return_type: Any = Any, is_signed: bool = False, bitlength2chars_fn = None,
                 is_unknown_length: bool = False, fixed_length: Union[int, Tuple[int, ...], None] = None, multiplier: int = 1, description: str = ''):

        # Consistency checks
        if is_unknown_length and fixed_length is not None:
            raise ValueError("Can't set is_unknown_length and give a value for fixed_length.")
        if int(multiplier) != multiplier or multiplier <= 0:
            raise ValueError("multiplier must be an positive integer")

        self.name = name
        self.description = description
        self.return_type = return_type
        self.is_signed = is_signed
        self.is_unknown_length = is_unknown_length
        if isinstance(fixed_length, Iterable):
            self.fixed_length = tuple(fixed_length)
        elif fixed_length is not None:
            self.fixed_length = (fixed_length,)
        else:
            self.fixed_length = tuple()
        self.multiplier = multiplier

        self.set_fn = set_fn

        if self.fixed_length:
            if len(self.fixed_length) == 1:
                def length_checked_get_fn(bs):
                    if len(bs) != self.fixed_length[0]:
                        raise InterpretError(f"'{self.name}' dtypes must have a length of {self.fixed_length[0]}, but received a length of {len(bs)}.")
                    return get_fn(bs)
            else:
                def length_checked_get_fn(bs):
                    if len(bs) not in self.fixed_length:
                        raise InterpretError(f"'{self.name}' dtypes must have one of the lengths {self.fixed_length}, but received a length of {len(bs)}.")
                    return get_fn(bs)
            self.get_fn = length_checked_get_fn  # Interpret everything and check the length
        else:
            self.get_fn = get_fn  # Interpret everything

        # Create a reading function from the get_fn.
        if self.is_unknown_length:
            # For unknown lengths the get_fn is really a reading function, so switch them around and create a new get_fn
            self.read_fn = get_fn
            def new_get_fn(bs):
                try:
                    value, length = self.read_fn(bs, 0)
                except ReadError:
                    raise InterpretError
                if length != len(bs):
                    raise ValueError  # TODO
                return value
            self.get_fn = new_get_fn
        else:
            if len(self.fixed_length) == 1:
                def read_fn(bs, start):
                    return self.get_fn(bs[start:start + self.fixed_length[0]])
            else:
                def read_fn(bs, start, length):
                    return self.get_fn(bs[start:start + length])
            self.read_fn = read_fn
        self.bitlength2chars_fn = bitlength2chars_fn

    def getDtype(self, length: Optional[int] = None) -> Dtype:
        if self.fixed_length:
            if length is None:
                if len(self.fixed_length) == 1:
                    length = self.fixed_length[0]
            else:
                if length not in self.fixed_length:
                    if len(self.fixed_length) == 1:
                        raise ValueError(f"A length of {length} was supplied for the '{self.name}' dtype, but its only allowed length is {self.fixed_length[0]}.")
                    else:
                        raise ValueError(f"A length of {length} was supplied for the '{self.name}' dtype which is not one of its possible lengths (must be one of {self.fixed_length}).")
        if length is None:
            d = Dtype.create(self, None)
            return d
        if self.is_unknown_length:
            raise ValueError("Length shouldn't be supplied for dtypes that are variable length.")
        d = Dtype.create(self, length)
        return d

    def __str__(self) -> str:
        s = f"{self.name} -> {self.return_type.__name__}:  # {self.description}\n"
        s += f"is_signed={self.is_signed}, is_unknown_length={self.is_unknown_length}, fixed_length={self.fixed_length!s}, multiplier={self.multiplier}"
        return s

class Register:

    _instance: Optional[Register] = None

    def __new__(cls) -> Register:
        # Singleton. Only one Register instance can ever exist.
        if cls._instance is None:
            cls._instance = super(Register, cls).__new__(cls)
            cls.names: Dict[str, DtypeDefinition] = {}
            cls._unknowable_length_names_cache: Tuple[str] = tuple()
            cls._modified_flag: bool = False
        return cls._instance

    @classmethod
    def add_dtype(cls, definition: DtypeDefinition):
        cls.names[definition.name] = definition
        cls._modified_flag = True
        if definition.get_fn is not None:
            setattr(Bits, definition.name, property(fget=definition.get_fn, doc=f"The bitstring as {definition.description}. Read only."))
        if definition.set_fn is not None:
            setattr(BitArray, definition.name, property(fget=definition.get_fn, fset=definition.set_fn, doc=f"The bitstring as {definition.description}. Read and write."))

    @classmethod
    def add_dtype_alias(cls, name: str, alias: str):
        cls.names[alias] = cls.names[name]
        definition = cls.names[alias]
        cls._modified_flag = True
        if definition.get_fn is not None:
            setattr(Bits, alias, property(fget=definition.get_fn, doc=f"An alias for '{name}'. Read only."))
        if definition.set_fn is not None:
            setattr(BitArray, alias, property(fget=definition.get_fn, fset=definition.set_fn, doc=f"An alias for '{name}'. Read and write."))

    @classmethod
    def get_dtype(cls, name: str, length: Optional[int]) -> Dtype:
        try:
            definition = cls.names[name]
        except KeyError:
            raise ValueError
        else:
            return definition.getDtype(length)

    @classmethod
    def __getitem__(cls, name: str) -> DtypeDefinition:
        return cls.names[name]

    @classmethod
    def __delitem__(cls, name: str) -> None:
        del cls.names[name]

    @classmethod
    def unknowable_length_names(cls) -> Tuple[str]:
        if cls._modified_flag:
            cls.refresh()
        return cls._unknowable_length_names_cache

    @classmethod
    def refresh(cls) -> None:
        cls._unknowable_length_names_cache = tuple(dt_name for dt_name in cls.names if cls.names[dt_name].is_unknown_length)
        d: Dict[str, int] = {}
        cls._modified_flag = False

    def __repr__(self) -> str:
        s = [f"{'key':<12}:{'name':^12}{'signed':^8}{'unknown_length':^16}{'fixed_length':^13}{'multiplier':^12}{'return_type':<13}"]
        s.append('-' * 85)
        for key in self.names:
            m = self.names[key]
            fixed = '' if not m.fixed_length else m.fixed_length
            ret = 'None' if m.return_type is None else m.return_type.__name__
            s.append(f"{key:<12}:{m.name:>12}{m.is_signed:^8}{m.is_unknown_length:^16}{fixed!s:^13}{m.multiplier:^12}{ret:<13} # {m.description}")
        return '\n'.join(s)


# Create the Register singleton
dtype_register = Register()