import pytest

import bitstring
from bitstring import Array, BitArray, Bits, Dtype, Reader, pack


def test_creation_and_bits_property():
    bits = Bits("0x12345")
    r = Reader(bits, 4)
    assert r.bits is bits
    assert len(r) == 20
    assert r.pos == 4
    assert repr(r) == "Reader(<Bits of length 20 bits>, pos=4)"

    with pytest.raises(TypeError):
        Reader("0x234")
    with pytest.raises(TypeError):
        Reader(b"hello")


def test_bits_is_read_only():
    r = Reader(Bits("0x12345"))
    with pytest.raises(AttributeError):
        r.bits = BitArray("0xff")


def test_position_is_range_checked():
    r = Reader(Bits("0xf"))
    r.pos = 4
    assert r.pos == 4
    with pytest.raises(ValueError):
        r.pos = 5
    with pytest.raises(ValueError):
        r.pos = -1
    assert r.pos == 4

    with pytest.raises(ValueError):
        Reader(Bits("0xf"), pos=100)
    with pytest.raises(TypeError):
        r.pos = "4"


def test_byte_pos():
    r = Reader(Bits("0xff"), pos=3)
    with pytest.raises(ValueError):
        _ = r.byte_pos
    r.pos = 8
    assert r.byte_pos == 1

    r = Reader(Bits.from_zeros(64))
    r.byte_pos = 6
    assert r.pos == 48
    assert r.byte_pos == 6
    with pytest.raises(ValueError):
        r.byte_pos = 9


def test_remaining_and_at_end():
    r = Reader(Bits("0x160120f"), pos=12)
    assert r.remaining == 16
    assert not r.at_end
    r.pos += 16
    assert r.remaining == 0
    assert r.at_end


def test_read_value():
    r = Reader(Bits("0x12345"), 4)
    assert r.read_value("u4") == 2
    assert r.pos == 8
    assert r.read_value(Dtype("hex4")) == "3"
    assert r.pos == 12
    # An unsized dtype takes everything that is left.
    assert r.read_value("hex") == "45"
    assert r.pos == 20


def test_read_value_of_variable_length_dtype():
    r = Reader(Bits("ue=12, ue=3"))
    assert r.read_value("ue") == 12
    assert r.read_value("ue") == 3
    assert r.at_end


def test_read_value_rejects_multiple_dtypes():
    r = Reader(Bits("0x1234"))
    with pytest.raises(ValueError):
        r.read_value("u8, u8")
    assert r.pos == 0


def test_read_value_rejects_a_bit_count():
    r = Reader(Bits("0x1234"))
    with pytest.raises(TypeError):
        r.read_value(8)


def test_read_bits():
    r = Reader(Bits("0x160120f"))
    assert r.read_bits(12).hex == "160"
    assert r.pos == 12
    assert r.read_bits(0) == Bits()
    # Equivalent to the fixed-length bits dtype.
    r.pos = 0
    assert r.read_value("bits12").hex == "160"


def test_read_bits_rejects_a_bitstring():
    r = Reader(Bits("0x1234"))
    with pytest.raises(TypeError):
        r.read_bits(Bits("0x12"))
    with pytest.raises(ValueError):
        r.read_bits(-1)


def test_short_reads_raise_and_leave_pos_alone():
    r = Reader(Bits("0xff"), 4)
    for call in (lambda: r.read_bits(5),
                 lambda: r.read_value("u5"),
                 lambda: r.peek_value("u5"),
                 lambda: r.read_list("u2, u3")):
        with pytest.raises(bitstring.ReadError):
            call()
        assert r.pos == 4


def test_read_list():
    r = Reader(Bits("0b10001111001"))
    assert r.read_list("pad:1, uint:3, pad:4, uint:3") == [0, 1]
    assert r.pos == 11

    r.pos = 0
    assert r.read_list(["5", "3", 3]) == [Bits("0b10001"), Bits("0b111"), Bits("0b001")]
    assert r.pos == 11

    r = Reader(Bits("0x0102"))
    assert r.read_list("bits8, hex:b", b=4) == [Bits("0x01"), "0"]
    assert r.pos == 12


