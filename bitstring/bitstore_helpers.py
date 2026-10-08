from __future__ import annotations

from tibs import Tibs, ByteOrder

import math
import operator
from collections.abc import Callable
import functools
import bitstring


ConstBitStore = bitstring.bitstore.ConstBitStore

from bitstring.helpers import tidy_input_string


def _whole_number(value: str | int) -> int:
    """An int from a value, or from the string form a format string token gives.

    int() would truncate a float, so `Bits(u=3.9, length=8)` quietly packed 3. tibs
    rejects a float outright when packing in bulk, so this keeps the two agreeing.
    """
    if isinstance(value, str):
        return int(value)
    try:
        return operator.index(value)
    except TypeError:
        raise ValueError(f"An integer dtype needs a whole number, but received {value!r}, "
                         f"which is a {type(value).__name__}.") from None


def _int_to_tibs(i: int, length: int, signed: bool, little_endian: bool) -> Tibs:
    try:
        if signed:
            return Tibs.from_i(i, length, ByteOrder.Little if little_endian else ByteOrder.Unspecified)
        return Tibs.from_u(i, length, ByteOrder.Little if little_endian else ByteOrder.Unspecified)
    except (OverflowError, ValueError) as e:
        raise ValueError(e)


def _misplaced_prefix_error(s: str, prefix: str, example: str, e: ValueError) -> ValueError:
    """A clearer error than the core's 'invalid character' when a prefix is part way through.

    Only called once the core has rejected s, so valid strings never pay for the check.
    """
    if prefix not in s.removeprefix(prefix):
        return e
    return ValueError(
        f"A '{prefix}' prefix can only come at the start, but '{s}' has one later on. Join "
        f"separate literals with commas instead, for example '{prefix}{example}, {prefix}{example}', "
        f"or repeat a bitstring with *, as in Bits('{prefix}{example}') * 10.")


# The core accepts one optional leading prefix, and rejects any later one. Version 4
# removed the prefix from anywhere, which made '0x55' * 10 work but also quietly
# accepted strings such as '10b1' as '0b11'.

def bin2bitstore(binstring: str) -> ConstBitStore:
    binstring = tidy_input_string(binstring)
    try:
        return ConstBitStore.from_bin(binstring)
    except ValueError as e:
        raise _misplaced_prefix_error(binstring, '0b', '0101', e) from None


def hex2bitstore(hexstring: str) -> ConstBitStore:
    hexstring = tidy_input_string(hexstring)
    try:
        return ConstBitStore(Tibs.from_hex(hexstring))
    except ValueError as e:
        raise _misplaced_prefix_error(hexstring, '0x', '55', e) from None


def oct2bitstore(octstring: str) -> ConstBitStore:
    octstring = tidy_input_string(octstring)
    try:
        return ConstBitStore(Tibs.from_oct(octstring))
    except ValueError as e:
        raise _misplaced_prefix_error(octstring, '0o', '17', e) from None


def int2bitstore(i: int, length: int, signed: bool) -> ConstBitStore:
    i = _whole_number(i)
    t = _int_to_tibs(i, length, signed, little_endian=False)
    return ConstBitStore(t)


def intle2bitstore(i: int, length: int, signed: bool) -> ConstBitStore:
    i = _whole_number(i)
    t = _int_to_tibs(i, length, signed, little_endian=True)
    return ConstBitStore(t)


def float2bitstore(f: str | float, length: int, big_endian: bool) -> ConstBitStore:
    f = float(f)
    t = Tibs.from_f(f, length, ByteOrder.Big if big_endian else ByteOrder.Little)
    return ConstBitStore(t)


CACHE_SIZE = 256

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
    '0x': hex2bitstore,
    '0X': hex2bitstore,
    '0b': bin2bitstore,
    '0B': bin2bitstore,
    '0o': oct2bitstore,
    '0O': oct2bitstore,
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
    bs = d.pack(value)._bitstore.to_const()
    if token_length is not None and len(bs) != d._bitlength:
        raise ValueError(f"Token with length {token_length} packed with value of length {len(bs)} "
                                      f"({name}:{token_length}={value}).")
    return bs



def ue2bitstore(i: str | int) -> ConstBitStore:
    i = _whole_number(i)
    if i < 0:
        raise ValueError("Cannot use negative initialiser for unsigned exponential-Golomb.")
    # The code is i + 1 in binary, after as many zeros as it has bits following its leading 1.
    return ConstBitStore(Tibs.from_u(i + 1, 2 * (i + 1).bit_length() - 1))


def se2bitstore(i: str | int) -> ConstBitStore:
    i = _whole_number(i)
    if i > 0:
        u = (i * 2) - 1
    else:
        u = -2 * i
    return ue2bitstore(u)


