from __future__ import annotations

from typing import Union
from bitformat import MutableBits, Endianness, DtypeSingle, DtypeKind
import bitstring

MutableBitStore = bitstring.bitstore.MutableBitStore
ConstBitStore = bitstring.bitstore.ConstBitStore

from bitstring.helpers import tidy_input_string

bin_dtype = DtypeSingle.from_params(DtypeKind.BIN)
oct_dtype = DtypeSingle.from_params(DtypeKind.OCT)
hex_dtype = DtypeSingle.from_params(DtypeKind.HEX)

def bin2bitstore(binstring: str) -> ConstBitStore:
    binstring = tidy_input_string(binstring)
    binstring = binstring.replace('0b', '')
    mb = MutableBits.from_dtype(bin_dtype, binstring)
    return ConstBitStore._from_mutablebits(mb)


def hex2bitstore(hexstring: str) -> ConstBitStore:
    hexstring = tidy_input_string(hexstring)
    hexstring = hexstring.replace('0x', '')
    mb = MutableBits.from_dtype(hex_dtype, hexstring)
    return ConstBitStore._from_mutablebits(mb)


def oct2bitstore(octstring: str) -> ConstBitStore:
    octstring = tidy_input_string(octstring)
    octstring = octstring.replace('0o', '')
    mb = MutableBits.from_dtype(oct_dtype, octstring)
    return ConstBitStore._from_mutablebits(mb)


def int2bitstore(i: int, length: int, signed: bool) -> ConstBitStore:
    dtype = DtypeSingle.from_params(DtypeKind.INT if signed else DtypeKind.UINT, length)
    mb = MutableBits.from_dtype(dtype, i)
    return ConstBitStore._from_mutablebits(mb)


def intle2bitstore(i: int, length: int, signed: bool) -> ConstBitStore:
    dtype = DtypeSingle.from_params(DtypeKind.INT if signed else DtypeKind.UINT, length, Endianness.LITTLE)
    mb = MutableBits.from_dtype(dtype, i)
    return ConstBitStore._from_mutablebits(mb)


def float2bitstore(f: Union[str, float], length: int, big_endian: bool) -> ConstBitStore:
    dtype = DtypeSingle.from_params(DtypeKind.FLOAT, length, Endianness.BIG if big_endian else Endianness.LITTLE)
    mb = MutableBits.from_dtype(dtype, f)
    return ConstBitStore._from_mutablebits(mb)
