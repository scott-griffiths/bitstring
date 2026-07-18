#!/usr/bin/env python
"""
Module-level unit tests.
"""
import bitstring
import copy
import pickle
from collections import abc
import sys
import os


sys.path.insert(0, '..')
THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestModuleData:

    def test_all(self):
        exported = ['Reader', 'BitArray',
                    'Bits', 'pack', 'Error', 'ReadError', 'Array',
                    'InterpretError', 'ByteAlignError', 'CreationError', 'Dtype']
        assert set(bitstring.__all__) == set(exported)

    def test_pyproject_version(self):
        filename = os.path.join(THIS_DIR, '../pyproject.toml')
        try:
            with open(filename) as pyprojectfile:
                found = False
                for line in pyprojectfile.readlines():
                    if line.startswith("version"):
                        assert not found
                        assert bitstring.__version__ in line
                        found = True
            assert found
        except FileNotFoundError:
            pass  # Doesn't run on CI.

    def test_no_internal_names_in_namespace(self):
        # Only the public API and genuine submodules should be visible on the package.
        submodules = {'array_', 'bitarray_', 'bits', 'bitstore', 'bitstore_helpers',
                      'colour', 'dtypes', 'exceptions', 'fp8', 'helpers', 'luts', 'methods', 'mxfp',
                      'reader', 'utils'}
        public = {n for n in dir(bitstring) if not n.startswith('_')}
        unexpected = public - set(bitstring.__all__) - submodules
        assert unexpected == set()

    def test_tibs_does_not_leak_from_bitstore_layer(self):
        # Only the bitstore files should touch the .tibs attribute of the bitstore
        # classes - everything else should go through the bitstore interface.
        import re
        package_dir = os.path.dirname(bitstring.__file__)
        allowed = {'bitstore.py', 'bitstore_helpers.py'}
        for filename in sorted(os.listdir(package_dir)):
            if filename.endswith('.py') and filename not in allowed:
                with open(os.path.join(package_dir, filename)) as f:
                    source = f.read()
                assert re.search(r'\.tibs\b', source) is None, f"'.tibs' accessed in {filename}"

    def test_module_version_matches_pyproject_exactly(self):
        filename = os.path.join(THIS_DIR, '../pyproject.toml')
        try:
            with open(filename) as pyprojectfile:
                for line in pyprojectfile:
                    if line.startswith("version"):
                        pyproject_version = line.split("=", 1)[1].strip().strip('"')
                        assert bitstring.__version__ == pyproject_version
                        return
        except FileNotFoundError:
            pass  # Doesn't run on CI.


class TestCopy:
    def test_const_bit_array_copy(self):
        cba = bitstring.Bits.from_zeros(100)
        cba_copy = copy.copy(cba)
        assert cba is cba_copy

    def test_bit_array_copy(self):
        ba = bitstring.BitArray.from_zeros(100)
        ba_copy = copy.copy(ba)
        assert not ba is ba_copy
        assert not ba._bitstore is ba_copy._bitstore
        assert ba == ba_copy

    def test_reader_copy(self):
        bits = bitstring.Bits.from_zeros(100)
        r = bitstring.Reader(bits, 50)
        r_copy = copy.copy(r)
        assert r_copy.pos == 50
        assert r_copy.bits is bits


