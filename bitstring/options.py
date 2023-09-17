from __future__ import annotations

from bitstring.bits import Bits
from bitstring.bitarray import BitArray
from bitstring.bitstore import BitStore


class Options:
    """Internal class to create singleton module options instance."""

    _instance = None

    def __init__(self):
        self.set_lsb0(False)
        self._bytealigned = False

    @property
    def lsb0(self) -> bool:
        return self._lsb0

    @lsb0.setter
    def lsb0(self, value: bool) -> None:
        self.set_lsb0(value)

    def set_lsb0(self, value: bool) -> None:
        self._lsb0 = bool(value)

        if self._lsb0:
            Bits._find = Bits._find_lsb0  # type: ignore
            Bits._rfind = Bits._rfind_lsb0  # type: ignore
            Bits._findall = Bits._findall_lsb0  # type: ignore

            BitArray._ror = BitArray._rol_msb0  # type: ignore
            BitArray._rol = BitArray._ror_msb0  # type: ignore
            BitArray._append = BitArray._append_lsb0  # type: ignore
            # An LSB0 prepend is an MSB0 append
            BitArray._prepend = BitArray._append_msb0  # type: ignore

            BitStore.__setitem__ = BitStore.setitem_lsb0  # type: ignore
            BitStore.__delitem__ = BitStore.delitem_lsb0  # type: ignore
            BitStore.getindex = BitStore.getindex_lsb0
            BitStore.getslice = BitStore.getslice_lsb0
            BitStore.invert = BitStore.invert_lsb0  # type: ignore
        else:
            Bits._find = Bits._find_msb0  # type: ignore
            Bits._rfind = Bits._rfind_msb0  # type: ignore
            Bits._findall = Bits._findall_msb0  # type: ignore

            BitArray._ror = BitArray._ror_msb0  # type: ignore
            BitArray._rol = BitArray._rol_msb0  # type: ignore
            BitArray._append = BitArray._append_msb0  # type: ignore
            BitArray._prepend = BitArray._append_lsb0  # type: ignore

            BitStore.__setitem__ = BitStore.setitem_msb0  # type: ignore
            BitStore.__delitem__ = BitStore.delitem_msb0  # type: ignore
            BitStore.getindex = BitStore.getindex_msb0
            BitStore.getslice = BitStore.getslice_msb0
            BitStore.invert = BitStore.invert_msb0  # type: ignore

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

