#!/usr/bin/env python
import pytest
import io
import sys
import bitstring
import array
import os
import re
from bitstring import InterpretError, Bits, BitArray
from tibs import Mutibs, Tibs
from hypothesis import given
import hypothesis.strategies as st

sys.path.insert(0, "..")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def remove_unprintable(s: str) -> str:
    colour_escape = re.compile(r"(?:\x1B[@-_])[0-?]*[ -/]*[@-~]")
    return colour_escape.sub("", s)



class TestCreation:
    def test_explicit_factory_methods(self, tmp_path):
        assert Bits.from_string("0xf, u4=1") == "0xf1"
        assert Bits.from_dtype("u8", 12) == "0x0c"
        assert Bits.from_bytes(b"\xf0", offset=1, length=3) == "0b111"
        assert Bits.from_bools([True, 0, "x"]) == "0b101"
        assert Bits.from_zeros(5) == "0b00000"
        assert Bits.from_ones(5) == "0b11111"
        assert Bits.from_joined(["0xa", "0xb"]) == "0xab"
        assert Bits.from_joined([]) == Bits()

        filename = tmp_path / "factory.bin"
        filename.write_bytes(b"\x12\x34")
        file_bits = Bits.from_file(filename)
        assert file_bits == "0x1234"
        assert eval(repr(file_bits)) == file_bits
        with filename.open("rb") as f:
            assert Bits.from_file(f, offset=4, length=8) == "0x23"

    def test_to_bitarray(self):
        bits = Bits("0b101")
        bitarray = bits.to_bitarray()
        assert type(bitarray) is BitArray
        assert bitarray == bits
        bitarray.append("0b1")
        assert bits == "0b101"
        assert bitarray == "0b1011"

    @pytest.mark.parametrize("cls", [Bits, BitArray])
    @pytest.mark.parametrize("attribute", ["len", "length"])
    def test_length_properties_removed(self, cls, attribute):
        bits = cls("0b101")
        assert len(bits) == 3
        with pytest.raises(AttributeError):
            getattr(bits, attribute)

    def test_tibs_conversion(self):
        tibs = Tibs.from_bin("101")
        bits = Bits.from_tibs(tibs)
        assert type(bits) is Bits
        assert bits == "0b101"
        assert bits.to_tibs() is tibs
        assert Bits("0b101").to_tibs() == tibs

        mutibs = Mutibs.from_bin("101")
        bits = Bits.from_tibs(mutibs)
        assert type(bits) is Bits
        assert bits == "0b101"
        mutibs.append(0)
        assert bits == "0b101"

    @pytest.mark.parametrize("tibs_type", [Tibs, Mutibs])
    def test_constructor_accepts_tibs_types(self, tibs_type):
        tibs = tibs_type.from_bin("101")
        bits = Bits(tibs)
        assert type(bits) is Bits
        assert bits == "0b101"
        if tibs_type is Tibs:
            assert bits.to_tibs() is tibs

    @pytest.mark.parametrize("tibs_type", [Tibs, Mutibs])
    def test_constructor_rejects_tibs_types_with_length_or_offset(self, tibs_type):
        tibs = tibs_type.from_bin("101")
        with pytest.raises(bitstring.CreationError, match="explicit length"):
            Bits(tibs, length=2)
        with pytest.raises(bitstring.CreationError, match="offset"):
            Bits(tibs, offset=1)

    def test_mutibs_input_is_copied(self):
        source = Mutibs.from_bin("101")
        constructed = Bits(source)
        from_tibs = Bits.from_tibs(source)

        source.append(0)

        assert constructed == "0b101"
        assert from_tibs == "0b101"

    def test_tibs_types_promote_as_bits_type(self):
        tibs = Tibs.from_bin("101")
        mutibs = Mutibs.from_bin("101")
        bits = Bits("0b00101")

        assert bits.find(tibs) == 2
        assert bits.endswith(mutibs)
        assert Bits("0b10100").startswith(tibs)
        assert Bits.from_joined([Tibs.from_bin("10"), mutibs]) == "0b10101"
        assert bitstring.pack("bits3", tibs) == "0b101"
        assert bitstring.pack("bits3", mutibs) == "0b101"

    def test_to_bytes_and_to_file_aliases(self, tmp_path):
        bits = Bits("0b101")
        assert bits.to_bytes() == b"\xa0"
        assert bits.tobytes() == b"\xa0"
        assert bytes(bits) == b"\xa0"

        filename = tmp_path / "bits.bin"
        with filename.open("wb") as f:
            bits.to_file(f)
        assert filename.read_bytes() == b"\xa0"

        filename = tmp_path / "bits_alias.bin"
        with filename.open("wb") as f:
            bits.tofile(f)
        assert filename.read_bytes() == b"\xa0"

    @pytest.mark.parametrize("cls", [Bits, BitArray])
    def test_positional_integer_constructor_removed(self, cls):
        with pytest.raises(TypeError, match="from_zeros"):
            cls(5)

    @pytest.mark.parametrize("cls", [Bits, BitArray])
    def test_filename_keyword_removed(self, cls, tmp_path):
        filename = tmp_path / "source.bin"
        filename.write_bytes(b"\xff")
        with pytest.raises(bitstring.CreationError, match="from_file"):
            cls(filename=filename)

    @pytest.mark.parametrize("cls", [Bits, BitArray])
    def test_bytes_keyword_removed(self, cls):
        with pytest.raises(bitstring.CreationError, match="from_bytes"):
            cls(bytes=b"\xff")

    @pytest.mark.parametrize("cls", [Bits, BitArray])
    def test_ambiguous_constructor_sources_removed(self, cls, tmp_path):
        with pytest.raises(TypeError, match="from_bools"):
            cls([1, 0, 1])
        with pytest.raises(TypeError, match="from_bytes"):
            cls(io.BytesIO(b"\xff"))
        with pytest.raises(TypeError, match="from_bytes"):
            cls(array.array("B", [0xff]))

        filename = tmp_path / "source.bin"
        filename.write_bytes(b"\xff")
        with filename.open("rb") as f:
            with pytest.raises(TypeError, match="from_file"):
                cls(f)

    @pytest.mark.parametrize("cls", [Bits, BitArray])
    def test_fromstring_compatibility_alias(self, cls):
        s = cls.fromstring("u4=15, 0b01")
        assert type(s) is cls
        assert s == cls.from_string("u4=15, 0b01")

    def test_creation_from_bytes(self):
        s = Bits.from_bytes(b"\xa0\xff")
        assert (len(s), s.hex) == (16, "a0ff")
        s = Bits.from_bytes(b"abc", length=0)
        assert s == ""

    @given(st.binary())
    def test_creation_from_bytes_roundtrip(self, data):
        s = Bits.from_bytes(data)
        assert s.bytes == data

    def test_creation_from_bytes_errors(self):
        with pytest.raises(bitstring.CreationError):
            Bits.from_bytes(b"abc", length=25)

    def test_creation_from_data_with_offset(self):
        s1 = Bits.from_bytes(b"\x0b\x1c\x2f", offset=0, length=20)
        s2 = Bits.from_bytes(b"\xa0\xb1\xc2", offset=4)
        assert (len(s2), s2.hex) == (20, "0b1c2")
        assert (len(s1), s1.hex) == (20, "0b1c2")
        assert s1 == s2

    def test_creation_from_hex(self):
        s = Bits(hex="0xA0ff")
        assert (len(s), s.hex) == (16, "a0ff")
        s = Bits(hex="0x0x0X")
        assert (len(s), s.hex) == (0, "")

    def test_creation_from_hex_with_whitespace(self):
        s = Bits(hex="  \n0 X a  4e       \r3  \n")
        assert s.hex == "a4e3"

    @pytest.mark.parametrize("bad_val", ["0xx0", "0xX0", "0Xx0", "-2e"])
    def test_creation_from_hex_errors(self, bad_val: str):
        with pytest.raises(bitstring.CreationError):
            Bits(hex=bad_val)
        with pytest.raises(bitstring.CreationError):
            Bits("0x2", length=2)
        with pytest.raises(bitstring.CreationError):
            Bits("0x3", offset=1)

    def test_creation_from_bin(self):
        s = Bits(bin="1010000011111111")
        assert (len(s), s.hex) == (16, "a0ff")
        s = Bits(bin="00")[:1]
        assert s.bin == "0"
        s = Bits(bin=" 0000 \n 0001\r ")
        assert s.bin == "00000001"

    def test_creation_from_bin_with_whitespace(self):
        s = Bits(bin="  \r\r\n0   B    00   1 1 \t0 ")
        assert s.bin == "00110"

    def test_creation_from_oct_errors(self):
        s = Bits("0b00011")
        with pytest.raises(bitstring.InterpretError):
            _ = s.oct
        with pytest.raises(bitstring.CreationError):
            _ = Bits("oct=8")

    def test_offset_constructor_keyword_removed(self):
        with pytest.raises(bitstring.CreationError, match="offset"):
            Bits(u=12, length=8, offset=1)

    def test_long_numeric_keyword_initialisers_are_compatibility_aliases(self):
        assert Bits(uint=4, length=10) == Bits(u=4, length=10)
        assert Bits(int=-2, length=10) == Bits(i=-2, length=10)
        assert Bits(float=1.5, length=16) == Bits(f=1.5, length=16)
        assert BitArray(uint=4, length=10) == BitArray(u=4, length=10)
        assert BitArray(int=-2, length=10) == BitArray(i=-2, length=10)
        assert BitArray(float=1.5, length=16) == BitArray(f=1.5, length=16)

    def test_creation_from_u_errors(self):
        with pytest.raises(bitstring.CreationError):
            Bits(u=-1, length=10)
        with pytest.raises(bitstring.CreationError):
            Bits(u=12)
        with pytest.raises(bitstring.CreationError):
            Bits(u=4, length=2)
        with pytest.raises(bitstring.CreationError):
            Bits(u=0, length=0)
        with pytest.raises(bitstring.CreationError):
            Bits(u=12, length=-12)

    def test_creation_from_i(self):
        s = Bits(i=0, length=4)
        assert s.bin == "0000"
        s = Bits(i=1, length=2)
        assert s.bin == "01"
        s = Bits(i=-1, length=11)
        assert s.bin == "11111111111"
        s = Bits(i=12, length=7)
        assert s.int == 12
        s = Bits(i=-243, length=108)
        assert (s.int, len(s)) == (-243, 108)
        for length in range(6, 10):
            for value in range(-17, 17):
                s = Bits(i=value, length=length)
                assert (s.int, len(s)) == (value, length)
        _ = Bits(i=10, length=8)

    @pytest.mark.parametrize("value, length", [[-1, 0], [12, None], [4, 3], [-5, 3]])
    def test_creation_from_i_errors(self, value, length):
        with pytest.raises(bitstring.CreationError):
            _ = Bits(i=value, length=length)

    def test_creation_from_se(self):
        for i in range(-100, 10):
            s = Bits(se=i)
            assert s.se == i
        with pytest.raises(bitstring.CreationError):
            _ = Bits(se=10, length=40)

    def test_creation_from_se_with_offset(self):
        with pytest.raises(bitstring.CreationError, match="offset"):
            Bits(se=-13, offset=1)

    def test_creation_from_se_errors(self):
        with pytest.raises(bitstring.CreationError):
            Bits(se=-5, length=33)
        with pytest.raises(bitstring.CreationError):
            Bits("se2=0")
        s = Bits(bin="001000")
        with pytest.raises(bitstring.InterpretError):
            _ = s.se

    def test_creation_from_ue(self):
        for i in range(0, 20):
            assert Bits(ue=i).ue == i

    def test_creation_from_ue_with_offset(self):
        with pytest.raises(bitstring.CreationError, match="offset"):
            Bits(ue=104, offset=2)

    def test_creation_from_ue_errors(self):
        with pytest.raises(bitstring.CreationError):
            Bits(ue=-1)
        with pytest.raises(bitstring.CreationError):
            Bits(ue=1, length=12)
        s = Bits(bin="10")
        with pytest.raises(bitstring.InterpretError):
            _ = s.ue

    def test_creation_from_bool(self):
        a = Bits("bool=1")
        assert a == "bool=1"
        b = Bits("bool:1=0")
        assert b == [0]
        c = bitstring.pack("bool=1, 2*bool", 0, 1)
        assert c == "0b101"
        d = bitstring.pack("bool:1=1, 2*bool1", 1, 0)
        assert d == "0b110"

    def test_creation_from_bool_errors(self):
        with pytest.raises(ValueError):
            _ = Bits("bool=3")
        with pytest.raises(bitstring.CreationError):
            _ = Bits(bool=0, length=2)

    def test_creation_keyword_error(self):
        with pytest.raises(bitstring.CreationError):
            Bits(squirrel=5)

    def test_creation_from_memoryview(self):
        x = bytes(bytearray(range(20)))
        m = memoryview(x[10:15])
        b = Bits(m)
        assert b.unpack("5*u8") == [10, 11, 12, 13, 14]


