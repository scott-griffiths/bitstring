# LLM generated test cases
import bitstring
from tibs import Mutibs
import pytest


ConstBitStore = bitstring.bitstore.ConstBitStore
MutableBitStore = bitstring.bitstore.MutableBitStore


def test_mutable_bitstore_ilshift_keeps_binding_and_returns_self() -> None:
    bs = MutableBitStore(Mutibs.from_bin("1011"))
    original_id = id(bs)

    bs <<= 1

    assert id(bs) == original_id
    assert bs.to_bin() == "0110"


def test_mutable_bitstore_irshift_keeps_binding_and_returns_self() -> None:
    bs = MutableBitStore(Mutibs.from_bin("1011"))
    original_id = id(bs)

    bs >>= 1

    assert id(bs) == original_id
    assert bs.to_bin() == "0101"


def test_const_bitstore_eq_non_bitstore_returns_false() -> None:
    bs = ConstBitStore.from_bin("1")
    assert (bs == 1) is False


def test_mutable_bitstore_eq_non_bitstore_returns_false() -> None:
    bs = MutableBitStore(Mutibs.from_bin("1"))
    assert (bs == 1) is False


def test_from_bytes_no_truncation_uses_tibs_fast_path(monkeypatch) -> None:
    calls = []
    real_tibs = bitstring.bitstore.Tibs
    real_mutibs = bitstring.bitstore.Mutibs

    class RecordingTibs:
        from_zeros = staticmethod(real_tibs.from_zeros)

        @staticmethod
        def from_bytes(data, /, bit_offset=None, bit_length=None):
            calls.append(("Tibs", bit_offset, bit_length))
            return real_tibs.from_bytes(data, bit_offset=bit_offset, bit_length=bit_length)

    class RecordingMutibs:
        @staticmethod
        def from_bytes(data, /, bit_offset=None, bit_length=None):
            calls.append(("Mutibs", bit_offset, bit_length))
            return real_mutibs.from_bytes(data, bit_offset=bit_offset, bit_length=bit_length)

    monkeypatch.setattr(bitstring.bitstore, "Tibs", RecordingTibs)
    monkeypatch.setattr(bitstring.bitstore, "Mutibs", RecordingMutibs)

    assert bitstring.Bits.from_bytes(b"\x12\x34") == "0x1234"
    assert bitstring.Bits.from_bytes(b"\x12\x34", offset=0) == "0x1234"
    assert bitstring.BitArray.from_bytes(b"\x12\x34") == "0x1234"
    assert bitstring.BitArray.from_bytes(b"\x12\x34", offset=0) == "0x1234"
    assert calls == [
        ("Tibs", None, None),
        ("Tibs", None, None),
        ("Mutibs", None, None),
        ("Mutibs", None, None),
    ]

    calls.clear()
    assert bitstring.Bits.from_bytes(b"\x12\x34", offset=4) == "0x234"
    assert bitstring.BitArray.from_bytes(b"\x12\x34", offset=4) == "0x234"
    assert calls == [("Tibs", 4, None), ("Mutibs", 4, None)]

    calls.clear()
    assert bitstring.Bits.from_bytes(b"\x12\x34", offset=0, length=8) == "0x12"
    assert bitstring.BitArray.from_bytes(b"\x12\x34", offset=0, length=8) == "0x12"
    assert calls == [("Tibs", 0, 8), ("Mutibs", 0, 8)]


def test_dtype_instances_compare_by_name_and_length() -> None:
    from bitstring.dtypes import Dtype

    a = Dtype("uint8")
    b = Dtype("uint16")

    assert a != b
    assert len({a, b}) == 2
    assert Dtype("uint8") == a
    assert len({a, Dtype("uint", 8)}) == 1


def test_dtype_ube_zero_length_rejected() -> None:
    from bitstring.dtypes import Dtype
    import pytest

    with pytest.raises(ValueError):
        _ = Dtype("ube0")


def test_array_fromfile_reads_from_current_file_position(tmp_path) -> None:
    from bitstring.array_ import Array

    p = tmp_path / "fromfile.bin"
    p.write_bytes(bytes([1, 2, 3, 4]))

    with p.open("rb") as f:
        f.seek(1)
        a = Array.from_file("uint8", f, 2)

    assert a.tolist() == [2, 3]


def test_pack_with_zero_repeated_group_needs_no_values() -> None:
    s = bitstring.pack("0*(uint:8)")
    assert len(s) == 0


def test_array_iadd_with_array_is_in_place() -> None:
    from bitstring.array_ import Array

    a = Array("int8", [1, 2])
    alias = a
    a += Array("int8", [3, 4])

    assert a is alias
    assert alias.tolist() == [4, 6]


