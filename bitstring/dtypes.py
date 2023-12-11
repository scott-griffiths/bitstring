from __future__ import annotations

import functools
from typing import Optional, Dict, Any, Union, Tuple
from bitstring.utils import parse_name_length_token

CACHE_SIZE = 256

class Dtype:

    __slots__ = ('name', 'length', 'bitlength', 'read_fn', 'set_fn', 'get_fn', 'return_type', 'is_signed', 'is_unknown_length')

    def __new__(cls, __token: Union[str, Dtype, None] = None, length: Optional[int] = None, length_is_in_bits: bool = False) -> Dtype:
        if isinstance(__token, Dtype):
            return __token
        if __token is not None:
            register = Register()
            __token = ''.join(__token.split())
            if length is None:
                name, length = parse_name_length_token(__token)
            else:
                name = __token
            d = register.get_dtype(name, length, length_is_in_bits)
            return d
        else:
            return super(Dtype, cls).__new__(cls)

    def __hash__(self) -> int:
        return 0  # TODO: Optimise :)

    @property
    def is_integer(self) -> bool:
        return self.return_type == int

    @property
    def is_float(self) -> bool:
        return self.return_type == float

    @classmethod
    @functools.lru_cache(CACHE_SIZE)
    def create(cls, meta_dtype: MetaDtype, length: Optional[int]) -> Dtype:
        x = cls.__new__(cls)
        x.name = meta_dtype.name
        x.bitlength = x.length = length
        if x.bitlength is not None:
            x.bitlength *= meta_dtype.multiplier
        x.read_fn = functools.partial(meta_dtype.read_fn, length=x.bitlength)
        if meta_dtype.set_fn is None:
            x.set_fn = None
        else:
            x.set_fn = functools.partial(meta_dtype.set_fn, length=x.bitlength)
        x.get_fn = meta_dtype.get_fn
        x.return_type = meta_dtype.return_type
        x.is_signed = meta_dtype.is_signed
        x.is_unknown_length = meta_dtype.is_unknown_length
        return x

    def __str__(self) -> str:
        length_str = '' if (self.length == 0) else str(self.length)
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

    def __init__(self, name: str, description: str, set_fn, read_fn, get_fn, return_type: Any, bitlength2chars_fn, is_signed: bool,
                 is_unknown_length: bool, fixed_length: Optional[int] = None, multiplier: int = 1):
        # Consistency checks
        if is_unknown_length and fixed_length is not None:
            raise ValueError("Can't set is_unknown_length and give a value for length.")

        self.name = name
        self.description = description
        self.return_type = return_type
        self.is_signed = is_signed
        self.is_unknown_length = is_unknown_length
        self.fixed_length = fixed_length
        self.multiplier = multiplier

        self.set_fn = set_fn
        self.read_fn = read_fn  # With a start and usually a length
        self.get_fn = get_fn    # Interpret everything

        self.bitlength2chars_fn = bitlength2chars_fn

    def getDtype(self, length: Optional[int] = None) -> Dtype:
        if length is None:
            if self.fixed_length is None and not self.is_unknown_length:
                raise ValueError(f"No length given for dtype '{self.name}', and meta type is not fixed length.")
            d = Dtype.create(self, None)
            return d
        if self.is_unknown_length:
            raise ValueError("Length shouldn't be supplied for dtypes that are variable length.")
        if self.fixed_length is not None:
            if length != 0 and length != self.fixed_length:
                raise ValueError  # TODO
            length = self.fixed_length
        d = Dtype.create(self, length)
        return d

    def __str__(self) -> str:
        s = f"{self.name} -> {self.return_type.__name__}:  # {self.description}\n"
        s += f"is_signed={self.is_signed}, is_unknown_length={self.is_unknown_length}, fixed_length={self.fixed_length}, multiplier={self.multiplier}"
        return s

class Register:

    _instance: Optional[Register] = None

    def __new__(cls) -> Register:
        # Singleton. Only one Register instance can ever exist.
        if cls._instance is None:
            cls._instance = super(Register, cls).__new__(cls)
            cls.name_to_meta_dtype: Dict[str, MetaDtype] = {}
            cls._unknowable_length_names_cache: Tuple[str] = tuple()
            cls._always_fixed_length_cache: Dict[str, int] = {}
            cls._modified_flag: bool = False
        return cls._instance

    @classmethod
    def add_meta_dtype(cls, meta_dtype: MetaDtype):
        cls.name_to_meta_dtype[meta_dtype.name] = meta_dtype
        cls._modified_flag = True

    @classmethod
    def add_meta_dtype_alias(cls, name: str, alias: str):
        cls.name_to_meta_dtype[alias] = cls.name_to_meta_dtype[name]
        cls._modified_flag = True

    @classmethod
    def get_dtype(cls, name: str, length: Optional[int], length_is_in_bits: bool = False) -> Dtype:
        try:
            meta_type = cls.name_to_meta_dtype[name]
        except KeyError:
            raise ValueError
        if length_is_in_bits and meta_type.multiplier != 1:
            # We have a bit length for a type which must be a multiple of bits long
            new_length, remainder = divmod(length, meta_type.multiplier)
            if remainder != 0:
                raise ValueError(f"The '{name}' type must have a bit length that is a multiple of {meta_type.multiplier}"
                                 f" so cannot be created from {length} bits.")
            return meta_type.getDtype(new_length)
        else:
            return meta_type.getDtype(length)

    @classmethod
    def unknowable_length_names(cls) -> Tuple[str]:
        if cls._modified_flag:
            cls.refresh()
        return cls._unknowable_length_names_cache

    @classmethod
    def always_fixed_length(cls) -> Dict[str, int]:
        if cls._modified_flag:
            cls.refresh()
        return cls._always_fixed_length_cache

    @classmethod
    def refresh(cls) -> None:
        cls._unknowable_length_names_cache = tuple(dt_name for dt_name in cls.name_to_meta_dtype if cls.name_to_meta_dtype[dt_name].is_unknown_length)
        d: Dict[str, int] = {}
        for mt in cls.name_to_meta_dtype:
            if cls.name_to_meta_dtype[mt].fixed_length is not None:
                d[mt] = cls.name_to_meta_dtype[mt].fixed_length
        cls._always_fixed_length_cache = d
        cls._modified_flag = False

    def __str__(self) -> str:
        s = [f"{'key':<12}:{'name':^12}{'signed':^8}{'unknown_length':^16}{'fixed_length':^13}{'multiplier':^12}{'return_type':<13}"]
        s.append('-' * 85)
        for key in self.name_to_meta_dtype:
            m = self.name_to_meta_dtype[key]
            fixed = '' if m.fixed_length is None else m.fixed_length
            ret = 'None' if m.return_type is None else m.return_type.__name__
            s.append(f"{key:<12}:{m.name:>12}{m.is_signed:^8}{m.is_unknown_length:^16}{fixed:^13}{m.multiplier:^12}{ret:<13} # {m.description}")
        return '\n'.join(s)