class TestInitialisation:
    def test_empty_init(self):
        a = Bits()
        assert a == ""

    def test_no_pos(self):
        a = Bits("0xabcdef")
        with pytest.raises(AttributeError):
            _ = a.pos

    def test_find(self):
        a = Bits("0xabcd")
        assert a.find("0xab") == 0
        assert "0xab" in a
        r = a.find("0xbc")
        assert r == 4
        r = a.find("0x23462346246", bytealigned=True)
        assert r is None

    def test_rfind(self):
        a = Bits("0b11101010010010")
        b = a.rfind("0b010")
        assert b == 11
        assert a.rfind("0b111") == 0

    def test_find_all(self):
        a = Bits("0b0010011")
        b = list(a.findall([1]))
        assert b == [2, 5, 6]
        t = BitArray("0b10")
        tp = list(t.findall("0b1"))
        assert tp == [0]

    @pytest.mark.parametrize(
        "call",
        [
            lambda s: s.find("0b1", 0),
            lambda s: s.rfind("0b1", 0),
            lambda s: s.findall("0b1", 0),
            lambda s: s.cut(1, 0),
            lambda s: s.split("0b1", 0),
            lambda s: s.startswith("0b1", 0),
            lambda s: s.endswith("0b1", 0),
            lambda s: s.replace("0b1", "0b0", 0),
            lambda s: s.reverse(0, 2),
            lambda s: s.rol(1, 0, 2),
            lambda s: s.ror(1, 0, 2),
        ],
    )
    def test_optional_range_arguments_are_keyword_only(self, call):
        with pytest.raises(TypeError):
            call(BitArray("0b1010"))


