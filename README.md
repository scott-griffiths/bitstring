

![bitstring](https://raw.githubusercontent.com/scott-griffiths/bitstring/main/doc/bitstring_logo_small.png "bitstring")

**bitstring** is a Python library to help make the creation and analysis of all types of bit-level binary data as simple and efficient as possible. It has been actively maintained since 2006.


[![CI badge](https://github.com/scott-griffiths/bitstring/actions/workflows/.github/workflows/ci.yml/badge.svg)](https://github.com/scott-griffiths/bitstring/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/readthedocs/bitstring?logo=readthedocs&logoColor=white)](https://bitstring.readthedocs.io/en/latest/)
[![Codacy Badge](https://img.shields.io/codacy/grade/8869499b2eed44548fa1a5149dd451f4?logo=codacy)](https://app.codacy.com/gh/scott-griffiths/bitstring/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Dependents](https://img.shields.io/librariesio/dependents/pypi/bitstring?logo=libraries.io&logoColor=white)](https://libraries.io/pypi/bitstring)
&nbsp; &nbsp;
[![Pepy Total Downloads](https://img.shields.io/pepy/dt/bitstring?logo=python&logoColor=white&labelColor=blue&color=blue)](https://www.pepy.tech/projects/bitstring)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/bitstring?label=%40&labelColor=blue&color=blue)](https://pypistats.org/packages/bitstring)

----

> [!NOTE]
> To see what's been added, improved or fixed, and also to see what's coming in the next version, see the [release notes](https://github.com/scott-griffiths/bitstring/blob/main/release_notes.md).

> [!IMPORTANT]
> The `main` branch now contains the upcoming bitstring 5.0 work. It is visible here for testing and feedback, but it is not the current released version. The released PyPI line is still bitstring 4.x; use `pip install bitstring` or pin `bitstring<5` for the stable API. Source maintenance for 4.x is on the `4.x-maintenance` branch.

# Version 5.0 preview

Version 5.0 of bitstring is in development. This is a major update with breaking changes.

Reasons to upgrade include:

* Significantly better performance using the new [tibs](https://github.com/scott-griffiths/tibs) Rust core.
* A simpler model for sequential reading: `Bits` and `BitArray` store data, while `Reader` stores the current bit position.
* A clearer, more explicit API for construction, conversion and dtype names.
* Removal of old compatibility layers, including the `bitarray` dependency, LSB0 mode and the old stream classes.
* A smaller internal codebase that should be easier to maintain and optimise further.

## Upgrading from version 4

Version 5 is worth moving to if you need the improved performance, want the cleaner current API, or want to keep up to
date with future bitstring development. The changes are quite broad, so if your existing code is stable and performance
is not a problem, there is no need to migrate immediately.

For details on the source changes you may need, see the [Upgrading to version 5](https://bitstring.readthedocs.io/en/latest/upgrading_to_version_5.html) guide.

## What's this 'tibs' thing that everyone is talking about?

bitstring 5 is built on [tibs](https://github.com/scott-griffiths/tibs), a simpler and more focussed Python library for
binary data, written in Rust for speed. It's by the same author as bitstring so they can complement each other's needs.
If you want a leaner interface and do not need all of bitstring's higher-level format handling and historical API, tibs may be a better fit for new code.

Tibs is still in beta but should hit 1.0 before bitstring 5.0 is released.
Please do try it, as all feedback is welcome.

<a href="https://github.com/scott-griffiths/tibs">
  <img src="https://raw.githubusercontent.com/scott-griffiths/tibs/main/doc/tibs.png" alt="tibs" width="30%">
</a>

A sleek Python library for binary data

----

# Bitstring Overview

* Efficiently store and manipulate binary data in idiomatic Python.
* Create bitstrings from hex, octal, binary, files, formatted strings, bytes, integers and floats of different endiannesses.
* Powerful binary packing and unpacking functions.
* Bit-level slicing, joining, searching, replacing and more.
* Create and manipulate arrays of fixed-length bitstrings.
* Read from and interpret bitstrings as streams of binary data.
* Rich API - chances are that whatever you want to do there's a simple and elegant way of doing it.
* Open source software, released under the MIT licence.

# Documentation

Extensive documentation for the bitstring library is available.
Some starting points are given below:

* [Released 4.x documentation](https://bitstring.readthedocs.io/en/stable/)
* [Upcoming 5.0 documentation](https://bitstring.readthedocs.io/en/latest/)
* [Upgrading from 4.x to 5.0](https://bitstring.readthedocs.io/en/latest/upgrading_to_version_5.html)

There is also an introductory walkthrough notebook for the 5.0 branch on [binder](https://mybinder.org/v2/gh/scott-griffiths/bitstring/main?labpath=doc%2Fwalkthrough.ipynb).

# Examples

These examples show the upcoming 5.0 API from `main`.


### Creation
```pycon
>>> from bitstring import Bits, BitArray, Reader, pack
>>> a = BitArray(bin='00101')
>>> b = Bits.from_file(a_file_object)
>>> c = BitArray('0xff, 0b101, 0o65, u6=22')
>>> d = pack('ile16, hex=a, 0b1', 100, a='0x34f')
>>> e = pack('<16h', *range(16))
```

### Different interpretations, slicing and concatenation
```pycon
>>> a = BitArray('0x3348')
>>> a.hex, a.bin, a.u, a.f, a.bytes
('3348', '0011001101001000', 13128, 0.2275390625, b'3H')
>>> a[10:3:-1].bin
'0101100'
>>> '0b100' + 3*a
BitArray('0x866906690669, 0b000')
```

### Reading data sequentially
```pycon
>>> b = Reader(Bits('0x160120f'))
>>> b.read(12).hex
'160'
>>> b.pos = 0
>>> b.read('u12')
352
>>> b.read_list('u12, bin3')
[288, '111']
```

### Searching, inserting and deleting
```pycon
>>> c = BitArray('0b00010010010010001111')   # c.hex == '0x1248f'
>>> c.find('0x48')
8
>>> c.replace('0b001', '0xabc')
>>> c.insert('0b0000', pos=3)
>>> del c[12:16]
```

### Arrays of fixed-length formats
```pycon
>>> from bitstring import Array
>>> a = Array('u7', [9, 100, 3, 1])
>>> a.data
BitArray('0x1390181')
>>> a[::2] *= 5
>>> a
Array('u7', [45, 100, 15, 1])
```


<sub>Copyright (c) 2006 - 2026 Scott Griffiths</sub>
