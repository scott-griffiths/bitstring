from __future__ import annotations

import struct
import math
import functools
from typing import Union, Optional, Dict, Callable
import bitarray
import bitstring
from bitstring.fp8 import p4binary_fmt, p3binary_fmt
from bitstring.mxfp import (e3m2mxfp_fmt, e2m3mxfp_fmt, e2m1mxfp_fmt, e4m3mxfp_saturate_fmt,
                            e5m2mxfp_saturate_fmt, e4m3mxfp_overflow_fmt, e5m2mxfp_overflow_fmt)
from bitstring.helpers import tidy_input_string

BitStore = bitstring.bitstore.BitStore


def bin2bitstore(binstring: str) -> BitStore:
    binstring = tidy_input_string(binstring)
    binstring = binstring.replace('0b', '')
    try:
        return BitStore.from_binary_string(binstring)
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


def int2bitstore(i: int, length: int, signed: bool) -> BitStore:
    i = int(i)
    try:
        x = BitStore(bitarray.util.int2ba(i, length=length, endian='big', signed=signed))
    except OverflowError as e:
        if signed:
            if i >= (1 << (length - 1)) or i < -(1 << (length - 1)):
                raise bitstring.CreationError(f"{i} is too large a signed integer for a bitstring of length {length}. "
                                    f"The allowed range is [{-(1 << (length - 1))}, {(1 << (length - 1)) - 1}].")
        else:
            if i >= (1 << length):
                raise bitstring.CreationError(f"{i} is too large an unsigned integer for a bitstring of length {length}. "
                                    f"The allowed range is [0, {(1 << length) - 1}].")
            if i < 0:
                raise bitstring.CreationError("uint cannot be initialised with a negative number.")
        raise e
    return x


def intle2bitstore(i: int, length: int, signed: bool) -> BitStore:
    x = int2bitstore(i, length, signed).tobytes()
    return BitStore.frombytes(x[::-1])


def float2bitstore(f: Union[str, float], length: int, big_endian: bool) -> BitStore:
    f = float(f)
    fmt = {16: '>e', 32: '>f', 64: '>d'}[length] if big_endian else {16: '<e', 32: '<f', 64: '<d'}[length]
    try:
        b = struct.pack(fmt, f)
    except OverflowError:
        # If float64 doesn't fit it automatically goes to 'inf'. This reproduces that behaviour for other types.
        b = struct.pack(fmt, float('inf') if f > 0 else float('-inf'))
    return BitStore.frombytes(b)

