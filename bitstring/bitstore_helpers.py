from __future__ import annotations

import sys
import struct
import functools
from typing import Union, Optional, Dict, Callable
import bitarray
from bitstring.bitstore import BitStore
import bitstring
from bitstring.fp8 import e4m3float_fmt, e5m2float_fmt


byteorder: str = sys.byteorder

# The size of various caches used to improve performance
CACHE_SIZE = 256


def tidy_input_string(s: str) -> str:
    """Return string made lowercase and with all whitespace and underscores removed."""
    try:
        t = s.split()
    except (AttributeError, TypeError):
        raise ValueError(f"Expected str object but received a {type(s)} with value {s}.")
    return ''.join(t).lower().replace('_', '')


@functools.lru_cache(CACHE_SIZE)
def str_to_bitstore(s: str) -> BitStore:
    try:
        _, tokens = bitstring.utils.tokenparser(s)
    except ValueError as e:
        raise bitstring.CreationError(*e.args)
    bs = BitStore()
    for token in tokens:
        bs += bitstore_from_token(*token)
    bs.immutable = True
    return bs


def bin2bitstore(binstring: str) -> BitStore:
    binstring = tidy_input_string(binstring)
    binstring = binstring.replace('0b', '')
    return bin2bitstore_unsafe(binstring)


def bin2bitstore_unsafe(binstring: str) -> BitStore:
    try:
        return BitStore(binstring)
    except ValueError:
        raise bitstring.CreationError(f"Invalid character in bin initialiser {binstring}.")


def hex2bitstore(hexstring: str) -> BitStore:
    hexstring = tidy_input_string(hexstring)
    hexstring = hexstring.replace('0x', '')
    try:
        ba = bitarray.util.hex2ba(hexstring)
    except ValueError:
        raise bitstring.CreationError("Invalid symbol in hex initialiser.")
    return BitStore(ba)


def oct2bitstore(octstring: str) -> BitStore:
    octstring = tidy_input_string(octstring)
    octstring = octstring.replace('0o', '')
    try:
        ba = bitarray.util.base2ba(8, octstring)
    except ValueError:
        raise bitstring.CreationError("Invalid symbol in oct initialiser.")
    return BitStore(ba)


def ue2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i < 0:
        raise bitstring.CreationError("Cannot use negative initialiser for unsigned exponential-Golomb.")
    if i == 0:
        return BitStore('1')
    tmp = i + 1
    leadingzeros = -1
    while tmp > 0:
        tmp >>= 1
        leadingzeros += 1
    remainingpart = i + 1 - (1 << leadingzeros)
    return BitStore('0' * leadingzeros + '1') + uint2bitstore(remainingpart, leadingzeros)


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
    return BitStore('1' if i == 0 else '0' + '0'.join(bin(i + 1)[3:]) + '1')


def sie2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i == 0:
        return BitStore('1')
    else:
        return uie2bitstore(abs(i)) + (BitStore('1') if i < 0 else BitStore('0'))


def bfloat2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    try:
        b = struct.pack('>f', f)
    except OverflowError:
        # For consistency we overflow to 'inf'.
        b = struct.pack('>f', float('inf') if f > 0 else float('-inf'))
    return BitStore(frombytes=b[0:2])


def bfloatle2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    try:
        b = struct.pack('<f', f)
    except OverflowError:
        # For consistency we overflow to 'inf'.
        b = struct.pack('<f', float('inf') if f > 0 else float('-inf'))
    return BitStore(frombytes=b[2:4])


def e4m3float2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    u = e4m3float_fmt.float_to_int8(f)
    return uint2bitstore(u, 8)


def e5m2float2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    u = e5m2float_fmt.float_to_int8(f)
    return uint2bitstore(u, 8)


def uint2bitstore(uint: Union[str, int], length: int) -> BitStore:
    uint = int(uint)
    try:
        if length is None:
            raise ValueError("No bit length provided when initialising from unsigned int.")
        x = BitStore(bitarray.util.int2ba(uint, length=length, endian='big', signed=False))
    except OverflowError as e:
        if uint >= (1 << length):
            msg = f"{uint} is too large an unsigned integer for a bitstring of length {length}. " \
                  f"The allowed range is [0, {(1 << length) - 1}]."
            raise bitstring.CreationError(msg)
        if uint < 0:
            raise bitstring.CreationError("uint cannot be initialised with a negative number.")
        raise e
    return x