def uie2bitstore(i: str | int) -> ConstBitStore:
    i = _whole_number(i)
    if i < 0:
        raise ValueError("Cannot use negative initialiser for unsigned interleaved exponential-Golomb.")
    return ConstBitStore.from_bin('1' if i == 0 else '0' + '0'.join(bin(i + 1)[3:]) + '1')


def sie2bitstore(i: str | int) -> ConstBitStore:
    i = _whole_number(i)
    if i == 0:
        return ConstBitStore.from_bin('1')
    else:
        return uie2bitstore(abs(i)) + (ConstBitStore.from_bin('1') if i < 0 else ConstBitStore.from_bin('0'))


# The tibs dtypes for the bfloat and narrow float formats, looked up once rather than
# parsed from a name on every pack.
_TIBS_BFLOAT = bitstring.bitstore.tibs_dtype_for('bfloat', 16)
_TIBS_BFLOATLE = bitstring.bitstore.tibs_dtype_for('bfloatle', 16)
_TIBS_P4BINARY = bitstring.bitstore.tibs_dtype_for('p4binary', 8)
_TIBS_P3BINARY = bitstring.bitstore.tibs_dtype_for('p3binary', 8)
_TIBS_E4M3MXFP_SATURATE = bitstring.bitstore.tibs_dtype_for('e4m3mxfp_saturate', 8)
_TIBS_E4M3MXFP_OVERFLOW = bitstring.bitstore.tibs_dtype_for('e4m3mxfp_overflow', 8)
_TIBS_E5M2MXFP_SATURATE = bitstring.bitstore.tibs_dtype_for('e5m2mxfp_saturate', 8)
_TIBS_E5M2MXFP_OVERFLOW = bitstring.bitstore.tibs_dtype_for('e5m2mxfp_overflow', 8)
_TIBS_E3M2MXFP = bitstring.bitstore.tibs_dtype_for('e3m2mxfp', 6)
_TIBS_E2M3MXFP = bitstring.bitstore.tibs_dtype_for('e2m3mxfp', 6)
_TIBS_E2M1MXFP = bitstring.bitstore.tibs_dtype_for('e2m1mxfp', 4)
_TIBS_E8M0MXFP = bitstring.bitstore.tibs_dtype_for('e8m0mxfp', 8)
_TIBS_MXINT = bitstring.bitstore.tibs_dtype_for('mxint', 8)

# The bfloat and narrow float formats are all encoded by tibs, which rounds once,
# directly from the Python float, with round-to-nearest ties-to-even. The formats that
# can't represent NaN are pre-checked here so that the error names the bitstring dtype
# rather than tibs' own name for it.

def bfloat2bitstore(f: str | float, big_endian: bool) -> ConstBitStore:
    return ConstBitStore.from_value(_TIBS_BFLOAT if big_endian else _TIBS_BFLOATLE, float(f))


def p4binary2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore.from_value(_TIBS_P4BINARY, float(f))


def p3binary2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore.from_value(_TIBS_P3BINARY, float(f))


def e4m3mxfp_saturate2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore.from_value(_TIBS_E4M3MXFP_SATURATE, float(f))


def e4m3mxfp_overflow2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore.from_value(_TIBS_E4M3MXFP_OVERFLOW, float(f))


def e5m2mxfp_saturate2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore.from_value(_TIBS_E5M2MXFP_SATURATE, float(f))


def e5m2mxfp_overflow2bitstore(f: str | float) -> ConstBitStore:
    return ConstBitStore.from_value(_TIBS_E5M2MXFP_OVERFLOW, float(f))


def e3m2mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e3m2mxfp format as it has no representation for it.")
    return ConstBitStore.from_value(_TIBS_E3M2MXFP, f)


def e2m3mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m3mxfp format as it has no representation for it.")
    return ConstBitStore.from_value(_TIBS_E2M3MXFP, f)


def e2m1mxfp2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to e2m1mxfp format as it has no representation for it.")
    return ConstBitStore.from_value(_TIBS_E2M1MXFP, f)


def e8m0mxfp2bitstore(f: str | float) -> ConstBitStore:
    # No rounding is done for this one - the value has to land exactly on a power of two.
    f = float(f)
    try:
        return ConstBitStore.from_value(_TIBS_E8M0MXFP, f)
    except ValueError:
        raise ValueError(f"{f} is not a valid e8m0mxfp value. It must be exactly 2 ** i, for -127 <= i <= 127 or float('nan') as no rounding will be done.")


def mxint2bitstore(f: str | float) -> ConstBitStore:
    f = float(f)
    if math.isnan(f):
        raise ValueError("Cannot convert float('nan') to mxint format as it has no representation for it.")
    return ConstBitStore.from_value(_TIBS_MXINT, f)