def test_array_fromfile_negative_n_rejected(tmp_path) -> None:
    from bitstring.array_ import Array
    import pytest

    p = tmp_path / "fromfile_negative.bin"
    p.write_bytes(bytes([1, 2, 3]))

    with p.open("rb") as f:
        with pytest.raises(ValueError):
            _ = Array.from_file("uint8", f, -1)


def test_dtype_ube_negative_length_rejected() -> None:
    from bitstring.dtypes import Dtype
    import pytest

    with pytest.raises(ValueError):
        _ = Dtype("ube", -8)


def test_pack_negative_repeat_factor_rejected() -> None:
    import pytest

    with pytest.raises(ValueError):
        _ = bitstring.pack("-2*uint:8")


def test_options_object_removed() -> None:
    assert not hasattr(bitstring, "options")


def test_array_insert_very_negative_index_clamps_to_start() -> None:
    from bitstring.array_ import Array

    a = Array("uint8", [10, 20, 30])
    a.insert(-100, 5)
    assert a.tolist() == [5, 10, 20, 30]


def test_array_isub_with_array_is_in_place() -> None:
    from bitstring.array_ import Array

    a = Array("int8", [5, 7])
    alias = a
    a -= Array("int8", [2, 3])

    assert a is alias
    assert alias.tolist() == [3, 4]


def test_array_imul_with_array_is_in_place() -> None:
    from bitstring.array_ import Array

    a = Array("int8", [2, 3])
    alias = a
    a *= Array("int8", [4, 5])

    assert a is alias
    assert alias.tolist() == [8, 15]


def test_array_ifloordiv_with_array_is_in_place() -> None:
    from bitstring.array_ import Array

    a = Array("int8", [8, 15])
    alias = a
    a //= Array("int8", [2, 5])

    assert a is alias
    assert alias.tolist() == [4, 3]


def test_array_itruediv_with_array_is_in_place() -> None:
    from bitstring.array_ import Array

    a = Array("float16", [8.0, 15.0])
    alias = a
    a /= Array("float16", [2.0, 5.0])

    assert a is alias
    assert alias.tolist() == [4.0, 3.0]


def test_array_ilshift_with_array_is_in_place() -> None:
    from bitstring.array_ import Array

    a = Array("uint8", [1, 2])
    alias = a
    a <<= Array("uint8", [3, 2])

    assert a is alias
    assert alias.tolist() == [8, 8]


def test_array_irshift_with_array_is_in_place() -> None:
    from bitstring.array_ import Array

    a = Array("uint8", [16, 18])
    alias = a
    a >>= Array("uint8", [3, 1])

    assert a is alias
    assert alias.tolist() == [2, 9]


def test_array_imod_with_array_is_in_place() -> None:
    from bitstring.array_ import Array

    a = Array("uint8", [20, 19])
    alias = a
    a %= Array("uint8", [6, 7])

    assert a is alias
    assert alias.tolist() == [2, 5]


def test_array_fromfile_honours_current_position_for_eof(tmp_path) -> None:
    from bitstring.array_ import Array
    import pytest

    p = tmp_path / "fromfile_eof.bin"
    p.write_bytes(bytes([1, 2, 3]))

    with p.open("rb") as f:
        f.seek(2)
        with pytest.raises(EOFError):
            _ = Array.from_file("uint8", f, 2)


# ---------------------------------------------------------------------------
# From a bug hunt over the 5.0 API.
# ---------------------------------------------------------------------------


# Assigning to a dtype property goes through the property fset, which is the plain
# Bits._setX method, and those all assign an immutable store. A BitArray used to lose
# its mutable store that way, and every later mutating method failed on it.

def test_bitarray_is_still_mutable_after_setting_the_hex_property() -> None:
    b = bitstring.BitArray("0x00")
    b.hex = "ff"

    b.set(1, 0)
    assert b == "0xff"


def test_bitarray_is_still_mutable_after_setting_the_u_property() -> None:
    b = bitstring.BitArray("0x0000")
    b.u = 5

    b[0] = 1
    assert b == "0x8005"


def test_bitarray_is_still_mutable_after_setting_a_variable_length_property() -> None:
    b = bitstring.BitArray("0x00")
    b.ue = 5

    b.invert(0)
    assert b == "0b10110"


def test_setting_a_dtype_property_keeps_the_store_mutable() -> None:
    # The same fault stated directly: the store type must not change.
    b = bitstring.BitArray("0x00")
    before = type(b._bitstore)
    b.bin = "1010"
    assert type(b._bitstore) is before


# __eq__ promotes the other operand so that anything describing the same bits compares
# equal. A str that isn't a valid token used to raise ValueError out of the promotion
# rather than simply comparing unequal.

def test_equality_with_an_unparseable_string_is_false() -> None:
    assert (bitstring.Bits("0xff") == "hello") is False


def test_equality_with_a_valueless_token_string_is_false() -> None:
    # 'u8' parses as a token but has no value, so promotion raises rather than
    # reporting that the two objects simply aren't equal.
    assert (bitstring.Bits("0xff") == "u8") is False


