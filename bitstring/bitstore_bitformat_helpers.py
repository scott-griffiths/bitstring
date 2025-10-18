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
