from __future__ import annotations

from tibs import Tibs, ByteOrder

import struct
import math
from collections.abc import Callable
import functools
import bitstring
from bitstring.fp8 import p4binary_fmt, p3binary_fmt
from bitstring.mxfp import (e3m2mxfp_fmt, e2m3mxfp_fmt, e2m1mxfp_fmt, e4m3mxfp_saturate_fmt,
                            e5m2mxfp_saturate_fmt, e4m3mxfp_overflow_fmt, e5m2mxfp_overflow_fmt)


MutableBitStore = bitstring.bitstore.MutableBitStore
ConstBitStore = bitstring.bitstore.ConstBitStore

from bitstring.helpers import tidy_input_string


def _int_to_tibs(i: int, length: int, signed: bool, little_endian: bool) -> Tibs:
    try:
        if signed:
            return Tibs.from_i(i, length, ByteOrder.Little if little_endian else ByteOrder.Unspecified)
        return Tibs.from_u(i, length, ByteOrder.Little if little_endian else ByteOrder.Unspecified)
    except (OverflowError, ValueError) as e:
        # Keep tibs validation for normal sizes and unsupported values.
        if length <= 128:
            raise ValueError(e)
    byteorder = "little" if little_endian else "big"
    b = i.to_bytes((length + 7) // 8, byteorder=byteorder, signed=signed)
    offset = (-length) % 8
    return Tibs.from_bytes(b, offset=offset, length=length)


def bin2bitstore(binstring: str) -> ConstBitStore:
    binstring = tidy_input_string(binstring)
    binstring = binstring.replace('0b', '')
    return ConstBitStore.from_bin(binstring)


def hex2bitstore(hexstring: str) -> ConstBitStore:
    hexstring = tidy_input_string(hexstring)
    hexstring = hexstring.replace('0x', '')
    return ConstBitStore(Tibs.from_hex(hexstring))


def oct2bitstore(octstring: str) -> ConstBitStore:
    octstring = tidy_input_string(octstring)
    octstring = octstring.replace('0o', '')
    return ConstBitStore(Tibs.from_oct(octstring))


def int2bitstore(i: int, length: int, signed: bool) -> ConstBitStore:
    i = int(i)
    t = _int_to_tibs(i, length, signed, little_endian=False)
    return ConstBitStore(t)


def intle2bitstore(i: int, length: int, signed: bool) -> ConstBitStore:
    i = int(i)
    t = _int_to_tibs(i, length, signed, little_endian=True)
    return ConstBitStore(t)


def float2bitstore(f: str | float, length: int, big_endian: bool) -> ConstBitStore:
    f = float(f)
    t = Tibs.from_f(f, length, ByteOrder.Big if big_endian else ByteOrder.Little)
    return ConstBitStore(t)


CACHE_SIZE = 256

def _to_const_bitstore(bs: MutableBitStore | ConstBitStore) -> ConstBitStore:
    if isinstance(bs, ConstBitStore):
        return bs
    return ConstBitStore(bs.tibs.to_tibs())


def _bin_literal_to_const_bitstore(binstring: str) -> ConstBitStore:
    binstring = tidy_input_string(binstring)
    binstring = binstring.replace('0b', '')
    return ConstBitStore.from_bin(binstring)


def _hex_literal_to_const_bitstore(hexstring: str) -> ConstBitStore:
    hexstring = tidy_input_string(hexstring)
    hexstring = hexstring.replace('0x', '')
    return ConstBitStore(Tibs.from_hex(hexstring))


def _oct_literal_to_const_bitstore(octstring: str) -> ConstBitStore:
    octstring = tidy_input_string(octstring)
    octstring = octstring.replace('0o', '')
    return ConstBitStore(Tibs.from_oct(octstring))


@functools.lru_cache(CACHE_SIZE)
def str_to_bitstore(s: str) -> ConstBitStore:
    # Fast path for literal-only strings (e.g. "0xff, 0b101, 0o7").
    try:
        return ConstBitStore(Tibs.from_string(s))
    except ValueError:
        pass
    _, tokens = bitstring.utils.tokenparser(s)
    constbitstores = [bitstore_from_token(*token) for token in tokens]
    return ConstBitStore.join(constbitstores)


literal_bit_funcs: dict[str, Callable[..., ConstBitStore]] = {
    '0x': _hex_literal_to_const_bitstore,
    '0X': _hex_literal_to_const_bitstore,
    '0b': _bin_literal_to_const_bitstore,
    '0B': _bin_literal_to_const_bitstore,
    '0o': _oct_literal_to_const_bitstore,
    '0O': _oct_literal_to_const_bitstore,
}


def bitstore_from_token(name: str, token_length: int | None, value: str | None) -> ConstBitStore:
    if name in literal_bit_funcs:
        return literal_bit_funcs[name](value)
    try:
        d = bitstring.dtypes.Dtype(name, token_length)
    except ValueError as e:
        raise bitstring.CreationError(f"Can't parse token: {e}")
    if value is None and name != 'pad':
        raise ValueError(f"Token {name} requires a value.")
    bs = d.pack(value)._bitstore
    bs = _to_const_bitstore(bs)
    if token_length is not None and len(bs) != d.bitlength:
        raise bitstring.CreationError(f"Token with length {token_length} packed with value of length {len(bs)} "
                                      f"({name}:{token_length}={value}).")
    return bs



def ue2bitstore(i: str | int) -> ConstBitStore:
    i = int(i)
    if i < 0:
        raise bitstring.CreationError("Cannot use negative initialiser for unsigned exponential-Golomb.")
    if i == 0:
        return ConstBitStore.from_bin('1')
    tmp = i + 1
    leadingzeros = -1
    while tmp > 0:
        tmp >>= 1
        leadingzeros += 1
    remainingpart = i + 1 - (1 << leadingzeros)
    return ConstBitStore.from_bin('0' * leadingzeros + '1') + int2bitstore(remainingpart, leadingzeros, False)


def se2bitstore(i: str | int) -> ConstBitStore:
    i = int(i)
    if i > 0:
        u = (i * 2) - 1
    else:
        u = -2 * i
    return ue2bitstore(u)


def uie2bitstore(i: str | int) -> ConstBitStore:
    i = int(i)
    if i < 0:
        raise bitstring.CreationError("Cannot use negative initialiser for unsigned interleaved exponential-Golomb.")
    return ConstBitStore.from_bin('1' if i == 0 else '0' + '0'.join(bin(i + 1)[3:]) + '1')


def sie2bitstore(i: str | int) -> ConstBitStore:
    i = int(i)
    if i == 0:
        return ConstBitStore.from_bin('1')
    else:
        return uie2bitstore(abs(i)) + (ConstBitStore.from_bin('1') if i < 0 else ConstBitStore.from_bin('0'))


def bfloat2bitstore(f: str | float, big_endian: bool) -> ConstBitStore:
    f = float(f)
    fmt = '>f' if big_endian else '<f'
    try:
        b = struct.pack(fmt, f)
    except OverflowError:
        # For consistency, we overflow to 'inf'.
        b = struct.pack(fmt, float('inf') if f > 0 else float('-inf'))
    return ConstBitStore.from_bytes(b[0:2]) if big_endian else ConstBitStore.from_bytes(b[2:4])


def p4binary2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    u = p4binary_fmt.float_to_int8(f)
    return int2bitstore(u, 8, False)


def p3binary2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    u = p3binary_fmt.float_to_int8(f)
    return int2bitstore(u, 8, False)


def e4m3mxfp_saturate2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    u = e4m3mxfp_saturate_fmt.float_to_int(f)
    return int2bitstore(u, 8, False)


def e4m3mxfp_overflow2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    u = e4m3mxfp_overflow_fmt.float_to_int(f)
    return int2bitstore(u, 8, False)


def e5m2mxfp_saturate2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    u = e5m2mxfp_saturate_fmt.float_to_int(f)
    return int2bitstore(u, 8, False)


def e5m2mxfp_overflow2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    u = e5m2mxfp_overflow_fmt.float_to_int(f)
    return int2bitstore(u, 8, False)


def e3m2mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e3m2mxfp format as it has no representation for it.")
    u = e3m2mxfp_fmt.float_to_int(f)
    return int2bitstore(u, 6, False)


def e2m3mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m3mxfp format as it has no representation for it.")
    u = e2m3mxfp_fmt.float_to_int(f)
    return int2bitstore(u, 6, False)


def e2m1mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m1mxfp format as it has no representation for it.")
    u = e2m1mxfp_fmt.float_to_int(f)
    return int2bitstore(u, 4, False)


e8m0mxfp_allowed_values = [float(2 ** x) for x in range(-127, 128)]


def e8m0mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        return ConstBitStore.from_bin('11111111')
    try:
        i = e8m0mxfp_allowed_values.index(f)
    except ValueError:
        raise ValueError(f"{f} is not a valid e8m0mxfp value. It must be exactly 2 ** i, for -127 <= i <= 127 or float('nan') as no rounding will be done.")
    return int2bitstore(i, 8, False)


def mxint2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to mxint format as it has no representation for it.")
    f *= 2 ** 6  # Remove the implicit scaling factor
    if f > 127:  # 1 + 63/64
        return ConstBitStore.from_bin('01111111')
    if f <= -128:  # -2
        return ConstBitStore.from_bin('10000000')
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