def test_inequality_with_an_unparseable_string_is_true() -> None:
    assert (bitstring.Bits("0xff") != "hello") is True


def test_bitarray_equality_with_an_unparseable_string_is_false() -> None:
    assert (bitstring.BitArray("0xff") == "nope") is False


# A dtype attribute that can't be calculated for this bitstring is a ValueError: the
# attribute exists, the data just can't be read as it. An AttributeError is only for a
# name that isn't a dtype at all. This holds however the dtype is spelled, so the bare
# 'hex' and the lengthed 'u16' behave the same way.

@pytest.mark.parametrize("attribute", ["hex", "f", "bool", "bytes", "bfloat", "u16", "floatle"])
def test_a_property_that_cannot_be_calculated_is_a_value_error(attribute: str) -> None:
    # Three bits is a valid length for u, i and oct, but for none of these.
    b = bitstring.Bits("0b101")
    with pytest.raises(ValueError):
        _ = getattr(b, attribute)


def test_an_empty_bitstring_has_no_integer_value() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Bits("").u


def test_an_exp_golomb_property_of_the_wrong_data_is_a_value_error() -> None:
    # Nothing to do with the length here - 0xff just isn't a single code.
    with pytest.raises(ValueError):
        _ = bitstring.Bits("0xff").ue


@pytest.mark.parametrize("attribute", ["nonsense", "h12", "f256", "pad", "bits"])
def test_a_name_that_is_not_a_dtype_is_an_attribute_error(attribute: str) -> None:
    with pytest.raises(AttributeError):
        _ = getattr(bitstring.Bits("0xff"), attribute)


# Dtype.pack checks the result against the dtype's own length. Dtype.unpack used to
# check only the dtype class's allowed lengths, so a dtype would happily interpret a
# bitstring of a completely different length.

def test_dtype_unpack_rejects_data_longer_than_the_dtype() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Dtype("u8").unpack("0xffff")


def test_dtype_unpack_rejects_data_shorter_than_the_dtype() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Dtype("u8").unpack("0b1")


def test_dtype_unpack_of_a_float_uses_the_dtype_length() -> None:
    # 32 bits get read as a float32 by a Dtype that says it is 16 bits wide.
    with pytest.raises(ValueError):
        _ = bitstring.Dtype("f16").unpack(bitstring.Bits.from_zeros(32))


def test_dtype_unpack_and_pack_agree_about_length() -> None:
    d = bitstring.Dtype("hex8")
    packed = d.pack("ff")
    assert len(packed) == d.bitlength
    with pytest.raises(ValueError):
        _ = d.unpack("0xffff")


# byteswap() takes 'an iterable of integers', and iterates it once to validate it and
# again to total it. An iterator was empty by the second pass, so the call silently did
# nothing and reported zero repeats.

def test_byteswap_accepts_an_iterator_of_byte_sizes() -> None:
    from_list = bitstring.BitArray("0x00112233")
    from_iterator = bitstring.BitArray("0x00112233")

    list_repeats = from_list.byteswap([1, 3])
    iterator_repeats = from_iterator.byteswap(iter([1, 3]))

    assert iterator_repeats == list_repeats
    assert from_iterator == from_list


# overwrite() used to have no self-aliasing guard, so an internal assertion fired and a
# bare AssertionError reached the caller. insert() handles the same case by copying.

def test_overwrite_with_self_at_a_non_zero_position() -> None:
    a = bitstring.BitArray("0xab")
    a.overwrite(4, a)  # AssertionError
    assert a == "0xaab"


# A zero-length dtype used to pass Array's "must be fixed length" check, and then every
# operation divided by the item size. Array rejects variable length dtypes with a
# ValueError and now rejects these the same way.

@pytest.mark.parametrize("dtype", ["bin0", "hex0", "oct0", "bytes0", "bits0", "pad0"])
def test_array_rejects_a_zero_length_dtype(dtype: str) -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Array(dtype)


def test_read_array_with_a_zero_length_dtype() -> None:
    r = bitstring.Reader(bitstring.Bits("0xff"))
    with pytest.raises(ValueError):
        _ = r.read_array("bin0")
    assert r.pos == 0


def test_array_pp_with_a_zero_length_format(capsys) -> None:
    # Bits.pp('bin0') works - 0 means 'don't split into groups' - and the same
    # format used to divide by zero in Array.pp before it got that far.
    bitstring.Array("u8", [1, 2]).pp("bin0", color=False)
    assert "0000000100000010" in capsys.readouterr().out


def test_array_dtype_setter_rejects_a_zero_length_dtype() -> None:
    a = bitstring.Array("u8", [1, 2])
    with pytest.raises(ValueError):
        a.dtype = "bin0"
    with pytest.raises(ValueError):
        a.dtype = bitstring.Dtype("bin0")
    assert a.to_list() == [1, 2]