class TestCut:
    def test_cut(self):
        s = Bits("0b000111" * 10)
        for t in s.cut(6):
            assert t.bin == "000111"


class TestInterleavedExpGolomb:
    def test_creation(self):
        s1 = Bits(uie=0)
        s2 = Bits(uie=1)
        assert s1 == [1]
        assert s2 == [0, 0, 1]
        s1 = Bits(sie=0)
        s2 = Bits(sie=-1)
        s3 = Bits(sie=1)
        assert s1 == [1]
        assert s2 == [0, 0, 1, 1]
        assert s3 == [0, 0, 1, 0]

    def test_creation_from_property(self):
        s = BitArray()
        s.uie = 45
        assert s.uie == 45
        s.sie = -45
        assert s.sie == -45

    def test_interpretation(self):
        for x in range(101):
            assert Bits(uie=x).uie == x
        for x in range(-100, 100):
            assert Bits(sie=x).sie == x

    def test_errors(self):
        for f in ["sie=100, 0b1001", "0b00", "uie=100, 0b1001"]:
            s = Bits.from_string(f)
            with pytest.raises(bitstring.InterpretError):
                _ = s.sie
            with pytest.raises(bitstring.InterpretError):
                _ = s.uie
        with pytest.raises(ValueError):
            Bits(uie=-10)


