from __future__ import annotations

from tibs import Tibs, ByteOrder

import math
from collections.abc import Callable
import functools
import bitstring


MutableBitStore = bitstring.bitstore.MutableBitStore
ConstBitStore = bitstring.bitstore.ConstBitStore

from bitstring.helpers import tidy_input_string


def _int_to_tibs(i: int, length: int, signed: bool, little_endian: bool) -> Tibs:
    try:
        if signed:
            return Tibs.from_i(i, length, ByteOrder.Little if little_endian else ByteOrder.Unspecified)
        return Tibs.from_u(i, length, ByteOrder.Little if little_endian else ByteOrder.Unspecified)
    except (OverflowError, ValueError) as e:
        raise ValueError(e)


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
        raise ValueError(f"Can't parse token: {e}")
    if value is None and name != 'pad':
        raise ValueError(f"Token {name} requires a value.")
    bs = d.pack(value)._bitstore
    bs = _to_const_bitstore(bs)
    if token_length is not None and len(bs) != d._bitlength:
        raise ValueError(f"Token with length {token_length} packed with value of length {len(bs)} "
                                      f"({name}:{token_length}={value}).")
    return bs



def ue2bitstore(i: str | int) -> ConstBitStore:
    i = int(i)
    if i < 0:
        raise ValueError("Cannot use negative initialiser for unsigned exponential-Golomb.")
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
        raise ValueError("Cannot use negative initialiser for unsigned interleaved exponential-Golomb.")
    return ConstBitStore.from_bin('1' if i == 0 else '0' + '0'.join(bin(i + 1)[3:]) + '1')


def sie2bitstore(i: str | int) -> ConstBitStore:
    i = int(i)
    if i == 0:
        return ConstBitStore.from_bin('1')
    else:
        return uie2bitstore(abs(i)) + (ConstBitStore.from_bin('1') if i < 0 else ConstBitStore.from_bin('0'))


# The bfloat and narrow float formats are all encoded by tibs, which rounds once,
# directly from the Python float, with round-to-nearest ties-to-even. The formats that
# can't represent NaN are pre-checked here so that the error names the bitstring dtype
# rather than tibs' own name for it.

def bfloat2bitstore(f: str | float, big_endian: bool) -> ConstBitStore:
    return ConstBitStore(Tibs.from_value('bf16_be' if big_endian else 'bf16_le', float(f)))


def p4binary2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore(Tibs.from_value('binary8p4', float(f)))


def p3binary2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore(Tibs.from_value('binary8p3', float(f)))


def e4m3mxfp_saturate2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore(Tibs.from_value('ocp_e4m3_saturate', float(f)))


def e4m3mxfp_overflow2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore(Tibs.from_value('ocp_e4m3_overflow', float(f)))


def e5m2mxfp_saturate2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore(Tibs.from_value('ocp_e5m2_saturate', float(f)))


def e5m2mxfp_overflow2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore(Tibs.from_value('ocp_e5m2_overflow', float(f)))


def e3m2mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e3m2mxfp format as it has no representation for it.")
    return ConstBitStore(Tibs.from_value('ocp_e3m2', f))


def e2m3mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m3mxfp format as it has no representation for it.")
    return ConstBitStore(Tibs.from_value('ocp_e2m3', f))


def e2m1mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m1mxfp format as it has no representation for it.")
    return ConstBitStore(Tibs.from_value('ocp_e2m1', f))


def e8m0mxfp2bitstore(f: str | float) -> ConstBitStore:
    # No rounding is done for this one - the value has to land exactly on a power of two.
    f = float(f)
    try:
        return ConstBitStore(Tibs.from_value('ocp_e8m0', f))
    except ValueError:
        raise ValueError(f"{f} is not a valid e8m0mxfp value. It must be exactly 2 ** i, for -127 <= i <= 127 or float('nan') as no rounding will be done.")


def mxint2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to mxint format as it has no representation for it.")
    return ConstBitStore(Tibs.from_value('ocp_int8', f))