# Array's dtype validation used to run only on the string spelling. A Dtype object was
# stored without any check, so a variable length dtype got in and left an Array that
# raised from len(), to_list() and repr().

def test_array_rejects_a_variable_length_dtype_object() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Array(bitstring.Dtype("ue"))  # Array('ue') does raise


def test_array_dtype_setter_rejects_a_variable_length_dtype_object() -> None:
    a = bitstring.Array("u8", [1, 2])
    with pytest.raises(ValueError):
        a.dtype = bitstring.Dtype("ue")  # a.dtype = 'ue' does raise
    assert a.to_list() == [1, 2]


# ---------------------------------------------------------------------------
# The rest of the bug hunt. Three of these turned out to be deliberate behaviour
# rather than faults, and are pinned here so they don't get reported again.
# ---------------------------------------------------------------------------
# Lengths and integer values used to be pushed through int(), which truncates a float
# and parses a string rather than rejecting either.

def test_from_zeros_rejects_a_fractional_length() -> None:
    with pytest.raises(TypeError):
        _ = bitstring.Bits.from_zeros(3.7)  # currently makes 3 bits


def test_from_ones_rejects_a_fractional_length() -> None:
    with pytest.raises(TypeError):
        _ = bitstring.Bits.from_ones(3.7)


def test_from_zeros_rejects_a_string_length() -> None:
    with pytest.raises(TypeError):
        _ = bitstring.Bits.from_zeros("8")  # currently makes 8 bits


def test_array_from_zeros_rejects_a_fractional_item_count() -> None:
    with pytest.raises(TypeError):
        _ = bitstring.Array.from_zeros("u8", 2.7)


def test_uint_initialiser_rejects_a_fractional_value() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Bits(u=3.9, length=8)  # currently packs 3


def test_int_dtype_pack_rejects_a_fractional_value() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Dtype("u8").pack(3.9)


@pytest.mark.parametrize("dtype", ["u8", "i8", "ue", "u:8"])
def test_a_fractional_value_is_rejected_by_every_integer_route(dtype: str) -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Dtype(dtype).pack(3.9)


def test_integer_array_arithmetic_still_truncates() -> None:
    # Deliberate, and pinned by test_array.py: `a /= 2` on an integer dtype keeps the
    # whole part. The operators truncate before packing, so rejecting a fractional
    # value in the dtype itself doesn't change any of this.
    assert (bitstring.Array("int9", [-1, 0, 3]) * 2.5).to_list() == [-2, 0, 7]
    a = bitstring.Array("i21", [-5, -4, 0, 2, 100])
    a /= 2
    assert a.to_list() == [-2, -2, 0, 1, 50]
    assert (bitstring.Array("i16", [5]) / bitstring.Array("i16", [2])).to_list() == [2]
    # A float dtype keeps the fraction, as it always did.
    assert (bitstring.Array("f16", [5.0]) / 4).to_list() == [1.25]


# The 'bits' dtype declares a return_type of Bits, and unpack()/read_value() give a
# Bits. Array reads through its own BitArray buffer, so its elements come out mutable.

def test_array_bits_elements_have_the_dtype_return_type() -> None:
    a = bitstring.Array("bits8", [bitstring.Bits("0xff")])
    assert type(a[0]) is bitstring.Dtype("bits8").return_type
    assert type(a.to_list()[0]) is bitstring.Bits


# append() and extend() refuse to work on an Array whose data isn't a whole number of
# items, but insert() is documented as still working and leaving the trailing bits
# alone. Pinning that, as it looks like an inconsistency until you read doc/array.rst.

def test_array_insert_works_with_trailing_bits() -> None:
    a = bitstring.Array("u8", [1, 2], trailing_bits="0b1")
    a.insert(1, 9)
    assert a.to_list() == [1, 9, 2]
    assert a.trailing_bits == "0b1"
    with pytest.raises(ValueError):
        a.append(3)
    with pytest.raises(ValueError):
        a.extend([3])


# The literal prefix is treated as noise and removed wherever it appears, not just at
# the front. That makes the '0x55' * 10 idiom work and is what test_bits.py pins with
# Bits(hex='0x0x0X') == Bits(); it reads like a bug until you find those, so pin it here
# too rather than flagging it again.

@pytest.mark.parametrize("literal", ["0x55", "0b101", "0o77"])
def test_a_repeated_literal_is_one_bitstring(literal: str) -> None:
    assert bitstring.Bits(literal * 10) == bitstring.Bits(literal) * 10


@pytest.mark.parametrize("kwargs, expected", [({"hex": "0x0x0"}, "0x0"), ({"hex": "ff0x"}, "0xff"),
                                              ({"bin": "10b1"}, "0b11"), ({"oct": "70o7"}, "0o77")])
def test_a_repeated_prefix_is_dropped_rather_than_rejected(kwargs: dict, expected: str) -> None:
    assert bitstring.Bits(**kwargs) == bitstring.Bits(expected)