class TestFileBased:
    def setup_method(self):
        filename = os.path.join(THIS_DIR, "smalltestfile")
        self.a = Bits.from_file(filename)
        self.b = Bits.from_file(filename, offset=16)
        self.c = Bits.from_file(filename, offset=20, length=16)
        self.d = Bits.from_file(filename, offset=20, length=4)

    def test_creation_with_offset(self):
        assert str(self.a) == "0x0123456789abcdef"
        assert str(self.b) == "0x456789abcdef"
        assert str(self.c) == "0x5678"

    def test_bit_operators(self):
        x = self.b[4:20]
        assert x == "0x5678"
        assert (x & self.c).hex == self.c.hex
        assert self.c ^ self.b[4:20] == Bits.from_zeros(16)
        assert self.a[23:36] | self.c[3:] == self.c[3:]
        y = x & self.b[4:20]
        assert y == self.c
        assert repr(y) == repr(self.c)

    def test_addition(self):
        _ = self.d + "0x1"
        x = self.a[20:24] + self.c[-4:] + self.c[8:12]
        assert x == "0x587"
        x = self.b + x
        assert x.hex == "456789abcdef587"
        x = BitArray(x)
        del x[12:24]
        assert x == "0x456abcdef587"


class TestComparisons:
    def test_unorderable(self):
        a = Bits.from_zeros(5)
        b = Bits.from_zeros(5)
        with pytest.raises(TypeError):
            _ = a < b
        with pytest.raises(TypeError):
            _ = a > b
        with pytest.raises(TypeError):
            _ = a <= b
        with pytest.raises(TypeError):
            _ = a >= b


