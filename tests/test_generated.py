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
        def from_bytes(data, /, offset=None, length=None):
            calls.append(("Tibs", offset, length))
            return real_tibs.from_bytes(data, offset=offset, length=length)

    class RecordingMutibs:
        @staticmethod
        def from_bytes(data, /, offset=None, length=None):
            calls.append(("Mutibs", offset, length))
            return real_mutibs.from_bytes(data, offset=offset, length=length)

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
    assert calls == [("Tibs", 4, 12), ("Mutibs", 4, None)]

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


# Bits.__getattr__ raises AttributeError for a length mismatch so that hasattr() works,
# but that only covers names with a length in them, such as 'u16'. The bare names are
# real properties, and their length check used to come out as a ValueError that
# hasattr() and getattr() don't catch.

def test_hasattr_is_false_for_a_property_of_the_wrong_length() -> None:
    assert hasattr(bitstring.Bits("0b1"), "hex") is False


def test_hasattr_is_false_for_the_u_property_of_an_empty_bitstring() -> None:
    assert hasattr(bitstring.Bits(""), "u") is False


def test_getattr_default_is_used_for_a_property_of_the_wrong_length() -> None:
    assert getattr(bitstring.Bits("0b1"), "hex", "default") == "default"
    # The lengthed spelling of the same thing already behaves like this.
    assert getattr(bitstring.Bits("0b1"), "u16", "default") == "default"


def test_a_wrong_length_interpretation_is_still_a_value_error() -> None:
    # InterpretationError is both, so code that caught ValueError keeps working.
    with pytest.raises(ValueError):
        _ = bitstring.Bits("0b1").hex
    with pytest.raises(bitstring.InterpretationError):
        _ = bitstring.Bits("0b1").hex


@pytest.mark.parametrize("attribute", ["hex", "f", "bool", "bytes", "bfloat", "u16", "floatle"])
def test_wrong_length_properties_are_missing_rather_than_broken(attribute: str) -> None:
    # Three bits is a valid length for u, i and oct, but for none of these.
    b = bitstring.Bits("0b101")
    assert hasattr(b, attribute) is False
    assert getattr(b, attribute, None) is None


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
# Still open. The rest of the bug hunt, not yet fixed, so these fail.
# ---------------------------------------------------------------------------
# Lengths and integer values are pushed through int(), which truncates a float and
# parses a string, rather than rejecting either.

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