# unpack() accepts a Dtype wherever it accepts a format string; pack() only accepts
# strings, and an unhelpful TypeError comes out of trying to iterate the Dtype.

def test_pack_accepts_a_dtype_like_unpack_does() -> None:
    assert bitstring.pack(bitstring.Dtype("u8"), 5) == "0x05"


def test_pack_accepts_a_list_of_dtypes_like_unpack_does() -> None:
    assert bitstring.pack([bitstring.Dtype("u8"), bitstring.Dtype("u8")], 1, 2) == "0x0102"


# set() and invert() take 'either a single bit position or an iterable of bit
# positions'. all() and count()'s sibling any() take only the iterable form.

def test_all_accepts_a_single_position_like_set_does() -> None:
    assert bitstring.Bits("0xff").all(1, 0) is True


def test_any_accepts_a_single_position_like_set_does() -> None:
    assert bitstring.Bits("0xff").any(1, 0) is True


# ---------------------------------------------------------------------------
# From a review of the 5.0 code in October 2026.
# ---------------------------------------------------------------------------


# insert() turns a negative index into a bit position against the whole of the data,
# trailing bits included, so the new item lands part way through an existing one.

def test_array_insert_negative_index_with_trailing_bits() -> None:
    a = bitstring.Array("u8", [1, 2], trailing_bits="0xf")
    a.insert(-1, 99)
    assert a.to_list() == [1, 99, 2]  # currently [1, 6, 50]
    assert a.trailing_bits == "0xf"


# A memoryview is a bytes-like object, and bytes(mv) is its data whatever its format.
# tibs 2.0.1 read it item by item instead, which is only right for format 'B'. Fixed in
# tibs 2.0.2, which is now the minimum version.

def _non_byte_memoryviews() -> list:
    import array
    return [
        pytest.param(memoryview(array.array("H", [1, 2])), id="H-small"),  # currently 16 bits, no error
        pytest.param(memoryview(array.array("H", [1, 258])), id="H"),
        pytest.param(memoryview(array.array("b", [-1, 1])), id="b"),
        pytest.param(memoryview(b"ab").cast("c"), id="c"),
        pytest.param(memoryview(b"abcd").cast("B", (2, 2)), id="2d"),
        pytest.param(memoryview(array.array("d", [1.0])), id="d"),
    ]


@pytest.mark.parametrize("mv", _non_byte_memoryviews())
@pytest.mark.parametrize("cls", [bitstring.Bits, bitstring.BitArray])
def test_from_bytes_uses_the_bytes_of_a_non_byte_memoryview(cls, mv) -> None:
    assert cls.from_bytes(mv).to_bytes() == bytes(mv)


@pytest.mark.parametrize("mv", _non_byte_memoryviews())
def test_a_non_byte_memoryview_promotes_to_its_bytes(mv) -> None:
    assert bitstring.Bits(mv).to_bytes() == bytes(mv)


# Bits.from_bytes() works out the bits available from len(data), which for a memoryview
# counts items, not bytes. BitArray.from_bytes() leaves that to the store and is right.

@pytest.mark.parametrize("cls", [bitstring.Bits, bitstring.BitArray])
def test_from_bytes_offset_counts_the_bytes_of_a_memoryview(cls) -> None:
    import array
    mv = memoryview(array.array("H", [1, 258]))  # 4 bytes, but len(mv) == 2
    assert cls.from_bytes(mv, offset=4) == bitstring.Bits(bytes(mv))[4:]  # Bits currently gives 12 bits


@pytest.mark.parametrize("cls", [bitstring.Bits, bitstring.BitArray])
def test_from_bytes_length_counts_the_bytes_of_a_memoryview(cls) -> None:
    import array
    mv = memoryview(array.array("H", [1, 258]))
    assert cls.from_bytes(mv, length=24) == bitstring.Bits(bytes(mv))[:24]  # Bits currently raises


# An offset past the end of the data gives 'Negative bit length given: -4.' from Bits,
# a length the caller never passed. BitArray says what's actually wrong.

@pytest.mark.parametrize("cls", [bitstring.Bits, bitstring.BitArray])
def test_from_bytes_offset_past_the_end_names_the_offset(cls) -> None:
    with pytest.raises(ValueError, match="[Oo]ffset"):
        _ = cls.from_bytes(b"\x0f", offset=12)


# A dtype without a list of allowed lengths accepts a negative one, which then reads
# backwards or breaks len(). from_zeros() and friends already reject these.

@pytest.mark.parametrize("name", ["bin", "bytes", "bits"])
def test_dtype_negative_length_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Dtype(name, -1)


def test_unpack_with_a_negative_length_dtype_is_rejected() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Bits("0xff").unpack([bitstring.Dtype("bin", -1), "bin"])  # currently ['1111111', '1']


