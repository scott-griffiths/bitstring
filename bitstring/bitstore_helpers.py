from __future__ import annotations

from tibs import Mutibs

import struct
import math
from typing import Union, Dict, Callable, Optional
import functools
import bitstring
from bitstring.fp8 import p4binary_fmt, p3binary_fmt
from bitstring.mxfp import (e3m2mxfp_fmt, e2m3mxfp_fmt, e2m1mxfp_fmt, e4m3mxfp_saturate_fmt,
                            e5m2mxfp_saturate_fmt, e4m3mxfp_overflow_fmt, e5m2mxfp_overflow_fmt)


MutableBitStore = bitstring.bitstore.MutableBitStore

from bitstring.helpers import tidy_input_string


def bin2bitstore(binstring: str) -> MutableBitStore:
    binstring = tidy_input_string(binstring)
    binstring = binstring.replace('0b', '')
    mb = Mutibs.from_bin(binstring)
    return MutableBitStore(mb)


def hex2bitstore(hexstring: str) -> MutableBitStore:
    hexstring = tidy_input_string(hexstring)
    hexstring = hexstring.replace('0x', '')
    mb = Mutibs.from_hex(hexstring)
    return MutableBitStore(mb)


def oct2bitstore(octstring: str) -> MutableBitStore:
    octstring = tidy_input_string(octstring)
    octstring = octstring.replace('0o', '')
    mb = Mutibs.from_oct(octstring)
    return MutableBitStore(mb)


