import pytest
import sys
import io
import bitstring as bs
from bitstring import Dtype
from bitstring.dtypes import DtypeDefinition, dtype_register

sys.path.insert(0, '..')


class TestBasicFunctionality:

    def test_setting_bool(self):
        b = Dtype('bool')
        assert str(b) == 'bool'
        assert b.name == 'bool'
        assert b.length == 1

        b2 = Dtype('bool:1')
        assert b == b2
        # self.assertTrue(b is b2)

    def test_reading(self):
        b = Dtype('u8')
        a = bs.Reader(bs.Bits('0xff00ff'))
        x = a.read_value(b)
        assert x == 255
        x = a.read_value(b)
        assert x == 0

    def test_setting_with_length(self):
        d = Dtype('uint', 12)
        assert str(d) == 'u12'
        assert d.length == 12
        assert d.name == 'u'

    def test_short_numeric_names_are_canonical(self):
        assert Dtype('uint12') == Dtype('u12')
        assert Dtype('int12') == Dtype('i12')
        assert Dtype('float16') == Dtype('f16')
        assert str(Dtype('uint12')) == 'u12'
        assert str(Dtype('int12')) == 'i12'
        assert str(Dtype('float16')) == 'f16'
        assert repr(Dtype('uint', 12)) == "Dtype('u', 12)"
        assert repr(Dtype('int', 12)) == "Dtype('i', 12)"
        assert repr(Dtype('float', 16)) == "Dtype('f', 16)"

    def test_short_endian_numeric_names_are_canonical(self):
        assert Dtype('uintbe16') == Dtype('ube16')
        assert Dtype('uintle16') == Dtype('ule16')
        assert Dtype('intbe16') == Dtype('ibe16')
        assert Dtype('intle16') == Dtype('ile16')
        assert Dtype('floatbe16') == Dtype('fbe16') == Dtype('f16')
        assert Dtype('floatle16') == Dtype('fle16')
        assert str(Dtype('uintbe16')) == 'ube16'
        assert str(Dtype('uintle16')) == 'ule16'
        assert str(Dtype('intbe16')) == 'ibe16'
        assert str(Dtype('intle16')) == 'ile16'
        assert str(Dtype('floatbe16')) == 'f16'
        assert str(Dtype('fbe16')) == 'f16'
        assert str(Dtype('floatle16')) == 'fle16'
        for token in ['uintne16', 'une16', 'intne16', 'ine16', 'floatne16', 'fne16']:
            with pytest.raises(ValueError):
                _ = Dtype(token)

    def test_short_endian_keyword_names_are_canonical(self):
        assert bs.Bits(ube=1, length=16) == bs.Bits(uintbe=1, length=16)
        assert bs.Bits(ule=1, length=16) == bs.Bits(uintle=1, length=16)
        assert bs.Bits(ibe=-1, length=16) == bs.Bits(intbe=-1, length=16)
        assert bs.Bits(ile=-1, length=16) == bs.Bits(intle=-1, length=16)
        assert bs.Bits(fbe=1.5, length=32) == bs.Bits(floatbe=1.5, length=32)
        assert bs.Bits(fle=1.5, length=32) == bs.Bits(floatle=1.5, length=32)
        for name in ['une', 'uintne', 'ine', 'intne', 'fne', 'floatne']:
            with pytest.raises(ValueError):
                _ = bs.Bits(**{name: 1}, length=16)

    def test_pack_errors(self):
        dtype = Dtype('uint8')
        value = 'not_an_integer'
        with pytest.raises(ValueError):
            dtype.pack(value)

    def test_pack(self):
        dtype = Dtype('se')
        x = dtype.pack(10001)
        assert x.se == 10001

    def test_unpack(self):
        dtype = Dtype('uint:12')
        x = dtype.unpack('0x3ff')
        assert x == 1023

    def test_old_pack_unpack_names_removed(self):
        assert not hasattr(Dtype, 'build')
        assert not hasattr(Dtype, 'parse')

    def test_dtype_callable_helpers_are_private(self):
        dtype = Dtype('u8')
        for attribute in ['get_fn', 'set_fn', 'read_fn']:
            with pytest.raises(AttributeError):
                getattr(dtype, attribute)
        assert dtype.pack(3) == bs.Bits('0x03')
        assert dtype.unpack('0x03') == 3
        reader = bs.Reader(bs.Bits.from_string('0x0304'))
        assert reader.read_value(dtype) == 3
        array = bs.Array(dtype, [3, 4])
        assert array.to_list() == [3, 4]
        output = io.StringIO()
        bs.Bits('0x03').pp('u8', stream=output, show_offset=False, color=False)
        assert '3' in output.getvalue()

    def test_immutability(self):
        d = Dtype('e3m2mxfp')
        with pytest.raises(AttributeError):
            d.length = 8
        with pytest.raises(AttributeError):
            d.name = 'uint8'

    def test_variable_lengths(self):
        d = Dtype('ue')
        a = bs.Reader(bs.Bits().join([d.pack(v) for v in [1, 100, 3, 17, 4]]))
        assert a.read_value(d) == 1
        assert a.read_value(d) == 100
        assert a.read_value(d) == 3
        assert a.read_value(d) == 17
        assert a.read_value(d) == 4

    def test_packing_bits(self):
        d = Dtype('bits3')
        a = d.pack('0b101')
        assert a == '0b101'
        with pytest.raises(ValueError):
            d.pack('0b1010')

    def test_packing_bin(self):
        d = Dtype('bin9')
        a = d.pack('0b000111000')
        assert a == '0b000111000'
        with pytest.raises(ValueError):
            d.pack('0b0001110000')

    def test_packing_ints(self):
        d = Dtype('i3')
        a = d.pack(-3)
        assert a == '0b101'
        with pytest.raises(ValueError):
            d.pack(4)