def test_array_with_a_negative_length_dtype_is_rejected() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Array.from_bytes(bitstring.Dtype("bytes", -1), b"abcd")


# A float length gets stored as a float, and only fails later with "'float' object
# cannot be interpreted as an integer" from wherever it's first used.

@pytest.mark.parametrize("length", [7.0, 8.5])
def test_dtype_float_length_rejected(length: float) -> None:
    with pytest.raises((TypeError, ValueError)):
        _ = bitstring.Dtype("u", length)  # 7.0 currently gives Dtype('u', 7.0)


def test_initialiser_float_length_rejected_with_a_clear_message() -> None:
    with pytest.raises((TypeError, ValueError), match="length"):
        _ = bitstring.Bits(u=3, length=6.0)


# Assigning an int to a slice works out the slice's length without its step, so a
# reversed slice looks empty.

def test_assigning_an_int_to_a_negative_step_slice() -> None:
    a = bitstring.BitArray("0x00")
    a[5:2:-1] = 1  # currently a ValueError about a zero length
    b = bitstring.BitArray("0x00")
    b[5:2:-1] = "0b001"
    assert a == b


# Smaller ones, where the expected behaviour is a judgement call.

# Array.from_file() reads an empty file as an empty Array, but Bits and BitArray fail on
# mmap's 'cannot mmap an empty file'. 4.x had the same failure.

@pytest.mark.parametrize("cls", [bitstring.Bits, bitstring.BitArray])
def test_from_file_reads_an_empty_file(cls, tmp_path) -> None:
    p = tmp_path / "empty.bin"
    p.write_bytes(b"")
    assert len(cls.from_file(p)) == 0


# cut() and split() are generators, so bad arguments only raise once iteration starts.
# findall() checks them at the call, as it isn't a generator itself.

def test_cut_rejects_a_bad_length_when_called() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Bits("0xff").cut(0)


def test_split_rejects_an_empty_delimiter_when_called() -> None:
    with pytest.raises(ValueError):
        _ = bitstring.Bits("0xff").split("")


# ---------------------------------------------------------------------------
# The bulk versions of operations that used to work an item or a byte at a time,
# each checked against a reference that does it the slow way.
# ---------------------------------------------------------------------------


def _random_array(seed: str, dtype: str, n: int, trailing: int = 0) -> bitstring.Array:
    import random
    rng = random.Random(seed)
    a = bitstring.Array(dtype)
    a.data = bitstring.BitArray.from_bools([rng.random() < 0.5 for _ in range(n * a.itemsize + trailing)])
    return a


def _items(a: bitstring.Array) -> list:
    """The raw bits of each whole item."""
    return [a.data[i * a.itemsize: (i + 1) * a.itemsize] for i in range(len(a))]


@pytest.mark.parametrize("op, dtype, n, trailing", [
    ("&", "u8", 7, 0),   # No trailing bits, so done on the Array's own buffer.
    ("|", "i5", 7, 3),   # Trailing bits, which both forms leave alone.
    ("^", "u3", 5, 2),
    ("&", "u8", 0, 0),   # Empty.
])
def test_array_bitwise_op_matches_per_item(op: str, dtype: str, n: int, trailing: int) -> None:
    import copy
    import operator
    fn, ifn = {"&": (operator.and_, operator.iand), "|": (operator.or_, operator.ior),
               "^": (operator.xor, operator.ixor)}[op]
    a = _random_array(op + dtype, dtype, n, trailing)
    value = bitstring.Bits("0b" + "10" * a.itemsize)[:a.itemsize]
    expected = bitstring.Bits.from_joined([fn(item, value) for item in _items(a)])
    original = a.data.copy()
    # Both forms leave any trailing bits alone.
    assert fn(a, value).data == expected + a.trailing_bits
    assert a.data == original
    b = copy.copy(a)
    data = b.data
    ifn(b, value)
    assert b.data == expected + a.trailing_bits
    if not trailing:
        assert b.data is data


@pytest.mark.parametrize("op, dtype, value", [
    ("+", "i12", -3), ("-", "u16", 1), ("*", "f32", 2.5), ("//", "i12", 2), ("/", "u16", 2),
    ("%", "i12", 5),
    ("//", "u8", 0),  # Every item fails, which has to be the same error either way.
])
def test_array_in_place_arithmetic_matches_out_of_place(op: str, dtype: str, value) -> None:
    import operator
    fn, ifn = {"+": (operator.add, operator.iadd), "-": (operator.sub, operator.isub),
               "*": (operator.mul, operator.imul), "//": (operator.floordiv, operator.ifloordiv),
               "/": (operator.truediv, operator.itruediv), "%": (operator.mod, operator.imod)}[op]
    a = bitstring.Array(dtype, [1, 5, 17, 100, 200])
    try:
        expected = fn(a, value)
    except ValueError as e:
        with pytest.raises(ValueError, match=str(e).split(":")[0]):
            ifn(a[:], value)
        return
    b = a[:]
    assert ifn(b, value) is b
    assert b.data == expected.data and b.dtype == expected.dtype