def int2bitstore(i: Union[str, int], length: int) -> BitStore:
    i = int(i)
    try:
        if length is None:
            raise ValueError("No bit length provided when initialising from signed int.")
        x = BitStore(bitarray.util.int2ba(i, length=length, endian='big', signed=True))
    except OverflowError as e:
        if i >= (1 << (length - 1)) or i < -(1 << (length - 1)):
            raise bitstring.CreationError(f"{i} is too large a signed integer for a bitstring of length {length}. "
                                f"The allowed range is [{-(1 << (length - 1))}, {(1 << (length - 1)) - 1}].")
        else:
            raise e
    return x


def uintbe2bitstore(i: Union[str, int], length: int) -> BitStore:
    if length % 8 != 0:
        raise bitstring.CreationError(f"Big-endian integers must be whole-byte. Length = {length} bits.")
    return uint2bitstore(i, length)


def intbe2bitstore(i: int, length: int) -> BitStore:
    if length % 8 != 0:
        raise bitstring.CreationError(f"Big-endian integers must be whole-byte. Length = {length} bits.")
    return int2bitstore(i, length)


def uintle2bitstore(i: int, length: int) -> BitStore:
    if length % 8 != 0:
        raise bitstring.CreationError(f"Little-endian integers must be whole-byte. Length = {length} bits.")
    x = uint2bitstore(i, length).tobytes()
    return BitStore(frombytes=x[::-1])


def intle2bitstore(i: int, length: int) -> BitStore:
    if length % 8 != 0:
        raise bitstring.CreationError(f"Little-endian integers must be whole-byte. Length = {length} bits.")
    x = int2bitstore(i, length).tobytes()
    return BitStore(frombytes=x[::-1])


def float2bitstore(f: Union[str, float], length: int) -> BitStore:
    f = float(f)
    fmt = {16: '>e', 32: '>f', 64: '>d'}[length]
    try:
        b = struct.pack(fmt, f)
        assert len(b) * 8 == length
    except (OverflowError, struct.error) as e:
        # If float64 doesn't fit it automatically goes to 'inf'. This reproduces that behaviour for other types.
        if length in [16, 32]:
            b = struct.pack(fmt, float('inf') if f > 0 else float('-inf'))
        else:
            raise e
    return BitStore(frombytes=b)


def floatle2bitstore(f: Union[str, float], length: int) -> BitStore:
    f = float(f)
    fmt = {16: '<e', 32: '<f', 64: '<d'}[length]
    try:
        b = struct.pack(fmt, f)
        assert len(b) * 8 == length
    except (OverflowError, struct.error) as e:
        # If float64 doesn't fit it automatically goes to 'inf'. This reproduces that behaviour for other types.
        if length in [16, 32]:
            b = struct.pack(fmt, float('inf') if f > 0 else float('-inf'))
        else:
            raise e
    return BitStore(frombytes=b)


def bytes2bitstore(b: bytes, length: int) -> BitStore:
    return BitStore(frombytes=b[:length])


literal_bit_funcs: Dict[str, Callable[..., BitStore]] = {
    '0x': hex2bitstore,
    '0X': hex2bitstore,
    '0b': bin2bitstore,
    '0B': bin2bitstore,
    '0o': oct2bitstore,
    '0O': oct2bitstore,
}

def bitstore_from_token(name: str, token_length: Optional[int], value: Optional[str]) -> BitStore:
    try:
        d = bitstring.dtypes.Dtype(name, token_length)
    except ValueError as e:
        if name in literal_bit_funcs:
            bs = literal_bit_funcs[name](value)
        else:
            raise bitstring.CreationError(f"Can't parse token: {e}")
    else:
        b = bitstring.bits.Bits()
        if value is None and name != 'pad':
            # 'pad' is a special case - the only dtype that can be constructed from a length with no value.
            raise ValueError
        d.set_fn(b, value)
        bs = b._bitstore
        if token_length is not None and len(bs) != d.bitlength:
            raise bitstring.CreationError(f"Token with length {token_length} packed with value of length {len(bs)} "
                                f"({name}:{token_length}={value}).")
    return bs
