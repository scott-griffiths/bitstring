from __future__ import annotations

import functools
from typing import Optional, Dict, Any, Union, Tuple
from collections.abc import Iterable
import bitstring
from bitstring import utils

CACHE_SIZE = 256


class Dtype:

    __slots__ = ('read_fn', 'name', 'set_fn', 'get_fn', 'return_type', 'is_signed', 'is_unknown_length', 'bitlength', 'bits_per_item', 'length')

    def __new__(cls, token: Union[str, Dtype, None] = None, /, length: Optional[int] = None) -> Dtype:
        if isinstance(token, cls):
            return token
        if token is not None:
            if length is None:
                return cls._new_from_token(token)
            else:
                return dtype_register.get_dtype(token, length)
        return super(Dtype, cls).__new__(cls)

    @classmethod
    @functools.lru_cache(CACHE_SIZE)
    def _new_from_token(cls, token: str) -> Dtype:
        token = ''.join(token.split())
        return dtype_register.get_dtype(*utils.parse_name_length_token(token))

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
        if x.is_unknown_length or len(dtype_register.names[x.name].allowed_lengths) == 1:
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
        hide_length = self.is_unknown_length or len(dtype_register.names[self.name].allowed_lengths) == 1 or self.length is None
        length_str = '' if hide_length else str(self.length)
        return f"{self.name}{length_str}"

    def __repr__(self) -> str:
        hide_length = self.is_unknown_length or len(dtype_register.names[self.name].allowed_lengths) == 1 or self.length is None
        length_str = '' if hide_length else ', ' + str(self.length)
        return f"{self.__class__.__name__}('{self.name}{length_str}')"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Dtype):
            return self.name == other.name and self.length == other.length
        return False


class AllowedLengths:
    def __init__(self, value: Tuple[int, ...] = tuple()) -> None:
        if len(value) >= 3 and value[-1] is Ellipsis:
            step = value[1] - value[0]
            for i in range(1, len(value) - 1):
                if value[i] - value[i - 1] != step:
                    raise ValueError(f"Allowed length tuples must be equally spaced when final element is Ellipsis, but got {value}.")
            infinity = 1_000_000_000_000_000  # Rough approximation.
            self.value = range(value[0], infinity, step)
        else:
            self.value = value

    def __str__(self) -> str:
        if isinstance(self.value, range):
            return f"({self.value[0]}, {self.value[1]}, ...)"
        return str(self.value)

    def __contains__(self, other: Any) -> bool:
        return other in self.value

    def __len__(self) -> int:
        return len(self.value)


