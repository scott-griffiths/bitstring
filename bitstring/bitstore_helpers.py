from __future__ import annotations

import sys
import struct
import functools
from typing import Union, Optional, Dict, Callable
import bitarray
import bitarray.util
from bitstring.utils import tokenparser
from bitstring.exceptions import CreationError, InterpretError
from bitstring.fp8 import e4m3float_fmt, e5m2float_fmt
from bitstring.bitstore import BitStore

byteorder: str = sys.byteorder

# The size of various caches used to improve performance
CACHE_SIZE = 256


def tidy_input_string(s: str) -> str:
    """Return string made lowercase and with all whitespace and underscores removed."""
    try:
        l = s.split()
    except (AttributeError, TypeError):
        raise ValueError(f"Expected str object but received a {type(s)} with value {s}.")
    return ''.join(l).lower().replace('_', '')

# TODO: Shouldn't this be different for LSB0? The bitstores should be reversed before concatenating and we can raise an error for variable length tokens.
@functools.lru_cache(CACHE_SIZE)
def str_to_bitstore(s: str) -> BitStore:
    try:
        _, tokens = tokenparser(s)
    except ValueError as e:
        raise CreationError(*e.args)
    bs = BitStore()
    if tokens:
        bs = bs + bitstore_from_token(*tokens[0])
        for token in tokens[1:]:
            bs = bs + bitstore_from_token(*token)
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
        raise CreationError(f"Invalid character in bin initialiser {binstring}.")


def hex2bitstore(hexstring: str) -> BitStore:
    hexstring = tidy_input_string(hexstring)
    hexstring = hexstring.replace('0x', '')
    try:
        ba = bitarray.util.hex2ba(hexstring)
    except ValueError:
        raise CreationError("Invalid symbol in hex initialiser.")
    return BitStore(ba)


def oct2bitstore(octstring: str) -> BitStore:
    octstring = tidy_input_string(octstring)
    octstring = octstring.replace('0o', '')
    try:
        ba = bitarray.util.base2ba(8, octstring)
    except ValueError:
        raise CreationError("Invalid symbol in oct initialiser.")
    return BitStore(ba)


def ue2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i < 0:
        raise CreationError("Cannot use negative initialiser for unsigned exponential-Golomb.")
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
        raise CreationError("Cannot use negative initialiser for unsigned interleaved exponential-Golomb.")
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


def e4m3float_2bitstore(f: Union[str, float]) -> BitStore:
    f = float(f)
    u = e4m3float_fmt.float_to_int8(f)
    return uint2bitstore(u, 8)


def e5m2float_2bitstore(f: Union[str, float]) -> BitStore:
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
            raise CreationError(msg)
        if uint < 0:
            raise CreationError("uint cannot be initialised with a negative number.")
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
            raise CreationError(f"{i} is too large a signed integer for a bitstring of length {length}. "
                                f"The allowed range is [{-(1 << (length - 1))}, {(1 << (length - 1)) - 1}].")
        else:
            raise e
    return x


def uintbe2bitstore(i: Union[str, int], length: int) -> BitStore:
    if length % 8 != 0:
        raise CreationError(f"Big-endian integers must be whole-byte. Length = {length} bits.")
    return uint2bitstore(i, length)


def intbe2bitstore(i: int, length: int) -> BitStore:
    if length % 8 != 0:
        raise CreationError(f"Big-endian integers must be whole-byte. Length = {length} bits.")
    return int2bitstore(i, length)


def uintle2bitstore(i: int, length: int) -> BitStore:
    if length % 8 != 0:
        raise CreationError(f"Little-endian integers must be whole-byte. Length = {length} bits.")
    x = uint2bitstore(i, length).tobytes()
    return BitStore(frombytes=x[::-1])


def intle2bitstore(i: int, length: int) -> BitStore:
    if length % 8 != 0:
        raise CreationError(f"Little-endian integers must be whole-byte. Length = {length} bits.")
    x = int2bitstore(i, length).tobytes()
    return BitStore(frombytes=x[::-1])


