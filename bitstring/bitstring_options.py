from __future__ import annotations

import bitstring
import os

ConstBitStore = bitstring.bitstore.ConstBitStore
MutableBitStore = bitstring.bitstore.MutableBitStore

class Options:
    """Internal class to create singleton module options instance."""

    _instance = None

    def __init__(self):
        self.set_lsb0(False)
        self._bytealigned = False
        self.mxfp_overflow = 'saturate'

        self.no_color = False
        no_color = os.getenv('NO_COLOR')
        self.no_color = True if no_color else False

    def using_rust_core(self):
        x = ConstBitStore()
        return x.using_rust_core()

    @property
    def mxfp_overflow(self) -> str:
        return self._mxfp_overflow

    @mxfp_overflow.setter
    def mxfp_overflow(self, value: str) -> None:
        allowed_values = ('saturate', 'overflow')
        if value not in allowed_values:
            raise ValueError(f"mxfp_overflow must be one of {allowed_values}, not {value}.")
        self._mxfp_overflow = value

    def __repr__(self) -> str:
        attributes = {attr: getattr(self, attr) for attr in dir(self) if not attr.startswith('_') and not callable(getattr(self, attr))}
        return '\n'.join(f"{attr}: {value!r}" for attr, value in attributes.items())

    @property
    def lsb0(self) -> bool:
        return self._lsb0

    @lsb0.setter
    def lsb0(self, value: bool) -> None:
        self.set_lsb0(value)

    def set_lsb0(self, value: bool) -> None:
        self._lsb0 = bool(value)
        Bits = bitstring.bits.Bits
        BitArray = bitstring.bitarray_.BitArray

        lsb0_methods = {
            Bits: {'_find': Bits._find_lsb0, '_rfind': Bits._rfind_lsb0, '_findall': Bits._findall_lsb0},
            BitArray: {'_ror': BitArray._rol_msb0, '_rol': BitArray._ror_msb0, '_append': BitArray._append_lsb0,
                       '_prepend': BitArray._append_msb0},
            ConstBitStore: {'__setitem__': None, '__delitem__': None, 'invert': None,
                            'getindex': ConstBitStore.getindex_lsb0, 'getslice': ConstBitStore.getslice_lsb0,
                       'getslice_withstep': ConstBitStore.getslice_withstep_lsb0},
            MutableBitStore: {'__setitem__': MutableBitStore.setitem_lsb0, '__delitem__': MutableBitStore.delitem_lsb0,
                       'getindex': MutableBitStore.getindex_lsb0, 'getslice': MutableBitStore.getslice_lsb0,
                       'getslice_withstep': MutableBitStore.getslice_withstep_lsb0, 'invert': MutableBitStore.invert_lsb0}
        }
        msb0_methods = {
            Bits: {'_find': Bits._find_msb0, '_rfind': Bits._rfind_msb0, '_findall': Bits._findall_msb0},
            BitArray: {'_ror': BitArray._ror_msb0, '_rol': BitArray._rol_msb0, '_append': BitArray._append_msb0,
                       '_prepend': BitArray._append_lsb0},
            ConstBitStore: {'__setitem__': None, '__delitem__': None, 'invert': None,
                            'getindex': ConstBitStore.getindex_msb0, 'getslice': ConstBitStore.getslice_msb0,
                       'getslice_withstep': ConstBitStore.getslice_withstep_msb0},
            MutableBitStore: {'__setitem__': MutableBitStore.setitem_msb0, '__delitem__': MutableBitStore.delitem_msb0,
                       'getindex': MutableBitStore.getindex_msb0, 'getslice': MutableBitStore.getslice_msb0,
                       'getslice_withstep': MutableBitStore.getslice_withstep_msb0, 'invert': MutableBitStore.invert_msb0}
        }
        methods = lsb0_methods if self._lsb0 else msb0_methods
        for cls, method_dict in methods.items():
            for attr, method in method_dict.items():
                setattr(cls, attr, method)

    @property
    def bytealigned(self) -> bool:
        return self._bytealigned

    @bytealigned.setter
    def bytealigned(self, value: bool) -> None:
        self._bytealigned = bool(value)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Options, cls).__new__(cls)
        return cls._instance


class Colour:
    def __new__(cls, use_colour: bool) -> Colour:
        x = super().__new__(cls)
        if use_colour:
            cls.blue = '\033[34m'
            cls.purple = '\033[35m'
            cls.green = '\033[32m'
            cls.off = '\033[0m'
        else:
            cls.blue = cls.purple = cls.green = cls.off = ''
        return x