class DtypeDefinition:
    # Represents a class of dtypes, such as uint or float, rather than a concrete dtype such as uint8.

    def __init__(self, name: str, set_fn, get_fn, return_type: Any = Any, is_signed: bool = False, bitlength2chars_fn = None,
                 is_unknown_length: bool = False, allowed_lengths: Tuple[int, ...] = tuple(), multiplier: int = 1, description: str = ''):

        # Consistency checks
        if is_unknown_length and allowed_lengths:
            raise ValueError("Can't set is_unknown_length and give a value for allowed_lengths.")
        if int(multiplier) != multiplier or multiplier <= 0:
            raise ValueError("multiplier must be an positive integer")

        self.name = name
        self.description = description
        self.return_type = return_type
        self.is_signed = is_signed
        self.is_unknown_length = is_unknown_length
        self.allowed_lengths = AllowedLengths(allowed_lengths)

        self.multiplier = multiplier

        self.set_fn = set_fn

        if self.allowed_lengths:
            def length_checked_get_fn(bs):
                if len(bs) not in self.allowed_lengths:
                    raise bitstring.InterpretError(f"'{self.name}' dtypes must have a length in {self.allowed_lengths}, but received a length of {len(bs)}.")
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
                except bitstring.ReadError:
                    raise bitstring.InterpretError
                if length != len(bs):
                    raise ValueError  # TODO
                return value
            self.get_fn = new_get_fn
        else:
            if len(self.allowed_lengths) == 1:
                def read_fn(bs, start):
                    return self.get_fn(bs[start:start + self.allowed_lengths.value[0]])
            else:
                def read_fn(bs, start, length):
                    return self.get_fn(bs[start:start + length])
            self.read_fn = read_fn
        self.bitlength2chars_fn = bitlength2chars_fn

    def getDtype(self, length: Optional[int] = None) -> Dtype:
        if self.allowed_lengths:
            if length is None:
                if len(self.allowed_lengths) == 1:
                    length = self.allowed_lengths.value[0]
            else:
                if length not in self.allowed_lengths:
                    if len(self.allowed_lengths) == 1:
                        raise ValueError(f"A length of {length} was supplied for the '{self.name}' dtype, but its only allowed length is {self.allowed_lengths.value[0]}.")
                    else:
                        raise ValueError(f"A length of {length} was supplied for the '{self.name}' dtype which is not one of its possible lengths (must be one of {self.allowed_lengths}).")
        if length is None:
            d = Dtype.create(self, None)
            return d
        if self.is_unknown_length:
            raise ValueError(f"A length ({length}) shouldn't be supplied for the dtype '{self.name}' as it has unknown length.")
        d = Dtype.create(self, length)
        return d

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}(name='{self.name}', description='{self.description}', return_type={self.return_type.__name__}, "
        s += f"is_signed={self.is_signed}, is_unknown_length={self.is_unknown_length}, allowed_lengths={self.allowed_lengths!s}, multiplier={self.multiplier})"
        return s

class Register:

    _instance: Optional[Register] = None
    names: Dict[str, DtypeDefinition] = {}

    def __new__(cls) -> Register:
        # Singleton. Only one Register instance can ever exist.
        if cls._instance is None:
            cls._instance = super(Register, cls).__new__(cls)
        return cls._instance

    @classmethod
    def add_dtype(cls, definition: DtypeDefinition):
        cls.names[definition.name] = definition
        if definition.get_fn is not None:
            setattr(bitstring.bits.Bits, definition.name, property(fget=definition.get_fn, doc=f"The bitstring as {definition.description}. Read only."))
        if definition.set_fn is not None:
            setattr(bitstring.bitarray_.BitArray, definition.name, property(fget=definition.get_fn, fset=definition.set_fn, doc=f"The bitstring as {definition.description}. Read and write."))

    @classmethod
    def add_dtype_alias(cls, name: str, alias: str):
        cls.names[alias] = cls.names[name]
        definition = cls.names[alias]
        if definition.get_fn is not None:
            setattr(bitstring.bits.Bits, alias, property(fget=definition.get_fn, doc=f"An alias for '{name}'. Read only."))
        if definition.set_fn is not None:
            setattr(bitstring.bitarray_.BitArray, alias, property(fget=definition.get_fn, fset=definition.set_fn, doc=f"An alias for '{name}'. Read and write."))

    @classmethod
    def get_dtype(cls, name: str, length: Optional[int]) -> Dtype:
        try:
            definition = cls.names[name]
        except KeyError:
            raise ValueError(f"Unknown Dtype name '{name}'.")
        else:
            return definition.getDtype(length)

    @classmethod
    def __getitem__(cls, name: str) -> DtypeDefinition:
        return cls.names[name]

    @classmethod
    def __delitem__(cls, name: str) -> None:
        del cls.names[name]

    def __repr__(self) -> str:
        s = [f"{'key':<12}:{'name':^12}{'signed':^8}{'unknown_length':^16}{'allowed_lengths':^16}{'multiplier':^12}{'return_type':<13}"]
        s.append('-' * 85)
        for key in self.names:
            m = self.names[key]
            allowed = '' if not m.allowed_lengths else m.allowed_lengths
            ret = 'None' if m.return_type is None else m.return_type.__name__
            s.append(f"{key:<12}:{m.name:>12}{m.is_signed:^8}{m.is_unknown_length:^16}{allowed!s:^16}{m.multiplier:^12}{ret:<13} # {m.description}")
        return '\n'.join(s)


# Create the Register singleton
dtype_register = Register()