def int2bitstore(i: int, length: int, signed: bool) -> MutableBitStore:
    i = int(i)
    if length <= 128:
        try:
            if signed:
                mb = Mutibs.from_i(i, length=length)
            else:
                mb = Mutibs.from_u(i, length=length)
        except OverflowError as e:
            raise ValueError(e)
    else:
        b = i.to_bytes((length + 7) // 8, byteorder="big", signed=signed)
        offset = 8 - (length % 8)
        mb = Mutibs.from_bytes(b)
        if offset != 8:
            mb = mb[offset:]
    return MutableBitStore(mb)


def intle2bitstore(i: int, length: int, signed: bool) -> MutableBitStore:
    i = int(i)
    if length <= 128:
        try:
            if signed:
                mb = Mutibs.from_i(i, length=length)
            else:
                mb = Mutibs.from_u(i, length=length)
        except OverflowError as e:
            raise ValueError(e)
        mb.byte_swap()
    else:
        b = i.to_bytes((length + 7) // 8, byteorder="little", signed=signed)
        offset = 8 - (length % 8)
        mb = Mutibs.from_bytes(b)
        if offset != 8:
            mb = mb[offset:]
    return MutableBitStore(mb)


def float2bitstore(f: Union[str, float], length: int, big_endian: bool) -> MutableBitStore:
    f = float(f)
    mb = Mutibs.from_f(f, length)
    if not big_endian:
        mb.byte_swap()
    return MutableBitStore(mb)


CACHE_SIZE = 256

@functools.lru_cache(CACHE_SIZE)
def str_to_bitstore(s: str) -> MutableBitStore:
    _, tokens = bitstring.utils.tokenparser(s)
    constbitstores = [bitstore_from_token(*token) for token in tokens]
    return MutableBitStore.join(constbitstores)


literal_bit_funcs: Dict[str, Callable[..., MutableBitStore]] = {
    '0x': hex2bitstore,
    '0X': hex2bitstore,
    '0b': bin2bitstore,
    '0B': bin2bitstore,
    '0o': oct2bitstore,
    '0O': oct2bitstore,
}


def bitstore_from_token(name: str, token_length: Optional[int], value: Optional[str]) -> MutableBitStore:
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



def ue2bitstore(i: Union[str, int]) -> MutableBitStore:
    i = int(i)
    if i < 0:
        raise bitstring.CreationError("Cannot use negative initialiser for unsigned exponential-Golomb.")
    if i == 0:
        return MutableBitStore.from_bin('1')
    tmp = i + 1
    leadingzeros = -1
    while tmp > 0:
        tmp >>= 1
        leadingzeros += 1
    remainingpart = i + 1 - (1 << leadingzeros)
    return MutableBitStore.from_bin('0' * leadingzeros + '1') + int2bitstore(remainingpart, leadingzeros, False)


def se2bitstore(i: Union[str, int]) -> MutableBitStore:
    i = int(i)
    if i > 0:
        u = (i * 2) - 1
    else:
        u = -2 * i
    return ue2bitstore(u)


def uie2bitstore(i: Union[str, int]) -> MutableBitStore:
    i = int(i)
    if i < 0:
        raise bitstring.CreationError("Cannot use negative initialiser for unsigned interleaved exponential-Golomb.")
    return MutableBitStore.from_bin('1' if i == 0 else '0' + '0'.join(bin(i + 1)[3:]) + '1')


def sie2bitstore(i: Union[str, int]) -> MutableBitStore:
    i = int(i)
    if i == 0:
        return MutableBitStore.from_bin('1')
    else:
        return uie2bitstore(abs(i)) + (MutableBitStore.from_bin('1') if i < 0 else MutableBitStore.from_bin('0'))


def bfloat2bitstore(f: Union[str, float], big_endian: bool) -> MutableBitStore:
    f = float(f)
    fmt = '>f' if big_endian else '<f'
    try:
        b = struct.pack(fmt, f)
    except OverflowError:
        # For consistency, we overflow to 'inf'.
        b = struct.pack(fmt, float('inf') if f > 0 else float('-inf'))
    return MutableBitStore.from_bytes(b[0:2]) if big_endian else MutableBitStore.from_bytes(b[2:4])


def p4binary2bitstore(f: Union[str, float]) -> MutableBitStore:
    f = float(f)
    u = p4binary_fmt.float_to_int8(f)
    return int2bitstore(u, 8, False)


def p3binary2bitstore(f: Union[str, float]) -> MutableBitStore:
    f = float(f)
    u = p3binary_fmt.float_to_int8(f)
    return int2bitstore(u, 8, False)


def e4m3mxfp2bitstore(f: Union[str, float]) -> MutableBitStore:
    f = float(f)
    if bitstring.options.mxfp_overflow == 'saturate':
        u = e4m3mxfp_saturate_fmt.float_to_int(f)
    else:
        u = e4m3mxfp_overflow_fmt.float_to_int(f)
    return int2bitstore(u, 8, False)


def e5m2mxfp2bitstore(f: Union[str, float]) -> MutableBitStore:
    f = float(f)
    if bitstring.options.mxfp_overflow == 'saturate':
        u = e5m2mxfp_saturate_fmt.float_to_int(f)
    else:
        u = e5m2mxfp_overflow_fmt.float_to_int(f)
    return int2bitstore(u, 8, False)


def e3m2mxfp2bitstore(f: Union[str, float]) -> MutableBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e3m2mxfp format as it has no representation for it.")
    u = e3m2mxfp_fmt.float_to_int(f)
    return int2bitstore(u, 6, False)


def e2m3mxfp2bitstore(f: Union[str, float]) -> MutableBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m3mxfp format as it has no representation for it.")
    u = e2m3mxfp_fmt.float_to_int(f)
    return int2bitstore(u, 6, False)


def e2m1mxfp2bitstore(f: Union[str, float]) -> MutableBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m1mxfp format as it has no representation for it.")
    u = e2m1mxfp_fmt.float_to_int(f)
    return int2bitstore(u, 4, False)


e8m0mxfp_allowed_values = [float(2 ** x) for x in range(-127, 128)]


def e8m0mxfp2bitstore(f: Union[str, float]) -> MutableBitStore:
    f = float(f)
    if math.isnan(f):
        return MutableBitStore.from_bin('11111111')
    try:
        i = e8m0mxfp_allowed_values.index(f)
    except ValueError:
        raise ValueError(f"{f} is not a valid e8m0mxfp value. It must be exactly 2 ** i, for -127 <= i <= 127 or float('nan') as no rounding will be done.")
    return int2bitstore(i, 8, False)


def mxint2bitstore(f: Union[str, float]) -> MutableBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to mxint format as it has no representation for it.")
    f *= 2 ** 6  # Remove the implicit scaling factor
    if f > 127:  # 1 + 63/64
        return MutableBitStore.from_bin('01111111')
    if f <= -128:  # -2
        return MutableBitStore.from_bin('10000000')
    # Want to round to nearest, so move by 0.5 away from zero and round down by converting to int
    if f >= 0.0:
        f += 0.5
        i = int(f)
        # For ties-round-to-even
        if f - i == 0.0 and i % 2:
            i -= 1
    else:
        f -= 0.5
        i = int(f)
        if f - i == 0.0 and i % 2:
            i += 1
    return int2bitstore(i, 8, True)