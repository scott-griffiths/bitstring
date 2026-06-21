# LLM generated test cases
import bitstring


ConstBitStore = bitstring.bitstore.ConstBitStore
MutableBitStore = bitstring.bitstore.MutableBitStore


def test_mutable_bitstore_ilshift_keeps_binding_and_returns_self() -> None:
    bs = MutableBitStore.from_bin("1011")
    original_id = id(bs)

    bs <<= 1

    assert id(bs) == original_id
    assert bs.to_bin() == "0110"


def test_mutable_bitstore_irshift_keeps_binding_and_returns_self() -> None:
    bs = MutableBitStore.from_bin("1011")
    original_id = id(bs)

    bs >>= 1

    assert id(bs) == original_id
    assert bs.to_bin() == "0101"


def test_const_bitstore_eq_non_bitstore_returns_false() -> None:
    bs = ConstBitStore.from_bin("1")
    assert (bs == 1) is False


def test_mutable_bitstore_eq_non_bitstore_returns_false() -> None:
    bs = MutableBitStore.from_bin("1")
    assert (bs == 1) is False


def test_dtype_scaled_instances_compare_distinct() -> None:
    from bitstring.dtypes import Dtype

    a = Dtype("uint8", scale=2)
    b = Dtype("uint8", scale=3)

    assert a != b
    assert len({a, b}) == 2


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
        a = Array("uint8")
        a.fromfile(f, 2)

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
        a = Array("uint8")
        with pytest.raises(ValueError):
            a.fromfile(f, -1)


def test_dtype_ube_negative_length_rejected() -> None:
    from bitstring.dtypes import Dtype
    import pytest

    with pytest.raises(ValueError):
        _ = Dtype("ube", -8)


def test_pack_negative_repeat_factor_rejected() -> None:
    import pytest

    with pytest.raises(ValueError):
        _ = bitstring.pack("-2*uint:8")


def test_options_constructor_does_not_reset_singleton_state() -> None:
    from bitstring.bitstring_options import Options

    old_bytealigned = bitstring.options.bytealigned
    old_overflow = bitstring.options.mxfp_overflow
    try:
        bitstring.options.bytealigned = True
        bitstring.options.mxfp_overflow = "overflow"
        Options()
        assert bitstring.options.bytealigned is True
        assert bitstring.options.mxfp_overflow == "overflow"
    finally:
        bitstring.options.bytealigned = old_bytealigned
        bitstring.options.mxfp_overflow = old_overflow


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
        a = Array("uint8")
        with pytest.raises(EOFError):
            a.fromfile(f, 2)
        assert a.tolist() == [3]
