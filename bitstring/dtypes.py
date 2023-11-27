from __future__ import annotations

import functools
from typing import Optional, Dict, Any, Union, Tuple
from bitstring.utils import parse_name_length_token


class Dtype:

    __slots__ = ('name', 'length', 'bitlength', 'read_fn', 'set_fn', 'get_fn', 'return_type', 'is_integer', 'is_signed', 'is_float', 'is_fixed_length', 'is_unknown_length')

    def __new__(cls, __token: Union[str, Dtype, None] = None, length: Optional[int] = None) -> Dtype:
        if isinstance(__token, Dtype):
            return __token
        if __token is not None:
            register = Register()
            __token = ''.join(__token.split())
            if length is None:
                name, length = parse_name_length_token(__token)
            else:
                name = __token
            d = register.get_dtype(name, length)
            return d
        else:
            return super(Dtype, cls).__new__(cls)

    def __hash__(self) -> int:
        return 0  # TODO: Optimise :)

    @classmethod
    def create(cls, name: str, length: Optional[int], set_fn, read_fn, get_fn, return_type: Any, is_integer: bool, is_float: bool, is_signed: bool,
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
        x.return_type = return_type
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

    def __init__(self, name: str, description: str, set_fn, read_fn, get_fn, return_type: Any, bitlength2chars_fn, is_integer: bool, is_float: bool, is_signed: bool,
                 is_unknown_length: bool, length: Optional[int] = None, length_multiplier: Optional[int] = None):
        # Consistency checks
        if is_unknown_length and length is not None:
            raise ValueError("Can't set is_unknown_length and give a value for length.")
        if is_float and is_integer:
            raise ValueError("Can't have type that is both float and integer.")

        self.name = name
        self.description = description
        self.return_type = return_type
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

        self.bitlength2chars_fn = bitlength2chars_fn

    def getDtype(self, length: Optional[int] = None) -> Dtype:
        if length is None:
            if not self.is_fixed_length and not self.is_unknown_length:
                raise ValueError(f"No length given for dtype '{self.name}', and meta type is not fixed length.")
            d = Dtype.create(self.name, None, self.set_fn, self.read_fn, self.get_fn, self.return_type, self.is_integer, self.is_float, self.is_signed,
                             self.is_unknown_length, self.is_fixed_length, self.length_multiplier)
            return d
        if self.is_unknown_length:
            raise ValueError("Length shouldn't be supplied for dtypes that are variable length.")
        if self.is_fixed_length:
            if length != 0 and length != self.length:
                raise ValueError  # TODO
            length = self.length
        d = Dtype.create(self.name, length, self.set_fn, self.read_fn, self.get_fn, self.return_type, self.is_integer, self.is_float, self.is_signed,
                         self.is_unknown_length, self.is_fixed_length, self.length_multiplier)
        return d


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
    def get_dtype(cls, name: str, length: Optional[int]) -> Dtype:
        try:
            meta_type = cls.name_to_meta_dtype[name]
        except KeyError:
            raise ValueError
        d = meta_type.getDtype(length)
        if length != 0 and not d.is_unknown_length:
            if meta_type.length_multiplier is not None:
                length *= meta_type.length_multiplier
        return d

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
            if cls.name_to_meta_dtype[mt].is_fixed_length:
                d[mt] = cls.name_to_meta_dtype[mt].length
        cls._always_fixed_length_cache = d
        cls._modified_flag = False

