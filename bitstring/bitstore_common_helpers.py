from __future__ import annotations

import struct
import math
from typing import Union, Dict, Callable, Optional
import functools
import bitstring
from bitstring.fp8 import p4binary_fmt, p3binary_fmt
from bitstring.mxfp import (e3m2mxfp_fmt, e2m3mxfp_fmt, e2m1mxfp_fmt, e4m3mxfp_saturate_fmt,
                            e5m2mxfp_saturate_fmt, e4m3mxfp_overflow_fmt, e5m2mxfp_overflow_fmt)

helpers = bitstring.bitstore_helpers
BitStore = bitstring.bitstore.BitStore


CACHE_SIZE = 256

@functools.lru_cache(CACHE_SIZE)
def str_to_bitstore(s: str) -> BitStore:
    _, tokens = bitstring.utils.tokenparser(s)
    bs = BitStore()
    for token in tokens:
        bs += bitstore_from_token(*token)
    bs.immutable = True
    return bs


literal_bit_funcs: Dict[str, Callable[..., BitStore]] = {
    '0x': helpers.hex2bitstore,
    '0X': helpers.hex2bitstore,
    '0b': helpers.bin2bitstore,
    '0B': helpers.bin2bitstore,
    '0o': helpers.oct2bitstore,
    '0O': helpers.oct2bitstore,
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



def ue2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i < 0:
        raise bitstring.CreationError("Cannot use negative initialiser for unsigned exponential-Golomb.")
    if i == 0:
        return BitStore.from_binary_string('1')
    tmp = i + 1
    leadingzeros = -1
    while tmp > 0:
        tmp >>= 1
        leadingzeros += 1
    remainingpart = i + 1 - (1 << leadingzeros)
    return BitStore.from_binary_string('0' * leadingzeros + '1') + helpers.int2bitstore(remainingpart, leadingzeros, False)


def se2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i > 0:
        u = (i * 2) - 1
    else:
        u = -2 * i
    return ue2bitstore(u)


def uie2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i < 0:
        raise bitstring.CreationError("Cannot use negative initialiser for unsigned interleaved exponential-Golomb.")
    return BitStore.from_binary_string('1' if i == 0 else '0' + '0'.join(bin(i + 1)[3:]) + '1')


def sie2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i == 0:
        return BitStore.from_binary_string('1')
    else:
        return uie2bitstore(abs(i)) + (BitStore.from_binary_string('1') if i < 0 else BitStore.from_binary_string('0'))


def bfloat2bitstore(f: Union[str, float], big_endian: bool) -> BitStore:
    f = float(f)
    fmt = '>f' if big_endian else '<f'
    try:
        b = struct.pack(fmt, f)
    except OverflowError:
        # For consistency, we overflow to 'inf'.
        b = struct.pack(fmt, float('inf') if f > 0 else float('-inf'))
    return BitStore.frombytes(b[0:2]) if big_endian else BitStore.frombytes(b[2:4])


def p4binary2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    u = p4binary_fmt.float_to_int8(f)
    return helpers.int2bitstore(u, 8, False)


def p3binary2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    u = p3binary_fmt.float_to_int8(f)
    return helpers.int2bitstore(u, 8, False)


def e4m3mxfp2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    if bitstring.options.mxfp_overflow == 'saturate':
        u = e4m3mxfp_saturate_fmt.float_to_int(f)
    else:
        u = e4m3mxfp_overflow_fmt.float_to_int(f)
    return helpers.int2bitstore(u, 8, False)


def e5m2mxfp2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    if bitstring.options.mxfp_overflow == 'saturate':
        u = e5m2mxfp_saturate_fmt.float_to_int(f)
    else:
        u = e5m2mxfp_overflow_fmt.float_to_int(f)
    return helpers.int2bitstore(u, 8, False)


def e3m2mxfp2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e3m2mxfp format as it has no representation for it.")
    u = e3m2mxfp_fmt.float_to_int(f)
    return helpers.int2bitstore(u, 6, False)


def e2m3mxfp2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m3mxfp format as it has no representation for it.")
    u = e2m3mxfp_fmt.float_to_int(f)
    return helpers.int2bitstore(u, 6, False)


def e2m1mxfp2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m1mxfp format as it has no representation for it.")
    u = e2m1mxfp_fmt.float_to_int(f)
    return helpers.int2bitstore(u, 4, False)


e8m0mxfp_allowed_values = [float(2 ** x) for x in range(-127, 128)]


def e8m0mxfp2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    if math.isnan(f):
        return BitStore.from_binary_string('11111111')
    try:
        i = e8m0mxfp_allowed_values.index(f)
    except ValueError:
        raise ValueError(f"{f} is not a valid e8m0mxfp value. It must be exactly 2 ** i, for -127 <= i <= 127 or float('nan') as no rounding will be done.")
    return helpers.int2bitstore(i, 8, False)


def mxint2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to mxint format as it has no representation for it.")
    f *= 2 ** 6  # Remove the implicit scaling factor
    if f > 127:  # 1 + 63/64
        return BitStore.from_binary_string('01111111')
    if f <= -128:  # -2
        return BitStore.from_binary_string('10000000')
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
    return helpers.int2bitstore(i, 8, True)