class TestSubclassing:
    def test_is_instance(self):
        class SubBits(bitstring.Bits):
            pass

        a = SubBits()
        assert isinstance(a, SubBits)

    def test_class_type(self):
        class SubBits(bitstring.Bits):
            pass

        assert SubBits().__class__ == SubBits


class TestLongBoolConversion:
    def test_long_bool(self):
        a = Bits.from_zeros(1000)
        b = bool(a)
        assert b is True


class TestPadToken:
    def test_creation(self):
        a = Bits.from_string("pad:10")
        assert a == Bits.from_zeros(10)
        b = Bits("pad:0")
        assert b == Bits()
        c = Bits("0b11, pad:1, 0b111")
        assert c == Bits("0b110111")

    def test_pack(self):
        s = bitstring.pack("0b11, pad:3, 0b1")
        assert s.bin == "110001"
        d = bitstring.pack("pad:c", c=12)
        assert d == Bits.from_zeros(12)
        e = bitstring.pack("0xf, uint12, pad:1, bin, pad4, 0b10", 0, "111")
        assert e.bin == "11110000000000000111000010"

    def test_unpack(self):
        s = Bits("0b111000111")
        x, y = s.unpack("3, pad:3, 3")
        assert (x, y.u) == ("0b111", 7)
        x, y = s.unpack("2, pad2, bin")
        assert (x.u2, y) == (3, "00111")
        x = s.unpack("pad:1, pad:2, pad:3")
        assert x == []

    def test_unpack_bug(self):
        t = Bits("0o755, ue=12, i3=-1")
        a, b = t.unpack("pad:9, ue, i3")
        assert (a, b) == (12, -1)


class TestModifiedByAddingBug:
    def test_adding(self):
        a = Bits("0b0")
        b = Bits("0b11")
        c = a + b
        assert c == "0b011"
        assert a == "0b0"
        assert b == "0b11"

    def test_adding2(self):
        a = Bits.from_zeros(100)
        b = Bits.from_zeros(101)
        c = a + b
        assert a == Bits.from_zeros(100)
        assert b == Bits.from_zeros(101)
        assert c == Bits.from_zeros(201)


class TestWrongTypeBug:
    def test_append_to_bits(self):
        a = Bits(BitArray())
        with pytest.raises(AttributeError):
            a.append("0b1")
        assert type(a) == Bits
        b = Bits(BitArray())
        assert type(b) == Bits


class TestInitFromArray:
    @given(st.sampled_from(["B", "H", "I", "L", "Q", "f", "d"]))
    def test_empty_array(self, t):
        a = array.array(t)
        b = Bits.from_bytes(a.tobytes())
        assert len(b) == 0

    def test_single_byte(self):
        a = array.array("B", b"\xff")
        b = Bits.from_bytes(a.tobytes())
        assert len(b) == 8
        assert b.hex == "ff"

    def test_signed_short(self):
        a = array.array("h")
        a.append(10)
        a.append(-1)
        b = Bits.from_bytes(a.tobytes())
        assert len(b) == 32
        assert b.bytes == a.tobytes()

    def test_double(self):
        a = array.array("d", [0.0, 1.0, 2.5])
        b = Bits.from_bytes(a.tobytes())
        assert len(b) == 192
        native_f64 = "fle:64" if sys.byteorder == "little" else "f:64"
        c, d, e = b.unpack(f"3*{native_f64}")
        assert (c, d, e) == (0.0, 1.0, 2.5)