class TestPicklingAndDeepCopying:
    # Pickling supports multiprocessing and caching, and is also what deepcopy uses.

    def test_bits_roundtrips(self):
        for s in ['', '0b101', '0xabcde', '0xff, 0b1']:
            bits = bitstring.Bits(s) if s else bitstring.Bits()
            assert pickle.loads(pickle.dumps(bits)) == bits
            assert copy.deepcopy(bits) == bits

    def test_bitarray_roundtrips_and_is_independent(self):
        ba = bitstring.BitArray('0xff, 0b1')
        unpickled = pickle.loads(pickle.dumps(ba))
        assert unpickled == ba
        duplicate = copy.deepcopy(ba)
        duplicate.append('0b1')
        assert ba == '0xff, 0b1'
        assert duplicate == '0xff, 0b11'

    def test_dtype_roundtrips(self):
        for d in [bitstring.Dtype('u8'), bitstring.Dtype('ue'), bitstring.Dtype('bool'),
                  bitstring.Dtype('e3m2mxfp', scale=0.5)]:
            assert pickle.loads(pickle.dumps(d)) == d

    def test_array_roundtrips(self):
        a = bitstring.Array('u12', [1, 2, 3])
        assert pickle.loads(pickle.dumps(a)).equals(a)
        assert copy.deepcopy(a).equals(a)
        scaled = bitstring.Array(bitstring.Dtype('e3m2mxfp', scale=0.5), [2.0, 4.0])
        assert pickle.loads(pickle.dumps(scaled)).equals(scaled)

    def test_reader_roundtrips(self):
        r = bitstring.Reader(bitstring.Bits('0xabcd'), pos=4)
        for duplicate in [pickle.loads(pickle.dumps(r)), copy.deepcopy(r)]:
            assert duplicate.bits == r.bits
            assert duplicate.pos == 4
            assert duplicate.read('u4') == 0xb

    def test_file_backed_bits_roundtrip(self, tmp_path):
        filename = tmp_path / 'pickle.bin'
        filename.write_bytes(b'\x12\x34')
        bits = bitstring.Bits.from_file(filename)
        assert pickle.loads(pickle.dumps(bits)) == bits

    def test_deepcopy_of_container(self):
        d = {'a': bitstring.Bits('0b101'), 'b': [bitstring.BitArray('0xff')]}
        d_copy = copy.deepcopy(d)
        assert d_copy['a'] == d['a']
        assert d_copy['b'][0] == d['b'][0]


class TestInterning:
    def test_bits(self):
        a = bitstring.Bits('0xf')
        b = bitstring.Bits('0xf')
        assert a._bitstore is b._bitstore
        c = bitstring.Bits('0b1111')
        assert not a is c

    def test_bits_cache(self):
        a = bitstring.Bits('0b11000')
        b = bitstring.Bits('0b11000')
        assert a._bitstore is b._bitstore
        assert not a is b


class TestABCs:
    def test_base_classes(self):
        # The classes deliberately do not conform to the sequence ABCs.
        # see https://github.com/scott-griffiths/bitstring/issues/261
        bits = bitstring.Bits()
        assert not isinstance(bits, abc.Sequence)
        assert not isinstance(bits, abc.MutableSequence)

        bitarray = bitstring.BitArray()
        assert not isinstance(bitarray, abc.MutableSequence)
        assert not isinstance(bitarray, abc.Sequence)

        bitarray = bitstring.BitArray()
        assert not isinstance(bitarray, abc.MutableSequence)
        assert not isinstance(bitarray, abc.Sequence)


class TestNoFixedLengthPackingBug:

    def test_packing_bytes_with_no_length(self):
        a = bitstring.pack('bytes', b'abcd')
        assert a.bytes == b'abcd'

    def test_packing_bin_with_no_length(self):
        a = bitstring.pack('bin', '0001')
        assert a.bin == '0001'

    def test_packing_hex_with_no_length(self):
        a = bitstring.pack('hex', 'abcd')
        assert a.hex == 'abcd'

    def test_reading_bytes_with_no_length(self):
        a = bitstring.Reader(bitstring.Bits(b'hello'))
        b = a.read('bytes')
        assert b == b'hello'

    def test_reading_bin_with_no_length(self):
        a = bitstring.Reader(bitstring.Bits('0b1101'))
        b = a.read('bin')
        assert b == '1101'

    def test_reading_u_with_no_length(self):
        a = bitstring.Reader(bitstring.Bits('0b1101'))
        b = a.read('u')
        assert b == 13

    def test_reading_f_with_no_length(self):
        a = bitstring.Reader(bitstring.Bits(f=14, length=16))
        b = a.read('f')
        assert b == 14.0

    def test_pack_returns_bits(self):
        a = bitstring.pack('u8=1')
        assert type(a) is bitstring.Bits
