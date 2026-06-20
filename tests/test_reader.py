import pytest

import bitstring
from bitstring import BitArray, Bits, Dtype, Reader, pack


def test_creation_and_bits_property():
    bits = Bits("0x12345")
    r = Reader(bits, 4)
    assert r.bits is bits
    assert len(r) == 20
    assert r.pos == 4
    assert repr(r) == "Reader(<Bits of length 20 bits>, pos=4)"

    mutable_bits = BitArray("0xff")
    r.bits = mutable_bits
    assert r.bits is mutable_bits
    assert r.pos == 4

    with pytest.raises(TypeError):
        Reader("0x234")
    with pytest.raises(TypeError):
        Reader(b"hello")
    with pytest.raises(TypeError):
        r.bits = "0xff"


def test_lax_position_storage():
    r = Reader(Bits("0xf"), pos=100)
    assert r.pos == 100
    with pytest.raises(ValueError):
        r.read(1)
    assert r.pos == 100

    r.pos = -10
    assert r.bitpos == -10
    with pytest.raises(ValueError):
        r.read(1)
    assert r.pos == -10

    r.bytepos = 6
    assert r.pos == 48
    assert r.bytepos == 6


def test_bytepos_requires_alignment():
    r = Reader(Bits("0xff"), pos=3)
    with pytest.raises(bitstring.ByteAlignError):
        _ = r.bytepos
    r.pos = 8
    assert r.bytepos == 1


def test_read_and_peek():
    r = Reader(Bits("0x12345"), 4)
    assert r.read(4) == "0x2"
    assert r.pos == 8
    assert r.read("u4") == 3
    assert r.pos == 12
    assert r.peek(Dtype("hex4")) == "4"
    assert r.pos == 12
    assert r.read("hex") == "45"
    assert r.pos == 20


def test_read_failure_restores_pos():
    r = Reader(Bits("0xff"), 4)
    with pytest.raises(bitstring.ReadError):
        r.read(5)
    assert r.pos == 4

    with pytest.raises(bitstring.ReadError):
        r.read("uint5")
    assert r.pos == 4

    with pytest.raises(bitstring.ReadError):
        r.peek("uint5")
    assert r.pos == 4


def test_readlist_and_peeklist():
    r = Reader(Bits("0b10001111001"))
    assert r.readlist("pad:1, uint:3, pad:4, uint:3") == [0, 1]
    assert r.pos == 11

    r.pos = 0
    assert r.readlist(["5", "3", 3]) == [Bits("0b10001"), Bits("0b111"), Bits("0b001")]
    assert r.pos == 11

    r = Reader(Bits("0x0102"))
    assert r.peeklist("bits8, hex:b", b=4) == [Bits("0x01"), "0"]
    assert r.pos == 0


def test_readto():
    r = Reader(Bits("0xaabb"))
    assert r.readto("0xaa", bytealigned=True) == "0xaa"
    assert r.bytepos == 1

    r = Reader(Bits("0xaabb00aa00bb"))
    assert r.readto("0x00", bytealigned=True) == "0xaabb00"
    assert r.bytepos == 3
    assert r.readto("0xaa", bytealigned=True) == "0xaa"

    old_pos = r.pos
    with pytest.raises(bitstring.ReadError):
        r.readto("0xcc", bytealigned=True)
    assert r.pos == old_pos

    with pytest.raises(ValueError):
        r.readto(4)


def test_bytealign():
    r = Reader(Bits("0xabcdef"), pos=3)
    assert r.bytealign() == 5
    assert r.pos == 8
    assert r.bytealign() == 0

    r = Reader(Bits("0b1"), pos=1)
    with pytest.raises(ValueError):
        r.bytealign()
    assert r.pos == 1


def test_find_and_rfind_update_pos_only_on_success():
    r = Reader(Bits("0b000111000111"), pos=5)
    assert r.find("0b111") == 3
    assert r.pos == 3
    assert r.find("0b101") is None
    assert r.pos == 3
    assert r.rfind("0b111") == 9
    assert r.pos == 9


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.find("0b1", 0),
        lambda r: r.rfind("0b1", 0),
        lambda r: r.readto("0b1", False),
    ],
)
def test_reader_optional_search_arguments_are_keyword_only(call):
    with pytest.raises(TypeError):
        call(Reader(Bits("0b1010")))


def test_mutable_bits_are_exposed_directly():
    bits = BitArray("0x00ff")
    r = Reader(bits)
    assert r.bits is bits
    assert r.read("u8") == 0
    assert r.pos == 8

    r.bits.append("0xff")
    assert bits == "0x00ffff"
    assert r.pos == 8
    assert r.read("u8") == 255

    bits.clear()
    assert r.pos == 16
    with pytest.raises(ValueError):
        r.read(1)
    assert r.pos == 16


def test_reader_with_pack_result():
    bits = pack("uint8, uint8", 1, 2)
    assert type(bits) is Bits
    r = Reader(bits)
    assert r.read("uint8") == 1
    assert r.read("uint8") == 2