def test_read_array():
    r = Reader(Bits("0x0102030405"))
    assert r.read_array("u8", 3) == Array("u8", [1, 2, 3])
    assert r.pos == 24
    assert r.read_array("u8") == Array("u8", [4, 5])
    assert r.at_end


def test_read_array_leaves_a_partial_item():
    r = Reader(Bits("0x0102") + Bits("0b101"))
    assert r.read_array("u8") == Array("u8", [1, 2])
    assert r.remaining == 3


def test_read_array_errors():
    r = Reader(Bits("0x0102"))
    with pytest.raises(bitstring.ReadError):
        r.read_array("u8", 3)
    assert r.pos == 0
    with pytest.raises(ValueError):
        r.read_array("u8", -1)
    with pytest.raises(ValueError):
        r.read_array("ue", 2)


def test_peeking():
    r = Reader(Bits("0x01ff"))
    assert r.peek_value("u8") == 1
    assert r.pos == 0
    assert r.peek_bits(4).bin == "0000"
    assert r.pos == 0
    r.pos = 8
    assert r.peek_value("u8") == 255
    assert r.pos == 8


def test_bookmark():
    r = Reader(Bits("0x01ff02"))
    with r.bookmark() as same_reader:
        assert same_reader is r
        assert r.read_list("u8, u16") == [1, 65282]
        assert r.pos == 24
    assert r.pos == 0


def test_bookmark_restores_after_an_exception():
    r = Reader(Bits("0x01ff02"), pos=8)
    with pytest.raises(bitstring.ReadError):
        with r.bookmark():
            r.read_bits(8)
            r.read_bits(100)
    assert r.pos == 8


def test_align():
    r = Reader(Bits.from_zeros(64), pos=3)
    assert r.align() == 5
    assert r.pos == 8
    assert r.align() == 0
    assert r.align(32) == 24
    assert r.pos == 32

    with pytest.raises(ValueError):
        r.align(0)
    with pytest.raises(ValueError):
        r.align(-8)
    assert r.pos == 32


def test_align_past_the_end_raises():
    r = Reader(Bits("0b1"), pos=1)
    with pytest.raises(ValueError):
        r.align()
    assert r.pos == 1


def test_seek_to_and_seek_past():
    r = Reader(Bits("0xaabbcc00dd"))
    assert r.seek_to("0x00", byte_aligned=True) is True
    assert r.byte_pos == 3
    # A match under the cursor is found where it is.
    assert r.seek_to("0x00", byte_aligned=True) is True
    assert r.byte_pos == 3
    assert r.seek_past("0x00", byte_aligned=True) is True
    assert r.byte_pos == 4


def test_seek_past_makes_progress_in_a_loop():
    r = Reader(Bits("0x0000010c0000011f"))
    values = []
    while r.seek_past("0x000001", byte_aligned=True):
        values.append(r.read_value("u8"))
    assert values == [12, 31]


def test_seek_back_to():
    r = Reader(Bits("0x00ff00ff"), pos=32)
    assert r.seek_back_to("0xff") is True
    assert r.pos == 24
    assert r.seek_back_to("0xff") is True
    assert r.pos == 8
    assert r.seek_back_to("0xff") is False
    assert r.pos == 8


def test_a_missed_seek_returns_false_and_does_not_move():
    r = Reader(Bits("0b000111000111"), pos=5)
    assert r.seek_to("0b101") is False
    assert r.pos == 5
    assert r.seek_past("0b101") is False
    assert r.pos == 5
    assert r.seek_back_to("0b101") is False
    assert r.pos == 5


def test_seeks_search_forwards_from_pos_only():
    r = Reader(Bits("0b000111000111"), pos=5)
    assert r.seek_to("0b111") is True
    assert r.pos == 9