class TestRelengthingADtype:
    # Dtype(existing_dtype, length) re-lengths rather than dropping the length.

    def test_length_is_honoured(self):
        assert Dtype(Dtype('u8'), 16) == Dtype('u16')
        assert Dtype(Dtype('u8'), 16).length == 16
        assert Dtype(Dtype('u8'), 8) == Dtype('u8')

    def test_no_length_returns_the_same_object(self):
        d = Dtype('u8')
        assert Dtype(d) is d

    def test_the_new_length_is_validated(self):
        # Going back through the register means the same errors as any other length.
        with pytest.raises(ValueError):
            Dtype(Dtype('bool'), 8)
        with pytest.raises(ValueError):
            Dtype(Dtype('f32'), 12)
        with pytest.raises(ValueError):
            Dtype(Dtype('se'), 8)

    def test_length_is_in_the_dtype_own_units(self):
        # 'bytes' counts bytes, not bits, on both the old and new dtype.
        d = Dtype(Dtype('bytes2'), 4)
        assert d.length == 4
        assert d.bitlength == 32

    def test_a_relengthed_dtype_is_usable(self):
        assert bs.Bits('0xffff').unpack(Dtype(Dtype('u8'), 16)) == [65535]


class TestNonPropertyDtypes:
    # 'pad' is a format string directive rather than an interpretation, and the
    # property form of 'bits' would just be the identity, so neither appears in
    # the attribute namespace of Bits or BitArray.

    @pytest.mark.parametrize("attribute", ['pad', 'pad8', 'bits', 'bits8'])
    def test_not_readable_as_a_property(self, attribute):
        b = bs.Bits('0xff')
        assert not hasattr(b, attribute)
        with pytest.raises(AttributeError):
            getattr(b, attribute)

    @pytest.mark.parametrize("attribute", ['pad', 'bits'])
    def test_not_settable_as_a_property(self, attribute):
        b = bs.BitArray('0xff')
        with pytest.raises(AttributeError):
            setattr(b, attribute, '0x00')

    @pytest.mark.parametrize("keyword", ['pad', 'bits'])
    def test_not_usable_as_an_initialiser_keyword(self, keyword):
        with pytest.raises(ValueError):
            bs.Bits(**{keyword: 8})

    def test_still_usable_in_format_strings(self):
        # The dtypes themselves are unaffected - only the attribute access is gone.
        assert bs.Bits('0xff').unpack('bits8') == [bs.Bits('0xff')]
        assert bs.Bits('0xff').unpack('pad4, u4') == [15]
        assert bs.pack('u8, pad8, u8', 1, 2) == '0x010002'
        assert bs.Reader(bs.Bits('0xff')).read_value('pad4') is None
        assert Dtype('pad8').name == 'pad'
        assert Dtype('bits8').name == 'bits'

    def test_not_listed_in_the_property_docstring(self):
        for cls in (bs.Bits, bs.BitArray):
            if cls.__doc__ is not None:
                assert 'pad --' not in cls.__doc__
                assert 'bits --' not in cls.__doc__
                assert 'hex --' in cls.__doc__


class TestChangingTheRegister:

    def test_retrieving_meta_dtype(self):
        r = dtype_register
        u = r['uint']
        u2 = r['u']
        assert u == u2
        with pytest.raises(KeyError):
            i = r['integer']

    def test_removing_type(self):
        r = dtype_register
        bfloat = r['bfloat']
        del r['bfloat']
        with pytest.raises(KeyError):
            i = r['bfloat']
        with pytest.raises(KeyError):
            del r['penguin']
        r.add_dtype(bfloat)


class TestCreatingNewDtypes:

    def test_new_alias(self):
        dtype_register.add_dtype_alias('bin', 'cat')
        a = bs.BitArray('0b110110')
        r = bs.Reader(a)
        assert a.cat == '110110'
        assert r.read_value('cat4') == '1101'
        a.cat = '11110000'
        assert a.unpack('cat') == ['11110000']

    def test_new_type(self):
        md = DtypeDefinition('uint_r', bs.Bits._setuint, bs.Bits._getuint)
        dtype_register.add_dtype(md)
        a = bs.BitArray('0xf')
        assert a.uint_r == 15
        a.uint_r = 1
        assert a == '0x1'
        a += 'uint_r100=0'
        assert a == '0x1, 0b' + '0'*100

    def test_new_type_with_getter(self):
        def get_fn(bs):
            return bs.count(1)
        md = DtypeDefinition('counter', None, get_fn)
        dtype_register.add_dtype(md)
        a = bs.BitArray('0x010f')
        r = bs.Reader(a)
        assert a.counter == 5
        assert r.read_list('2*counter8') == [1, 4]
        assert a.unpack('counter7, counter') == [0, 5]
        with pytest.raises(AttributeError):
            a.counter = 4

    def test_invalid_dtypes(self):
        with pytest.raises(TypeError):
            _ = Dtype()
        with pytest.raises(ValueError):
            _ = Dtype('float17')