def test_array_in_place_arithmetic_keeps_a_nan_payload_like_out_of_place() -> None:
    # A signalling NaN used to lose its payload with += but not with +.
    a = bitstring.Array("f16")
    a.data = bitstring.BitArray("0xfd03, 0x3c00")
    b = a[:]
    b += 1000
    assert b.data == (a + 1000).data


@pytest.mark.parametrize("dtype, n", [("u8", 9), ("i5", 6), ("u8", 0)])
def test_array_reverse_matches_reversed_items(dtype: str, n: int) -> None:
    a = _random_array(dtype, dtype, n)
    expected = bitstring.Bits.from_joined(reversed(_items(a)))
    data = a.data
    a.reverse()
    assert a.data == expected
    assert a.data is data


def test_array_reverse_keeps_the_exact_bits_of_each_item() -> None:
    a = bitstring.Array("f16")
    a.data = bitstring.BitArray("0xfd03, 0x3c00, 0x7e01")  # Including NaNs with payloads.
    a.reverse()
    assert a.data == "0x7e01, 0x3c00, 0xfd03"


@pytest.mark.parametrize("n, key", [
    (9, slice(None, None, 2)),
    (9, slice(None, None, -1)),
    (9, slice(8, 1, -3)),
    (9, slice(100, -100, -4)),  # Out of range bounds are clamped.
    (9, slice(5, 5, 2)),        # Nothing picked.
    (0, slice(None, None, -1)),
])
def test_array_slice_matches_items_picked_one_at_a_time(n: int, key: slice) -> None:
    a = _random_array(str(key), "i5", n, trailing=3)  # The trailing bits are never picked.
    picked = a[key]
    assert picked.data == bitstring.Bits.from_joined(_items(a)[key])
    assert picked.dtype == a.dtype
    assert type(picked.data) is bitstring.BitArray


def _byteswap_reference(bits: bitstring.Bits, sizes: list, start: int, end: int, repeat: bool) -> tuple:
    """Swap one group of bytes at a time, as BitArray.byteswap() used to.

    Only whole patterns that finish by end are swapped, with or without repeat.
    """
    b = bitstring.BitArray(bits)
    total = 8 * sum(sizes)
    final = end if repeat else min(start + total, end)
    repeats = 0
    for pattern_end in range(start + total, final + 1, total):
        pos = pattern_end - total
        for size in sizes:
            if pos + 8 * size > len(b):
                raise ValueError("Swapping past the end of the bitstring.")
            b[pos: pos + 8 * size] = bitstring.Bits.from_bytes(b[pos: pos + 8 * size].to_bytes()[::-1])
            pos += 8 * size
        repeats += 1
    return repeats, b


@pytest.mark.parametrize("fmt, sizes, length, start, end, repeat", [
    (2, [2], 128, None, None, True),            # Equal groups repeated to the end.
    ([2, 2], [2, 2], 64, None, None, True),     # The same, given as a list.
    (3, [3], 65, None, None, True),             # The groups don't fill the bitstring.
    ("<2h", [2, 2], 40, 3, 59, True),           # A format string, from an unaligned start.
    (8, [8], 128, 8, 40, True),                 # The range is smaller than one group.
    (None, [5], 40, None, None, True),          # The whole bitstring.
    (2, [2], 40, None, None, False),            # A single swap that fits.
    (8, [8], 128, 8, 40, False),                # A single swap would pass end, so none is done.
    ("q", [8], 40, None, None, False),          # Likewise past the end of the data.
    ([1, 2], [1, 2], 65, None, None, True),     # Mixed sizes, which still go a group at a time.
    (">hhl", [2, 2, 4], 128, 1, None, True),
    (2, [2], 0, None, None, True),              # Empty.
])
def test_byteswap_matches_swapping_one_group_at_a_time(fmt, sizes, length, start, end, repeat) -> None:
    bits = bitstring.Bits("0b" + "1101001" * 20)[:length]
    s, e, _ = slice(start, end).indices(length)
    try:
        expected_repeats, expected = _byteswap_reference(bits, sizes, s, max(s, e), repeat)
    except ValueError:
        with pytest.raises(ValueError):
            bitstring.BitArray(bits).byteswap(fmt, start, end, repeat)
        return
    b = bitstring.BitArray(bits)
    assert b.byteswap(fmt, start, end, repeat) == expected_repeats
    assert b == expected


@pytest.mark.parametrize("dtype", ["u24", "f64"])
def test_array_byteswap_reverses_the_bytes_of_each_item(dtype: str) -> None:
    a = _random_array(dtype, dtype, 9)
    expected = bitstring.Bits.from_joined(bitstring.Bits.from_bytes(item.to_bytes()[::-1]) for item in _items(a))
    a.byteswap()
    assert a.data == expected


