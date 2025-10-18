from __future__ import annotations

import struct
import math
import functools
from typing import Union, Optional, Dict, Callable
from bitformat import MutableBits, Bits, Endianness, DtypeSingle, DtypeKind
import bitstring
from bitstring.fp8 import p4binary_fmt, p3binary_fmt
from bitstring.mxfp import (e3m2mxfp_fmt, e2m3mxfp_fmt, e2m1mxfp_fmt, e4m3mxfp_saturate_fmt,
                            e5m2mxfp_saturate_fmt, e4m3mxfp_overflow_fmt, e5m2mxfp_overflow_fmt)
BitStore = bitstring.bitstore.BitStore
from bitstring.helpers import tidy_input_string

# The size of various caches used to improve performance
CACHE_SIZE = 256

@functools.lru_cache(CACHE_SIZE)
def str_to_bitstore(s: str) -> BitStore:
    _, tokens = bitstring.utils.tokenparser(s)
    bs = BitStore()
    for token in tokens:
        bs += bitstore_from_token(*token)
    bs.immutable = True
    return bs


def bin2bitstore(binstring: str) -> BitStore:
    binstring = tidy_input_string(binstring)
    binstring = binstring.replace('0b', '')
    mb = Bits._from_bin(binstring).to_mutable_bits()
    return BitStore.from_mutablebits(mb)


def hex2bitstore(hexstring: str) -> BitStore:
    hexstring = tidy_input_string(hexstring)
    hexstring = hexstring.replace('0x', '')
    mb = Bits._from_hex(hexstring).to_mutable_bits()
    return BitStore.from_mutablebits(mb)


def oct2bitstore(octstring: str) -> BitStore:
    octstring = tidy_input_string(octstring)
    octstring = octstring.replace('0o', '')
    mb = Bits._from_oct(octstring).to_mutable_bits()
    return BitStore.from_mutablebits(mb)


def int2bitstore(i: int, length: int, signed: bool) -> BitStore:
    dtype = DtypeSingle.from_params(DtypeKind.INT if signed else DtypeKind.UINT, length)
    mb = MutableBits.from_dtype(dtype, i)
    return BitStore.from_mutablebits(mb)


def intle2bitstore(i: int, length: int, signed: bool) -> BitStore:
    dtype = DtypeSingle.from_params(DtypeKind.INT if signed else DtypeKind.UINT, length, Endianness.LITTLE)
    mb = MutableBits.from_dtype(dtype, i)
    return BitStore.from_mutablebits(mb)


def float2bitstore(f: Union[str, float], length: int, big_endian: bool) -> BitStore:
    dtype = DtypeSingle.from_params(DtypeKind.FLOAT, length, Endianness.BIG if big_endian else Endianness.LITTLE)
    mb = MutableBits.from_dtype(dtype, f)
    return BitStore.from_mutablebits(mb)


literal_bit_funcs: Dict[str, Callable[..., BitStore]] = {
    '0x': hex2bitstore,
    '0X': hex2bitstore,
    '0b': bin2bitstore,
    '0B': bin2bitstore,
    '0o': oct2bitstore,
    '0O': oct2bitstore,
}


def bitstore_from_token(name: str, token_length: Optional[int], value: Optional[str]) -> BitStore:
    if name in literal_bit_funcs:
        return literal_bit_funcs[name](value)
    try:
        d = bitstring.dtypes.Dtype(name, token_length)
    except ValueError as e:
        raise bitstring.CreationError(f"Can't parse token: {e}")
    if value is None and name != 'pad':
        raise ValueError(f"Token {name} requires a value.")
    bs = d.build(value)._bitstore
    if token_length is not None and len(bs) != d.bitlength:
        raise bitstring.CreationError(f"Token with length {token_length} packed with value of length {len(bs)} "
                                      f"({name}:{token_length}={value}).")
    return bs