def test_searching_with_a_mask():
    r = Reader(Bits("0x1f2f3a"))
    assert r.seek_to("0x0f", byte_aligned=True, mask="0x0f") is True
    assert r.pos == 0
    assert r.seek_past("0x0f", byte_aligned=True, mask="0x0f") is True
    assert r.pos == 8
    assert r.seek_to("0x0f", byte_aligned=True, mask="0x0f") is True
    assert r.pos == 8
    r.pos = 16
    assert r.seek_to("0x0f", byte_aligned=True, mask="0x0f") is False


def test_search_arguments_can_be_positional():
    r = Reader(Bits("0x00aa"))
    assert r.seek_to("0xaa", True) is True
    assert r.pos == 8


def test_searching_rejects_empty_and_integer_needles():
    r = Reader(Bits("0x1234"))
    for call in (lambda bs: r.seek_to(bs),
                 lambda bs: r.seek_past(bs),
                 lambda bs: r.seek_back_to(bs),
                 lambda bs: r.read_to(bs),
                 lambda bs: r.read_past(bs)):
        with pytest.raises(ValueError):
            call(Bits())
        with pytest.raises(TypeError):
            call(4)


def test_read_to_and_read_past():
    r = Reader(Bits("0xaabbcc00dd"))
    assert r.read_to("0x00", byte_aligned=True).hex == "aabbcc"
    assert r.byte_pos == 3
    assert r.read_past("0x00", byte_aligned=True).hex == "00"
    assert r.byte_pos == 4

    r = Reader(Bits("0xaabb"))
    assert r.read_to("0xaa", byte_aligned=True) == Bits()
    assert r.pos == 0
    assert r.read_past("0xaa", byte_aligned=True) == "0xaa"
    assert r.byte_pos == 1


def test_a_missed_read_to_raises_and_does_not_move():
    r = Reader(Bits("0xaabb00aa00bb"), pos=8)
    with pytest.raises(bitstring.ReadError):
        r.read_to("0xcc", byte_aligned=True)
    assert r.pos == 8
    with pytest.raises(bitstring.ReadError):
        r.read_past("0xcc", byte_aligned=True)
    assert r.pos == 8


def test_from_file(tmp_path):
    path = tmp_path / "data.bin"
    path.write_bytes(b"\x01\x02\x03\x04")
    r = Reader.from_file(path)
    assert len(r) == 32
    assert r.pos == 0
    assert r.read_value("u16") == 258

    r = Reader.from_file(path, offset=8, length=8)
    assert len(r) == 8
    assert r.read_value("u8") == 2

    with open(path, "rb") as f:
        r = Reader.from_file(f)
    assert r.read_bits(8) == "0x01"


def test_mutable_bits_are_exposed_directly():
    bits = BitArray("0x00ff")
    r = Reader(bits)
    assert r.bits is bits
    assert r.read_value("u8") == 0
    assert r.pos == 8

    r.bits.append("0xff")
    assert bits == "0x00ffff"
    assert r.pos == 8
    assert r.read_value("u8") == 255


def test_reading_a_bitarray_that_has_shrunk():
    bits = BitArray("0x00ff")
    r = Reader(bits, pos=16)
    bits.clear()
    assert r.pos == 16
    with pytest.raises(bitstring.ReadError):
        r.read_bits(1)
    assert r.pos == 16
    assert r.remaining == 0
    assert r.at_end
    # A search clamps the stale position rather than raising.
    assert r.seek_to("0x00") is False


def test_reader_with_pack_result():
    bits = pack("uint8, uint8", 1, 2)
    assert type(bits) is Bits
    r = Reader(bits)
    assert r.read_value("uint8") == 1
    assert r.read_value("uint8") == 2


@pytest.mark.parametrize(
    "name",
    ["read", "readlist", "peek", "peek_list", "peeklist", "readto",
     "byte_align", "bytealign", "find", "rfind", "bitpos", "bytepos"],
)
def test_version_4_names_explain_themselves(name):
    r = Reader(Bits("0x1234"))
    with pytest.raises(AttributeError, match="bitstring 5"):
        getattr(r, name)


def test_unknown_attribute_still_raises_a_plain_error():
    r = Reader(Bits("0x1234"))
    with pytest.raises(AttributeError):
        r.no_such_thing
