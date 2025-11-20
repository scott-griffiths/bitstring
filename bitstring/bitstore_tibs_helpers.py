from __future__ import annotations

from typing import Union
# from bitformat import MutableBits, Endianness, DtypeSingle, DtypeKind
from tibs import Tibs, Mutibs
import bitstring

MutableBitStore = bitstring.bitstore.MutableBitStore
ConstBitStore = bitstring.bitstore.ConstBitStore

from bitstring.helpers import tidy_input_string


def bin2bitstore(binstring: str) -> ConstBitStore:
    binstring = tidy_input_string(binstring)
    binstring = binstring.replace('0b', '')
    mb = Mutibs.from_bin(binstring)
    return ConstBitStore._from_mutablebits(mb)


def hex2bitstore(hexstring: str) -> ConstBitStore:
    hexstring = tidy_input_string(hexstring)
    hexstring = hexstring.replace('0x', '')
    mb = Mutibs.from_hex(hexstring)
    return ConstBitStore._from_mutablebits(mb)


def oct2bitstore(octstring: str) -> ConstBitStore:
    octstring = tidy_input_string(octstring)
    octstring = octstring.replace('0o', '')
    mb = Mutibs.from_oct(octstring)
    return ConstBitStore._from_mutablebits(mb)


def int2bitstore(i: int, length: int, signed: bool) -> ConstBitStore:
    i = int(i)
    if length <= 128:
        if signed:
            mb = Mutibs.from_i(i, length=length)
        else:
            mb = Mutibs.from_u(i, length=length)
    else:
        b = i.to_bytes((length + 7) // 8, byteorder="big", signed=signed)
        offset = 8 - (length % 8)
        mb = Tibs.from_bytes(b)
        if offset != 8:
            mb = mb[offset:]
    return ConstBitStore._from_mutablebits(mb)


def intle2bitstore(i: int, length: int, signed: bool) -> ConstBitStore:
    i = int(i)
    if length <= 128:
        if signed:
            mb = Mutibs.from_i(i, length=length)
        else:
            mb = Mutibs.from_u(i, length=length)
    else:
        b = i.to_bytes((length + 7) // 8, byteorder="big", signed=signed)
        offset = 8 - (length % 8)
        mb = Mutibs.from_bytes(b)
        if offset != 8:
            mb = mb[offset:]
    mb.byte_swap()
    return ConstBitStore._from_mutablebits(mb)


def float2bitstore(f: Union[str, float], length: int, big_endian: bool) -> ConstBitStore:
    f = float(f)
    mb = Mutibs.from_f(f, length)
    if not big_endian:
        mb.byte_swap()
    return ConstBitStore._from_mutablebits(mb)
