
import pytest
import sys
import bitstring as bs
from bitstring import Dtype, DtypeDefinition, Bits

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
        a = bs.BitStream('0xff00ff')
        x = a.read(b)
        assert x == 255
        x = a.read(b)
        assert x == 0

    def test_setting_with_length(self):
        d = Dtype('uint', 12)
        assert str(d) == 'uint12'
        assert d.length == 12
        assert d.name == 'uint'

    def test_build_errors(self):
        dtype = Dtype('uint8')
        value = 'not_an_integer'
        with pytest.raises(ValueError):
            dtype.build(value)

    def test_build(self):
        dtype = Dtype('se')
        x = dtype.build(10001)
        assert x.se == 10001

    def test_parse(self):
        dtype = Dtype('uint:12')
        x = dtype.parse('0x3ff')
        assert x == 1023

    def test_immutability(self):
        d = Dtype('e3m2mxfp')
        with pytest.raises(AttributeError):
            d.length = 8
        with pytest.raises(AttributeError):
            d.name = 'uint8'
        with pytest.raises(AttributeError):
            d.scale = 2

    def test_variable_lengths(self):
        d = Dtype('ue')
        a = bs.BitStream().join([d.build(v) for v in [1, 100, 3, 17, 4]])
        assert a.read(d) == 1
        assert a.read(d) == 100
        assert a.read(d) == 3
        assert a.read(d) == 17
        assert a.read(d) == 4
        a.pos = 0
        ds = Dtype('ue', scale=-3)
        assert a.read(ds) == -3
        assert a.read(ds) == -300
        assert a.read(ds) == -9
        assert a.read(ds) == -51
        assert a.read(ds) == -12

    def test_building_bits(self):
        d = Dtype('bits3')
        a = d.build('0b101')
        assert a == '0b101'
        with pytest.raises(ValueError):
            d.build('0b1010')

    def test_building_bin(self):
        d = Dtype('bin9')
        a = d.build('0b000111000')
        assert a == '0b000111000'
        with pytest.raises(ValueError):
            d.build('0b0001110000')

    def test_building_ints(self):
        d = Dtype('i3')
        a = d.build(-3)
        assert a == '0b101'
        with pytest.raises(ValueError):
            d.build(4)


class TestChangingTheRegister:

    def test_retrieving_meta_dtype(self):
        r = bs.dtype_register
        u = r['uint']
        u2 = r['u']
        assert u == u2
        with pytest.raises(KeyError):
            i = r['integer']

    def test_removing_type(self):
        r = bs.dtype_register
        del r['bfloat']
        with pytest.raises(KeyError):
            i = r['bfloat']
        with pytest.raises(KeyError):
            del r['penguin']


class TestCreatingNewDtypes:

    def test_new_alias(self):
        bs.dtype_register.add_dtype_alias('bin', 'cat')
        a = bs.BitStream('0b110110')
        assert a.cat == '110110'
        assert a.read('cat4') == '1101'
        a.cat = '11110000'
        assert a.unpack('cat') == ['11110000']

    def test_new_type(self):
        md = DtypeDefinition('uint_r', bs.Bits._setuint, bs.Bits._getuint)
        bs.dtype_register.add_dtype(md)
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
        bs.dtype_register.add_dtype(md)
        a = bs.BitStream('0x010f')
        assert a.counter == 5
        assert a.readlist('2*counter8') == [1, 4]
        assert a.unpack('counter7, counter') == [0, 5]
        with pytest.raises(AttributeError):
            a.counter = 4

    def test_invalid_dtypes(self):
        with pytest.raises(TypeError):
            _ = Dtype()
        with pytest.raises(ValueError):
            _ = Dtype('float17')