def float2bitstore(f: Union[str, float], length: int) -> BitStore:
    f = float(f)
    try:
        fmt = {16: '>e', 32: '>f', 64: '>d'}[length]
    except KeyError:
        raise InterpretError(f"Floats can only be 16, 32 or 64 bits long, not {length} bits")
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
    try:
        fmt = {16: '<e', 32: '<f', 64: '<d'}[length]
    except KeyError:
        raise InterpretError(f"Floats can only be 16, 32 or 64 bits long, not {length} bits")
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


# Create native-endian functions as aliases depending on the byteorder
if byteorder == 'little':
    uintne2bitstore = uintle2bitstore
    intne2bitstore = intle2bitstore
    bfloatne2bitstore = bfloatle2bitstore
    floatne2bitstore = floatle2bitstore
else:
    uintne2bitstore = uintbe2bitstore
    intne2bitstore = intbe2bitstore
    bfloatne2bitstore = bfloat2bitstore
    floatne2bitstore = float2bitstore

# Given a string of the format 'name=value' get a bitstore representing it by using
# _name2bitstore_func[name](value)
name2bitstore_func: Dict[str, Callable[..., BitStore]] = {
    'hex': hex2bitstore,
    'h': hex2bitstore,
    '0x': hex2bitstore,
    '0X': hex2bitstore,
    'bin': bin2bitstore,
    'b': bin2bitstore,
    '0b': bin2bitstore,
    '0B': bin2bitstore,
    'oct': oct2bitstore,
    'o': oct2bitstore,
    '0o': oct2bitstore,
    '0O': oct2bitstore,
    'se': se2bitstore,
    'ue': ue2bitstore,
    'sie': sie2bitstore,
    'uie': uie2bitstore,
    'bfloat': bfloat2bitstore,
    'bfloatbe': bfloat2bitstore,
    'bfloatle': bfloatle2bitstore,
    'bfloatne': bfloatne2bitstore,
    'e4m3float': e4m3float_2bitstore,
    'e5m2float': e5m2float_2bitstore,
}

# Given a string of the format 'name[:]length=value' get a bitstore representing it by using
# _name2bitstore_func_with_length[name](value, length)
name2bitstore_func_with_length: Dict[str, Callable[..., BitStore]] = {
    'uint': uint2bitstore,
    'int': int2bitstore,
    'u': uint2bitstore,
    'i': int2bitstore,
    'uintbe': uintbe2bitstore,
    'intbe': intbe2bitstore,
    'uintle': uintle2bitstore,
    'intle': intle2bitstore,
    'uintne': uintne2bitstore,
    'intne': intne2bitstore,
    'float': float2bitstore,
    'f': float2bitstore,
    'floatbe': float2bitstore,  # same as 'float'
    'floatle': floatle2bitstore,
    'floatne': floatne2bitstore,
    'bytes': bytes2bitstore
}


def bitstore_from_token(name: str, token_length: Optional[int], value: Optional[str]) -> BitStore:
    if token_length == 0:
        return BitStore()
    # For pad token just return the length in zero bits
    if name == 'pad':
        bs = BitStore(token_length)
        bs.setall(0)
        return bs
    if value is None:
        if token_length is None:
            raise ValueError(f"Token has no value ({name}=???).")
        else:
            raise ValueError(f"Token has no value ({name}:{token_length}=???).")

    if name in name2bitstore_func:
        bs = name2bitstore_func[name](value)
    elif name in name2bitstore_func_with_length:
        bs = name2bitstore_func_with_length[name](value, token_length)
    elif name == 'bool':
        if value in (1, 'True', '1'):
            bs = BitStore('1')
        elif value in (0, 'False', '0'):
            bs = BitStore('0')
        else:
            raise CreationError("bool token can only be 'True' or 'False'.")
    else:
        raise CreationError(f"Can't parse token name {name}.")
    if token_length is not None and len(bs) != token_length:
        raise CreationError(f"Token with length {token_length} packed with value of length {len(bs)} "
                            f"({name}:{token_length}={value}).")
    return bs