@pytest.mark.parametrize("cls", [bitstring.Bits, bitstring.BitArray])
def test_reading_exp_golomb_codes_in_place(cls) -> None:
    import random
    rng = random.Random(0)
    kinds = [rng.choice(["ue", "se", "uie", "sie"]) for _ in range(30)]
    values = [rng.randint(0, 500) if k in ("ue", "uie") else rng.randint(-500, 500) for k in kinds]
    data = bitstring.Bits.from_joined(bitstring.Bits(**{k: v}) for k, v in zip(kinds, values))
    r = bitstring.Reader(cls(data + "0x00ff"))
    for k, v in zip(kinds, values):
        assert r.read_value(k) == v
    assert r.pos == len(data)
    assert cls(data).unpack(",".join(kinds)) == values


@pytest.mark.parametrize("cls", [bitstring.Bits, bitstring.BitArray])
def test_a_truncated_exp_golomb_code_is_a_read_error_and_doesnt_move(cls) -> None:
    for kind in ("ue", "se", "uie", "sie"):
        r = bitstring.Reader(cls("0b1" + bitstring.Bits(**{kind: 37})[:-1]))
        assert r.read_value("ue") == 0
        with pytest.raises(bitstring.ReadError, match=f"'{kind}' code at bit position 1"):
            r.read_value(kind)
        assert r.pos == 1


def _native_int_dtype(typecode: str, bits: int) -> str:
    import sys
    endian = "le" if sys.byteorder == "little" else "be"
    return f"{'i' if typecode.islower() else 'u'}{endian}{bits}"


@pytest.mark.parametrize("typecode", ["l", "L"])
def test_array_extend_from_array_uses_its_real_item_size(typecode: str) -> None:
    import array
    values = [1, 2] if typecode == "L" else [1, -2]
    other = array.array(typecode, values)
    a = bitstring.Array(_native_int_dtype(typecode, other.itemsize * 8))
    a.extend(other)
    assert a.to_list() == values


@pytest.mark.parametrize("typecode", ["l", "L"])
def test_array_extend_from_array_rejects_a_different_item_size(typecode: str) -> None:
    import array
    other = array.array(typecode, [1, 2])
    wrong_bits = 32 if other.itemsize == 8 else 64
    a = bitstring.Array(_native_int_dtype(typecode, wrong_bits))
    with pytest.raises(ValueError):
        a.extend(other)
    assert len(a) == 0


@pytest.mark.parametrize("fmt", [4, "<hh", [1, 2]])
def test_byteswap_without_repeat_doesnt_swap_past_end(fmt) -> None:
    a = bitstring.BitArray("0x0102030405")
    assert a.byteswap(fmt, end=16, repeat=False) == 0
    assert a == "0x0102030405"


def test_byteswap_without_repeat_swaps_only_a_pattern_that_fits_before_end() -> None:
    a = bitstring.BitArray("0x0102030405")
    assert a.byteswap("<hh", end=24, repeat=False) == 0
    assert a == "0x0102030405"
    assert a.byteswap("<hh", end=32, repeat=False) == 1
    assert a == "0x0201040305"


@pytest.mark.parametrize("length", [8.7, 8.0, "8"])
def test_pack_rejects_a_keyword_length_that_isnt_an_integer(length) -> None:
    with pytest.raises(TypeError):
        bitstring.pack("u:n", 3, n=length)


def test_pack_not_enough_values_message_counts_only_tokens_that_take_values() -> None:
    with pytest.raises(ValueError, match=r"\b2 values"):
        bitstring.pack("0xff, u8, pad4, u8", 1)


def test_repr_of_every_dtype_definition() -> None:
    register = bitstring.dtypes.dtype_register
    for name in register.names:
        assert register[name].name in repr(register[name])


def test_bitarray_subclass_copy_keeps_its_type() -> None:
    import copy

    class MyBitArray(bitstring.BitArray):
        pass

    a = MyBitArray("0xf")
    for b in (a.copy(), copy.copy(a)):
        assert type(b) is MyBitArray
        assert b == a and b is not a


@pytest.mark.parametrize("op, iop", [("__and__", "__iand__"), ("__or__", "__ior__"), ("__xor__", "__ixor__"),
                                     ("__rand__", "__iand__"), ("__ror__", "__ior__"), ("__rxor__", "__ixor__")])
def test_array_bitwise_ops_keep_trailing_bits_like_the_in_place_ops(op: str, iop: str) -> None:
    a = bitstring.Array("u8", [1, 2], trailing_bits="0b11")
    result = getattr(a, op)("0x0f")
    assert result.trailing_bits == "0b11"
    in_place = bitstring.Array("u8", [1, 2], trailing_bits="0b11")
    getattr(in_place, iop)("0x0f")
    assert result.equals(in_place)