class TestIteration:
    def test_iterate_empty_bits(self):
        assert list(Bits.from_bools([])) == []
        assert list(Bits.from_bools([1, 0])[1:1]) == []

    def test_iterate_non_empty_bits(self):
        assert list(Bits.from_bools([1, 0])) == [True, False]
        assert list(Bits.from_bools([1, 0, 0, 1])[1:3]) == [False, False]

    def test_iterate_long_bits(self):
        assert list(Bits.from_bools([1, 0]) * 1024) == [True, False] * 1024


class TestContainsBug:
    def test_contains(self):
        a = Bits("0b1, 0x0001dead0001")
        assert "0xdead" in a
        assert "0xfeed" not in a

        assert "0b1" in Bits("0xf")
        assert "0b0" not in Bits("0xf")


class TestByteStoreImmutablity:
    def test_immutability_bug_append(self):
        a = Bits("0b111")
        b = a + "0b000"
        c = BitArray(b)
        c[1] = 0
        assert c.bin == "101000"
        assert a.bin3 == "111"
        assert b.bin == "111000"

    def test_immutability_bug_prepend(self):
        a = Bits("0b111")
        b = "0b000" + a
        c = BitArray(b)
        c[1] = 1
        assert b.bin == "000111"
        assert c.bin == "010111"


class TestUnderscoresInLiterals:
    def test_hex_creation(self):
        a = Bits(hex="ab_cd__ef")
        assert a.hex == "abcdef"
        b = Bits("0x0102_0304")
        assert b.uint == 0x0102_0304

    def test_binary_creation(self):
        a = Bits(bin="0000_0001_0010")
        assert a.bin == "000000010010"
        b = Bits.from_string("0b0011_1100_1111_0000")
        assert b.bin == "0011110011110000"
        v = 0b1010_0000
        c = Bits(u=0b1010_0000, length=8)
        assert c.uint == v

    def test_octal_creation(self):
        a = Bits(oct="0011_2233_4455_6677")
        assert a.uint == 0o001122334455_6677
        b = Bits("0o123_321_123_321")
        assert b.uint == 0o123_321_123321


