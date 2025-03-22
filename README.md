

![bitstring](https://raw.githubusercontent.com/scott-griffiths/bitstring/main/doc/bitstring_logo_small.png "bitstring")

**bitstring** is a Python library to help make the creation and analysis of all types of bit-level binary data as simple and efficient as possible. It has been actively maintained since 2006.

The library has has now been downloaded over 100 million times! &nbsp; &nbsp; ✨ [![Pepy Total Downloads](https://img.shields.io/pepy/dt/bitstring?label=Downloads:&labelColor=orange&color=orange)](https://www.pepy.tech/projects/bitstring) ✨



[![CI badge](https://github.com/scott-griffiths/bitstring/actions/workflows/.github/workflows/ci.yml/badge.svg)](https://github.com/scott-griffiths/bitstring/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/readthedocs/bitstring?logo=readthedocs&logoColor=white)](https://bitstring.readthedocs.io/en/latest/)
[![Codacy Badge](https://img.shields.io/codacy/grade/8869499b2eed44548fa1a5149dd451f4?logo=codacy)](https://app.codacy.com/gh/scott-griffiths/bitstring/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Dependents (via libraries.io)](https://img.shields.io/librariesio/dependents/pypi/bitstring?logo=libraries.io&logoColor=white)](https://libraries.io/pypi/bitstring)
&nbsp; &nbsp;
[![Pepy Total Downloads](https://img.shields.io/pepy/dt/bitstring?logo=python&logoColor=white&labelColor=blue&color=blue)](https://www.pepy.tech/projects/bitstring)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/bitstring?label=%40&labelColor=blue&color=blue)](https://pypistats.org/packages/bitstring)

----

> [!NOTE]
> To see what been added, improved or fixed, and also to see what's coming in the next version, see the [release notes](https://github.com/scott-griffiths/bitstring/blob/main/release_notes.md).


# Overview

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

* [Overview](https://bitstring.readthedocs.io/en/stable/index.html)
* [Quick Reference](https://bitstring.readthedocs.io/en/stable/quick_reference.html)
* [Full Reference](https://bitstring.readthedocs.io/en/stable/reference.html)

There is also an introductory walkthrough notebook on [binder](https://mybinder.org/v2/gh/scott-griffiths/bitstring/main?labpath=doc%2Fwalkthrough.ipynb).

# Examples

### Installation
```
$ pip install bitstring
```

### Creation
```pycon
>>> from bitstring import Bits, BitArray, BitStream, pack
>>> a = BitArray(bin='00101')
>>> b = Bits(a_file_object)
>>> c = BitArray('0xff, 0b101, 0o65, uint6=22')
>>> d = pack('intle16, hex=a, 0b1', 100, a='0x34f')
>>> e = pack('<16h', *range(16))
```

### Different interpretations, slicing and concatenation
```pycon
>>> a = BitArray('0x3348')
>>> a.hex, a.bin, a.uint, a.float, a.bytes
('3348', '0011001101001000', 13128, 0.2275390625, b'3H')
>>> a[10:3:-1].bin
'0101100'
>>> '0b100' + 3*a
BitArray('0x866906690669, 0b000')
```

### Reading data sequentially
```pycon
>>> b = BitStream('0x160120f')
>>> b.read(12).hex
'160'
>>> b.pos = 0
>>> b.read('uint12')
352
>>> b.readlist('uint12, bin3')
[288, '111']
```

### Searching, inserting and deleting
```pycon
>>> c = BitArray('0b00010010010010001111')   # c.hex == '0x1248f'
>>> c.find('0x48')
(8,)
>>> c.replace('0b001', '0xabc')
>>> c.insert('0b0000', pos=3)
>>> del c[12:16]
```

### Arrays of fixed-length formats
```pycon
>>> from bitstring import Array
>>> a = Array('uint7', [9, 100, 3, 1])
>>> a.data
BitArray('0x1390181')
>>> a[::2] *= 5
>>> a
Array('uint7', [45, 100, 15, 1])
```


<sub>Copyright (c) 2006 - 2025 Scott Griffiths</sub>