class TestPrettyPrinting:
    def test_simplest_cases(self):
        a = Bits("0b101011110000")
        s = io.StringIO()
        a.pp(stream=s)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='bin', length=12 bits> [
 0: 10101111 0000    
]
"""
        )

        s = io.StringIO()
        a.pp("hex", stream=s)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='hex', length=12 bits> [
 0: af 0 
]
"""
        )

        s = io.StringIO()
        a.pp("oct", stream=s)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='oct', length=12 bits> [
 0: 5360
]
"""
        )

    def test_small_width(self):
        a = Bits.from_zeros(20)
        s = io.StringIO()
        a.pp(fmt="bin", stream=s, width=5)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='bin', length=20 bits> [
 0: 00000000
 8: 00000000
16: 0000    
]
"""
        )

    def test_separator(self):
        a = Bits("0x0f0f") * 9
        s = io.StringIO()
        a.pp("hex:32", sep="!-!", stream=s)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='hex32', length=144 bits> [
  0: 0f0f0f0f!-!0f0f0f0f!-!0f0f0f0f!-!0f0f0f0f
] + trailing_bits = 0x0f0f
"""
        )

    def test_multi_line(self):
        a = Bits.from_zeros(100)
        s = io.StringIO()
        a.pp("bin", sep="", stream=s, width=80)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='bin', length=100 bits> [
  0: 000000000000000000000000000000000000000000000000000000000000000000000000
 72: 0000000000000000000000000000                                            
]
"""
        )

    def test_multiformat(self):
        a = Bits("0b1111000011110000")
        s = io.StringIO()
        a.pp(stream=s, fmt="bin, hex")
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='bin, hex', length=16 bits> [
 0: 11110000 11110000 : f0 f0
]
"""
        )
        s = io.StringIO()
        a.pp(stream=s, fmt="hex, bin:12")
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='hex, bin12', length=16 bits> [
 0: f0f : 111100001111
] + trailing_bits = 0x0
"""
        )

    def test_multi_line_multi_format(self):
        a = Bits(i=-1, length=112)
        s = io.StringIO()
        a.pp(stream=s, fmt="bin:8, hex:8", width=42)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='bin8, hex8', length=112 bits> [
  0: 11111111 11111111 11111111 : ff ff ff
 24: 11111111 11111111 11111111 : ff ff ff
 48: 11111111 11111111 11111111 : ff ff ff
 72: 11111111 11111111 11111111 : ff ff ff
 96: 11111111 11111111          : ff ff   
]
"""
        )
        s = io.StringIO()
        a.pp(stream=s, fmt="bin, hex", width=41)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='bin, hex', length=112 bits> [
  0: 11111111 11111111 : ff ff
 16: 11111111 11111111 : ff ff
 32: 11111111 11111111 : ff ff
 48: 11111111 11111111 : ff ff
 64: 11111111 11111111 : ff ff
 80: 11111111 11111111 : ff ff
 96: 11111111 11111111 : ff ff
]
"""
        )

        a = bytearray(range(0, 256))
        b = Bits.from_bytes(a)
        s = io.StringIO()
        b.pp(stream=s, fmt="bytes")
        assert (
            remove_unprintable(s.getvalue())
            == r"""<Bits, fmt='bytes', length=2048 bits> [
   0: ĀāĂă ĄąĆć ĈĉĊċ ČčĎď ĐđĒē ĔĕĖė ĘęĚě ĜĝĞğ  !"# $%&' ()*+ ,-./ 0123 4567 89:; <=>? @ABC DEFG HIJK LMNO PQRS TUVW XYZ[
 736: \]^_ `abc defg hijk lmno pqrs tuvw xyz{ |}~ſ ƀƁƂƃ ƄƅƆƇ ƈƉƊƋ ƌƍƎƏ ƐƑƒƓ ƔƕƖƗ Ƙƙƚƛ ƜƝƞƟ ƠơƢƣ ƤƥƦƧ ƨƩƪƫ ƬƭƮƯ ưƱƲƳ ƴƵƶƷ
1472: Ƹƹƺƻ Ƽƽƾƿ ǀǁǂǃ ǄǅǆǇ ǈǉǊǋ ǌǍǎǏ ǐǑǒǓ ǔǕǖǗ ǘǙǚǛ ǜǝǞǟ ǠǡǢǣ ǤǥǦǧ ǨǩǪǫ ǬǭǮǯ ǰǱǲǳ ǴǵǶǷ ǸǹǺǻ ǼǽǾÿ                         
]
"""
        )

    def test_group_size_errors(self):
        a = Bits.from_zeros(120)
        with pytest.raises(ValueError):
            a.pp("hex:3")
        with pytest.raises(ValueError):
            a.pp("hex:4, oct")

    def test_zero_group_size(self):
        a = Bits.from_zeros(600)
        s = io.StringIO()
        a.pp("bin0", stream=s, show_offset=False)
        expected_output = """<Bits, fmt='bin0', length=600 bits> [
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output

        a = Bits.from_zeros(400)
        s = io.StringIO()
        a.pp(stream=s, fmt="hex:0", show_offset=False, width=80)
        expected_output = """<Bits, fmt='hex0', length=400 bits> [
00000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000                                                            
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output

        s = io.StringIO()
        a = Bits(u=10, length=48)
        a.pp(stream=s, width=20, fmt="hex:0, oct:0", show_offset=False)
        expected_output = """<Bits, fmt='hex0, oct0', length=48 bits> [
000000 : 00000000
00000a : 00000012
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output

    def test_oct(self):
        a = Bits("0o01234567" * 20)
        s = io.StringIO()
        a.pp(stream=s, fmt="oct", show_offset=False, width=20)
        expected_output = """<Bits, fmt='oct', length=480 bits> [
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output

        t = io.StringIO()
        a.pp("hex, oct:0", width=1, show_offset=False, stream=t)
        expected_output = """<Bits, fmt='hex, oct0', length=480 bits> [
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
]
"""
        assert remove_unprintable(t.getvalue()) == expected_output

    def test_bytes(self):
        a = Bits.from_bytes(b"helloworld!!" * 5)
        s = io.StringIO()
        a.pp(stream=s, fmt="bytes", show_offset=False, width=48)
        expected_output = """<Bits, fmt='bytes', length=480 bits> [
hell owor ld!! hell owor ld!! hell owor ld!!
hell owor ld!! hell owor ld!!               
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output
        s = io.StringIO()
        a.pp(stream=s, fmt="bytes0", show_offset=False, width=40)
        expected_output = """<Bits, fmt='bytes0', length=480 bits> [
helloworld!!helloworld!!helloworld!!hell
oworld!!helloworld!!                    
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output

    def test_bool(self):
        a = Bits("0b1100")
        s = io.StringIO()
        a.pp(stream=s, fmt="bool", show_offset=False, width=20)
        expected_output = """<Bits, fmt='bool', length=4 bits> [
1 1 0 0
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output


class TestPrettyPrintingErrors:
    def test_wrong_formats(self):
        a = Bits("0x12341234")
        with pytest.raises(ValueError):
            a.pp("binary")
        with pytest.raises(ValueError):
            a.pp("bin, bin, bin")

    def test_interpret_problems(self):
        a = Bits.from_zeros(7)
        with pytest.raises(InterpretError):
            a.pp("oct")
        with pytest.raises(InterpretError):
            a.pp("hex")
        with pytest.raises(InterpretError):
            a.pp("bin, bytes")


class TestPrettyPrinting_NewFormats:
    def test_f_formats(self):
        a = Bits("f32=10.5")
        s = io.StringIO()
        a.pp("f32", stream=s)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='f32', length=32 bits> [
 0:                    10.5
]
"""
        )
        s = io.StringIO()
        a.pp("f16", stream=s)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='f16', length=32 bits> [
 0:                2.578125                     0.0
]
"""
        )

    def test_u(self):
        a = Bits().join([Bits(u=x, length=12) for x in range(40, 105)])
        s = io.StringIO()
        a.pp("u, hex12", stream=s)
        assert (
            remove_unprintable(s.getvalue())
            == """<Bits, fmt='u, hex12', length=780 bits> [
  0:   40   41   42   43   44   45   46   47   48   49   50   51 : 028 029 02a 02b 02c 02d 02e 02f 030 031 032 033
144:   52   53   54   55   56   57   58   59   60   61   62   63 : 034 035 036 037 038 039 03a 03b 03c 03d 03e 03f
288:   64   65   66   67   68   69   70   71   72   73   74   75 : 040 041 042 043 044 045 046 047 048 049 04a 04b
432:   76   77   78   79   80   81   82   83   84   85   86   87 : 04c 04d 04e 04f 050 051 052 053 054 055 056 057
576:   88   89   90   91   92   93   94   95   96   97   98   99 : 058 059 05a 05b 05c 05d 05e 05f 060 061 062 063
720:  100  101  102  103  104                                    : 064 065 066 067 068                            
]
"""
        )

    def test_i_and_f(self):
        a = BitArray(f=76.25, length=64) + "0b11111"
        s = io.StringIO()
        a.pp("i64, f", stream=s)
        assert (
            remove_unprintable(s.getvalue())
            == """<BitArray, fmt='i64, f', length=69 bits> [
 0:  4635066033680416768 :                    76.25
] + trailing_bits = 0b11111
"""
        )


class TestCopy:
    def test_copy_method(self):
        s = Bits("0xc00dee")
        t = s.copy()
        assert s == t


def test_native_endian_integer_dtypes_removed():
    for name in ["une", "ine"]:
        with pytest.raises(bitstring.CreationError):
            _ = Bits(**{name: 1}, length=16)
    for token in ["une16=454", "ine:64=-1000"]:
        with pytest.raises(bitstring.CreationError):
            _ = Bits(token)


def test_large_ints():
    s = Bits(i=-1, length=123)
    assert s.int == -1
    s = Bits(i=-1, length=201)
    assert s.int == -1
    s = Bits(u=12, length=201)
    assert s.uint == 12
